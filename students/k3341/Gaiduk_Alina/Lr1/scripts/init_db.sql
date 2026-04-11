-- Option A — if psql is on PATH:
--   psql -U postgres -h 127.0.0.1 -f scripts/init_db.sql
-- Option B — without psql (from Lr1, .env with POSTGRES_BOOTSTRAP_URL):
--   py scripts/init_db.py
-- Password must match DATABASE_URL in your .env (default: app_password).

CREATE USER app_user WITH PASSWORD 'app_password';
CREATE DATABASE time_manager OWNER app_user;
