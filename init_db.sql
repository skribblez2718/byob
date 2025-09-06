-- Bootstrap PostgreSQL for the blog app
-- Run as a PostgreSQL superuser (e.g., postgres)
-- Replace <STRONG_PASSWORD_HERE> before running.

-- 1) Create least-privileged role for the app
DO $$
BEGIN
   IF NOT EXISTS (
      SELECT 1 FROM pg_roles WHERE rolname = 'blog'
   ) THEN
      CREATE ROLE blog LOGIN PASSWORD '<STRONG_PASSWORD_HERE>';  -- CHANGE THIS
   END IF;
END $$;

-- 2) Create the database if it doesn't exist
SELECT 'CREATE DATABASE blog'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'blog')\gexec

-- 3) Connect to the database and set up schema
\c blog

-- Ensure the app role cannot create databases/schemas by default
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE blog FROM PUBLIC;

-- Allow the app role to connect to the DB
GRANT CONNECT ON DATABASE blog TO blog;

-- 3a) Create dedicated application schema
CREATE SCHEMA IF NOT EXISTS blog AUTHORIZATION blog;

-- 3b) Grant minimal privileges on the blog schema
GRANT USAGE ON SCHEMA blog TO blog;
GRANT CREATE ON SCHEMA blog TO blog;  -- needed so migrations can create tables

-- Privileges on existing tables and sequences in blog schema (noop initially)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA blog TO blog;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA blog TO blog;

-- Default privileges for future objects created in blog schema by the blog role
ALTER DEFAULT PRIVILEGES FOR ROLE blog IN SCHEMA blog
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO blog;
ALTER DEFAULT PRIVILEGES FOR ROLE blog IN SCHEMA blog
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO blog;

-- Set the search_path so unqualified table names map to the blog schema
ALTER DATABASE blog SET search_path = blog;
ALTER ROLE blog IN DATABASE blog SET search_path = blog;

-- Optional: Make the blog role the owner of the schema if you want it to manage migrations entirely
-- (This grants more power than least-privilege.)
-- ALTER SCHEMA public OWNER TO blog;
