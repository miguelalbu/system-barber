"""HTTP routes of the identity module, one file per resource. Thin: the service decides."""

from app.modules.identity.router import auth, barbers, settings, team, tenant, units

routers = [auth.router, tenant.router, units.router, settings.router, team.router, barbers.router]
