"""HTTP routes of the catalog, one file per resource. Thin: the service decides."""

from app.modules.catalog.router import barber_services, services

routers = [services.router, barber_services.router]
