"""
Circuit Breaker pattern implementation for preventing cascading failures
"""
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any, Optional
import structlog

logger = structlog.get_logger()


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    
    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Too many failures, reject all requests immediately
    - HALF_OPEN: Testing recovery, allow limited requests
    
    Thresholds:
    - failure_threshold: Number of failures before opening circuit
    - recovery_timeout: Seconds to wait before attempting recovery
    - success_threshold: Successful calls needed in HALF_OPEN to close circuit
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        success_threshold: int = 2,
        timeout_duration: int = 60,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.timeout_duration = timeout_duration
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None
        
        logger.info(
            "circuit_breaker_initialized",
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold
        )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.state != CircuitState.OPEN:
            return False
        
        if not self.opened_at:
            return True
        
        elapsed = (datetime.utcnow() - self.opened_at).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def _record_success(self):
        """Record a successful call"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(
                "circuit_breaker_success_in_half_open",
                success_count=self.success_count,
                success_threshold=self.success_threshold
            )
            
            if self.success_count >= self.success_threshold:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            self.success_count += 1
    
    def _record_failure(self):
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        self.success_count = 0
        
        logger.warning(
            "circuit_breaker_failure_recorded",
            failure_count=self.failure_count,
            failure_threshold=self.failure_threshold,
            state=self.state.value
        )
        
        if self.state == CircuitState.HALF_OPEN:
            self._open_circuit()
        elif self.failure_count >= self.failure_threshold:
            self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit (stop allowing requests)"""
        self.state = CircuitState.OPEN
        self.opened_at = datetime.utcnow()
        
        logger.error(
            "circuit_breaker_opened",
            failure_count=self.failure_count,
            opened_at=self.opened_at.isoformat()
        )
    
    def _close_circuit(self):
        """Close the circuit (resume normal operation)"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.opened_at = None
        
        logger.info("circuit_breaker_closed")
    
    def _half_open_circuit(self):
        """Move to half-open state (test recovery)"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        
        logger.info("circuit_breaker_half_opened")
    
    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Result from the function
        
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If the function raises an exception
        """
        # Check if we should attempt reset
        if self._should_attempt_reset():
            self._half_open_circuit()
        
        # Reject if circuit is open
        if self.state == CircuitState.OPEN:
            logger.warning(
                "circuit_breaker_rejected_request",
                state=self.state.value,
                opened_at=self.opened_at.isoformat() if self.opened_at else None
            )
            raise CircuitBreakerError(
                f"Circuit breaker is OPEN. Service unavailable. "
                f"Will retry after {self.recovery_timeout} seconds."
            )
        
        # Attempt the call
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise e
    
    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
        }


# Global circuit breaker instance for LLM service
llm_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30,
    success_threshold=2
)
