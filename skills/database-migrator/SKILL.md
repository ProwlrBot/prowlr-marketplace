---
name: database-migrator
description: Use this skill when the user wants to run database migrations, manage schema changes, use alembic, upgrade or downgrade a database schema, or track schema versions.
---

# Database Migrator

## Overview

Manages database schema migrations safely: Alembic for SQLAlchemy projects, raw SQL with version tracking for others. Always backup before migrating, always support rollback.

## Alembic (SQLAlchemy Projects)

### Setup
```bash
pip install alembic sqlalchemy
alembic init migrations
# Edit migrations/env.py to set your DATABASE_URL and metadata
```

### Generate migration from model changes
```bash
alembic revision --autogenerate -m "add users table"
```

### Apply migrations
```bash
alembic upgrade head        # apply all pending
alembic upgrade +1          # apply next one
alembic downgrade -1        # roll back one
alembic downgrade base      # roll back everything
```

### Programmatic migration
```python
from alembic.config import Config
from alembic import command

def migrate(db_url: str, direction: str = "head") -> None:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)
    if direction == "head":
        command.upgrade(cfg, "head")
    elif direction.startswith("-") or direction.startswith("+"):
        command.upgrade(cfg, direction)
    else:
        command.downgrade(cfg, direction)
```

### Check current state
```python
def get_migration_status(db_url: str) -> dict:
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine
    engine = create_engine(db_url)
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        return {
            "current": ctx.get_current_revision(),
            "heads": ctx.get_current_heads(),
        }
```

## Raw SQL Migrations (Version Tracking Table)

```python
import sqlite3  # or psycopg2 / pymysql

def ensure_migrations_table(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def get_applied(conn) -> set[str]:
    return {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}

def apply_migration(conn, version: str, sql: str) -> None:
    applied = get_applied(conn)
    if version in applied:
        return
    conn.executescript(sql) if hasattr(conn, "executescript") else conn.execute(sql)
    conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
    conn.commit()
    print(f"Applied migration {version}")

# Usage:
MIGRATIONS = {
    "001_create_users": """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "002_add_name": "ALTER TABLE users ADD COLUMN name TEXT;",
}

def run_all(conn) -> None:
    ensure_migrations_table(conn)
    for version, sql in sorted(MIGRATIONS.items()):
        apply_migration(conn, version, sql)
```

## PostgreSQL with psycopg2

```python
import psycopg2

def pg_migrate(dsn: str, migration_sql: str) -> None:
    """Run a migration in a transaction — rolls back on error."""
    conn = psycopg2.connect(dsn)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(migration_sql)
        print("Migration applied.")
    except Exception as e:
        print(f"Migration FAILED, rolled back: {e}")
        raise
    finally:
        conn.close()
```

## Pre-Migration Backup

```python
import subprocess, datetime

def backup_postgres(dsn: str, output_dir: str = ".") -> str:
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"{output_dir}/backup_{stamp}.sql"
    subprocess.run(["pg_dump", dsn, "-f", out], check=True)
    return out

def backup_sqlite(db_path: str, output_dir: str = ".") -> str:
    import shutil, datetime
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"{output_dir}/backup_{stamp}.db"
    shutil.copy2(db_path, out)
    return out
```

## Quick Reference

| Task | Tool | Command |
|------|------|---------|
| Auto-gen migration | alembic | `alembic revision --autogenerate -m "..."` |
| Apply all | alembic | `alembic upgrade head` |
| Rollback one | alembic | `alembic downgrade -1` |
| Show history | alembic | `alembic history --verbose` |
| Current version | alembic | `alembic current` |
| Backup PostgreSQL | pg_dump | `pg_dump $DSN -f backup.sql` |
| Backup SQLite | shutil.copy2 | Copy the .db file |
