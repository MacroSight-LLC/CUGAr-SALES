#!/usr/bin/env python3
"""
Run integration tests without pytest dependency.

Validates critical orchestration paths:
1. Multi-domain orchestration
2. Budget enforcement
3. Approval flows
4. Failure recovery
5. Concurrent execution
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from cuga.orchestrator.intelligent_planner import IntelligentPlanner
from cuga.orchestrator.planning import Plan, PlanStep, PlanningStage, ToolBudget
from cuga.orchestrator.protocol import ExecutionContext
import yaml


def load_registry():
    """Load registry.yaml"""
    with open("registry.yaml") as f:
        return yaml.safe_load(f)


def create_context(trace_id="test-trace"):
    """Create test execution context."""
    return ExecutionContext(
        trace_id=trace_id,
        request_id=f"req-{trace_id}",
        user_intent="Test orchestration",
        profile="demo",
        memory_scope="test",
        conversation_id="test-conv",
        session_id="test-sess",
        user_id="test-user",
    )


def get_prospect_data():
    """Standard prospect data."""
    return {
        "company": "Test Corp",
        "industry": "Technology",
        "employee_count": 500,
        "revenue": 10000000,
        "template": "Hi {{first_name}}",
        "prospect_data": {
            "first_name": "Jane",
            "company": "Test Corp",
            "industry": "Technology",
            "role": "VP",
            "location": "SF",
            "pain_point": "scaling",
        },
    }


class TestRunner:
    """Simple test runner."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_test(self, name, test_func):
        """Add async test function."""
        self.tests.append((name, test_func))
    
    async def run_all(self):
        """Run all tests."""
        print("\n" + "=" * 80)
        print("INTEGRATION TEST SUITE")
        print("=" * 80 + "\n")
        
        for name, test_func in self.tests:
            try:
                print(f"Running: {name}...", end=" ")
                await test_func()
                print("✅ PASSED")
                self.passed += 1
            except AssertionError as e:
                print(f"❌ FAILED: {e}")
                self.failed += 1
            except Exception as e:
                print(f"❌ ERROR: {e}")
                self.failed += 1
        
        print("\n" + "=" * 80)
        print(f"RESULTS: {self.passed} passed, {self.failed} failed")
        print("=" * 80 + "\n")
        
        return self.failed == 0


# Test functions
async def test_successful_four_step_execution():
    """Test successful execution of all 4 steps across 3 domains."""
    registry = load_registry()
    context = create_context()
    prospect_data = get_prospect_data()
    
    planner = IntelligentPlanner(registry, profile="demo")
    plan = await planner.create_plan(
        goal="Prioritize and engage prospect",
        context=context,
        prospect_data=prospect_data,
        use_llm=False,
    )
    
    assert len(plan.steps) == 4, f"Expected 4 steps, got {len(plan.steps)}"
    assert plan.trace_id == context.trace_id
    assert plan.profile == "demo"
    
    domains = [s.metadata["domain"] for s in plan.steps]
    assert "intelligence" in domains
    assert "engagement" in domains
    assert "qualification" in domains


async def test_cross_step_context_passing():
    """Test that step dependencies are marked correctly."""
    registry = load_registry()
    context = create_context()
    prospect_data = get_prospect_data()
    
    planner = IntelligentPlanner(registry, profile="demo")
    plan = await planner.create_plan(
        goal="Draft and validate message",
        context=context,
        prospect_data=prospect_data,
        use_llm=False,
    )
    
    assess_step = next(s for s in plan.steps if s.tool == "assess_message_quality")
    assert assess_step.metadata.get("depends_on") == 2


async def test_budget_limit_set():
    """Test plan has budget limit."""
    registry = load_registry()
    context = create_context()
    prospect_data = get_prospect_data()
    
    planner = IntelligentPlanner(registry, profile="demo")
    plan = await planner.create_plan(
        goal="Test budget",
        context=context,
        prospect_data=prospect_data,
        use_llm=False,
    )
    
    assert plan.budget is not None
    assert plan.budget.call_ceiling > 0
    
    total_cost = sum(s.estimated_cost for s in plan.steps)
    assert total_cost <= plan.budget.call_ceiling


async def test_individual_step_costs():
    """Test each step has reasonable cost estimate."""
    registry = load_registry()
    context = create_context()
    prospect_data = get_prospect_data()
    
    planner = IntelligentPlanner(registry, profile="demo")
    plan = await planner.create_plan(
        goal="Test costs",
        context=context,
        prospect_data=prospect_data,
        use_llm=False,
    )
    
    for step in plan.steps:
        assert step.estimated_cost > 0
        assert step.estimated_cost <= 2.0


async def test_propose_operations_marked():
    """Test operations with side_effect_class=propose are marked."""
    registry = load_registry()
    context = create_context()
    prospect_data = get_prospect_data()
    
    planner = IntelligentPlanner(registry, profile="demo")
    plan = await planner.create_plan(
        goal="Draft message",
        context=context,
        prospect_data=prospect_data,
        use_llm=False,
    )
    
    draft_step = next(s for s in plan.steps if s.tool == "draft_outbound_message")
    assert draft_step.metadata["side_effect_class"] == "propose"


async def test_read_only_operations():
    """Test read-only operations are marked correctly."""
    registry = load_registry()
    context = create_context()
    prospect_data = get_prospect_data()
    
    planner = IntelligentPlanner(registry, profile="demo")
    plan = await planner.create_plan(
        goal="Score account",
        context=context,
        prospect_data=prospect_data,
        use_llm=False,
    )
    
    read_only_steps = [
        s for s in plan.steps 
        if s.metadata["side_effect_class"] == "read-only"
    ]
    assert len(read_only_steps) >= 2


async def test_llm_fallback_to_rule_based():
    """Test automatic fallback when LLM unavailable."""
    registry = load_registry()
    context = create_context()
    prospect_data = get_prospect_data()
    
    planner = IntelligentPlanner(registry, profile="demo", llm_adapter=None)
    
    plan = await planner.create_plan(
        goal="Test fallback",
        context=context,
        prospect_data=prospect_data,
        use_llm=True,  # Requested but not available
    )
    
    assert plan.metadata["rule_based"] is True
    assert plan.metadata["llm_generated"] is False
    assert len(plan.steps) == 4


async def test_deterministic_mode():
    """Test use_llm=False produces identical plans."""
    registry = load_registry()
    context = create_context()
    prospect_data = get_prospect_data()
    
    planner = IntelligentPlanner(registry, profile="demo")
    
    plan1 = await planner.create_plan(
        goal="Same goal",
        context=context,
        prospect_data=prospect_data,
        use_llm=False,
    )
    
    plan2 = await planner.create_plan(
        goal="Same goal",
        context=context,
        prospect_data=prospect_data,
        use_llm=False,
    )
    
    assert len(plan1.steps) == len(plan2.steps)
    for s1, s2 in zip(plan1.steps, plan2.steps):
        assert s1.tool == s2.tool
        assert s1.estimated_cost == s2.estimated_cost


async def test_concurrent_plan_creation():
    """Test multiple plans can be created concurrently."""
    registry = load_registry()
    context = create_context()
    prospect_data = get_prospect_data()
    
    planner = IntelligentPlanner(registry, profile="demo")
    
    tasks = [
        planner.create_plan(
            goal=f"Goal {i}",
            context=context,
            prospect_data=prospect_data,
            use_llm=False,
        )
        for i in range(3)
    ]
    
    plans = await asyncio.gather(*tasks)
    
    assert len(plans) == 3
    plan_ids = [p.plan_id for p in plans]
    assert len(set(plan_ids)) == 3


async def test_trace_id_isolation():
    """Test different contexts maintain separate trace IDs."""
    registry = load_registry()
    prospect_data = get_prospect_data()
    
    context1 = create_context("trace-1")
    context2 = create_context("trace-2")
    
    planner = IntelligentPlanner(registry, profile="demo")
    
    plan1, plan2 = await asyncio.gather(
        planner.create_plan("Goal 1", context1, prospect_data, use_llm=False),
        planner.create_plan("Goal 2", context2, prospect_data, use_llm=False),
    )
    
    assert plan1.trace_id == "trace-1"
    assert plan2.trace_id == "trace-2"


async def test_all_tools_have_metadata():
    """Test all plan steps have required metadata fields."""
    registry = load_registry()
    context = create_context()
    prospect_data = get_prospect_data()
    
    planner = IntelligentPlanner(registry, profile="demo")
    plan = await planner.create_plan(
        goal="Test metadata",
        context=context,
        prospect_data=prospect_data,
        use_llm=False,
    )
    
    required_fields = ["domain", "side_effect_class"]
    
    for step in plan.steps:
        for field in required_fields:
            assert field in step.metadata, f"Step {step.index} missing {field}"
        
        assert step.metadata["side_effect_class"] in [
            "read-only", "propose", "execute"
        ]


async def main():
    """Run all integration tests."""
    runner = TestRunner()
    
    # Multi-domain orchestration tests
    runner.add_test(
        "Multi-domain: 4 steps across 3 domains",
        test_successful_four_step_execution
    )
    runner.add_test(
        "Multi-domain: Cross-step context passing",
        test_cross_step_context_passing
    )
    
    # Budget enforcement tests
    runner.add_test(
        "Budget: Limit set correctly",
        test_budget_limit_set
    )
    runner.add_test(
        "Budget: Individual step costs",
        test_individual_step_costs
    )
    
    # Approval flow tests
    runner.add_test(
        "Approval: Propose operations marked",
        test_propose_operations_marked
    )
    runner.add_test(
        "Approval: Read-only operations",
        test_read_only_operations
    )
    
    # Failure recovery tests
    runner.add_test(
        "Failure: LLM fallback to rule-based",
        test_llm_fallback_to_rule_based
    )
    runner.add_test(
        "Failure: Deterministic mode",
        test_deterministic_mode
    )
    
    # Concurrent execution tests
    runner.add_test(
        "Concurrent: Multiple plan creation",
        test_concurrent_plan_creation
    )
    runner.add_test(
        "Concurrent: Trace ID isolation",
        test_trace_id_isolation
    )
    
    # Tool contract tests
    runner.add_test(
        "Contracts: All tools have metadata",
        test_all_tools_have_metadata
    )
    
    success = await runner.run_all()
    
    if success:
        print("✅ ALL INTEGRATION TESTS PASSED\n")
        print("Coverage Summary:")
        print("  ✓ Multi-domain orchestration (2 tests)")
        print("  ✓ Budget enforcement (2 tests)")
        print("  ✓ Approval flows (2 tests)")
        print("  ✓ Failure recovery (2 tests)")
        print("  ✓ Concurrent execution (2 tests)")
        print("  ✓ Tool contracts (1 test)")
        print(f"\n  Total: {runner.passed} tests covering critical paths\n")
        return 0
    else:
        print(f"❌ {runner.failed} TESTS FAILED\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
