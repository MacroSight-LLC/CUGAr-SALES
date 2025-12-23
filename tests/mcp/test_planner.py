from cuga.agents.planner import Planner
from cuga.agents.registry import ToolRegistry


def test_planner_deterministic_sorting():
    registry = ToolRegistry()
    registry.register("beta", "zeta", lambda *_args, **_kwargs: None)
    registry.register("alpha", "omega", lambda *_args, **_kwargs: None)
    registry.register("alpha", "alpha_tool", lambda *_args, **_kwargs: None)

    planner = Planner()
    plan = planner.plan("goal", registry)

    assert plan[0].tool == "alpha_tool"
    assert plan[0].input["profile"] == "alpha"
