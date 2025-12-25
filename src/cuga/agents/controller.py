"""Controller orchestrating planner and executor layers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .executor import ExecutionContext, ExecutionResult, Executor
from .planner import Planner, PlanningPreferences
from .registry import ToolRegistry


@dataclass
class Controller:
    planner: Planner
    executor: Executor
    registry: ToolRegistry

    def run(
        self,
        goal: str,
        profile: str,
        *,
        metadata: Dict[str, Any] | None = None,
        preferences: PlanningPreferences | None = None,
    ) -> ExecutionResult:
        sandboxed_registry = self.registry.sandbox(profile)
        plan_result = self.planner.plan(goal, sandboxed_registry, preferences=preferences)
        context = ExecutionContext(profile=profile, metadata=metadata)
        return self.executor.execute_plan(plan_result.steps, sandboxed_registry, context, trace=plan_result.trace)
