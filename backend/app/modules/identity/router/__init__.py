"""HTTP routes of the identity module, one file per resource. Thin: the service decides."""

from app.modules.identity.router import auth, barbers, team, tenant

routers = [auth.router, tenant.router, team.router, barbers.router]
