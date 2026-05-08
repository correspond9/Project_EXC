"""
Seed Script — Initial Admin User
==================================
Creates the first SUPER_ADMIN account in the database.

Usage (inside the running user-service container):
  docker-compose exec user-service python scripts/seed_admin.py

Or run it directly against a local Postgres instance:
  DATABASE_URL=postgresql+asyncpg://xchange:xchange@localhost:5432/xchange_db \
  python services/user-service/scripts/seed_admin.py

Environment variables:
  ADMIN_EMAIL     — email for the admin account (default: admin@xchange.local)
  ADMIN_PASSWORD  — password (default: ChangeMe123!)
  DATABASE_URL    — overrides the default connection string

The script is idempotent: running it a second time updates the password and
role of the existing account rather than creating a duplicate.
"""

import asyncio
import os
import sys
import uuid

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# ── Config ────────────────────────────────────────────────────────────────────

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://xchange:xchange@postgres:5432/xchange_db",
)

ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL",    "admin@xchange.local")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")

# ── Main ──────────────────────────────────────────────────────────────────────

async def seed() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()

    async with SessionLocal() as session:
        # Check if the account already exists
        result = await session.execute(
            text("SELECT id, role FROM users WHERE email = :email"),
            {"email": ADMIN_EMAIL},
        )
        existing = result.fetchone()

        if existing:
            # Update role and password — idempotent re-run
            await session.execute(
                text(
                    "UPDATE users "
                    "SET role = 'SUPER_ADMIN', "
                    "    password_hash = :ph, "
                    "    is_active = true, "
                    "    live_trading_enabled = true "
                    "WHERE email = :email"
                ),
                {"ph": password_hash, "email": ADMIN_EMAIL},
            )
            await session.commit()
            print(f"  ✓ Updated existing account '{ADMIN_EMAIL}' → role=SUPER_ADMIN")
        else:
            # Create brand-new SUPER_ADMIN account
            new_id = str(uuid.uuid4())
            await session.execute(
                text(
                    "INSERT INTO users "
                    "  (id, email, password_hash, role, trading_mode, kyc_status, "
                    "   is_active, live_trading_enabled) "
                    "VALUES "
                    "  (:id, :email, :ph, 'SUPER_ADMIN', 'SIMULATION', 'APPROVED', "
                    "   true, true)"
                ),
                {"id": new_id, "email": ADMIN_EMAIL, "ph": password_hash},
            )
            await session.commit()
            print(f"  ✓ Created SUPER_ADMIN account '{ADMIN_EMAIL}' (id={new_id})")

    await engine.dispose()

    print()
    print("  Login credentials")
    print(f"    Email    : {ADMIN_EMAIL}")
    print(f"    Password : {ADMIN_PASSWORD}")
    print()
    print("  ⚠  Change the password after your first login!")


if __name__ == "__main__":
    print()
    print("XChange — Admin Seed Script")
    print("=" * 40)
    asyncio.run(seed())
