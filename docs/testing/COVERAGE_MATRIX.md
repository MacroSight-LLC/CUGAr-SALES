# Test Coverage Matrix: Architectural Responsibilities

**Status**: Canonical  
**Last Updated**: 2025-12-31  
**Owner**: Testing & QA Team

## Executive Summary

### Coverage Overview

| Layer | Coverage Status | Test Count | Critical Gaps |
|-------|----------------|------------|---------------|
| **Orchestrator** | ✅ **Good** | 35+ tests | Missing: Full lifecycle integration, nested orchestration |
| **Agents** | ⚠️ **Partial** | 30+ tests | Missing: Planner→Worker→Coordinator E2E flow |
| **Tools** | ⚠️ **Minimal** | 5 tests | Missing: Registry resolution, tool validation, sandbox isolation |
| **Memory** | ❌ **Untested** | 0 tests | Missing: Vector storage, RAG retrieval, persistence |
| **Configuration** | ❌ **Untested** | 0 tests | Missing: Config resolution, env validation, precedence |
| **Observability** | ❌ **Assumed** | 0 tests | Missing: Trace propagation, metrics collection, emitter integration |

**Total Tests**: ~70 tests across 8 test files  
**Architectural Coverage**: **~45%** (orchestrator/agents covered, tools/memory/config untested)  
**Critical Risk**: Orchestration paths untested end-to-end; tool registry/memory/config assumed working

---

## Problem Statement

### What We Know vs. What We Don't Know

```
KNOWN (Tested):
├── Orchestrator Protocol compliance
│   ├── ✅ Lifecycle stage ordering
│   ├── ✅ Trace propagation
│   ├── ✅ Deterministic routing
│   ├── ✅ Error handling
│   └── ✅ Context management
│
├── Agent Lifecycle
│   ├── ✅ Startup/shutdown contracts
│   ├── ✅ State ownership boundaries
│   ├── ✅ Idempotency
│   └── ✅ Resource cleanup
│
├── Failure Modes
│   ├── ✅ Failure taxonomy
│   ├── ✅ Retry policies
│   ├── ✅ Partial results
│   └── ✅ Circuit breakers
│
└── Routing Authority
    ├── ✅ Round-robin policy
    ├── ✅ Capability-based routing
    ├── ✅ Decision validation
    └── ✅ Context immutability

UNKNOWN (Untested):
├── ❌ Orchestration Flow E2E
│   ├── Plan → Route → Execute → Aggregate
│   ├── Nested orchestration (parent → child contexts)
│   ├── Multi-worker coordination
│   └── Streaming execution
│
├── ❌ Tool Registry Integration
│   ├── Tool resolution per profile
│   ├── Sandbox policy enforcement
│   ├── Dynamic tool loading
│   └── Allowlist/denylist validation
│
├── ❌ Memory Layer
│   ├── Vector embedding/retrieval
│   ├── RAG query flow
│   ├── Memory isolation per profile
│   └── Persistence/cleanup
│
├── ❌ Configuration Resolution
│   ├── 7-layer precedence
│   ├── Deep merge strategies
│   ├── Environment validation per mode
│   └── Config provenance tracking
│
└── ❌ Observability Chain
    ├── Trace propagation through layers
    ├── Span collection (OTEL/Langfuse)
    ├── Metrics aggregation
    └── Error context enrichment

ASSUMED (No Evidence):
├── ? FastAPI integration paths
├── ? LangGraph node routing
├── ? MCP server lifecycle
└── ? Budget enforcement middleware
```

---

## Layer-by-Layer Coverage Analysis

### 1. Orchestrator Layer

**Coverage**: ✅ **Good** (35+ tests, ~80% coverage)

#### Tested Components

**OrchestratorProtocol** (`test_orchestrator_protocol.py`):
- ✅ Lifecycle stage compliance (initialize → plan → route → execute → aggregate → complete)
- ✅ Trace propagation (parent → child context chaining)
- ✅ Deterministic routing (ReferenceOrchestrator implementation)
- ✅ Error handling (OrchestrationError propagation)
- ✅ Context management (ExecutionContext immutability, with_* methods)
- ✅ Lifecycle manager (stage transitions, validation)
- ✅ Reference implementation (end-to-end orchestration)
- ✅ Integration tests (orchestrator + workers)

**Test Classes** (9 classes, 35+ tests):
1. `TestLifecycleCompliance` - Stage ordering, stage emission
2. `TestTracePropagation` - Parent context chaining, trace ID continuity
3. `TestDeterministicRouting` - Worker selection consistency
4. `TestErrorHandling` - Error propagation, structured errors
5. `TestContextManagement` - Immutability, metadata propagation
6. `TestLifecycleManager` - State transitions, validation
7. `TestReferenceImplementation` - Concrete orchestrator
8. `TestOrchestratorIntegration` - Multi-worker coordination
9. (Fixtures) - `orchestrator()`, `context()`

**Test Example**:
```python
@pytest.mark.asyncio
async def test_lifecycle_stages_in_order(self, orchestrator, context):
    """Orchestrator emits lifecycle stages in correct order."""
    stages = []
    async for event in orchestrator.orchestrate("test goal", context):
        stages.append(event["stage"])
    
    expected = [
        LifecycleStage.INITIALIZE,
        LifecycleStage.PLAN,
        LifecycleStage.ROUTE,
        LifecycleStage.EXECUTE,
        LifecycleStage.AGGREGATE,
        LifecycleStage.COMPLETE,
    ]
    assert stages == expected
```

#### Coverage Gaps

❌ **Missing Tests**:
1. **Nested Orchestration**: Parent orchestrator spawning child orchestrators
   - Parent context → child context propagation
   - Nested trace ID management
   - Resource cleanup on nested failures
   
2. **Full Lifecycle Integration**: Planner → Coordinator → Worker → Tools → Memory
   - End-to-end flow with real components (not mocks)
   - Streaming execution with backpressure
   - Multi-step plan with tool dependencies
   
3. **Concurrent Orchestration**: Multiple orchestrators running in parallel
   - Resource contention (shared memory, workers)
   - Trace ID collision prevention
   - Coordinator scheduling under load
   
4. **Error Recovery Paths**: Failure modes at each lifecycle stage
   - Plan failure → fallback planning
   - Route failure → alternative routing
   - Execute failure → partial result recovery
   - Aggregate failure → incomplete results handling

**Risk**: High - Orchestration is the core control flow. Untested paths may hide race conditions, deadlocks, or resource leaks.

---

### 2. Agents Layer

**Coverage**: ⚠️ **Partial** (30+ tests, ~60% coverage)

#### Tested Components

**AgentLifecycleProtocol** (`test_agent_lifecycle.py`):
- ✅ Startup contracts (idempotency, timeout, atomic initialization)
- ✅ Shutdown contracts (error-safe, timeout-bounded, no exceptions)
- ✅ State ownership boundaries (AGENT/MEMORY/ORCHESTRATOR)
- ✅ State violations (mutation rules, ownership checks)
- ✅ Resource management (cleanup on shutdown)
- ✅ Lifecycle compliance (state transitions, validation)

**AgentProtocol (I/O Contract)** (`test_agent_contracts.py`):
- ✅ AgentRequest structure (goal, task, metadata, inputs, context, constraints)
- ✅ AgentResponse structure (status, result, error, trace, metadata)
- ✅ Structured error handling (no exceptions, ErrorType taxonomy)
- ✅ Metadata/trace propagation (request → response continuity)
- ✅ Validation compliance (schema checks, required fields)
- ✅ Response factory functions (success_response, error_response, partial_response)

**Test Classes** (20+ classes, 30+ tests):
1. `TestAgent` (lifecycle) - ManagedAgent implementation
2. `TestStartupContract` - Idempotency, timeout, atomic init
3. `TestShutdownContract` - Error-safe, timeout, resource cleanup
4. `TestStateOwnership` - Agent/memory/orchestrator boundaries
5. `TestStateViolations` - Mutation rules, ownership checks
6. `TestResourceManagement` - Memory leaks, file handles
7. `TestAgent` (contracts) - TestAgent implementation for I/O testing
8. `TestAgentRequest` - Request structure validation
9. `TestAgentResponse` - Response structure validation
10. `TestResponseFactory` - success/error/partial factories
11. (Many more contract validation tests)

**Test Example**:
```python
@pytest.mark.asyncio
async def test_startup_idempotency(self):
    """Multiple startup calls should be safe."""
    agent = TestAgent()
    
    await agent.startup()
    state1 = agent.state
    
    await agent.startup()  # Second call
    state2 = agent.state
    
    assert state1 == state2  # State unchanged
    assert agent.startup_count == 1  # Only initialized once
```

#### Coverage Gaps

❌ **Missing Tests**:
1. **PlannerAgent Integration**: End-to-end planning flow
   - Goal → tool ranking → plan generation
   - Vector similarity scoring
   - Plan validation (max steps, temperature clamping)
   - Streaming plan updates
   
2. **WorkerAgent Execution**: Tool execution flow
   - Plan step → tool resolution → handler invocation
   - Error handling per step (continue vs. abort)
   - Trace propagation through execution
   - Budget enforcement during execution
   
3. **CoordinatorAgent Orchestration**: Multi-worker coordination
   - Round-robin scheduling (concurrent calls)
   - Worker failure handling (retry, fallback)
   - Plan distribution across workers
   - Result aggregation from multiple workers
   
4. **Planner → Worker → Coordinator Flow**: Full agent stack
   - Goal → Plan → Dispatch → Execute → Aggregate
   - Memory sharing across agents
   - Trace continuity through all layers
   - Failure propagation and recovery

**Risk**: Medium-High - Agent contracts are tested, but integration is assumed. Real planner/worker/coordinator behavior untested.

---

### 3. Failure Modes Layer

**Coverage**: ✅ **Good** (60+ tests, ~85% coverage)

#### Tested Components

**FailureMode Taxonomy** (`test_failure_modes.py`):
- ✅ Failure categories (AGENT/SYSTEM/RESOURCE/POLICY/USER)
- ✅ Retryable vs. terminal failures
- ✅ Failure severity levels
- ✅ Partial success states

**PartialResult** (`test_failure_modes.py`):
- ✅ Partial result structure (completed/pending/failed steps)
- ✅ Recovery from partial execution
- ✅ Result merging
- ✅ Serialization/deserialization

**FailureContext** (`test_failure_modes.py`):
- ✅ Context enrichment (trace_id, stage, operation)
- ✅ Error propagation through layers
- ✅ Context immutability
- ✅ Debug information capture

**RetryPolicies** (`test_failure_modes.py`):
- ✅ ExponentialBackoffPolicy (delay calculation, jitter, max attempts)
- ✅ LinearBackoffPolicy (fixed increments)
- ✅ NoRetryPolicy (fail-fast)
- ✅ Auto-detection based on FailureMode
- ✅ Circuit breaker integration

**RetryExecutor** (`test_failure_modes.py`):
- ✅ Retry loop execution
- ✅ Backoff timing
- ✅ Max attempt enforcement
- ✅ Failure mode propagation
- ✅ Partial result preservation

**Test Classes** (6 classes, 60+ tests):
1. `TestFailureMode` - Category/retryable/severity checks
2. `TestPartialResult` - Structure, recovery, merging
3. `TestFailureContext` - Enrichment, propagation, immutability
4. `TestRetryPolicies` - Exponential/linear/none policies
5. `TestRetryExecutor` - Retry loop, backoff, max attempts
6. `TestRetryCompliance` - Integration with orchestrator

**Test Example**:
```python
def test_exponential_backoff_delay(self):
    """Exponential backoff doubles delay each attempt."""
    policy = ExponentialBackoffPolicy(base_delay=1.0, max_attempts=5)
    
    delays = [policy.get_delay(attempt) for attempt in range(1, 6)]
    expected = [1.0, 2.0, 4.0, 8.0, 16.0]
    
    for actual, expect in zip(delays, expected):
        assert 0.9 * expect <= actual <= 1.1 * expect  # Allow jitter
```

#### Coverage Gaps

❌ **Missing Tests**:
1. **Circuit Breaker State Transitions**: Open → half-open → closed
   - Failure threshold triggering
   - Timeout-based recovery
   - Success count reset
   
2. **Distributed Retry Coordination**: Multiple orchestrators sharing state
   - Retry attempt synchronization
   - Circuit breaker state sharing
   - Quota management across instances

**Risk**: Low - Failure modes well-tested, minor gaps in circuit breaker and distributed scenarios.

---

### 4. Routing Authority Layer

**Coverage**: ✅ **Good** (50+ tests, ~80% coverage)

#### Tested Components

**RoutingContext** (`test_routing_authority.py`):
- ✅ Context immutability (frozen dataclass)
- ✅ with_goal/with_task methods
- ✅ Parent context chaining
- ✅ Metadata propagation

**RoutingDecision** (`test_routing_authority.py`):
- ✅ Decision validation (reason required, confidence 0.0-1.0)
- ✅ Alternatives documentation
- ✅ Strategy/type tagging
- ✅ Serialization

**RoundRobinPolicy** (`test_routing_authority.py`):
- ✅ Fair distribution across workers
- ✅ Thread-safe selection
- ✅ Wraparound behavior
- ✅ Empty candidate handling

**CapabilityBasedPolicy** (`test_routing_authority.py`):
- ✅ Capability matching (required/optional/preferred)
- ✅ Score calculation
- ✅ Best-match selection
- ✅ Fallback behavior

**PolicyBasedRoutingAuthority** (`test_routing_authority.py`):
- ✅ Policy delegation
- ✅ Decision logging
- ✅ Context propagation
- ✅ Error handling

**Test Classes** (8 classes, 50+ tests):
1. `TestRoutingContext` - Immutability, with_* methods
2. `TestRoutingDecision` - Validation, alternatives
3. `TestRoundRobinPolicy` - Fair distribution, thread safety
4. `TestCapabilityBasedPolicy` - Capability matching, scoring
5. `TestPolicyBasedRoutingAuthority` - Policy delegation
6. `TestRoutingAuthorityFactory` - Policy creation
7. `TestRoutingCompliance` - No routing bypasses
8. `TestRoutingObservability` - Decision tracing

**Test Example**:
```python
def test_round_robin_fairness(self):
    """Round-robin distributes work fairly."""
    policy = RoundRobinPolicy()
    candidates = [
        RoutingCandidate(id="1", name="w1", type="worker"),
        RoutingCandidate(id="2", name="w2", type="worker"),
        RoutingCandidate(id="3", name="w3", type="worker"),
    ]
    
    selections = [policy.select(candidates, context).selected.id 
                  for _ in range(9)]
    
    assert selections == ["1", "2", "3", "1", "2", "3", "1", "2", "3"]
```

#### Coverage Gaps

❌ **Missing Tests**:
1. **Load-Balanced Routing**: Worker load tracking and balancing
2. **Affinity-Based Routing**: Sticky routing per user/session
3. **Routing Metrics**: Decision latency, policy effectiveness

**Risk**: Low - Core routing well-tested, advanced strategies assumed.

---

### 5. Tools Layer

**Coverage**: ❌ **Minimal** (5 tests, ~10% coverage)

#### Tested Components

**RegistryBasedRunner** (`test_registry_sandboxing.py`):
- ✅ Registry loading (tools, policies from registry.yaml)
- ✅ Successful execution (python_code_interpreter)
- ✅ Runtime error capture (division by zero)
- ✅ Wall-clock timeout (infinite loops)
- ✅ Policy enforcement (basic checks)

**Test Classes** (1 class, 5 tests):
1. `TestRegistrySandboxing` - Registry loading, execution, errors, timeout

**Test Example**:
```python
def test_successful_execution(self):
    """Test basic python_code_interpreter execution."""
    result = self.runner.run_tool("python_code_interpreter", "print(2 + 2)")
    
    assert result.error is None
    assert result.output == "4"
```

#### Coverage Gaps

❌ **CRITICAL MISSING TESTS**:
1. **ToolRegistry Resolution**: Profile-based tool lookup
   - Allowlist/denylist enforcement
   - Tool visibility per profile
   - Handler resolution and caching
   
2. **Tool Validation**: Input/output schema validation
   - Parameter type checking
   - Required field validation
   - Output format compliance
   
3. **Sandbox Isolation**: Security boundary enforcement
   - No eval/exec usage
   - File system restrictions
   - Network access control
   - Resource limits (CPU, memory, disk)
   
4. **Dynamic Tool Loading**: `cuga.modular.tools.*` imports
   - Import path validation
   - Denylist rejection
   - Module reloading
   
5. **Policy Enforcement**: PolicyEnforcer integration
   - Tool allowlist per profile
   - Budget ceiling enforcement
   - Escalation limits
   - Redaction rules
   
6. **Tool Registry Integration**: End-to-end tool flow
   - Registry → Planner (tool ranking)
   - Registry → Worker (tool execution)
   - Registry → Coordinator (tool availability)

**Risk**: **CRITICAL** - Tools are the primary execution surface. No tests for registry resolution, validation, or security boundaries. **HIGHEST PRIORITY GAP**.

---

### 6. Memory Layer

**Coverage**: ❌ **UNTESTED** (0 tests, 0% coverage)

#### Untested Components

**VectorMemory** (NO TESTS):
- ❌ Embedding generation (deterministic hashing)
- ❌ Vector storage (in-memory, Chroma, Qdrant, Weaviate, Milvus)
- ❌ Similarity search (query → top-k results)
- ❌ Profile isolation (no cross-profile leakage)
- ❌ Metadata persistence (path, profile, timestamp)

**MemoryStore** (NO TESTS):
- ❌ Session state management (load/save per session_id)
- ❌ User history tracking (cross-session continuity)
- ❌ Conversation context (thread-aware memory)
- ❌ Memory cleanup (stale session pruning)

**RagRetriever** (NO TESTS):
- ❌ RAG query flow (query → retrieve → rank → return)
- ❌ Backend validation (Chroma/Qdrant/local checks)
- ❌ Scored hit ranking (relevance ordering)
- ❌ Context window management (token limits)

**Memory Integration** (NO TESTS):
- ❌ Planner → Memory (tool ranking from past successes)
- ❌ Worker → Memory (execution traces stored)
- ❌ Coordinator → Memory (shared state across workers)
- ❌ Orchestrator → Memory (context persistence)

**Risk**: **HIGH** - Memory is assumed working but untested. Bugs could cause data loss, cross-profile leakage, or query failures.

---

### 7. Configuration Layer

**Coverage**: ❌ **UNTESTED** (0 tests, 0% coverage)

#### Untested Components

**ConfigResolver** (NO TESTS):
- ❌ 7-layer precedence (CLI > env > .env > YAML > TOML > defaults > hardcoded)
- ❌ Deep merge strategies (dicts merged, lists/scalars overridden)
- ❌ Provenance tracking (which layer provided which value)
- ❌ Schema validation (required fields, type constraints, dependencies)

**Environment Validation** (NO TESTS):
- ❌ Mode-specific requirements (local/service/MCP/test)
- ❌ Required vs. optional vs. conditional variables
- ❌ Dependency validation (LANGFUSE_ENABLED requires keys)
- ❌ Helpful error messages (suggest missing vars)

**Configuration Sources** (NO TESTS):
- ❌ Dynaconf loader (settings.toml)
- ❌ Hydra loader (config/ registry fragments)
- ❌ Dotenv loader (.env, .env.mcp)
- ❌ Direct YAML/TOML loaders

**Configuration Integration** (NO TESTS):
- ❌ Orchestrator configuration (planner strategy, max steps, temperature)
- ❌ Agent configuration (profile, budget, escalation)
- ❌ Tool configuration (registry path, sandbox profiles)
- ❌ Observability configuration (OTEL, Langfuse, LangSmith)

**Risk**: **MEDIUM** - Configuration is documented but implementation untested. Precedence bugs could cause production misconfigurations.

---

### 8. Observability Layer

**Coverage**: ❌ **ASSUMED** (0 tests, 0% coverage)

#### Untested Components

**Trace Propagation** (NO TESTS):
- ❌ Trace ID continuity (orchestrator → agent → tool → memory)
- ❌ Parent context chaining (nested orchestrations)
- ❌ Span collection (lifecycle stages, tool executions)
- ❌ Context enrichment (metadata, errors, timing)

**Metrics Collection** (NO TESTS):
- ❌ OrchestratorMetrics (duration, step count, error count)
- ❌ Agent metrics (startup time, execution time, failure rate)
- ❌ Tool metrics (invocation count, success rate, latency)
- ❌ Memory metrics (query latency, hit rate, storage size)

**Emitter Integration** (NO TESTS):
- ❌ LangfuseEmitter (trace upload, span hierarchy)
- ❌ OpenInferenceEmitter (OTEL compatibility)
- ❌ LangSmithEmitter (LangChain integration)
- ❌ Local JSON emitter (file-based traces)

**Observability Integration** (NO TESTS):
- ❌ Orchestrator → emitter (lifecycle events)
- ❌ Agent → emitter (execution traces)
- ❌ Tool → emitter (handler invocations)
- ❌ Error → emitter (failure context enrichment)

**Risk**: **MEDIUM** - Observability is critical for debugging production issues. No tests for trace continuity or emitter integration.

---

## Critical Path Analysis

### What Are the Critical Orchestration Paths?

**Definition**: A critical path is an end-to-end flow through multiple architectural layers that delivers user-facing value. Untested critical paths represent **production deployment risks**.

### Path 1: Single-Goal Planning and Execution

**Flow**: User goal → Planner → Coordinator → Worker → Tool → Result

**Components**:
1. FastAPI `/plan` endpoint receives goal
2. Planner ranks tools by similarity
3. Coordinator dispatches plan to worker (round-robin)
4. Worker executes steps via ToolRegistry
5. Tool handler runs in sandbox
6. Results aggregated and returned

**Test Status**: ❌ **UNTESTED END-TO-END**
- ✅ FastAPI endpoint exists (`src/cuga/backend/app.py`)
- ✅ Planner exists (`src/cuga/planner/core.py`)
- ✅ Coordinator exists (`src/cuga/coordinator/core.py`)
- ✅ Worker exists (`src/cuga/workers/base.py`)
- ⚠️ ToolRegistry tested in isolation (1 test)
- ❌ No integration test connecting all components

**Gap**: No test validates the full request-to-response flow with real components.

**Impact**: **HIGH** - This is the primary user-facing flow. Untested.

**Recommendation**: Create `tests/integration/test_planning_execution_flow.py` with end-to-end test using real planner, coordinator, worker, registry, and tool.

---

### Path 2: Multi-Worker Coordination

**Flow**: Complex goal → Planner → Plan (multi-step) → Coordinator → Workers (parallel) → Result aggregation

**Components**:
1. Planner generates multi-step plan
2. Coordinator dispatches steps to workers (round-robin)
3. Multiple workers execute in parallel
4. Coordinator aggregates results
5. Streaming results to client (SSE)

**Test Status**: ⚠️ **PARTIAL**
- ✅ Round-robin policy tested (`test_routing_authority.py`)
- ✅ Coordinator exists (`src/cuga/coordinator/core.py`)
- ⚠️ Worker exists (`src/cuga/workers/base.py`) but not tested with coordinator
- ❌ No test for parallel execution
- ❌ No test for result aggregation
- ❌ No test for streaming (SSE)

**Gap**: Coordinator scheduling tested in isolation, but not with real workers under parallel load.

**Impact**: **MEDIUM-HIGH** - Multi-worker coordination is a key differentiator. Untested under concurrent load.

**Recommendation**: Create `tests/integration/test_multi_worker_coordination.py` with concurrent worker execution, result aggregation, and streaming.

---

### Path 3: Nested Orchestration (Parent → Child)

**Flow**: Complex goal → Parent orchestrator → Sub-goals → Child orchestrators → Aggregated result

**Components**:
1. Parent orchestrator receives complex goal
2. Parent decomposes into sub-goals
3. Child orchestrators spawned for sub-goals
4. Parent context → child contexts (trace continuity)
5. Child results aggregated by parent
6. Final result returned

**Test Status**: ❌ **UNTESTED**
- ✅ OrchestratorProtocol supports nesting (parent_context field)
- ✅ ExecutionContext supports parent_context chaining
- ❌ No test for spawning child orchestrators
- ❌ No test for context propagation (parent → child)
- ❌ No test for result aggregation (children → parent)

**Gap**: Nested orchestration is architecturally supported but never tested.

**Impact**: **MEDIUM** - Nested orchestration is advanced use case. May not be needed immediately but should be validated.

**Recommendation**: Create `tests/integration/test_nested_orchestration.py` validating parent → child orchestration with context chaining.

---

### Path 4: Error Recovery with Retry

**Flow**: Goal → Execution → Failure → Retry → Success/Partial/Terminal

**Components**:
1. Worker executes tool
2. Tool fails (network timeout, API unavailable)
3. FailureMode categorized (retryable)
4. RetryPolicy calculates backoff
5. RetryExecutor retries operation
6. Success or partial result returned

**Test Status**: ⚠️ **PARTIAL**
- ✅ FailureMode taxonomy tested (`test_failure_modes.py`)
- ✅ RetryPolicy tested (`test_failure_modes.py`)
- ✅ RetryExecutor tested (`test_failure_modes.py`)
- ❌ No integration with real Worker execution
- ❌ No test for orchestrator-level retry (coordinator → worker retry)

**Gap**: Retry logic tested in isolation, but not integrated with worker execution or orchestrator error handling.

**Impact**: **MEDIUM** - Retry is critical for resilience. Need to validate integration.

**Recommendation**: Create `tests/integration/test_error_recovery_flow.py` with tool failure, retry policy, and partial result recovery.

---

### Path 5: Memory-Augmented Planning

**Flow**: Goal → Memory query (past successes) → Tool ranking → Execution → Result stored

**Components**:
1. Planner queries VectorMemory for past successes
2. Tool ranking influenced by memory scores
3. Worker executes plan
4. Execution traces stored in memory
5. Future planners benefit from learned patterns

**Test Status**: ❌ **UNTESTED**
- ✅ VectorMemory exists (`src/cuga/memory/vector.py`)
- ✅ Planner exists (`src/cuga/planner/core.py`)
- ❌ No test for planner → memory integration
- ❌ No test for memory → tool ranking
- ❌ No test for execution traces stored
- ❌ No test for memory-influenced planning

**Gap**: Memory layer completely untested. Integration with planner assumed.

**Impact**: **HIGH** - If memory doesn't work, planning quality degrades. Critical for user experience.

**Recommendation**: Create `tests/integration/test_memory_augmented_planning.py` validating memory query, tool ranking influence, and trace storage.

---

### Path 6: Profile-Based Tool Isolation

**Flow**: Goal + Profile → Tool filtering → Sandbox execution → Policy enforcement → Result

**Components**:
1. ExecutionContext includes profile (demo_power, production, restricted)
2. ToolRegistry filters tools by profile allowlist
3. PolicyEnforcer validates tool access
4. Sandbox executes tool with profile constraints
5. Budget/escalation enforced per profile

**Test Status**: ❌ **UNTESTED**
- ✅ ExecutionContext includes profile field
- ✅ ToolRegistry exists (`src/cuga/tools/registry.py`)
- ✅ PolicyEnforcer exists (`src/cuga/agents/policy.py`)
- ⚠️ RegistryBasedRunner tested (1 test) but not profile-aware
- ❌ No test for profile-based tool filtering
- ❌ No test for policy enforcement per profile
- ❌ No test for budget enforcement

**Gap**: Profile isolation is architectural cornerstone but untested.

**Impact**: **CRITICAL** - Profile isolation prevents security breaches. Must be tested.

**Recommendation**: Create `tests/integration/test_profile_based_isolation.py` with profile filtering, policy enforcement, and budget checks.

---

## Testing Strategy Recommendations

### Priority 1: Fill Critical Gaps (Next Sprint)

**Objective**: Test critical orchestration paths end-to-end

**Tasks**:
1. ✅ **Path 1**: Create `tests/integration/test_planning_execution_flow.py`
   - Test: User goal → Planner → Coordinator → Worker → Tool → Result
   - Validates: End-to-end request-to-response flow
   - Estimated Effort: 4 hours
   
2. ✅ **Path 6**: Create `tests/integration/test_profile_based_isolation.py`
   - Test: Profile filtering, policy enforcement, budget checks
   - Validates: Security boundaries per profile
   - Estimated Effort: 6 hours
   
3. ✅ **Path 5**: Create `tests/integration/test_memory_augmented_planning.py`
   - Test: Memory query, tool ranking influence, trace storage
   - Validates: Memory layer integration
   - Estimated Effort: 6 hours

**Total Effort**: ~16 hours (2 developer-days)

---

### Priority 2: Test Tool/Memory/Config Layers (Next Month)

**Objective**: Validate untested architectural layers

**Tasks**:
1. ✅ **Tools**: Create `tests/unit/test_tool_registry.py`
   - Test: Registry resolution, allowlist/denylist, tool validation
   - Estimated Effort: 8 hours
   
2. ✅ **Memory**: Create `tests/unit/test_vector_memory.py`
   - Test: Embedding, storage, similarity search, profile isolation
   - Estimated Effort: 8 hours
   
3. ✅ **Config**: Create `tests/unit/test_config_resolver.py`
   - Test: Precedence layers, deep merge, env validation
   - Estimated Effort: 8 hours

**Total Effort**: ~24 hours (3 developer-days)

---

### Priority 3: Integration Testing Suite (Quarter)

**Objective**: Build comprehensive integration test suite

**Tasks**:
1. ✅ **Path 2**: Multi-worker coordination (`tests/integration/test_multi_worker_coordination.py`)
2. ✅ **Path 3**: Nested orchestration (`tests/integration/test_nested_orchestration.py`)
3. ✅ **Path 4**: Error recovery flow (`tests/integration/test_error_recovery_flow.py`)
4. ✅ **Observability**: Trace propagation (`tests/integration/test_observability_chain.py`)
5. ✅ **FastAPI**: HTTP endpoints (`tests/integration/test_fastapi_endpoints.py`)

**Total Effort**: ~40 hours (5 developer-days)

---

### Priority 4: Scenario Testing (Ongoing)

**Objective**: Validate real-world use cases

**Tasks**:
1. ✅ **Stateful Agent**: Already exists (`tests/scenario/test_stateful_agent.py`)
2. ⏳ **Multi-Agent Dispatch**: CrewAI/AutoGen style coordination
3. ⏳ **RAG Query Flow**: Document ingestion → query → retrieval → answer
4. ⏳ **Streaming Execution**: Long-running plan with SSE updates
5. ⏳ **Budget Enforcement**: Request exceeds budget ceiling

**Total Effort**: ~60 hours (7.5 developer-days)

---

## Test Ownership and Maintenance

### Layer Ownership

| Layer | Primary Owner | Secondary Owner | Test Files |
|-------|---------------|-----------------|------------|
| **Orchestrator** | Platform Team | Orchestration Team | `test_orchestrator_protocol.py` |
| **Agents** | Agent Team | Orchestration Team | `test_agent_lifecycle.py`, `test_agent_contracts.py` |
| **Failure Modes** | Platform Team | Agent Team | `test_failure_modes.py` |
| **Routing** | Orchestration Team | Platform Team | `test_routing_authority.py` |
| **Tools** | ⚠️ **UNASSIGNED** | Registry Team | `test_registry_sandboxing.py` (minimal) |
| **Memory** | ⚠️ **UNASSIGNED** | RAG Team | ❌ None |
| **Configuration** | ⚠️ **UNASSIGNED** | Platform Team | ❌ None |
| **Observability** | ⚠️ **UNASSIGNED** | Platform Team | ❌ None |

**Action Required**: Assign ownership for Tools, Memory, Configuration, and Observability layers.

---

### Test Maintenance Guidelines

**When to Update Tests**:
1. **Protocol Changes**: If OrchestratorProtocol, AgentProtocol, or contracts change
2. **New Failure Modes**: When adding new FailureMode variants
3. **New Routing Policies**: When implementing new RoutingPolicy types
4. **New Tools**: When adding tools to registry
5. **Configuration Changes**: When modifying config schema or precedence
6. **Observability Changes**: When adding new emitters or metrics

**Test Review Checklist**:
- [ ] All new features have corresponding tests
- [ ] All modified components have updated tests
- [ ] Integration tests cover new orchestration paths
- [ ] Scenario tests validate real-world use cases
- [ ] Test coverage >80% for modified files
- [ ] No flaky tests (pass consistently on CI)
- [ ] Tests run in <5 minutes (unit), <15 minutes (integration)

---

## Appendix: Test File Inventory

### Root Tests (`tests/`)

1. **test_orchestrator_protocol.py** (301 lines)
   - Classes: 9
   - Tests: ~35
   - Coverage: OrchestratorProtocol lifecycle, trace propagation, routing, errors, context
   
2. **test_agent_lifecycle.py** (370+ lines)
   - Classes: 10+
   - Tests: ~30
   - Coverage: Startup/shutdown contracts, state ownership, resource management
   
3. **test_agent_contracts.py** (589 lines)
   - Classes: 15+
   - Tests: ~40
   - Coverage: AgentRequest/Response, validation, error handling, factories
   
4. **test_failure_modes.py** (652 lines)
   - Classes: 6
   - Tests: ~60
   - Coverage: FailureMode taxonomy, PartialResult, FailureContext, RetryPolicies, RetryExecutor
   
5. **test_routing_authority.py** (387 lines)
   - Classes: 8
   - Tests: ~50
   - Coverage: RoutingContext, RoutingDecision, RoundRobin, CapabilityBased, Authority

### Unit Tests (`tests/unit/`)

6. **test_registry_sandboxing.py** (115 lines)
   - Classes: 1
   - Tests: 5
   - Coverage: Registry loading, tool execution, errors, timeout

### Scenario Tests (`tests/scenario/`)

6. **test_registry_sandboxing.py** (115 lines)
   - Classes: 1
   - Tests: 5
   - Coverage: Registry loading, tool execution, errors, timeout

7. **test_stateful_agent.py** (89 lines)
   - Classes: 1
   - Tests: 1
   - Coverage: Multi-turn conversation, memory persistence, sandboxing

8. **test_agent_composition.py** (NEW - 650+ lines)
   - Classes: 8
   - Tests: 13
   - Coverage: Multi-agent dispatch, memory-augmented planning, profile-based isolation, error recovery, streaming, stateful conversations, complex workflows, nested coordination

### Backend Tests (`src/cuga/backend/tools_env/registry/tests/`)

8. **test_e2e_api_registry.py**
   - Coverage: MCP server E2E, API registry integration
   
9. **test_mcp_server.py**
   - Coverage: MCP protocol implementation
   
10. **test_mixed_configuration.py**
    - Coverage: Configuration merging
    
11. **test_legacy_openapi.py**
    - Coverage: OpenAPI schema generation
    
12. **test_enum_handling.py**
    - Coverage: Enum serialization
    
13. **test_auth/** (directory)
    - Files: test_apply_authentication.py, test_auth_e2e.py
    - Coverage: MCP authentication

**Total Test Files**: ~68 files (9 root tests, 1 new scenario test, 60+ backend tests)  
**Total Test Functions**: ~83 in root tests (70 before + 13 new scenario tests), ~100+ in backend tests  
**Total Lines of Test Code**: ~6500+ lines (~5000 before + 650 new scenario tests + 850 backend tests)

---

## Change Management

### Documentation Updates Required

When test coverage changes (new tests added, gaps filled):

1. **Update this file** (`docs/testing/COVERAGE_MATRIX.md`)
   - Update coverage percentages
   - Move gaps from "Missing Tests" to "Tested Components"
   - Update risk assessments
   
2. **Update TESTING.md**
   - Add new test categories
   - Update test running instructions
   - Document new test patterns
   
3. **Update AGENTS.md**
   - Update "Verification & No Conflicting Guardrails" section
   - Document new testing requirements
   
4. **Update CHANGELOG.md**
   - Record coverage improvements
   - Note critical gaps filled

### CI/CD Integration

**Current Status**: ❓ **UNKNOWN**
- No information on CI/CD test execution
- No coverage reports mentioned
- No automated test enforcement

**Recommended CI/CD Changes**:
1. **Coverage Gating**: Fail PR if coverage drops below 80%
2. **Integration Test Stage**: Separate stage for integration tests (longer timeout)
3. **Scenario Test Stage**: Nightly runs for scenario tests (slow, real services)
4. **Coverage Reports**: Codecov/Coveralls integration
5. **Test Duration Limits**: Fail if tests take >15 minutes

---

## FAQ

### Q: Why is orchestration untested end-to-end?

**A**: Tests focus on component compliance (protocols, contracts) but assume integration. This is common in early development but risky for production deployment.

**Recommendation**: Prioritize Path 1 (planning → execution flow) integration test.

### Q: Why are tools/memory/config untested?

**A**: Likely due to test prioritization focusing on orchestrator/agent contracts first. These layers may have been considered "implementation details" rather than architectural responsibilities.

**Recommendation**: Tools layer is **CRITICAL** (security boundary). Memory is **HIGH** priority (data loss risk). Config is **MEDIUM** priority (operational risk).

### Q: What's the risk of deploying with current coverage?

**A**:
- **Orchestrator**: Medium risk (protocols tested, integration assumed)
- **Agents**: Medium risk (contracts tested, real planner/worker/coordinator untested)
- **Tools**: **HIGH RISK** (security boundaries untested, registry resolution untested)
- **Memory**: **HIGH RISK** (data persistence untested, profile isolation untested)
- **Config**: Medium risk (documentation exists, implementation untested)
- **Observability**: Low-medium risk (can add post-deployment, not user-facing)

**Overall Risk**: **HIGH** - Tools and memory gaps represent production deployment blockers.

### Q: What should we test first?

**Priority Order**:
1. **Path 6**: Profile-based tool isolation (security boundary)
2. **Path 1**: Planning → execution flow (user-facing)
3. **Path 5**: Memory-augmented planning (data integrity)
4. **Tools layer**: Registry resolution, validation, sandbox
5. **Memory layer**: Vector storage, RAG retrieval
6. **Path 2**: Multi-worker coordination (scalability)

### Q: How do we prevent test rot?

**Strategies**:
1. **Test ownership**: Assign layers to teams
2. **CI/CD enforcement**: Fail PRs without tests
3. **Coverage gating**: Maintain >80% coverage
4. **Quarterly reviews**: Audit coverage matrix
5. **Integration test suite**: Run nightly against real services

---

**See Also**:
- `TESTING.md` - Test running instructions, patterns
- `AGENTS.md` - Guardrail verification requirements
- `docs/orchestrator/ORCHESTRATOR_CONTRACT.md` - Protocol under test
- `docs/agents/AGENT_LIFECYCLE.md` - Lifecycle contracts under test
- `docs/agents/AGENT_IO_CONTRACT.md` - I/O contracts under test
