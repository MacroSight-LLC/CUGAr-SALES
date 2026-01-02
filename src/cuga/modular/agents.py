from __future__ import annotations

import threading
import time
import warnings
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional

from .config import AgentConfig
from .llm.interface import LLM, MockLLM
from .memory import VectorMemory
from .tools import ToolRegistry, ToolSpec

# Observability infrastructure (v1.1.0+)
from cuga.observability import (
    PlanEvent,
    RouteEvent,
    ToolCallEvent,
    BudgetEvent,
    emit_event,
    get_collector,
)

# Legacy imports (deprecated in v1.1.0, will be removed in v1.3.0)
try:
    from .observability import BaseEmitter
    _LEGACY_OBSERVABILITY_AVAILABLE = True
except ImportError:
    BaseEmitter = None  # type: ignore
    _LEGACY_OBSERVABILITY_AVAILABLE = False

# Guardrails infrastructure (optional - only use if available)
try:
    from cuga.backend.guardrails.policy import GuardrailPolicy, budget_guard
    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False
    GuardrailPolicy = None  # type: ignore
    budget_guard = None  # type: ignore


@dataclass
class AgentPlan:
    steps: List[dict]
    trace: List[dict] = field(default_factory=list)


@dataclass
class AgentResult:
    output: Any
    trace: List[dict] = field(default_factory=list)


@dataclass
class PlannerAgent:
    registry: ToolRegistry
    memory: VectorMemory
    config: AgentConfig = field(default_factory=AgentConfig.from_env)
    llm: LLM = field(default_factory=MockLLM)

    def plan(self, goal: str, metadata: Optional[dict] = None) -> AgentPlan:
        """Create execution plan with observability event emission."""
        metadata = metadata or {}
        profile = metadata.get("profile", self.config.profile)
        trace_id = metadata.get("trace_id", f"plan-{id(self)}-{time.time()}")
        
        # Start timing for duration tracking
        start_time = time.perf_counter()
        
        # Backward compatibility: still populate trace list
        trace = [
            {"event": "plan:start", "goal": goal, "profile": profile, "trace_id": trace_id},
        ]
        
        # Rank and select tools
        scored_tools = self._rank_tools(goal)
        selected = scored_tools[: max(1, min(self.config.max_steps, len(scored_tools)))]
        
        # Build steps
        steps: List[dict] = []
        tool_names: List[str] = []
        for idx, (tool, score) in enumerate(selected):
            tool_names.append(tool.name)
            steps.append(
                {
                    "tool": tool.name,
                    "input": {"text": goal},
                    "reason": f"matched with score {score:.2f}",
                    "trace_id": trace_id,
                    "index": idx,
                }
            )
        
        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Emit plan_created event to new observability system
        try:
            plan_event = PlanEvent.create(
                trace_id=trace_id,
                goal=goal,
                steps_count=len(steps),
                tools_selected=tool_names,
                duration_ms=duration_ms,
                profile=profile,  # Pass as kwarg, not in attributes dict
                max_steps=self.config.max_steps,
            )
            emit_event(plan_event)
        except Exception as e:
            # Don't fail planning if observability fails
            print(f"Warning: Failed to emit plan_created event: {e}")
        
        # Backward compatibility traces
        trace.append({"event": "plan:steps", "count": len(steps), "trace_id": trace_id})
        
        # Store in memory
        self.memory.remember(goal, metadata={"profile": profile, "trace_id": trace_id})
        
        trace.append({"event": "plan:complete", "profile": profile, "trace_id": trace_id})
        return AgentPlan(steps=steps, trace=trace)

    def _rank_tools(self, goal: str) -> List[tuple[Any, float]]:
        import re

        terms = set(re.split(r"\W+", goal.lower()))
        ranked: List[tuple[Any, float]] = []
        
        # Handle both list-based (tools.py) and dict-based (tools/__init__.py) registries
        tools_iter = self.registry.tools if isinstance(self.registry.tools, list) else self.registry.tools.values()
        
        for tool in tools_iter:
            # Handle both ToolSpec objects and simple tool objects
            tool_name = getattr(tool, 'name', 'unknown')
            tool_desc = getattr(tool, 'description', '')
            corpus_text = f"{tool_name} {tool_desc}".lower()
            corpus = set(re.split(r"\W+", corpus_text))
            overlap = len(terms.intersection(corpus))
            score = overlap / max(len(terms), 1)
            if score > 0:
                ranked.append((tool, score))
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked


@dataclass
class WorkerAgent:
    registry: ToolRegistry
    memory: VectorMemory
    observability: Optional[Any] = None  # Legacy BaseEmitter (deprecated in v1.1.0, removed in v1.3.0)
    guardrail_policy: Optional[Any] = None  # GuardrailPolicy if guardrails enabled

    def __post_init__(self):
        """Emit deprecation warning if legacy observability is used."""
        if self.observability is not None:
            warnings.warn(
                "WorkerAgent.observability (BaseEmitter) is deprecated as of v1.1.0 and will be "
                "removed in v1.3.0. All events are now automatically emitted via "
                "cuga.observability.emit_event(). Remove the 'observability' parameter.",
                DeprecationWarning,
                stacklevel=2
            )

    def execute(self, steps: Iterable[dict], metadata: Optional[dict] = None) -> AgentResult:
        """Execute steps with observability and optional guardrail enforcement."""
        metadata = metadata or {}
        profile = metadata.get("profile", self.memory.profile)
        trace_id = metadata.get("trace_id", f"exec-{id(self)}-{time.time()}")
        trace: List[dict] = []
        output: Any = None
        
        for idx, step in enumerate(steps):
            tool_name = step["tool"]
            tool_input = step.get("input", {})
            
            # Get tool from registry
            try:
                tool = self.registry.get(tool_name)
                if tool is None:
                    raise KeyError(tool_name)
            except (KeyError, ValueError):
                error_msg = f"Tool {tool_name} not registered"
                
                # Emit error event
                try:
                    error_event = ToolCallEvent.create_error(
                        trace_id=trace_id,
                        tool_name=tool_name,
                        inputs=tool_input,
                        error_message=error_msg,
                        error_type="ToolNotFoundError",
                    )
                    emit_event(error_event)
                except Exception:
                    pass  # Don't fail on observability errors
                
                raise ValueError(error_msg)
            
            # Start timing
            start_time = time.perf_counter()
            
            # Emit tool_call_start event
            try:
                start_event = ToolCallEvent.create_start(
                    trace_id=trace_id,
                    tool_name=tool_name,
                    inputs=tool_input,
                    attributes={"profile": profile, "step_index": idx},
                )
                emit_event(start_event)
            except Exception as e:
                print(f"Warning: Failed to emit tool_call_start event: {e}")
            
            # Budget guard check (if guardrails enabled)
            if self.guardrail_policy and GUARDRAILS_AVAILABLE:
                try:
                    # Estimate cost (could be tool-specific in real implementation)
                    estimated_cost = 0.01  # Default cost per call (lower to allow testing)
                    budget_guard(self.guardrail_policy, cost=estimated_cost, calls=1, tokens=0)
                except ValueError as budget_error:
                    # Budget exhausted - emit budget_exceeded event
                    try:
                        budget = self.guardrail_policy.budget
                        utilization_pct = max(
                            (budget.current_cost / budget.max_cost * 100) if budget.max_cost > 0 else 0,
                            (budget.current_calls / budget.max_calls * 100) if budget.max_calls > 0 else 0,
                            (budget.current_tokens / budget.max_tokens * 100) if budget.max_tokens > 0 else 0,
                        )
                        budget_exceeded_event = BudgetEvent.create_exceeded(
                            trace_id=trace_id,
                            profile=profile,
                            budget_type="cost",  # Default to cost budget type
                            current_value=budget.current_cost,
                            limit=budget.max_cost,
                            utilization_pct=utilization_pct,
                        )
                        emit_event(budget_exceeded_event)
                    except Exception as e:
                        print(f"Warning: Failed to emit budget_exceeded event: {e}")
                    
                    # Emit error event
                    try:
                        error_event = ToolCallEvent.create_error(
                            trace_id=trace_id,
                            tool_name=tool_name,
                            inputs=tool_input,
                            error_message=str(budget_error),
                            error_type="BudgetExceededError",
                        )
                        emit_event(error_event)
                    except Exception:
                        pass
                    
                    raise budget_error
            
            # Execute tool
            context = {"profile": profile, "trace_id": trace_id}
            try:
                result = tool.handler(tool_input, context)
                output = result
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                # Emit tool_call_complete event
                try:
                    complete_event = ToolCallEvent.create_complete(
                        trace_id=trace_id,
                        tool_name=tool_name,
                        inputs=tool_input,
                        result=result,
                        duration_ms=duration_ms,
                    )
                    emit_event(complete_event)
                except Exception as e:
                    print(f"Warning: Failed to emit tool_call_complete event: {e}")
                
                # Backward compatibility trace
                event = {"event": "execute:step", "tool": tool_name, "index": idx, "trace_id": trace_id}
                trace.append(event)
                
            except Exception as tool_error:
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                # Emit tool_call_error event
                try:
                    error_event = ToolCallEvent.create_error(
                        trace_id=trace_id,
                        tool_name=tool_name,
                        inputs=tool_input,
                        error_message=str(tool_error),
                        error_type=type(tool_error).__name__,
                        duration_ms=duration_ms,
                    )
                    emit_event(error_event)
                except Exception as e:
                    print(f"Warning: Failed to emit tool_call_error event: {e}")
                
                # Re-raise the tool error
                raise tool_error
            
            # Legacy observability (deprecated in v1.1.0, will be removed in v1.3.0)
            # Note: This is redundant - events are already emitted above via emit_event()
            if self.observability:
                warnings.warn(
                    "BaseEmitter.emit() calls are deprecated and redundant. "
                    "Events are automatically emitted via cuga.observability.emit_event(). "
                    "This legacy path will be removed in v1.3.0.",
                    DeprecationWarning,
                    stacklevel=2
                )
                try:
                    self.observability.emit(
                        {"event": "tool", "name": tool_name, "profile": profile, "trace_id": trace_id}
                    )
                except Exception as e:
                    # Don't fail on legacy observability errors
                    print(f"Warning: Legacy observability emit failed: {e}")
        
        # Store output in memory
        self.memory.remember(str(output), metadata={"profile": profile, "trace_id": trace_id})
        return AgentResult(output=output, trace=trace)


@dataclass
class CoordinatorAgent:
    planner: PlannerAgent
    workers: List[WorkerAgent]
    memory: VectorMemory
    _next_worker_idx: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def dispatch(self, goal: str, trace_id: Optional[str] = None) -> AgentResult:
        """Dispatch goal to planner and worker with observability."""
        if trace_id is None:
            trace_id = f"coord-{id(self)}-{time.time()}"
        
        # Start timing for routing decision
        routing_start = time.perf_counter()
        
        # Create plan
        plan = self.planner.plan(
            goal, metadata={"profile": self.planner.config.profile, "trace_id": trace_id}
        )
        traces = list(plan.trace)
        
        if not self.workers:
            raise ValueError("No workers configured")
        
        # Select worker (round-robin)
        worker = self._select_worker()
        worker_idx = (self._next_worker_idx - 1) % len(self.workers)  # Get the index that was just selected
        
        # Calculate routing duration
        routing_duration_ms = (time.perf_counter() - routing_start) * 1000
        
        # Emit route_decision event
        try:
            route_event = RouteEvent.create(
                trace_id=trace_id,
                agent_selected=f"worker-{worker_idx}",
                alternatives_considered=[f"worker-{i}" for i in range(len(self.workers))],
                reason="round_robin",
                duration_ms=routing_duration_ms,
                attributes={
                    "worker_count": len(self.workers),
                    "selected_index": worker_idx,
                    "profile": self.planner.config.profile,
                },
            )
            emit_event(route_event)
        except Exception as e:
            print(f"Warning: Failed to emit route_decision event: {e}")
        
        # Execute with selected worker
        result = worker.execute(
            plan.steps, metadata={"profile": self.planner.config.profile, "trace_id": trace_id}
        )
        traces.extend(result.trace)
        return AgentResult(output=result.output, trace=traces)

    def _select_worker(self) -> WorkerAgent:
        """Thread-safe round-robin worker selection."""
        with self._lock:
            if not self.workers:
                raise ValueError("No workers available to select from.")
            worker = self.workers[self._next_worker_idx]
            self._next_worker_idx = (self._next_worker_idx + 1) % len(self.workers)
        return worker


def build_default_registry() -> ToolRegistry:
    """Build default registry with echo tool for testing."""
    # Create a simple tool object with name and handler attributes
    class SimpleTool:
        def __init__(self, name, description, handler_func):
            self.name = name
            self.description = description
            self.handler = handler_func
    
    registry = ToolRegistry()
    echo_tool = SimpleTool(
        name="echo",
        description="Echo text",
        handler_func=lambda inputs, ctx: inputs.get("text", "")
    )
    registry.register("echo", echo_tool)
    return registry
