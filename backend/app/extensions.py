"""
Shared Flask extension instances, created here to avoid circular imports
between app/__init__.py and app/models/*.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate

db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
