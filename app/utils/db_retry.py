"""Database connection retry utilities."""

import time
import functools
from typing import Any, Callable, TypeVar
from flask import current_app
from sqlalchemy.exc import OperationalError, DisconnectionError
from psycopg2 import OperationalError as Psycopg2OperationalError

F = TypeVar('F', bound=Callable[..., Any])

def retry_db_operation(max_retries: int = 3, delay: float = 0.5, backoff: float = 2.0):
    """
    Decorator to retry database operations on connection failures.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DisconnectionError, Psycopg2OperationalError) as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    # Only retry on connection-related errors
                    if any(keyword in error_msg for keyword in [
                        'ssl syscall error', 'eof detected', 'connection closed',
                        'server closed the connection', 'connection reset',
                        'connection timed out', 'could not connect',
                        'ssl error: decryption failed', 'bad record mac'
                    ]):
                        if attempt < max_retries:
                            current_app.logger.warning(
                                f"Database connection error on attempt {attempt + 1}/{max_retries + 1}: {str(e)}. "
                                f"Retrying in {current_delay:.1f}s..."
                            )
                            time.sleep(current_delay)
                            current_delay *= backoff
                            continue
                    
                    # Re-raise if not a retryable error or max retries exceeded
                    raise
                except Exception as e:
                    # Don't retry non-connection errors
                    raise
            
            # If we get here, all retries failed
            current_app.logger.error(f"Database operation failed after {max_retries + 1} attempts: {str(last_exception)}")
            raise last_exception
        
        return wrapper
    return decorator


def safe_db_operation(func: F, *args, **kwargs) -> Any:
    """
    Execute a database operation with retry logic.
    Use this for one-off operations that need retry protection.
    """
    @retry_db_operation()
    def _operation():
        return func(*args, **kwargs)
    
    return _operation()
