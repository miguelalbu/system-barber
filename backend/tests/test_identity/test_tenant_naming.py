"""The slug → schema guard: the DDL injection boundary (doc §6)."""

import pytest

from app.core.database import UnsafeSchemaName, assert_safe_schema_name, tenant_bind
from app.modules.identity.tenant_naming import InvalidSlug, schema_name_for, validate_slug


@pytest.mark.parametrize(
    ("slug", "schema"),
    [
        ("central", "tenant_central"),
        ("barbearia-do-ze", "tenant_barbearia_do_ze"),
        ("b2b", "tenant_b2b"),
        ("Central", "tenant_central"),  # normalized, not rejected
        ("a" * 40, "tenant_" + "a" * 40),
    ],
)
def test_valid_slugs_map_to_schema(slug, schema):
    assert schema_name_for(slug) == schema


@pytest.mark.parametrize(
    "slug",
    [
        "ab",  # too short
        "a" * 41,  # too long
        "1central",  # must start with a letter (and becomes a valid identifier)
        "central-",  # DNS label cannot end with a hyphen
        "cen--tral",  # repeated hyphen
        "cen_tral",  # underscore is not valid in a hostname (and keeps the mapping injective)
        "central.evil",
        "x'; DROP SCHEMA public CASCADE; --",
        'cen"tral',
        "çentral",
        "",
    ],
)
def test_invalid_slugs_are_rejected(slug):
    with pytest.raises(InvalidSlug):
        validate_slug(slug)


@pytest.mark.parametrize("slug", ["www", "api", "admin", "core", "public", "template"])
def test_reserved_slugs_are_rejected(slug):
    with pytest.raises(InvalidSlug, match="reservado"):
        validate_slug(slug)


@pytest.mark.parametrize(
    "schema",
    [
        "public",
        "tenant",
        "tenant_",
        "pg_catalog",
        'tenant_x"; DROP TABLE users; --',
        "TENANT_X",
        None,
    ],
)
def test_malicious_schema_name_from_the_database_never_reaches_sql(schema):
    """A corrupted `tenants.schema_name` fails here instead of becoming an identifier."""
    with pytest.raises(UnsafeSchemaName):
        assert_safe_schema_name(schema)
    with pytest.raises(UnsafeSchemaName):
        tenant_bind(schema)
