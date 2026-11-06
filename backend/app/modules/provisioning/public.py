"""
What other code may use from the control plane. No business module depends on
it — the Core calls it over HTTP; management commands use what is below.
"""

from app.modules.provisioning.model import CoreKey, CoreScope
from app.modules.provisioning.service.run_provisioning_job import (
    migrate_tenant_schema,
    read_schema_version,
)

__all__ = ["CoreKey", "CoreScope", "migrate_tenant_schema", "read_schema_version"]
