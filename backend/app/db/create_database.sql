-- Creates the expense_tracker database and a least-privilege application role.
-- This script does not drop databases, roles, or data.
-- It stops without changes if either object already exists.
-- Run it as the PostgreSQL superuser. psql prompts for passwords locally.

\set ON_ERROR_STOP on

SELECT EXISTS (
    SELECT 1 FROM pg_roles WHERE rolname = 'expense_tracker_app'
) AS role_exists \gset

SELECT EXISTS (
    SELECT 1 FROM pg_database WHERE datname = 'expense_tracker'
) AS db_exists \gset

\if :role_exists
\echo 'Role expense_tracker_app already exists. No changes were made.'
\quit 1
\endif

\if :db_exists
\echo 'Database expense_tracker already exists. No changes were made.'
\quit 1
\endif

CREATE ROLE expense_tracker_app
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    NOBYPASSRLS;

-- Prompts twice on this console. The password is not stored in the script.
\password expense_tracker_app

CREATE DATABASE expense_tracker OWNER expense_tracker_app;

REVOKE ALL ON DATABASE expense_tracker FROM PUBLIC;
GRANT CONNECT ON DATABASE expense_tracker TO expense_tracker_app;
