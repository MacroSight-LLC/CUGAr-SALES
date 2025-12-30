from cuga.guards.input_guard import InputGuard
from cuga.guards.orchestrator import GuardrailOrchestrator
from cuga.guards.output_guard import OutputGuard
from cuga.guards.tool_guard import ToolGuard


def test_orchestrator_routes():
    orchestrator = GuardrailOrchestrator(InputGuard(), ToolGuard(), OutputGuard())
    assert orchestrator.route("input", {"x": 1}).decision == "pass"
    assert orchestrator.route("tool", {"readonly": False}).decision == "review"
    assert orchestrator.route("output", {"y": 2}).decision == "pass"
