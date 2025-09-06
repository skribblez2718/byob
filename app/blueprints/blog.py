from __future__ import annotations

from flask import Blueprint

bp = Blueprint("blog", __name__)

import app.blueprints.view.user
