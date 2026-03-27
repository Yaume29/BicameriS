"""
Diadikos & Palladion - Retry Utilities
==========================
Generic retry decorator for functions, services, and initializations.
"""

import time
import logging
from functools import wraps
from typing import Callable, Type, Any, Optional

logger = logging.getLogger(__name__)


def retry(
    *,
    exceptions: tuple[Type[BaseException], ...] = (Exception,),
    max_attempts: int = 3,
    base_delay: float = 1.0,
    backoff: str = "exponential",
    logger_instance: Optional[logging.Logger] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator that retries the decorated function when one of the specified exceptions is raised.
    
    Args:
        exceptions: Tuple of exception types to catch and retry on
        max_attempts: Maximum number of attempts (default: 3)
        base_delay: Base delay in seconds between retries (default: 1.0)
        backoff: Either "exponential" or "linear" (default: "exponential")
        logger_instance: Optional logger instance (default: module logger)
    
    Example:
        @retry(exceptions=(ConnectionError,), max_attempts=4, base_delay=2)
        def fetch_data():
            ...
    """
    log = logger_instance or logger

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        log.error(
                            f"[Retry] {func.__name__} failed after {max_attempts} attempts: {exc}"
                        )
                        raise
                    delay = base_delay * (2 ** (attempt - 1)) if backoff == "exponential" else base_delay * attempt
                    log.warning(
                        f"[Retry] {func.__name__} attempt {attempt}/{max_attempts} failed: {exc}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    time.sleep(delay)
        return wrapper
    return decorator


def retry_async(
    *,
    exceptions: tuple[Type[BaseException], ...] = (Exception,),
    max_attempts: int = 3,
    base_delay: float = 1.0,
    backoff: str = "exponential",
    logger_instance: Optional[logging.Logger] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Async version of retry decorator.
    
    Example:
        @retry_async(exceptions=(ConnectionError,), max_attempts=3)
        async def fetch_data():
            ...
    """
    log = logger_instance or logger

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        log.error(
                            f"[Retry] {func.__name__} failed after {max_attempts} attempts: {exc}"
                        )
                        raise
                    delay = base_delay * (2 ** (attempt - 1)) if backoff == "exponential" else base_delay * attempt
                    log.warning(
                        f"[Retry] {func.__name__} attempt {attempt}/{max_attempts} failed: {exc}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    time.sleep(delay)
        return wrapper
    return decorator
