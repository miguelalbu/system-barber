"""
Slug and schema name of a shop — the DDL injection boundary (doc §6).

The slug is the shop's subdomain (`<slug>.<base_domain>`), so it follows DNS
label rules: lowercase letters, digits and hyphens. The schema name is derived
from it **once**, at provisioning, stored in `tenants.schema_name` and read
from there forever. Underscores are not allowed in the slug, so replacing `-`
with `_` is injective: two slugs never map to one schema.
"""

from __future__ import annotations

import re

from app.core.database import assert_safe_schema_name

SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{1,38}[a-z0-9]$")

# Subdomains we serve ourselves, words that would read as ours, and `template`
# (the schema the tenant migration check runs against).
RESERVED_SLUGS = frozenset(
    {
        "www",
        "app",
        "api",
        "admin",
        "painel",
        "static",
        "assets",
        "core",
        "docs",
        "public",
        "template",
        "mail",
    }
)


class InvalidSlug(ValueError):
    pass


def validate_slug(value: str) -> str:
    slug = value.strip().lower()
    if not SLUG_RE.fullmatch(slug) or "--" in slug:
        raise InvalidSlug(
            "slug deve ter de 3 a 40 caracteres: letras minúsculas, números e hífen, "
            "começando por letra e sem hífen no fim ou repetido"
        )
    if slug in RESERVED_SLUGS:
        raise InvalidSlug("slug reservado")
    return slug


def schema_name_for(slug: str) -> str:
    """Only for provisioning. Everywhere else, read `tenants.schema_name`."""
    return assert_safe_schema_name("tenant_" + validate_slug(slug).replace("-", "_"))
