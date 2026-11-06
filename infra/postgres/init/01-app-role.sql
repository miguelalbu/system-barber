-- Runtime role for the application.
--
-- The API never connects as the schema owner (DEC-012): this role has no DDL,
-- owns nothing, and only gets the DML each migration or provisioning job
-- grants it — on the control tables in `public` and inside each shop's
-- `tenant_<slug>` schema. A buggy raw query cannot create or drop anything.
-- Migrations and provisioning DDL run as the administrative user.

CREATE ROLE navalha_app WITH LOGIN PASSWORD 'navalha_app' NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;

GRANT CONNECT ON DATABASE navalha TO navalha_app;
GRANT USAGE ON SCHEMA public TO navalha_app;
