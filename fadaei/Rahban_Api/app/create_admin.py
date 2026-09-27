"""
    python -m app.create_admin
"""

import getpass
import sys

from .auth import hash_password
from .database import SessionLocal
from .models import Admin


def create_admin() -> None:

    db = SessionLocal()

    try:
        username = input("Admin username: ").strip()

        if not username:
            print("Username cant be empty.")
            sys.exit(1)

        existing = (
            db.query(Admin)
            .filter(Admin.username == username)
            .first()
        )

        if existing is not None:
            print(f"'{username}' already exists.")
            sys.exit(1)

        password = getpass.getpass("Admin password: ")
        password_confirm = getpass.getpass("Confirm password: ")

        if password != password_confirm:
            print("Passwords dont match!")
            sys.exit(1)

        if len(password) < 8:
            print("Password must be at least 8 characters.")
            sys.exit(1)

        admin = Admin(
            username=username,
            password_hash=hash_password(password),
        )

        db.add(admin)
        db.commit()

        print(f"{username} created successfully")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
