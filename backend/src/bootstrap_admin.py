"""
One-time bootstrap procedure to create or elevate the initial TradeRule AI Administrator.
Can be executed via CLI arguments or environment variables.

Usage:
    python backend/src/bootstrap_admin.py --email admin@example.com --password SecurePassword123! --name "Admin User"
Or:
    $env:BOOTSTRAP_ADMIN_EMAIL="admin@example.com"
    $env:BOOTSTRAP_ADMIN_PASSWORD="SecurePassword123!"
    python backend/src/bootstrap_admin.py
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add backend/src to path
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from auth import hash_password, validate_email_address, validate_password_strength
from db import User, create_user, get_db, get_user_by_email, init_db


def bootstrap_admin(
    email: str,
    password: str,
    name: str = "System Administrator",
    force: bool = False,
) -> None:
    # Initialize DB schema
    init_db()

    email = validate_email_address(email)
    validate_password_strength(password)

    db = next(get_db())
    try:
        # Check if any admin already exists
        existing_admins = db.query(User).filter(User.role == "admin").all()
        if existing_admins and not force:
            print(
                f"[INFO] An administrator already exists ({existing_admins[0].email}). "
                "Use --force if you intentionally wish to create or elevate another admin."
            )
            return

        existing_user = get_user_by_email(db, email)
        if existing_user:
            if existing_user.role == "admin":
                print(f"[INFO] User {email} is already an administrator.")
                return
            existing_user.role = "admin"
            existing_user.password_hash = hash_password(password)
            if name:
                existing_user.full_name = name
            db.commit()
            print(f"[SUCCESS] Existing user {email} successfully elevated to Administrator role.")
            return

        pwd_hash = hash_password(password)
        create_user(
            db=db,
            email=email,
            password_hash=pwd_hash,
            full_name=name,
            role="admin",
        )
        print(f"[SUCCESS] Administrator account created successfully for: {email}")

    finally:
        db.close()


def auto_bootstrap_admin_from_env() -> bool:
    """
    Attempt to bootstrap an initial administrator from environment variables.
    Safe for automated startup:
    - Exits quietly if no credentials configured.
    - Exits quietly if an administrator already exists.
    - Never logs passwords or secrets.
    """
    env_email = os.getenv("ADMIN_BOOTSTRAP_EMAIL") or os.getenv("BOOTSTRAP_ADMIN_EMAIL")
    env_password = os.getenv("ADMIN_BOOTSTRAP_PASSWORD") or os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
    env_name = os.getenv("ADMIN_BOOTSTRAP_NAME") or os.getenv("BOOTSTRAP_ADMIN_NAME", "TradeRule Administrator")

    if not env_email or not env_password:
        return False

    try:
        bootstrap_admin(
            email=env_email,
            password=env_password,
            name=env_name,
            force=False,
        )
        return True
    except Exception as exc:
        print(f"[WARN] Automatic administrator bootstrap skipped or failed: {exc}")
        return False


def main() -> None:
    env_email = os.getenv("ADMIN_BOOTSTRAP_EMAIL") or os.getenv("BOOTSTRAP_ADMIN_EMAIL")
    env_password = os.getenv("ADMIN_BOOTSTRAP_PASSWORD") or os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
    env_name = os.getenv("ADMIN_BOOTSTRAP_NAME") or os.getenv("BOOTSTRAP_ADMIN_NAME", "System Administrator")

    parser = argparse.ArgumentParser(description="Bootstrap TradeRule AI Administrator Account")
    parser.add_argument("--email", help="Admin email address", default=env_email)
    parser.add_argument("--password", help="Admin password", default=env_password)
    parser.add_argument("--name", help="Admin full name", default=env_name)
    parser.add_argument("--force", action="store_true", help="Force creation even if an admin exists")

    args = parser.parse_args()

    if not args.email or not args.password:
        print("[INFO] No administrator bootstrap credentials provided in environment or CLI flags.")
        print("[INFO] Skipping administrator bootstrap; existing users/admins remain unchanged.")
        return

    try:
        bootstrap_admin(
            email=args.email,
            password=args.password,
            name=args.name,
            force=args.force,
        )
    except Exception as exc:
        print(f"[ERROR] Failed to bootstrap administrator: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()

