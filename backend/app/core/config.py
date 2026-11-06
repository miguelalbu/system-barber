from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "dev"

    # Runtime connects with a role without DDL — only DML on the tables it uses
    # (DEC-012). Its username is the role provisioning grants in each new schema.
    database_url: str = "postgresql+asyncpg://navalha_app:navalha_app@localhost:5433/navalha"
    # Migrations connect as the schema owner, which needs DDL privileges.
    database_url_migrations: str = "postgresql+asyncpg://navalha:navalha@localhost:5433/navalha"
    redis_url: str = "redis://localhost:6380/0"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    invite_expiry_days: int = 7

    # Each shop is served at <slug>.<base_domain>, or at its own domain
    # pointed here by CNAME (tenants.custom_domain).
    base_domain: str = "navalha.local"

    cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def dev(self) -> bool:
        return self.environment == "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
