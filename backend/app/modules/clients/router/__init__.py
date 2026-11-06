"""HTTP routes of the clients module. Thin: the service decides."""

from app.modules.clients.router import clients

routers = [clients.router]
