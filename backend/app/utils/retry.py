"""
Retry utilities with exponential backoff for LLM API calls
"""
import asyncio
import logging
from typing import Callable, TypeVar, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)
import structlog

logger = structlog.get_logger()
std_logger = logging.getLogger(__name__)

T = TypeVar('T')

# Retry decorator for Gemini API calls
def retry_on_api_error(max_attempts: int = 3, min_wait: int = 1, max_wait: int = 10):
    """
    Retry decorator with exponential backoff for API errors.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
    """
    try:
        import google.api_core.exceptions as google_exceptions
        
        retryable_exceptions = (
            google_exceptions.ResourceExhausted,
            google_exceptions.ServiceUnavailable,
            google_exceptions.DeadlineExceeded,
            google_exceptions.InternalServerError,
            google_exceptions.Aborted,
            google_exceptions.GoogleAPIError,
            asyncio.TimeoutError,
        )
    except ImportError:
        # Fallback if google.api_core is not available
        retryable_exceptions = (asyncio.TimeoutError, Exception)
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(retryable_exceptions),
        before_sleep=before_sleep_log(std_logger, logging.INFO),
        after=after_log(std_logger, logging.INFO),
        reraise=True,
    )


async def call_with_retry(
    func: Callable[..., Any],
    *args: Any,
    max_attempts: int = 3,
    **kwargs: Any
) -> Any:
    """
    Call an async function with retry logic.
    
    Args:
        func: Async function to call
        *args: Positional arguments for the function
        max_attempts: Maximum number of attempts
        **kwargs: Keyword arguments for the function
    
    Returns:
        Result from the function
    
    Raises:
        Exception: If all retry attempts fail
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            logger.warning(
                "retry_attempt_failed",
                attempt=attempt + 1,
                max_attempts=max_attempts,
                error=str(e),
                error_type=type(e).__name__
            )
            
            if attempt < max_attempts - 1:
                wait_time = min(2 ** attempt, 10)
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    "all_retry_attempts_failed",
                    max_attempts=max_attempts,
                    error=str(e),
                    error_type=type(e).__name__
                )
    
    raise last_exception
