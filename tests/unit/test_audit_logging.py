from cuga.agents.controller import Controller
from cuga.agents.executor import ExecutionContext, Executor
from cuga.agents.planner import PlanStep, PlanningPreferences, PlanningResult
from cuga.agents.policy import PolicyEnforcer
from cuga.agents.registry import ToolRegistry


def test_executor_records_audit_trace_for_successful_step():
    registry = ToolRegistry()

    def echo_handler(payload, *, config, context):
        return payload["text"]

    registry.register("demo", "echo", echo_handler)
    sandbox = registry.sandbox("demo")
    executor = Executor()
    plan = [PlanStep(name="echo-step", tool="echo", input={"text": "hello"})]
    context = ExecutionContext(profile="demo", metadata={"request_id": "abc"})

    result = executor.execute_plan(plan, sandbox, context, trace=[])

    audit_entries = [item for item in result.trace if isinstance(item, dict) and item.get("event") == "execute_step"]

    assert result.output == "hello"
    assert len(audit_entries) == 1
    audit = audit_entries[0]
    assert audit["profile"] == "demo"
    assert audit["tool"] == "echo"
    assert audit["input"] == {"text": "hello"}
    assert audit["policy_decision"] == "allowed"
    assert audit["status"] == "success"


class _FailingPlanner:
    def plan(self, goal, registry, preferences: PlanningPreferences | None = None):
        return PlanningResult(
            steps=[PlanStep(name="fail-step", tool="boom", input={"text": "explode"})],
            trace=["planner-generated-step"],
            profile=registry.profiles().pop(),
            optimization=(preferences or PlanningPreferences()).optimization,
        )


def test_controller_trace_includes_audit_on_failure():
    registry = ToolRegistry()

    def failing_handler(*_args, **_kwargs):
        raise ValueError("boom")

    registry.register("audit", "boom", failing_handler)
    controller = Controller(
        planner=_FailingPlanner(),
        executor=Executor(),
        registry=registry,
        policy_enforcer=PolicyEnforcer(),
    )

    result = controller.run(goal="trigger failure", profile="audit", metadata={"request_id": "abc"})

    failure_entries = [item for item in result.trace if isinstance(item, dict) and item.get("status") == "error"]
    controller_entries = [item for item in result.trace if isinstance(item, dict) and item.get("event") == "controller_run"]

    assert result.output == {"status": "failed", "reason": "handler_error"}
    assert len(failure_entries) == 1
    failure_audit = failure_entries[0]
    assert failure_audit["tool"] == "boom"
    assert failure_audit["policy_decision"] == "allowed"
    assert failure_audit["error"] == "ValueError"
    assert "boom" not in str(result.output)

    assert len(controller_entries) == 1
    controller_audit = controller_entries[0]
    assert controller_audit["profile"] == "audit"
    assert controller_audit["policy_decision"] == "metadata_validated"
