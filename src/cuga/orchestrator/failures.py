"""
Failure Modes and Retry Semantics

Provides canonical failure taxonomy and retry policies enabling orchestrators
to safely manage execution with clear categorization of agent vs system errors,
retryable vs terminal failures, and partial success handling.

Problem Solved:
- Failures not clearly categorized (agent error vs system error)
- No distinction between retryable vs terminal errors
- Partial success handling undefined
- Prevents safe orchestrator execution management

Key Concepts:
    - FailureMode: Comprehensive failure categorization taxonomy
    - RetryPolicy: Pluggable retry strategies with exponential backoff
    - PartialResult: Structured partial success representation
    - FailureCategory: High-level failure classification (AGENT/SYSTEM/RESOURCE)
"""

from __future__ import annotations

import asyncio
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .protocol import ExecutionContext, OrchestrationError, LifecycleStage


# Type variables for generic retry
T = TypeVar("T")


class FailureCategory(str, Enum):
    """High-level failure categorization for routing decisions."""
    
    AGENT = "agent"              # Agent logic error (validation, business logic)
    SYSTEM = "system"            # System/infrastructure error (timeout, network)
    RESOURCE = "resource"        # Resource unavailable (tool, API, memory)
    POLICY = "policy"            # Policy violation (security, budget)
    USER = "user"                # User-caused error (invalid input, cancellation)


class FailureSeverity(str, Enum):
    """Failure severity levels for logging and escalation."""
    
    LOW = "low"                  # Expected failure, handled gracefully
    MEDIUM = "medium"            # Unexpected but recoverable
    HIGH = "high"                # Serious failure requiring attention
    CRITICAL = "critical"        # System integrity threatened


class FailureMode(str, Enum):
    """
    Comprehensive failure mode taxonomy.
    
    Each mode defines:
    - Category: AGENT/SYSTEM/RESOURCE/POLICY/USER
    - Retryable: Whether failure can be retried
    - Terminal: Whether execution should stop
    - Partial: Whether partial results may exist
    """
    
    # Agent Errors (logic/validation)
    AGENT_VALIDATION = "agent_validation"              # Input validation failed
    AGENT_TIMEOUT = "agent_timeout"                    # Agent exceeded timeout
    AGENT_LOGIC = "agent_logic"                        # Agent logic error
    AGENT_CONTRACT = "agent_contract"                  # I/O contract violation
    AGENT_STATE = "agent_state"                        # Invalid agent state
    
    # System Errors (infrastructure)
    SYSTEM_NETWORK = "system_network"                  # Network connectivity
    SYSTEM_TIMEOUT = "system_timeout"                  # System timeout
    SYSTEM_CRASH = "system_crash"                      # Process crash
    SYSTEM_OOM = "system_oom"                          # Out of memory
    SYSTEM_DISK = "system_disk"                        # Disk space/IO
    
    # Resource Errors (availability)
    RESOURCE_TOOL_UNAVAILABLE = "resource_tool"        # Tool not available
    RESOURCE_API_UNAVAILABLE = "resource_api"          # API not available
    RESOURCE_MEMORY_FULL = "resource_memory"           # Memory full
    RESOURCE_QUOTA = "resource_quota"                  # Quota exceeded
    RESOURCE_CIRCUIT_OPEN = "resource_circuit"         # Circuit breaker open
    
    # Policy Errors (security/constraints)
    POLICY_SECURITY = "policy_security"                # Security violation
    POLICY_BUDGET = "policy_budget"                    # Budget exceeded
    POLICY_ALLOWLIST = "policy_allowlist"              # Allowlist violation
    POLICY_RATE_LIMIT = "policy_rate_limit"            # Rate limit exceeded
    
    # User Errors (input/cancellation)
    USER_INVALID_INPUT = "user_invalid_input"          # Invalid user input
    USER_CANCELLED = "user_cancelled"                  # User cancellation
    USER_PERMISSION = "user_permission"                # Permission denied
    
    # Partial Success States
    PARTIAL_TOOL_FAILURES = "partial_tool_failures"    # Some tools failed
    PARTIAL_STEP_FAILURES = "partial_step_failures"    # Some steps failed
    PARTIAL_TIMEOUT = "partial_timeout"                # Partial completion before timeout
    
    @property
    def category(self) -> FailureCategory:
        """Get failure category."""
        if self.value.startswith("agent_"):
            return FailureCategory.AGENT
        elif self.value.startswith("system_"):
            return FailureCategory.SYSTEM
        elif self.value.startswith("resource_"):
            return FailureCategory.RESOURCE
        elif self.value.startswith("policy_"):
            return FailureCategory.POLICY
        elif self.value.startswith("user_"):
            return FailureCategory.USER
        elif self.value.startswith("partial_"):
            # Partial states inherit category from underlying failure
            return FailureCategory.AGENT
        return FailureCategory.SYSTEM
    
    @property
    def retryable(self) -> bool:
        """Whether failure is retryable."""
        retryable_modes = {
            # System errors often transient
            FailureMode.SYSTEM_NETWORK,
            FailureMode.SYSTEM_TIMEOUT,
            
            # Resource errors may recover
            FailureMode.RESOURCE_TOOL_UNAVAILABLE,
            FailureMode.RESOURCE_API_UNAVAILABLE,
            FailureMode.RESOURCE_CIRCUIT_OPEN,
            
            # Rate limits recoverable with backoff
            FailureMode.POLICY_RATE_LIMIT,
            
            # Agent timeouts may succeed with more time
            FailureMode.AGENT_TIMEOUT,
            
            # Partial states may be retried
            FailureMode.PARTIAL_TIMEOUT,
        }
        return self in retryable_modes
    
    @property
    def terminal(self) -> bool:
        """Whether failure is terminal (stop execution)."""
        terminal_modes = {
            # Policy violations are terminal
            FailureMode.POLICY_SECURITY,
            FailureMode.POLICY_BUDGET,
            FailureMode.POLICY_ALLOWLIST,
            
            # System integrity failures
            FailureMode.SYSTEM_CRASH,
            FailureMode.SYSTEM_OOM,
            
            # User cancellation
            FailureMode.USER_CANCELLED,
            
            # Contract violations
            FailureMode.AGENT_CONTRACT,
        }
        return self in terminal_modes
    
    @property
    def partial_results_possible(self) -> bool:
        """Whether partial results may exist."""
        return self.value.startswith("partial_") or self in {
            FailureMode.AGENT_TIMEOUT,
            FailureMode.SYSTEM_TIMEOUT,
            FailureMode.RESOURCE_QUOTA,
        }
    
    @property
    def severity(self) -> FailureSeverity:
        """Get failure severity."""
        if self.terminal:
            return FailureSeverity.CRITICAL
        elif self.category == FailureCategory.SYSTEM:
            return FailureSeverity.HIGH
        elif self.category in (FailureCategory.RESOURCE, FailureCategory.POLICY):
            return FailureSeverity.MEDIUM
        else:
            return FailureSeverity.LOW


@dataclass
class PartialResult:
    """
    Represents partial success with completed and failed components.
    
    Attributes:
        completed_steps: Steps that completed successfully
        failed_steps: Steps that failed
        partial_data: Partial output data
        failure_mode: Primary failure mode for failed steps
        recovery_strategy: Suggested recovery approach
        metadata: Additional partial result context
    """
    
    completed_steps: List[str]
    failed_steps: List[str]
    partial_data: Dict[str, Any]
    failure_mode: FailureMode
    recovery_strategy: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def completion_ratio(self) -> float:
        """Calculate completion ratio (0.0-1.0)."""
        total = len(self.completed_steps) + len(self.failed_steps)
        if total == 0:
            return 0.0
        return len(self.completed_steps) / total
    
    @property
    def is_recoverable(self) -> bool:
        """Whether partial result is recoverable."""
        return self.failure_mode.retryable and self.completion_ratio > 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "partial_data": self.partial_data,
            "failure_mode": self.failure_mode.value,
            "completion_ratio": self.completion_ratio,
            "recovery_strategy": self.recovery_strategy,
            "metadata": self.metadata,
        }


@dataclass
class FailureContext:
    """
    Comprehensive failure context for debugging and recovery.
    
    Attributes:
        mode: Failure mode classification
        stage: Lifecycle stage where failure occurred
        message: Human-readable failure description
        cause: Original exception
        execution_context: Execution context at failure time
        partial_result: Partial result (if applicable)
        retry_count: Number of retry attempts
        stack_trace: Stack trace for debugging
        metadata: Additional failure context
    """
    
    mode: FailureMode
    stage: LifecycleStage
    message: str
    cause: Optional[Exception] = None
    execution_context: Optional[ExecutionContext] = None
    partial_result: Optional[PartialResult] = None
    retry_count: int = 0
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_orchestration_error(self) -> OrchestrationError:
        """Convert to OrchestrationError for propagation."""
        return OrchestrationError(
            stage=self.stage,
            message=self.message,
            context=self.execution_context or ExecutionContext(trace_id="unknown"),
            cause=self.cause,
            recoverable=self.mode.retryable,
            metadata={
                "failure_mode": self.mode.value,
                "category": self.mode.category.value,
                "severity": self.mode.severity.value,
                "retry_count": self.retry_count,
                "partial_result": self.partial_result.to_dict() if self.partial_result else None,
                **self.metadata,
            },
        )
    
    @classmethod
    def from_exception(
        cls,
        exc: Exception,
        stage: LifecycleStage,
        context: Optional[ExecutionContext] = None,
        mode: Optional[FailureMode] = None,
    ) -> FailureContext:
        """
        Create FailureContext from exception with intelligent mode detection.
        
        Args:
            exc: Original exception
            stage: Lifecycle stage
            context: Execution context
            mode: Explicit failure mode (auto-detected if None)
        
        Returns:
            FailureContext with detected failure mode
        """
        import traceback
        
        # Auto-detect failure mode if not provided
        if mode is None:
            mode = cls._detect_failure_mode(exc)
        
        return cls(
            mode=mode,
            stage=stage,
            message=str(exc),
            cause=exc,
            execution_context=context,
            stack_trace=traceback.format_exc(),
            metadata={"exception_type": type(exc).__name__},
        )
    
    @staticmethod
    def _detect_failure_mode(exc: Exception) -> FailureMode:
        """Detect failure mode from exception type and message."""
        exc_type = type(exc).__name__
        exc_msg = str(exc).lower()
        
        # Check exception type patterns
        if "timeout" in exc_type.lower() or "timeout" in exc_msg:
            return FailureMode.SYSTEM_TIMEOUT
        elif "network" in exc_type.lower() or "connection" in exc_msg:
            return FailureMode.SYSTEM_NETWORK
        elif "memory" in exc_msg or "oom" in exc_msg:
            return FailureMode.SYSTEM_OOM
        elif "permission" in exc_msg or "forbidden" in exc_msg:
            return FailureMode.USER_PERMISSION
        elif "validation" in exc_msg or "invalid" in exc_msg:
            return FailureMode.AGENT_VALIDATION
        elif "rate limit" in exc_msg or "quota" in exc_msg:
            return FailureMode.POLICY_RATE_LIMIT
        elif "circuit" in exc_msg:
            return FailureMode.RESOURCE_CIRCUIT_OPEN
        elif "unavailable" in exc_msg or "not found" in exc_msg:
            return FailureMode.RESOURCE_TOOL_UNAVAILABLE
        
        # Default to agent logic error
        return FailureMode.AGENT_LOGIC


class RetryPolicy(ABC):
    """
    Abstract retry policy interface.
    
    Implementations define retry strategies (exponential backoff, linear, etc.)
    and decide when to retry based on failure context.
    """
    
    @abstractmethod
    def should_retry(self, failure: FailureContext) -> bool:
        """
        Determine if failure should be retried.
        
        Args:
            failure: Failure context
        
        Returns:
            True if retry should be attempted
        """
        ...
    
    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """
        Calculate retry delay for attempt number.
        
        Args:
            attempt: Retry attempt number (0-indexed)
        
        Returns:
            Delay in seconds before retry
        """
        ...
    
    @abstractmethod
    def get_max_attempts(self) -> int:
        """Get maximum retry attempts."""
        ...


@dataclass
class ExponentialBackoffPolicy(RetryPolicy):
    """
    Exponential backoff retry policy with jitter.
    
    Attributes:
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        multiplier: Delay multiplier per attempt
        jitter: Random jitter fraction (0.0-1.0)
        max_attempts: Maximum retry attempts
        retryable_modes: Failure modes to retry (None = use mode.retryable)
    """
    
    base_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: float = 0.1
    max_attempts: int = 3
    retryable_modes: Optional[List[FailureMode]] = None
    
    def should_retry(self, failure: FailureContext) -> bool:
        """Retry if mode is retryable and attempts not exhausted."""
        if failure.retry_count >= self.max_attempts:
            return False
        
        # Check custom retryable modes
        if self.retryable_modes is not None:
            return failure.mode in self.retryable_modes
        
        # Use mode's retryable property
        return failure.mode.retryable
    
    def get_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        delay = min(self.base_delay * (self.multiplier ** attempt), self.max_delay)
        
        # Add jitter
        if self.jitter > 0:
            jitter_amount = delay * self.jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0.0, delay)
    
    def get_max_attempts(self) -> int:
        """Return maximum attempts."""
        return self.max_attempts


@dataclass
class LinearBackoffPolicy(RetryPolicy):
    """
    Linear backoff retry policy.
    
    Attributes:
        delay: Fixed delay between attempts
        max_attempts: Maximum retry attempts
        retryable_modes: Failure modes to retry
    """
    
    delay: float = 2.0
    max_attempts: int = 3
    retryable_modes: Optional[List[FailureMode]] = None
    
    def should_retry(self, failure: FailureContext) -> bool:
        """Retry if mode is retryable and attempts not exhausted."""
        if failure.retry_count >= self.max_attempts:
            return False
        
        if self.retryable_modes is not None:
            return failure.mode in self.retryable_modes
        
        return failure.mode.retryable
    
    def get_delay(self, attempt: int) -> float:
        """Return fixed delay."""
        return self.delay
    
    def get_max_attempts(self) -> int:
        """Return maximum attempts."""
        return self.max_attempts


@dataclass
class NoRetryPolicy(RetryPolicy):
    """Policy that never retries (fail-fast)."""
    
    def should_retry(self, failure: FailureContext) -> bool:
        """Never retry."""
        return False
    
    def get_delay(self, attempt: int) -> float:
        """No delay (never retries)."""
        return 0.0
    
    def get_max_attempts(self) -> int:
        """Zero attempts."""
        return 0


class RetryExecutor:
    """
    Executes operations with retry logic based on policy.
    
    Integrates with orchestrator error propagation and failure tracking.
    """
    
    def __init__(self, policy: RetryPolicy):
        """
        Initialize retry executor.
        
        Args:
            policy: Retry policy to use
        """
        self.policy = policy
    
    async def execute_with_retry(
        self,
        operation: Callable[[], T],
        stage: LifecycleStage,
        context: Optional[ExecutionContext] = None,
        operation_name: str = "operation",
    ) -> T:
        """
        Execute operation with retry logic.
        
        Args:
            operation: Async or sync callable to execute
            stage: Lifecycle stage for failure context
            context: Execution context
            operation_name: Operation name for logging
        
        Returns:
            Operation result
        
        Raises:
            OrchestrationError: If all retries exhausted or terminal failure
        """
        attempt = 0
        last_failure: Optional[FailureContext] = None
        
        while attempt <= self.policy.get_max_attempts():
            try:
                # Execute operation (handle both sync and async)
                if asyncio.iscoroutinefunction(operation):
                    result = await operation()
                else:
                    result = operation()
                
                # Success!
                if last_failure and attempt > 0:
                    # Log successful retry
                    pass  # TODO: Add observability hook
                
                return result
            
            except Exception as exc:
                # Create failure context
                failure = FailureContext.from_exception(
                    exc=exc,
                    stage=stage,
                    context=context,
                    mode=None,  # Auto-detect
                )
                failure.retry_count = attempt
                failure.metadata["operation_name"] = operation_name
                
                last_failure = failure
                
                # Check if terminal
                if failure.mode.terminal:
                    raise failure.to_orchestration_error()
                
                # Check if should retry
                if not self.policy.should_retry(failure):
                    raise failure.to_orchestration_error()
                
                # Calculate delay
                delay = self.policy.get_delay(attempt)
                
                # Log retry attempt
                # TODO: Add observability hook
                
                # Wait before retry
                if delay > 0:
                    await asyncio.sleep(delay)
                
                attempt += 1
        
        # All retries exhausted
        if last_failure:
            raise last_failure.to_orchestration_error()
        
        # Should never reach here
        raise OrchestrationError(
            stage=stage,
            message=f"Retry logic failure for {operation_name}",
            context=context or ExecutionContext(trace_id="unknown"),
        )


def create_retry_policy(
    strategy: str = "exponential",
    max_attempts: int = 3,
    **kwargs: Any,
) -> RetryPolicy:
    """
    Factory function for creating retry policies.
    
    Args:
        strategy: Policy strategy ("exponential", "linear", "none")
        max_attempts: Maximum retry attempts
        **kwargs: Strategy-specific parameters
    
    Returns:
        RetryPolicy instance
    
    Raises:
        ValueError: If strategy unknown
    """
    if strategy == "exponential":
        return ExponentialBackoffPolicy(
            max_attempts=max_attempts,
            base_delay=kwargs.get("base_delay", 1.0),
            max_delay=kwargs.get("max_delay", 60.0),
            multiplier=kwargs.get("multiplier", 2.0),
            jitter=kwargs.get("jitter", 0.1),
        )
    elif strategy == "linear":
        return LinearBackoffPolicy(
            max_attempts=max_attempts,
            delay=kwargs.get("delay", 2.0),
        )
    elif strategy == "none":
        return NoRetryPolicy()
    else:
        raise ValueError(f"Unknown retry strategy: {strategy}")
