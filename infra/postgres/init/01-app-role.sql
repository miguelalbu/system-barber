-- Runtime role for the application.
--
-- It exists for one reason: superusers and table owners IGNORE Row-Level
-- Security. If the API connected as the administrative database user, the
-- per-tenant isolation policies would be worth nothing — every shop would see
-- every other shop.
--
-- This role is not a superuser, does not have BYPASSRLS, and does not own the
-- tables. Migrations keep running as the administrative user.

CREATE ROLE navalha_app WITH LOGIN PASSWORD 'navalha_app' NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;

GRANT CONNECT ON DATABASE navalha TO navalha_app;
GRANT USAGE ON SCHEMA public TO navalha_app;
