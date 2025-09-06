from __future__ import annotations

from flask import Blueprint

bp = Blueprint("auth", __name__)

# Import refactored auth view routes
import app.blueprints.view.auth  # noqa: F401
