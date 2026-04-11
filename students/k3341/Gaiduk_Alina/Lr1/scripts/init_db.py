"""
Create application role and database without psql (uses psycopg).

From the Lr1 folder:
  py scripts/init_db.py

Requires in .env:
  POSTGRES_BOOTSTRAP_URL — superuser URL to database "postgres", e.g.
    postgresql+psycopg://postgres:YOUR_PASSWORD@127.0.0.1:5432/postgres

  If the password contains @ : # / etc., put it in POSTGRES_BOOTSTRAP_PASSWORD instead
  and keep the URL without a password segment, e.g.
    POSTGRES_BOOTSTRAP_URL=postgresql+psycopg://postgres@127.0.0.1:5432/postgres
    POSTGRES_BOOTSTRAP_PASSWORD=your real password

Optional:
  DATABASE_URL — if set, user/password/database are taken from here (defaults otherwise).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
import psycopg.conninfo
from dotenv import load_dotenv
from psycopg import sql
from sqlalchemy.engine.url import make_url


def _bootstrap_conninfo(bootstrap_url: str) -> str:
    """Build a libpq conninfo string; optional POSTGRES_BOOTSTRAP_PASSWORD overrides URL password."""
    url = make_url(bootstrap_url)
    override = os.getenv("POSTGRES_BOOTSTRAP_PASSWORD")
    if override is not None:
        url = url.set(password=override)
    kwargs: dict[str, object] = {
        "host": url.host or "127.0.0.1",
        "port": url.port or 5432,
        "user": url.username,
        "dbname": url.database or "postgres",
    }
    if url.password is not None:
        kwargs["password"] = url.password
    return psycopg.conninfo.make_conninfo(**kwargs)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")

    bootstrap = os.getenv("POSTGRES_BOOTSTRAP_URL")
    if not bootstrap:
        print(
            "POSTGRES_BOOTSTRAP_URL is not set in .env.\n"
            "Example (replace YOUR_PASSWORD with the postgres superuser password):\n"
            "  POSTGRES_BOOTSTRAP_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@127.0.0.1:5432/postgres",
            file=sys.stderr,
        )
        return 1

    app_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://app_user:app_password@127.0.0.1:5432/time_manager",
    )
    target = make_url(app_url)
    if not target.username or not target.database:
        print("DATABASE_URL must include username and database name.", file=sys.stderr)
        return 1

    user = target.username
    password = target.password or ""
    dbname = target.database

    admin = _bootstrap_conninfo(bootstrap)

    try:
        with psycopg.connect(admin, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (user,))
                if cur.fetchone() is None:
                    cur.execute(
                        sql.SQL("CREATE USER {} WITH PASSWORD {}").format(
                            sql.Identifier(user),
                            sql.Literal(password),
                        ),
                    )
                    print(f"Created role {user!r}.")
                else:
                    cur.execute(
                        sql.SQL("ALTER USER {} WITH PASSWORD {}").format(
                            sql.Identifier(user),
                            sql.Literal(password),
                        ),
                    )
                    print(f"Role {user!r} already existed; password updated.")

                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
                if cur.fetchone() is None:
                    cur.execute(
                        sql.SQL("CREATE DATABASE {} OWNER {}").format(
                            sql.Identifier(dbname),
                            sql.Identifier(user),
                        )
                    )
                    print(f"Created database {dbname!r} owned by {user!r}.")
                else:
                    print(f"Database {dbname!r} already exists (left unchanged).")
    except psycopg.OperationalError as e:
        msg = str(e).lower()
        print(f"Connection failed: {e}", file=sys.stderr)
        if "password" in msg or "авторизац" in msg or "authentication" in msg:
            print(
                "\nСкорее всего неверный пароль суперпользователя в .env.\n"
                "- Проверьте POSTGRES_BOOTSTRAP_URL (пароль после postgres: …).\n"
                "- Если забыли пароль postgres: сбросьте его в pgAdmin или переустановите правило в data/pg_hba.conf "
                "(учебный вариант — через установщик PostgreSQL / Stack Builder).\n"
                "- Если в пароле есть символы @ : # / и т.п., задайте пароль так:\n"
                "    POSTGRES_BOOTSTRAP_URL=postgresql+psycopg://postgres@127.0.0.1:5432/postgres\n"
                "    POSTGRES_BOOTSTRAP_PASSWORD=ваш пароль целиком",
                file=sys.stderr,
            )
        return 1

    print("Done. Run: py -m alembic upgrade head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
