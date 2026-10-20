"""
Creates the first admin account, since public /auth/register can only
create 'applicant' accounts and the create-staff endpoint requires an
existing admin (chicken-and-egg problem on a fresh database).

Usage (from backend/, with the venv active and .env configured):
    python ../database/seeds/seed_admin.py admin@example.com "Admin Name" a-strong-password
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from app import create_app
from app.extensions import db
from app.models import User


def main():
    if len(sys.argv) != 4:
        print("Usage: python seed_admin.py <email> <full_name> <password>")
        sys.exit(1)

    email, full_name, password = sys.argv[1], sys.argv[2], sys.argv[3]

    app = create_app()
    with app.app_context():
        if User.query.filter_by(email=email).first():
            print(f"User {email} already exists -- nothing to do.")
            return

        user = User(email=email, full_name=full_name, role="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Created admin user: {email}")


if __name__ == "__main__":
    main()
