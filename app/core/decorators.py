import asyncio
import logging
import functools
from typing import Callable, Any

logger = logging.getLogger(__name__)

def async_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator for async functions to retry on exception with exponential backoff.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries. Error: {e}")
                        raise e
                    
                    logger.warning(f"Function {func.__name__} failed (Attempt {attempt+1}/{max_retries}). Retrying in {current_delay}s... Error: {e}")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator
