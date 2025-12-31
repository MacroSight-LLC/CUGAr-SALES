# Orchestrator Interface and Semantics

**Status**: Canonical Reference  
**Last Updated**: 2025-12-31  
**Audience**: Orchestrator implementers, agent developers, integration engineers

---

## 📋 Overview

This document serves as the **formal specification** for the CUGAR orchestrator interface, defining the complete contract for agent execution, failures, retries, and lifecycle management. All orchestrator implementations MUST conform to this specification.

### What This Document Provides

✅ **Formal API contracts** - Complete interface definitions with types  
✅ **Lifecycle semantics** - Stage ordering, guarantees, state transitions  
✅ **Failure taxonomy** - Comprehensive error classification with retry semantics  
✅ **Integration patterns** - How to implement, test, and extend orchestrators  
✅ **Reference implementations** - Working examples for common use cases

### Quick Navigation

| Topic | Document | Purpose |
|-------|----------|---------|
| **Core Contract** | [ORCHESTRATOR_CONTRACT.md](ORCHESTRATOR_CONTRACT.md) | Main protocol definition, lifecycle stages, routing |
| **Execution Context** | [EXECUTION_CONTEXT.md](EXECUTION_CONTEXT.md) | Immutable context propagation, trace continuity |
| **Failure Modes** | [FAILURE_MODES.md](FAILURE_MODES.md) | Error taxonomy, retry policies, partial results |
| **Routing Authority** | [ROUTING_AUTHORITY.md](ROUTING_AUTHORITY.md) | Routing decisions, policies, fallback strategies |
| **This Document** | README.md | Index and quick reference |

---

## 🎯 Orchestrator Contract (Formal Specification)

### Interface Definition

```python
from cuga.orchestrator import OrchestratorProtocol, ExecutionContext, LifecycleStage
from typing import AsyncIterator, Dict, Any

class OrchestratorProtocol(Protocol):
    """
    Canonical interface for all orchestrators in CUGAR agent system.
    
    All orchestration logic MUST implement this protocol to ensure:
    - Explicit lifecycle management (init → plan → route → execute → complete)
    - Trace continuity (trace_id propagation without mutation)
    - Error transparency (structured failures with recovery semantics)
    - Deterministic routing (same inputs → same decisions)
    
    Location: src/cuga/orchestrator/protocol.py
    Status: Canonical (breaking changes require major version bump)
    """
    
    async def orchestrate(
        self,
        goal: str,
        context: ExecutionContext,
        *,
        error_strategy: ErrorPropagation = ErrorPropagation.FAIL_FAST,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Primary orchestration method. Yields events as execution progresses.
        
        Args:
            goal: User goal/intent to execute
            context: Immutable execution context (trace_id, profile, metadata)
            error_strategy: How to handle failures (fail_fast, retry, fallback, continue)
        
        Yields:
            Lifecycle events: {"stage": LifecycleStage, "data": {...}, "context": context}
        
        Raises:
            OrchestrationError: On terminal failures (stage, message, context, cause)
        
        Guarantees:
            1. Events emitted in stage order (INITIALIZE → PLAN → ROUTE → EXECUTE → ...)
            2. trace_id preserved across all events
            3. Terminal stage (COMPLETE/FAILED/CANCELLED) emitted exactly once
            4. Errors structured with recovery metadata (recoverable flag, suggested action)
        
        Example:
            >>> ctx = ExecutionContext(trace_id="abc", profile="demo")
            >>> async for event in orchestrator.orchestrate("find flights", ctx):
            ...     print(f"{event['stage']}: {event['data']}")
        """
        ...
    
    def make_routing_decision(
        self,
        task: str,
        context: ExecutionContext,
        available_agents: List[str],
    ) -> RoutingDecision:
        """
        Make deterministic routing decision for task.
        
        Args:
            task: Task description/goal
            context: Current execution context
            available_agents: List of agent/worker identifiers
        
        Returns:
            RoutingDecision with target, reason, metadata, fallback
        
        Guarantees:
            1. Deterministic (same inputs → same decision)
            2. Justified (reason field explains selection)
            3. Fallback-aware (specifies fallback target if primary fails)
            4. Logged (decision emitted in trace)
        
        Example:
            >>> decision = orchestrator.make_routing_decision(
            ...     task="search web for docs",
            ...     context=ctx,
            ...     available_agents=["web_search", "rag_query"]
            ... )
            >>> decision.target        # "web_search"
            >>> decision.reason        # "Task contains 'search web' keyword"
            >>> decision.fallback      # "rag_query"
        """
        ...
    
    async def handle_error(
        self,
        error: OrchestrationError,
        strategy: ErrorPropagation,
    ) -> Optional[Dict[str, Any]]:
        """
        Handle orchestration errors per specified strategy.
        
        Args:
            error: OrchestrationError with stage, message, context, cause
            strategy: Error propagation strategy (fail_fast, retry, fallback, continue)
        
        Returns:
            Recovery result (if recoverable) or None (if terminal)
        
        Guarantees:
            1. Never silent (all errors logged with trace_id)
            2. Respects strategy (fail_fast raises, retry attempts recovery)
            3. Preserves partial results (available in error.metadata)
            4. Structured logging (stage, cause, recoverable flag)
        
        Example:
            >>> try:
            ...     result = await orchestrator.handle_error(error, ErrorPropagation.RETRY)
            ... except OrchestrationError as terminal:
            ...     logger.error(f"Terminal failure: {terminal.message}")
        """
        ...
    
    def get_lifecycle(self) -> AgentLifecycle:
        """
        Return lifecycle manager for initialization and teardown.
        
        Returns:
            AgentLifecycle instance with startup/shutdown/health_check methods
        
        Guarantees:
            1. startup() is idempotent (safe to call multiple times)
            2. shutdown() never raises exceptions (logs errors internally)
            3. health_check() returns current orchestrator health status
        
        Example:
            >>> lifecycle = orchestrator.get_lifecycle()
            >>> await lifecycle.startup(cleanup_on_error=True)
            >>> # ... orchestration ...
            >>> await lifecycle.shutdown(timeout=10.0)
        """
        ...
```

### Type Definitions

```python
# Lifecycle stages (enum)
class LifecycleStage(str, Enum):
    INITIALIZE = "initialize"  # Agent/resource setup
    PLAN = "plan"              # Task decomposition
    ROUTE = "route"            # Routing decision
    EXECUTE = "execute"        # Tool/step execution
    AGGREGATE = "aggregate"    # Results aggregation
    COMPLETE = "complete"      # Success exit
    FAILED = "failed"          # Error exit
    CANCELLED = "cancelled"    # User cancellation

# Error propagation strategies (enum)
class ErrorPropagation(str, Enum):
    FAIL_FAST = "fail_fast"    # Stop immediately on error (default)
    RETRY = "retry"            # Retry with exponential backoff
    FALLBACK = "fallback"      # Use fallback routing decision
    CONTINUE = "continue"      # Log error, continue remaining steps

# Execution context (immutable)
@dataclass(frozen=True)
class ExecutionContext:
    trace_id: str                               # REQUIRED
    request_id: str = ""
    profile: str = "default"
    user_intent: str = ""
    user_id: str = ""
    memory_scope: str = ""
    conversation_id: str = ""
    session_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_context: Optional[ExecutionContext] = None

# Routing decision (immutable)
@dataclass(frozen=True)
class RoutingDecision:
    target: str                      # Target agent/worker ID
    reason: str                      # Human-readable justification
    metadata: Dict[str, Any]         # Additional routing context
    fallback: Optional[str] = None   # Fallback target if primary fails

# Orchestration error (structured)
@dataclass
class OrchestrationError(Exception):
    stage: LifecycleStage             # Where error occurred
    message: str                      # Human-readable description
    context: ExecutionContext         # Context at failure time
    cause: Optional[Exception] = None # Original exception
    recoverable: bool = False         # Can this be recovered?
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## 🔄 Lifecycle Semantics

### Stage Ordering (Required)

```
┌──────────────┐
│  INITIALIZE  │  ← Agent/resource initialization (idempotent)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│     PLAN     │  ← Task decomposition (deterministic)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    ROUTE     │  ← Routing decision (explicit justification)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   EXECUTE    │  ← Tool/step execution (may repeat)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  AGGREGATE   │  ← Results collection
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   COMPLETE   │ OR  │    FAILED    │ OR  │  CANCELLED   │
└──────────────┘     └──────────────┘     └──────────────┘
  (success)            (error)             (user/system)
```

### Stage Guarantees

| Stage | Guarantee | Violation Handling |
|-------|-----------|-------------------|
| **INITIALIZE** | MUST complete before PLAN | OrchestrationError(stage=INITIALIZE, recoverable=True) |
| **PLAN** | MUST complete before ROUTE | OrchestrationError(stage=PLAN, recoverable=False) |
| **ROUTE** | MUST be emitted for each task | OrchestrationError(stage=ROUTE, recoverable=True) |
| **EXECUTE** | MAY repeat per routing decision | Errors handled per ErrorPropagation strategy |
| **AGGREGATE** | MUST collect all results before COMPLETE | Partial results preserved in error metadata |
| **Terminal** | COMPLETE/FAILED/CANCELLED emitted exactly once | Orchestrator state transition enforced |

### Lifecycle Events (Format)

```python
# Event structure (all lifecycle stages)
{
    "stage": LifecycleStage,          # Current stage (enum)
    "data": Dict[str, Any],           # Stage-specific data
    "context": ExecutionContext,      # Current execution context
    "timestamp": str,                 # ISO 8601 timestamp
    "metadata": Dict[str, Any]        # Additional event metadata
}

# INITIALIZE event
{
    "stage": "initialize",
    "data": {
        "orchestrator_type": "CoordinatorAgent",
        "workers": ["worker-1", "worker-2"],
        "resources_loaded": True
    },
    "context": ExecutionContext(...),
    "timestamp": "2025-12-31T12:00:00Z"
}

# PLAN event
{
    "stage": "plan",
    "data": {
        "goal": "find flights to NYC",
        "steps": [
            {"tool": "search_flights", "reason": "score=1.0"},
            {"tool": "compare_prices", "reason": "score=0.67"}
        ],
        "planner": "PlannerAgent"
    },
    "context": ExecutionContext(...),
    "timestamp": "2025-12-31T12:00:01Z"
}

# ROUTE event
{
    "stage": "route",
    "data": {
        "task": "search flights",
        "decision": {
            "target": "worker-1",
            "reason": "round-robin selection",
            "fallback": "worker-2"
        }
    },
    "context": ExecutionContext(...),
    "timestamp": "2025-12-31T12:00:02Z"
}

# EXECUTE event
{
    "stage": "execute",
    "data": {
        "tool": "search_flights",
        "worker": "worker-1",
        "input": {"origin": "JFK", "destination": "LAX"},
        "result": {"flights": [...]}
    },
    "context": ExecutionContext(...),
    "timestamp": "2025-12-31T12:00:03Z"
}

# COMPLETE event
{
    "stage": "complete",
    "data": {
        "output": {"flights": [...]},
        "steps_completed": 2,
        "duration_ms": 3000
    },
    "context": ExecutionContext(...),
    "timestamp": "2025-12-31T12:00:05Z"
}

# FAILED event
{
    "stage": "failed",
    "data": {
        "error": {
            "stage": "execute",
            "message": "Tool execution timeout",
            "cause": "TimeoutError",
            "recoverable": True
        },
        "partial_results": {"flights": [...]},
        "steps_completed": 1,
        "steps_total": 2
    },
    "context": ExecutionContext(...),
    "timestamp": "2025-12-31T12:00:04Z"
}
```

### State Transitions

```python
# Valid transitions (enforced by orchestrator)
INITIALIZE → PLAN → ROUTE → EXECUTE → AGGREGATE → COMPLETE ✅
INITIALIZE → PLAN → ROUTE → EXECUTE → FAILED ✅
INITIALIZE → FAILED ✅ (initialization error)
PLAN → FAILED ✅ (planning error)
ROUTE → FAILED ✅ (routing error)
EXECUTE → ROUTE → EXECUTE ✅ (multi-step execution)
* → CANCELLED ✅ (user/system cancellation)

# Invalid transitions (raise OrchestrationError)
COMPLETE → EXECUTE ❌ (terminal state violation)
FAILED → ROUTE ❌ (terminal state violation)
PLAN → EXECUTE ❌ (missing ROUTE stage)
ROUTE → AGGREGATE ❌ (missing EXECUTE stage)
```

---

## ⚠️ Failure Modes and Recovery

### Failure Taxonomy

Comprehensive classification system for all orchestration failures:

```python
from cuga.orchestrator.failures import FailureMode, FailureCategory

# Agent errors (validation, timeout, logic)
FailureMode.AGENT_VALIDATION      # Input validation failed
FailureMode.AGENT_TIMEOUT         # Agent exceeded timeout (retryable)
FailureMode.AGENT_LOGIC           # Agent logic error (terminal)
FailureMode.AGENT_CONTRACT        # I/O contract violation (terminal)
FailureMode.AGENT_STATE           # Invalid agent state (terminal)

# System errors (infrastructure)
FailureMode.SYSTEM_NETWORK        # Network connectivity (retryable)
FailureMode.SYSTEM_TIMEOUT        # System timeout (retryable)
FailureMode.SYSTEM_CRASH          # Process crash (terminal)
FailureMode.SYSTEM_OOM            # Out of memory (terminal)
FailureMode.SYSTEM_DISK           # Disk space/IO error

# Resource errors (availability)
FailureMode.RESOURCE_TOOL_UNAVAILABLE   # Tool unavailable (retryable)
FailureMode.RESOURCE_API_UNAVAILABLE    # API unavailable (retryable)
FailureMode.RESOURCE_MEMORY_FULL        # Memory full (terminal)
FailureMode.RESOURCE_QUOTA              # Quota exceeded (terminal)
FailureMode.RESOURCE_CIRCUIT_OPEN       # Circuit breaker open (retryable)

# Policy errors (security/constraints)
FailureMode.POLICY_SECURITY       # Security violation (terminal)
FailureMode.POLICY_BUDGET         # Budget exceeded (terminal)
FailureMode.POLICY_ALLOWLIST      # Allowlist violation (terminal)
FailureMode.POLICY_RATE_LIMIT     # Rate limit (retryable)

# User errors (input/cancellation)
FailureMode.USER_INVALID_INPUT    # Invalid user input (terminal)
FailureMode.USER_CANCELLED        # User cancellation (terminal)
FailureMode.USER_PERMISSION       # Permission denied (terminal)

# Partial success states
FailureMode.PARTIAL_TOOL_FAILURES # Some tools failed (recoverable)
FailureMode.PARTIAL_STEP_FAILURES # Some steps failed (recoverable)
FailureMode.PARTIAL_TIMEOUT       # Partial completion before timeout
```

### Failure Properties

Every failure mode has deterministic properties:

```python
mode = FailureMode.SYSTEM_NETWORK

# Automatic classification
mode.category                    # FailureCategory.SYSTEM
mode.retryable                   # True (can retry)
mode.terminal                    # False (not terminal)
mode.partial_results_possible    # False (no partial results)
mode.severity                    # FailureSeverity.HIGH

# Use in error handling
if mode.retryable and not mode.terminal:
    await retry_with_backoff(...)
elif mode.partial_results_possible:
    return partial_results
else:
    raise OrchestrationError(recoverable=False)
```

### Retry Policies

Pluggable retry strategies with configurable backoff:

```python
from cuga.orchestrator.failures import RetryPolicy, ExponentialBackoffPolicy

# Exponential backoff (recommended for transient errors)
policy = ExponentialBackoffPolicy(
    max_attempts=3,
    initial_delay=1.0,    # Start with 1 second
    max_delay=30.0,       # Cap at 30 seconds
    multiplier=2.0,       # Double delay each time
    jitter=True           # Add randomness to prevent thundering herd
)

# Linear backoff
policy = LinearBackoffPolicy(
    max_attempts=5,
    delay=5.0             # Fixed 5 second delay
)

# No retry (fail immediately)
policy = NoRetryPolicy()

# Usage in orchestrator
async def orchestrate_with_retry(goal, context):
    policy = ExponentialBackoffPolicy(max_attempts=3)
    
    async for attempt in policy.retry_generator():
        try:
            result = await execute_step(step, context)
            return result  # Success
        except OrchestrationError as err:
            if not err.recoverable or attempt.is_last:
                raise  # Terminal or last attempt
            logger.warning(f"Attempt {attempt.number} failed, retrying in {attempt.delay}s")
            await asyncio.sleep(attempt.delay)
```

### Error Handling Flow

```python
# Complete error handling pattern
async def orchestrate(goal, context, error_strategy=ErrorPropagation.FAIL_FAST):
    try:
        # Emit INITIALIZE
        yield {"stage": LifecycleStage.INITIALIZE, ...}
        
        # Emit PLAN
        plan = await planner.plan(goal, context)
        yield {"stage": LifecycleStage.PLAN, "data": {"steps": plan.steps}, ...}
        
        # Emit ROUTE + EXECUTE
        for step in plan.steps:
            decision = make_routing_decision(step.tool, context, workers)
            yield {"stage": LifecycleStage.ROUTE, "data": {"decision": decision}, ...}
            
            try:
                result = await worker.execute(step, context)
                yield {"stage": LifecycleStage.EXECUTE, "data": {"result": result}, ...}
            except ToolExecutionError as err:
                # Classify failure
                mode = classify_error(err)
                
                # Handle per strategy
                if error_strategy == ErrorPropagation.FAIL_FAST:
                    raise OrchestrationError(
                        stage=LifecycleStage.EXECUTE,
                        message=str(err),
                        context=context,
                        cause=err,
                        recoverable=mode.retryable
                    )
                elif error_strategy == ErrorPropagation.RETRY and mode.retryable:
                    result = await retry_with_backoff(worker.execute, step, context)
                    yield {"stage": LifecycleStage.EXECUTE, "data": {"result": result}, ...}
                elif error_strategy == ErrorPropagation.CONTINUE:
                    logger.warning(f"Step {step.tool} failed, continuing: {err}")
                    continue
        
        # Emit COMPLETE
        yield {"stage": LifecycleStage.COMPLETE, "data": {"status": "success"}, ...}
        
    except OrchestrationError as err:
        # Emit FAILED with structured error
        yield {
            "stage": LifecycleStage.FAILED,
            "data": {
                "error": {
                    "stage": err.stage.value,
                    "message": err.message,
                    "recoverable": err.recoverable,
                    "cause": str(err.cause) if err.cause else None
                },
                "context": err.context.to_dict()
            },
            "context": err.context
        }
        raise
```

---

## 🎯 Routing Semantics

### Routing Authority

All routing decisions MUST go through `RoutingAuthority` interface:

```python
from cuga.orchestrator import RoutingAuthority, RoutingPolicy

# Create routing authority with pluggable policy
authority = RoutingAuthority(policy=RoundRobinPolicy())

# Make routing decision
decision = authority.route(
    task="search flights",
    context=ExecutionContext(trace_id="abc", profile="demo"),
    available_targets=["worker-1", "worker-2", "worker-3"]
)

# RoutingDecision(
#     target="worker-1",
#     reason="round-robin selection (index=0)",
#     metadata={"worker_idx": 0, "total_workers": 3},
#     fallback="worker-2"
# )
```

### Routing Policies

Pluggable routing strategies:

```python
# Round-robin (default)
class RoundRobinPolicy(RoutingPolicy):
    def select_target(self, task, context, available_targets):
        idx = self._counter % len(available_targets)
        self._counter += 1
        return RoutingDecision(
            target=available_targets[idx],
            reason=f"round-robin selection (index={idx})",
            metadata={"worker_idx": idx},
            fallback=available_targets[(idx + 1) % len(available_targets)]
        )

# Capability-based
class CapabilityPolicy(RoutingPolicy):
    def select_target(self, task, context, available_targets):
        scores = [(target, self._score(task, target)) for target in available_targets]
        scores.sort(key=lambda x: x[1], reverse=True)
        return RoutingDecision(
            target=scores[0][0],
            reason=f"capability match (score={scores[0][1]})",
            metadata={"scores": dict(scores)},
            fallback=scores[1][0] if len(scores) > 1 else None
        )

# Load-balanced
class LoadBalancedPolicy(RoutingPolicy):
    def select_target(self, task, context, available_targets):
        loads = {t: self._get_load(t) for t in available_targets}
        target = min(loads, key=loads.get)
        return RoutingDecision(
            target=target,
            reason=f"lowest load ({loads[target]} active)",
            metadata={"loads": loads},
            fallback=sorted(loads, key=loads.get)[1]
        )
```

### Routing Requirements

All routing decisions MUST be:

1. **Deterministic**: Same inputs → same decision (for reproducibility)
2. **Justified**: `reason` field explains selection (for debuggability)
3. **Fallback-aware**: Specify fallback target if primary fails (for resilience)
4. **Logged**: Decision emitted in trace with metadata (for observability)

---

## 📊 Integration Patterns

### Pattern 1: Simple Orchestrator (Synchronous)

```python
from cuga.orchestrator import OrchestratorProtocol, ExecutionContext, LifecycleStage

class SimpleOrchestrator(OrchestratorProtocol):
    def __init__(self, planner, workers):
        self.planner = planner
        self.workers = workers
        self._worker_idx = 0
    
    async def orchestrate(self, goal, context, *, error_strategy=ErrorPropagation.FAIL_FAST):
        # INITIALIZE
        yield {"stage": LifecycleStage.INITIALIZE, "data": {}, "context": context}
        
        # PLAN
        plan = await self.planner.plan(goal, context)
        yield {"stage": LifecycleStage.PLAN, "data": {"steps": plan.steps}, "context": context}
        
        # ROUTE + EXECUTE
        for step in plan.steps:
            decision = self.make_routing_decision(step.tool, context, self.workers)
            yield {"stage": LifecycleStage.ROUTE, "data": {"decision": decision}, "context": context}
            
            worker = self.workers[decision.target]
            result = await worker.execute(step, context)
            yield {"stage": LifecycleStage.EXECUTE, "data": {"result": result}, "context": context}
        
        # COMPLETE
        yield {"stage": LifecycleStage.COMPLETE, "data": {"status": "success"}, "context": context}
    
    def make_routing_decision(self, task, context, available_agents):
        worker_id = self._worker_idx % len(available_agents)
        self._worker_idx += 1
        return RoutingDecision(
            target=worker_id,
            reason=f"round-robin (index={worker_id})",
            metadata={"worker_idx": worker_id},
            fallback=(worker_id + 1) % len(available_agents)
        )
```

### Pattern 2: Streaming Orchestrator (LangGraph)

```python
class StreamingOrchestrator(OrchestratorProtocol):
    def __init__(self, graph, agents):
        self.graph = graph
        self.agents = agents
    
    async def orchestrate(self, goal, context, *, error_strategy=ErrorPropagation.FAIL_FAST):
        # INITIALIZE
        yield {"stage": LifecycleStage.INITIALIZE, "data": {"graph": "langgraph"}, "context": context}
        
        # Stream from LangGraph
        async for event in self.graph.astream_events(
            {"goal": goal, "context": context.to_dict()},
            version="v2"
        ):
            # Map LangGraph events to lifecycle stages
            if event["event"] == "on_chain_start":
                yield {"stage": LifecycleStage.PLAN, "data": event["data"], "context": context}
            elif event["event"] == "on_tool_start":
                yield {"stage": LifecycleStage.EXECUTE, "data": event["data"], "context": context}
            elif event["event"] == "on_chain_end":
                yield {"stage": LifecycleStage.COMPLETE, "data": event["data"], "context": context}
```

### Pattern 3: Resilient Orchestrator (with Retry)

```python
class ResilientOrchestrator(OrchestratorProtocol):
    def __init__(self, planner, workers, retry_policy):
        self.planner = planner
        self.workers = workers
        self.retry_policy = retry_policy
    
    async def orchestrate(self, goal, context, *, error_strategy=ErrorPropagation.RETRY):
        # INITIALIZE
        yield {"stage": LifecycleStage.INITIALIZE, "data": {}, "context": context}
        
        # PLAN
        plan = await self.planner.plan(goal, context)
        yield {"stage": LifecycleStage.PLAN, "data": {"steps": plan.steps}, "context": context}
        
        # ROUTE + EXECUTE with retry
        for step in plan.steps:
            decision = self.make_routing_decision(step.tool, context, self.workers)
            yield {"stage": LifecycleStage.ROUTE, "data": {"decision": decision}, "context": context}
            
            # Retry loop
            async for attempt in self.retry_policy.retry_generator():
                try:
                    worker = self.workers[decision.target]
                    result = await worker.execute(step, context)
                    yield {"stage": LifecycleStage.EXECUTE, "data": {"result": result}, "context": context}
                    break  # Success
                except Exception as err:
                    mode = classify_error(err)
                    if not mode.retryable or attempt.is_last:
                        raise OrchestrationError(
                            stage=LifecycleStage.EXECUTE,
                            message=str(err),
                            context=context,
                            cause=err,
                            recoverable=mode.retryable
                        )
                    yield {
                        "stage": LifecycleStage.EXECUTE,
                        "data": {
                            "status": "retrying",
                            "attempt": attempt.number,
                            "delay": attempt.delay,
                            "error": str(err)
                        },
                        "context": context
                    }
                    await asyncio.sleep(attempt.delay)
        
        # COMPLETE
        yield {"stage": LifecycleStage.COMPLETE, "data": {"status": "success"}, "context": context}
```

---

## 🧪 Testing Requirements

All orchestrator implementations MUST pass these conformance tests:

### 1. Lifecycle Compliance

```python
async def test_lifecycle_stages_in_order():
    """Orchestrator emits lifecycle stages in correct order."""
    orchestrator = MyOrchestrator(...)
    context = ExecutionContext(trace_id="test-lifecycle", profile="test")
    
    stages = []
    async for event in orchestrator.orchestrate("test goal", context):
        stages.append(event["stage"])
    
    assert stages == [
        LifecycleStage.INITIALIZE,
        LifecycleStage.PLAN,
        LifecycleStage.ROUTE,
        LifecycleStage.EXECUTE,
        LifecycleStage.AGGREGATE,
        LifecycleStage.COMPLETE,
    ], f"Invalid stage order: {stages}"
```

### 2. Trace Continuity

```python
async def test_trace_id_propagation():
    """trace_id flows through all stages without mutation."""
    trace_id = "immutable-trace-123"
    context = ExecutionContext(trace_id=trace_id, profile="test")
    
    async for event in orchestrator.orchestrate("test", context):
        assert event["context"].trace_id == trace_id, \
            f"trace_id mutated: {event['context'].trace_id} != {trace_id}"
```

### 3. Error Handling

```python
async def test_fail_fast_stops_on_error():
    """FAIL_FAST strategy stops immediately on error."""
    orchestrator = MyOrchestrator(...)
    context = ExecutionContext(trace_id="test-fail-fast", profile="test")
    
    stages = []
    try:
        async for event in orchestrator.orchestrate("failing goal", context, error_strategy=ErrorPropagation.FAIL_FAST):
            stages.append(event["stage"])
    except OrchestrationError as err:
        assert err.stage == LifecycleStage.EXECUTE
        assert err.recoverable == False
    
    assert LifecycleStage.COMPLETE not in stages, "Should not complete after error"

async def test_retry_attempts_recovery():
    """RETRY strategy attempts recovery with backoff."""
    orchestrator = MyOrchestrator(...)
    context = ExecutionContext(trace_id="test-retry", profile="test")
    
    retries = 0
    async for event in orchestrator.orchestrate("retryable goal", context, error_strategy=ErrorPropagation.RETRY):
        if event["data"].get("status") == "retrying":
            retries += 1
    
    assert retries > 0, "Should have attempted retries"
```

### 4. Routing Determinism

```python
def test_routing_deterministic():
    """Same inputs produce same routing decision."""
    orchestrator = MyOrchestrator(...)
    context = ExecutionContext(trace_id="test-routing", profile="test")
    
    decision1 = orchestrator.make_routing_decision("task A", context, ["w1", "w2"])
    decision2 = orchestrator.make_routing_decision("task A", context, ["w1", "w2"])
    
    assert decision1.target == decision2.target, "Routing not deterministic"
    assert decision1.reason == decision2.reason, "Routing reason not deterministic"
```

### 5. Partial Results

```python
async def test_partial_results_preserved():
    """Partial results preserved on timeout/failure."""
    orchestrator = MyOrchestrator(...)
    context = ExecutionContext(trace_id="test-partial", profile="test")
    
    try:
        async for event in orchestrator.orchestrate("partial goal", context):
            pass
    except OrchestrationError as err:
        assert "partial_results" in err.metadata, "Partial results not preserved"
        assert len(err.metadata["partial_results"]) > 0, "No partial results captured"
```

---

## 📚 Related Documentation

### Core Specifications
- **[ORCHESTRATOR_CONTRACT.md](ORCHESTRATOR_CONTRACT.md)** - Complete protocol definition with lifecycle stages, routing decisions, error handling
- **[EXECUTION_CONTEXT.md](EXECUTION_CONTEXT.md)** - Immutable context propagation, trace continuity, nested orchestration
- **[FAILURE_MODES.md](FAILURE_MODES.md)** - Comprehensive error taxonomy with retry policies and partial result handling
- **[ROUTING_AUTHORITY.md](ROUTING_AUTHORITY.md)** - Routing decisions, pluggable policies, fallback strategies

### Architecture
- **[System Execution Narrative](../SYSTEM_EXECUTION_NARRATIVE.md)** - Complete request → response flow with orchestrator integration
- **[FastAPI Role](../architecture/FASTAPI_ROLE.md)** - Transport layer vs orchestration separation
- **[Architecture Overview](../../ARCHITECTURE.md)** - High-level system design

### Agent Contracts
- **[Agent I/O Contract](../agents/AGENT_IO_CONTRACT.md)** - AgentRequest/AgentResponse standardization
- **[Agent Lifecycle](../agents/AGENT_LIFECYCLE.md)** - Agent startup/shutdown/health contracts
- **[State Ownership](../agents/STATE_OWNERSHIP.md)** - AGENT vs MEMORY vs ORCHESTRATOR state boundaries

### Testing
- **[Scenario Testing](../testing/SCENARIO_TESTING.md)** - End-to-end orchestration scenario tests
- **[Coverage Matrix](../testing/COVERAGE_MATRIX.md)** - Test coverage by architectural layer

---

## ✅ Quick Reference Checklist

When implementing an orchestrator, ensure:

### Contract Compliance
- [ ] Implements `OrchestratorProtocol` interface
- [ ] Emits lifecycle stages in required order
- [ ] Returns `RoutingDecision` with target, reason, fallback
- [ ] Raises `OrchestrationError` with stage, message, context, cause
- [ ] Provides `AgentLifecycle` via `get_lifecycle()`

### Context Management
- [ ] Accepts immutable `ExecutionContext`
- [ ] Preserves `trace_id` across all events (no mutation)
- [ ] Propagates context to all agents/workers/tools
- [ ] Supports nested orchestration via `parent_context`

### Error Handling
- [ ] Classifies errors using `FailureMode` taxonomy
- [ ] Respects `ErrorPropagation` strategy (fail_fast, retry, fallback, continue)
- [ ] Preserves partial results in error metadata
- [ ] Never silently swallows errors (structured logging with trace_id)

### Routing
- [ ] Routing decisions are deterministic
- [ ] Decisions include justification (reason field)
- [ ] Specifies fallback target for resilience
- [ ] Emits routing decision in trace

### Testing
- [ ] Passes lifecycle compliance tests
- [ ] Passes trace propagation tests
- [ ] Passes error handling tests (all strategies)
- [ ] Passes routing determinism tests
- [ ] Passes partial results tests

---

## 🎓 For New Implementers

### Getting Started

1. **Read the core specifications** (in order):
   - [ORCHESTRATOR_CONTRACT.md](ORCHESTRATOR_CONTRACT.md) - Understand the protocol
   - [EXECUTION_CONTEXT.md](EXECUTION_CONTEXT.md) - Learn context propagation
   - [FAILURE_MODES.md](FAILURE_MODES.md) - Understand error handling
   - [ROUTING_AUTHORITY.md](ROUTING_AUTHORITY.md) - Learn routing patterns

2. **Study reference implementations**:
   - `src/cuga/modular/agents.py` - `CoordinatorAgent` (simple synchronous)
   - `src/cuga/coordinator/core.py` - `Coordinator` (async streaming)
   - `src/cuga/backend/cuga_graph/utils/controller.py` - `AgentRunner` (LangGraph integration)

3. **Review test suites**:
   - `tests/test_orchestrator_protocol.py` - Protocol compliance tests
   - `tests/scenario/test_agent_composition.py` - End-to-end orchestration tests

4. **Implement incrementally**:
   - Start with simple synchronous orchestrator
   - Add error handling and retry logic
   - Add routing policy
   - Add observability and tracing
   - Test against conformance suite

### Common Pitfalls

❌ **Don't**: Mix transport logic (HTTP parsing) in orchestrator  
✅ **Do**: Keep orchestration pure (delegates to Planner/Workers)

❌ **Don't**: Mutate `trace_id` or `ExecutionContext`  
✅ **Do**: Use `.with_*()` methods to create new contexts

❌ **Don't**: Swallow errors silently  
✅ **Do**: Raise structured `OrchestrationError` with stage/cause

❌ **Don't**: Make routing decisions inline  
✅ **Do**: Use `RoutingAuthority` with pluggable policies

❌ **Don't**: Hardcode retry logic  
✅ **Do**: Use `RetryPolicy` with configurable backoff

---

**For questions or contributions, see [CONTRIBUTING.md](../../CONTRIBUTING.md).**
