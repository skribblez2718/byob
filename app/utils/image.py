from __future__ import annotations

import io
import os
import secrets
import uuid
from typing import Tuple, Literal

from PIL import Image


ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP"}  # normalize JPG->JPEG
MAX_PIXELS = 20_000_000  # ~20MP safety cap

EXT_TO_FMT = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".webp": "WEBP",
}
FMT_TO_MIME = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "WEBP": "image/webp",
}
FMT_TO_DEFAULT_EXT = {
    "PNG": ".png",
    "JPEG": ".jpg",
    "WEBP": ".webp",
}


def _detect(image_bytes: bytes) -> tuple[str, int, int] | None:
    try:
        with Image.open(io.BytesIO(image_bytes)) as im:
            im.verify()  # header check
        with Image.open(io.BytesIO(image_bytes)) as im2:
            fmt = (im2.format or "").upper()
            w, h = im2.size
        if fmt == "JPG":
            fmt = "JPEG"
        return fmt, w, h
    except Exception:
        return None


def validate_image(data: bytes, max_bytes: int = 5 * 1024 * 1024) -> Tuple[bool, str | None, dict]:
    """Validate image bytes. Returns (ok, error, info). info: format,width,height."""
    if not data:
        return False, "empty_file", {}
    if len(data) > max_bytes:
        return False, "file_too_large", {"max_bytes": max_bytes}

    detected = _detect(data)
    if not detected:
        return False, "invalid_image", {}
    fmt, width, height = detected

    if fmt not in ALLOWED_FORMATS:
        return False, "unsupported_format", {"format": fmt}

    if width * height > MAX_PIXELS:
        return False, "too_many_pixels", {"width": width, "height": height}

    return True, None, {"format": fmt, "width": width, "height": height}


def rewrite_image(
    data: bytes,
    target_format: Literal["PNG", "JPEG", "WEBP"] | None = None,
    max_size: tuple[int, int] | None = None,
) -> tuple[bytes, str, str]:
    """Re-encode the image to destroy any embedded payloads and strip metadata.
    Returns (bytes, format, mime).
    Randomization is applied slightly to encoding params to avoid deterministic output while
    remaining visually identical.
    """
    detected = _detect(data)
    if not detected:
        raise ValueError("invalid_image")
    src_fmt, _, _ = detected

    fmt = target_format or src_fmt
    if fmt not in ALLOWED_FORMATS:
        fmt = "PNG"  # safest default

    # Small randomization knobs
    rand = secrets.randbelow(3)  # 0..2

    with Image.open(io.BytesIO(data)) as im:
        # Resize if needed
        if max_size and (im.width > max_size[0] or im.height > max_size[1]):
            im.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Convert modes for target formats
        if fmt in {"JPEG", "WEBP"}:
            if im.mode in ("RGBA", "LA"):
                # flatten alpha to white background
                bg = Image.new("RGB", im.size, (255, 255, 255))
                bg.paste(im, mask=im.split()[-1])
                im = bg
            elif im.mode != "RGB":
                im = im.convert("RGB")
        elif fmt == "PNG":
            if im.mode not in ("RGBA", "RGB", "LA", "L"):
                im = im.convert("RGBA")

        out = io.BytesIO()
        save_kwargs: dict = {"optimize": True}
        if fmt == "JPEG":
            # quality 84-86 range, subsampling auto; remove all exif/icc by not passing them
            save_kwargs.update({"quality": 85 + rand - 1})
        elif fmt == "WEBP":
            save_kwargs.update({"quality": 85 + rand - 1, "method": 5})
        elif fmt == "PNG":
            # compress_level 6-8
            save_kwargs.update({"compress_level": 6 + rand})

        im.save(out, format=fmt, **save_kwargs)
        rewritten = out.getvalue()

    mime = FMT_TO_MIME[fmt]
    return rewritten, fmt, mime


def validate_and_rewrite(
    data: bytes,
    original_filename: str | None = None,
    max_bytes: int = 5 * 1024 * 1024,
    max_size: tuple[int, int] | None = None,
) -> tuple[bool, str | None, dict, bytes | None, str | None, str | None, str | None]:
    """Full OWASP flow: validate, then re-encode to strip payloads.
    Returns (ok, error, info, rewritten_bytes, detected_format, suggested_ext, safe_filename).
    If extension mismatch is found, info["extension_mismatch"] is set with suggested ext.
    """
    ok, err, info = validate_image(data, max_bytes=max_bytes)
    if not ok:
        return False, err, info, None, None, None, None

    # Guard against unexpected PIL processing errors
    try:
        rewritten, fmt, mime = rewrite_image(data, max_size=max_size)
    except Exception as e:
        return False, "processing_error", {**info, "exception": type(e).__name__}, None, None, None, None

    suggested_ext = FMT_TO_DEFAULT_EXT[fmt]
    # Always assign a safe randomized filename (we do not trust user-supplied names)
    safe_filename = f"{uuid.uuid4().hex}{suggested_ext}"
    if original_filename:
        _, ext = os.path.splitext(original_filename.lower())
        expected_fmt = EXT_TO_FMT.get(ext)
        if expected_fmt and expected_fmt != fmt:
            # surface mismatch; caller can correct the filename/extension
            info = {**info, "extension_mismatch": {"provided_ext": ext, "suggested_ext": suggested_ext}}
        elif not expected_fmt:
            # unknown extension; suggest one
            info = {**info, "extension_mismatch": {"provided_ext": ext or None, "suggested_ext": suggested_ext}}

    info = {**info, "mime": mime}
    return True, None, info, rewritten, fmt, suggested_ext, safe_filename


def save_validated_image_to_uploads(
    data: bytes, original_filename: str | None = None, max_size: tuple[int, int] | None = (720, 480)
) -> tuple[bool, str | None, dict, str | None]:
    """Validate and rewrite then persist to static/uploads directory.
    Returns (ok, error, info, static_path) where static_path is like 'uploads/<file>'.
    """
    try:
        ok, err, info, rewritten, fmt, suggested_ext, safe_filename = validate_and_rewrite(
            data, original_filename=original_filename, max_size=max_size
        )
        if not ok or not rewritten or not safe_filename:
            return False, err or "invalid_image", info, None
    except Exception as e:
        # Absolute last-resort guard; return structured error to caller
        return False, "processing_error", {"exception": type(e).__name__}, None

    # Determine uploads directory under app static (use a dedicated 'resume' subfolder)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "resume"))
    os.makedirs(base_dir, exist_ok=True)
    file_path = os.path.join(base_dir, safe_filename)
    try:
        with open(file_path, "wb") as f:
            f.write(rewritten)
    except Exception as e:
        return False, "write_failed", {"exception": type(e).__name__}, None
    return True, None, info, f"uploads/resume/{safe_filename}"


def save_validated_image_to_subdir(
    data: bytes,
    original_filename: str | None = None,
    subdir: str = "uploads/blog",
    max_size: tuple[int, int] | None = (720, 480),
) -> tuple[bool, str | None, dict, str | None]:
    """Validate, rewrite, and persist image bytes under app static/<subdir>.
    Returns (ok, error, info, static_path) where static_path is like 'uploads/blog/<file>'.
    Never raises; returns structured errors.
    """
    try:
        ok, err, info, rewritten, fmt, suggested_ext, safe_filename = validate_and_rewrite(
            data, original_filename=original_filename, max_size=max_size
        )
        if not ok or not rewritten or not safe_filename:
            return False, err or "invalid_image", info, None
    except Exception as e:
        return False, "processing_error", {"exception": type(e).__name__}, None

    # Normalize subdir like 'uploads/blog' (avoid leading/trailing slashes)
    subdir_norm = subdir.strip("/ ") or "uploads"

    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "static", *subdir_norm.split("/"))
    )
    os.makedirs(base_dir, exist_ok=True)
    file_path = os.path.join(base_dir, safe_filename)
    try:
        with open(file_path, "wb") as f:
            f.write(rewritten)
    except Exception as e:
        return False, "write_failed", {"exception": type(e).__name__}, None

    return True, None, info, f"{subdir_norm}/{safe_filename}"
