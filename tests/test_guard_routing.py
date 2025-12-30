from cuga.guards.orchestrator import GuardrailOrchestrator


def test_guard_routes_stages():
    orchestrator = GuardrailOrchestrator()
    assert orchestrator.route("input", {"text": "hi"}).decision == "pass"
    assert orchestrator.route("tool", {"tool": "write", "readonly": False}).decision == "review"
