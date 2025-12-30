import pytest

from cuga.langflow_components.planner_component import PlannerComponent


def test_planner_component_runs():
    component = PlannerComponent()
    result = component(goal="demo")
    assert result["plan"] == ["demo"]
