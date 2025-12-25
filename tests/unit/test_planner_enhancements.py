from cuga.agents.planner import Planner, PlanningPreferences
from cuga.agents.registry import ToolRegistry


def test_planner_builds_multi_step_plan_with_trace():
    registry = ToolRegistry()
    registry.register("demo", "fast", lambda *_a, **_k: None, cost=0.5, latency=0.3)
    registry.register("demo", "cheap", lambda *_a, **_k: None, cost=0.2, latency=0.9)

    planner = Planner()
    result = planner.plan("demo-goal", registry)

    assert len(result.steps) == 2
    assert result.trace


def test_planner_respects_optimization_goal():
    registry = ToolRegistry()
    registry.register("demo", "cheap", lambda *_a, **_k: None, cost=0.1, latency=0.9)
    registry.register("demo", "fast", lambda *_a, **_k: None, cost=0.8, latency=0.1)

    planner = Planner()
    cost_result = planner.plan("goal", registry, preferences=PlanningPreferences(optimization="cost", max_steps=1))
    latency_result = planner.plan("goal", registry, preferences=PlanningPreferences(optimization="latency", max_steps=1))

    assert cost_result.steps[0].tool == "cheap"
    assert latency_result.steps[0].tool == "fast"
    assert cost_result.trace != latency_result.trace
