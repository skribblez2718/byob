from __future__ import annotations

import bleach
import markdown as md
from pygments.formatters import HtmlFormatter

ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS.union(
    {"p", "pre", "code", "img", "h1", "h2", "h3", "h4", "h5", "h6", "span", "div", "br", "hr"}
)
ALLOWED_ATTRS = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "img": ["src", "alt", "title"],
    "code": ["class"],
    "span": ["class"],
}


def render_markdown(text: str) -> str:
    html = md.markdown(
        text or "",
        extensions=[
            "fenced_code",
            "codehilite",
            "tables",
            "toc",
            "sane_lists",
        ],
        extension_configs={
            "codehilite": {"guess_lang": False, "pygments_style": "default"}
        },
        output_format="html5",
    )
    cleaned = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    return cleaned


def pygments_css() -> str:
    return HtmlFormatter().get_style_defs('.codehilite')
