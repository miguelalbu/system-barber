"""The HTTP surface: OpenAPI wire schemas and every route's dependency chain."""

from __future__ import annotations

from fastapi.routing import APIRoute

from app.main import app
from app.modules.provisioning.router.tenants import core_openapi_schema
from tests.test_contracts._snapshot import assert_matches_snapshot


def _dependency_names(dependant) -> list[str]:
    """
    Names of every dependency a route resolves, depth first.

    `require(permission)` and `core_caller(scope)` return closures, so their name
    alone says nothing — what they guard is read from the closure and rendered as
    `require(team:manage)` or `core(tenant:provision)`. That is what makes a
    dropped or swapped guard fail this snapshot.
    """
    names: list[str] = []
    for dep in dependant.dependencies:
        call = dep.call
        if call is None:
            continue
        label = getattr(call, "__name__", type(call).__name__)
        for cell in getattr(call, "__closure__", None) or ():
            value = cell.cell_contents
            if type(value).__name__ == "Permission":
                label = f"require({value.value})"
            elif type(value).__name__ == "CoreScope":
                label = f"core({value.value})"
        names.append(label)
        names.extend(_dependency_names(dep))
    return names


def _api_routes(routes) -> list[APIRoute]:
    """
    Every APIRoute, including those of included routers.

    Since FastAPI 0.16x `include_router` keeps the router behind a wrapper with
    an `original_router` attribute instead of copying its routes into the app;
    older versions copy them. Both shapes are walked.
    """
    found: list[APIRoute] = []
    for route in routes:
        if isinstance(route, APIRoute):
            found.append(route)
        elif (inner := getattr(route, "original_router", None)) is not None:
            found.extend(_api_routes(inner.routes))
    return found


def test_openapi_schema_is_stable():
    assert_matches_snapshot("openapi", app.openapi())


def test_core_openapi_schema_is_stable():
    """The control plane's private contract with the platform Core."""
    assert_matches_snapshot("core_openapi", core_openapi_schema())


def test_route_table_with_guards_is_stable():
    routes = sorted(
        (
            {
                "path": route.path,
                "methods": sorted(route.methods),
                "status_code": route.status_code,
                "dependencies": _dependency_names(route.dependant),
            }
            for route in _api_routes(app.routes)
        ),
        key=lambda r: (r["path"], r["methods"]),
    )
    assert_matches_snapshot("routes", routes)
