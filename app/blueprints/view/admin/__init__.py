from __future__ import annotations

# Import routes to register them with the existing admin blueprint
# Each module imports `bp` from app.blueprints.admin
from app.blueprints.view.admin import dashboard  # noqa: E402,F401
from app.blueprints.view.admin import category  # noqa: E402,F401
from app.blueprints.view.admin import post  # noqa: E402,F401
from app.blueprints.view.admin import resume  # noqa: E402,F401
from app.blueprints.view.admin import project  # noqa: E402,F401
