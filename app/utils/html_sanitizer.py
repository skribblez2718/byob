"""
HTML sanitization utilities using bleach for secure content rendering.
Provides DOMPurify-equivalent functionality for Python/Flask applications.
"""
from __future__ import annotations

import bleach


# Allowed HTML tags for blog content
ALLOWED_TAGS = [
    # Text formatting
    'strong', 'b', 'em', 'i', 'u', 's', 'mark', 'small', 'sup', 'sub',
    # Links
    'a',
    # Lists
    'ul', 'ol', 'li',
    # Line breaks and paragraphs
    'br', 'p',
    # Code
    'code', 'pre',
    # Quotes
    'blockquote', 'cite',
    # Spans for styling (class only, no inline styles)
    'span',
]

# Allowed HTML attributes (no style attributes since CSP blocks inline CSS)
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'blockquote': ['cite'],
    'span': ['class'],
    'code': ['class'],
    'pre': ['class'],
    '*': ['id', 'class'],  # Allow id and class on all elements
}

# Allowed protocols for links
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks while allowing safe formatting.
    
    This function acts as the Python equivalent to DOMPurify, removing dangerous
    HTML elements, attributes, and JavaScript while preserving safe formatting.
    
    Args:
        html_content: Raw HTML content to sanitize
        
    Returns:
        Sanitized HTML content safe for rendering
    """
    if not html_content:
        return ""
    
    # Clean the HTML using bleach (no CSS sanitizer needed)
    cleaned_html = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,  # Strip disallowed tags instead of escaping
        strip_comments=True,  # Remove HTML comments
    )
    
    return cleaned_html


def sanitize_blog_paragraph(paragraph_content: str) -> str:
    """
    Sanitize paragraph content specifically for blog posts.
    
    This is optimized for paragraph content and allows basic formatting
    like bold, italic, links, and inline code.
    
    Args:
        paragraph_content: Raw paragraph HTML content
        
    Returns:
        Sanitized paragraph content
    """
    # Use a more restrictive set for paragraphs
    paragraph_tags = [
        'strong', 'b', 'em', 'i', 'u', 's', 'mark', 'small', 'sup', 'sub',
        'a', 'code', 'br', 'span', 'ul', 'ol', 'li'
    ]
    
    paragraph_attributes = {
        'a': ['href', 'title', 'target', 'rel'],
        'span': ['class', 'id'],
        'code': ['class', 'id'],
        'ul': ['class', 'id'],
        'ol': ['class', 'id'],
        'li': ['class', 'id']
    }
    
    cleaned_content = bleach.clean(
        paragraph_content,
        tags=paragraph_tags,
        attributes=paragraph_attributes,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )
    
    return cleaned_content


def is_safe_html(html_content: str) -> bool:
    """
    Check if HTML content is safe (doesn't contain dangerous elements).
    
    Args:
        html_content: HTML content to check
        
    Returns:
        True if content is safe, False if it contains dangerous elements
    """
    if not html_content:
        return True
    
    # Sanitize and compare - if they're the same, it was already safe
    sanitized = sanitize_html(html_content)
    return sanitized == html_content.strip()
