from __future__ import annotations

import os
import hashlib
from flask import current_app


def validate_secret_key() -> dict[str, str]:
    """
    Validate SECRET_KEY configuration and provide diagnostic information.
    Returns a dictionary with validation results.
    """
    results = {}
    
    # Check if SECRET_KEY is set in environment
    env_secret = os.getenv("SECRET_KEY")
    if env_secret:
        results["env_secret_key"] = "✓ Set in environment"
        results["env_secret_hash"] = hashlib.sha256(env_secret.encode()).hexdigest()[:16]
    else:
        results["env_secret_key"] = "✗ Not set in environment (will use random fallback)"
        results["env_secret_hash"] = "N/A"
    
    # Check Flask app config
    try:
        app_secret = current_app.config.get("SECRET_KEY")
        if app_secret:
            results["app_secret_key"] = "✓ Available in Flask config"
            if isinstance(app_secret, bytes):
                secret_str = app_secret.decode("utf-8")
            else:
                secret_str = str(app_secret)
            results["app_secret_hash"] = hashlib.sha256(secret_str.encode()).hexdigest()[:16]
            
            # Check consistency
            if env_secret and env_secret == secret_str:
                results["consistency"] = "✓ Environment and Flask config match"
            elif env_secret:
                results["consistency"] = "✗ Environment and Flask config differ"
            else:
                results["consistency"] = "⚠ Using Flask-generated secret (may change on restart)"
        else:
            results["app_secret_key"] = "✗ Not available in Flask config"
            results["app_secret_hash"] = "N/A"
            results["consistency"] = "✗ No secret key configured"
    except RuntimeError:
        results["app_secret_key"] = "✗ Flask app context not available"
        results["app_secret_hash"] = "N/A"
        results["consistency"] = "✗ Cannot validate without app context"
    
    return results


def log_secret_key_validation() -> None:
    """Log SECRET_KEY validation results for debugging."""
    results = validate_secret_key()
    
    current_app.logger.info("SECRET_KEY Validation Results:")
    for key, value in results.items():
        current_app.logger.info(f"  {key}: {value}")
