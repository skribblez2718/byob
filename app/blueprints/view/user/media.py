from __future__ import annotations

import hashlib
import io
from datetime import datetime

from flask import jsonify, send_file, make_response

from app.extensions import limiter
from app.repositories.blog import get_post_by_hex_id

from app.blueprints.blog import bp


@bp.get("/media/posts/<string:post_hex_id>")
@limiter.limit("300 per minute")
def media_post(post_hex_id: str):
    p = get_post_by_hex_id(post_hex_id)
    if not p or not getattr(p, "image_data", None) or not getattr(p, "image_mime", None):
        return jsonify({"error": "not_found"}), 404

    data = p.image_data
    mime = p.image_mime
    etag = hashlib.sha256(data).hexdigest()
    last_mod = getattr(p, "updated_at", None)
    resp = make_response(
        send_file(io.BytesIO(data), mimetype=mime, as_attachment=False, download_name=None)
    )
    resp.headers["Cache-Control"] = "public, max-age=3600"
    resp.headers["ETag"] = etag
    if isinstance(last_mod, datetime):
        resp.last_modified = last_mod
    return resp
