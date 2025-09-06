from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

# SQLAlchemy 2.0 style

db: SQLAlchemy = SQLAlchemy()
migrate: Migrate = Migrate()
login_manager: LoginManager = LoginManager()
csrf: CSRFProtect = CSRFProtect()
cache: Cache = Cache()

# Rate limiter (IP-based)
limiter: Limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])
