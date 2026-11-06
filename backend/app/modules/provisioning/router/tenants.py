"""
The control plane: `/core/*`, authenticated by `X-Core-Key`.

`include_in_schema=False` keeps these routes out of the public `/docs`:
publishing them there would tell everyone the control plane exists, where it
is and what it accepts. Their own OpenAPI is served at `/core/openapi.json`,
behind the key.
"""

from __future__ import annotations

import copy
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Response, status
from fastapi.openapi.utils import get_openapi

from app.modules.identity.public import TenantStatus
from app.modules.provisioning.dependencies import CoreCaller, core_caller
from app.modules.provisioning.model import CoreScope
from app.modules.provisioning.schemas import (
    CoreTenantDetail,
    CoreTenantOut,
    DestroyIn,
    InviteLinkOut,
    ProvisionAccepted,
    ProvisionIn,
)
from app.modules.provisioning.service.change_status import change_status
from app.modules.provisioning.service.destroy_tenant import destroy_tenant
from app.modules.provisioning.service.get_tenant import get_tenant as get_tenant_service
from app.modules.provisioning.service.list_tenants import list_tenants as list_tenants_service
from app.modules.provisioning.service.provision_tenant import provision_tenant
from app.modules.provisioning.service.reissue_invite import reissue_invite
from app.modules.provisioning.service.retry_job import retry_job
from app.modules.provisioning.service.run_provisioning_job import run_provisioning_job

router = APIRouter(prefix="/core", tags=["core"], include_in_schema=False)

Read = Annotated[CoreCaller, Depends(core_caller(CoreScope.TENANT_READ, write=False))]
Provision = Annotated[CoreCaller, Depends(core_caller(CoreScope.TENANT_PROVISION, write=True))]
Destroy = Annotated[CoreCaller, Depends(core_caller(CoreScope.TENANT_DESTROY, write=True))]


@router.post(
    "/tenants",
    response_model=ProvisionAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Provision a shop (async: 202 + job)",
)
async def provision(
    data: ProvisionIn,
    caller: Provision,
    response: Response,
    background: BackgroundTasks,
    idempotency_key: Annotated[str | None, Header(max_length=120)] = None,
):
    """
    Validates, records and answers **202** with the job; the work runs after
    the response. The same slug (or `Idempotency-Key`) again answers **200**
    with the existing job — never a second schema.
    """
    result = await provision_tenant(caller, data, idempotency_key)
    response.headers["Location"] = f"/core/tenants/{result.accepted.tenant_id}"
    if result.created:
        background.add_task(run_provisioning_job, result.accepted.job_id)
    else:
        response.status_code = status.HTTP_200_OK
    return result.accepted


@router.get("/tenants", response_model=list[CoreTenantOut], summary="Every shop")
async def list_tenants(caller: Read):
    return await list_tenants_service(caller)


@router.get(
    "/tenants/{tenant_id}",
    response_model=CoreTenantDetail,
    summary="A shop, its job, and the first-access link once",
)
async def get_tenant(tenant_id: uuid.UUID, caller: Read):
    return await get_tenant_service(caller, tenant_id)


@router.post(
    "/tenants/{tenant_id}/retry",
    response_model=ProvisionAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Resume a provisioning job that did not finish",
)
async def retry(tenant_id: uuid.UUID, caller: Provision, background: BackgroundTasks):
    accepted = await retry_job(caller, tenant_id)
    background.add_task(run_provisioning_job, accepted.job_id)
    return accepted


@router.post("/tenants/{tenant_id}/suspend", response_model=CoreTenantOut, summary="Suspend")
async def suspend(tenant_id: uuid.UUID, caller: Provision):
    return await change_status(caller, tenant_id, TenantStatus.SUSPENDED)


@router.post("/tenants/{tenant_id}/resume", response_model=CoreTenantOut, summary="Resume")
async def resume(tenant_id: uuid.UUID, caller: Provision):
    return await change_status(caller, tenant_id, TenantStatus.ACTIVE)


@router.post(
    "/tenants/{tenant_id}/invite",
    response_model=InviteLinkOut,
    summary="Reissue the owner's first-access link",
)
async def invite(tenant_id: uuid.UUID, caller: Provision):
    return await reissue_invite(caller, tenant_id)


@router.delete(
    "/tenants/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a suspended shop's data (scope tenant:destroy)",
)
async def destroy(tenant_id: uuid.UUID, data: DestroyIn, caller: Destroy):
    await destroy_tenant(caller, tenant_id, data)


def _documented(routes: list) -> list:
    """Copies flagged visible: get_openapi skips routes hidden from the public docs."""
    visible = []
    for route in routes:
        clone = copy.copy(route)
        clone.include_in_schema = True
        visible.append(clone)
    return visible


def core_openapi_schema() -> dict:
    schema = get_openapi(
        title="Navalha · Control plane",
        version="1.0.0",
        description="Called by the platform Core. Authenticate with the `X-Core-Key` header.",
        routes=_documented(router.routes),
    )
    schema.setdefault("components", {})["securitySchemes"] = {
        "CoreKey": {"type": "apiKey", "in": "header", "name": "X-Core-Key"}
    }
    schema["security"] = [{"CoreKey": []}]
    return schema


@router.get("/openapi.json", summary="OpenAPI of the control plane")
async def core_openapi(caller: Read):
    return core_openapi_schema()
