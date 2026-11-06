"""HTTP routes of the control plane. Out of the public /docs (doc §6)."""

from app.modules.provisioning.router import tenants

routers = [tenants.router]
