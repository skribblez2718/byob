"""Slug generation utilities."""
from __future__ import annotations

import re
import unicodedata


def slugify(text: str) -> str:
    """
    Convert a string to a URL-friendly slug.
    
    Args:
        text: The text to convert to a slug
        
    Returns:
        A URL-friendly slug string
    """
    if not text:
        return ""
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)
    
    # Remove all non-alphanumeric characters except hyphens
    text = re.sub(r'[^a-z0-9\-]', '', text)
    
    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)
    
    # Strip leading and trailing hyphens
    text = text.strip('-')
    
    return text
