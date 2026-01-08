"""
Integration tests for observability features.

Tests metrics aggregation, golden signals tracking, and Prometheus export.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

# Add src and project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

from cuga.orchestrator.metrics import get_metrics_aggregator, reset_metrics, MetricsAggregator
from demo_production import ProductionDemo


async def test_metrics_aggregator_initialization():
    """Test that metrics aggregator initializes correctly."""
    print("\n🧪 TEST: Metrics Aggregator Initialization")
    
    reset_metrics()
    aggregator = get_metrics_aggregator()
    
    assert isinstance(aggregator, MetricsAggregator), "Aggregator should be MetricsAggregator instance"
    
    summary = aggregator.get_summary()
    assert summary.total_executions == 0, "Should start with 0 executions"
    assert summary.success_rate == 0.0, "Should start with 0% success rate"
    
    print("✅ PASSED: Metrics aggregator initialized correctly")
    return True


async def test_single_execution_metrics():
    """Test metrics recording for a single execution."""
    print("\n🧪 TEST: Single Execution Metrics")
    
    reset_metrics()
    aggregator = get_metrics_aggregator()
    
    demo = ProductionDemo(profile="demo")
    
    prospect_data = {
        "company": "Test Corp",
        "industry": "Technology",
        "employee_count": 100,
        "revenue": 1000000,
        "template": "Test {{company}}",
        "prospect_data": {
            "first_name": "Test",
            "company": "Test Corp",
            "industry": "Technology",
            "role": "CEO",
            "location": "SF",
            "pain_point": "testing",
        },
    }
    
    await demo.run_demo(
        goal="Test metrics recording",
        prospect_data=prospect_data,
    )
    
    summary = aggregator.get_summary()
    
    assert summary.total_executions == 1, f"Should have 1 execution, got {summary.total_executions}"
    assert summary.successful_executions == 1, "Should have 1 successful execution"
    assert summary.failed_executions == 0, "Should have 0 failed executions"
    assert summary.success_rate == 1.0, f"Success rate should be 100%, got {summary.success_rate}"
    assert summary.error_rate == 0.0, f"Error rate should be 0%, got {summary.error_rate}"
    assert summary.total_steps == 4, f"Should have 4 steps, got {summary.total_steps}"
    assert summary.tool_call_count == 4, f"Should have 4 tool calls, got {summary.tool_call_count}"
    assert summary.total_approvals == 1, f"Should have 1 approval, got {summary.total_approvals}"
    
    print(f"  📊 Success Rate: {summary.success_rate:.1%}")
    print(f"  📊 Total Steps: {summary.total_steps}")
    print(f"  📊 Budget Used: {summary.total_budget_used:.1f}")
    print(f"  📊 Approvals: {summary.total_approvals}")
    
    print("✅ PASSED: Single execution metrics recorded correctly")
    return True


async def test_multiple_execution_aggregation():
    """Test metrics aggregation across multiple executions."""
    print("\n🧪 TEST: Multiple Execution Aggregation")
    
    reset_metrics()
    aggregator = get_metrics_aggregator()
    
    demo = ProductionDemo(profile="demo")
    
    # Run 3 executions
    for i in range(3):
        prospect_data = {
            "company": f"Company {i+1}",
            "industry": "Tech",
            "employee_count": 100,
            "revenue": 1000000,
            "template": "Test {{company}}",
            "prospect_data": {
                "first_name": f"Person{i+1}",
                "company": f"Company {i+1}",
                "industry": "Tech",
                "role": "CEO",
                "location": "SF",
                "pain_point": "testing",
            },
        }
        
        await demo.run_demo(
            goal=f"Test execution {i+1}",
            prospect_data=prospect_data,
        )
    
    summary = aggregator.get_summary()
    
    assert summary.total_executions == 3, f"Should have 3 executions, got {summary.total_executions}"
    assert summary.successful_executions == 3, "Should have 3 successful executions"
    assert summary.total_steps == 12, f"Should have 12 total steps (3x4), got {summary.total_steps}"
    assert summary.mean_steps_per_execution == 4.0, f"Should have 4 steps/execution, got {summary.mean_steps_per_execution}"
    assert summary.tool_call_count == 12, f"Should have 12 tool calls, got {summary.tool_call_count}"
    assert summary.total_approvals == 3, f"Should have 3 approvals, got {summary.total_approvals}"
    
    # Verify budget aggregation
    expected_budget = 2.7 * 3  # 2.7 per execution
    assert abs(summary.total_budget_used - expected_budget) < 0.1, \
        f"Budget should be ~{expected_budget}, got {summary.total_budget_used}"
    
    # Verify latency percentiles exist
    assert summary.latency_p50 > 0, "P50 latency should be positive"
    assert summary.latency_p95 > 0, "P95 latency should be positive"
    assert summary.latency_p99 > 0, "P99 latency should be positive"
    
    # Verify domain usage
    assert "intelligence" in summary.domain_usage, "Should have intelligence domain"
    assert "engagement" in summary.domain_usage, "Should have engagement domain"
    assert "qualification" in summary.domain_usage, "Should have qualification domain"
    
    print(f"  📊 Total Executions: {summary.total_executions}")
    print(f"  📊 Success Rate: {summary.success_rate:.1%}")
    print(f"  📊 Mean Steps/Execution: {summary.mean_steps_per_execution:.1f}")
    print(f"  📊 Total Budget: {summary.total_budget_used:.1f}")
    print(f"  📊 Latency P50: {summary.latency_p50:.0f}ms")
    print(f"  📊 Domain Usage: {dict(summary.domain_usage)}")
    
    print("✅ PASSED: Multiple execution aggregation works correctly")
    return True


async def test_prometheus_export_format():
    """Test Prometheus export format."""
    print("\n🧪 TEST: Prometheus Export Format")
    
    reset_metrics()
    aggregator = get_metrics_aggregator()
    
    # Record a simple execution
    aggregator.record_execution(
        trace_id="test-trace-123",
        success=True,
        duration_ms=1000,
        steps=4,
        budget_used=2.7,
        budget_limit=100,
        approvals=[],
        results=[
            {"tool": "test_tool", "domain": "test_domain", "status": "success"}
        ],
    )
    
    prometheus_output = aggregator.get_prometheus_metrics()
    
    # Verify required Prometheus format elements
    assert "# HELP cugar_success_rate" in prometheus_output, "Missing success_rate HELP"
    assert "# TYPE cugar_success_rate gauge" in prometheus_output, "Missing success_rate TYPE"
    assert "cugar_success_rate" in prometheus_output, "Missing success_rate metric"
    
    assert "# HELP cugar_error_rate" in prometheus_output, "Missing error_rate HELP"
    assert "# TYPE cugar_error_rate gauge" in prometheus_output, "Missing error_rate TYPE"
    
    assert "# HELP cugar_latency_ms" in prometheus_output, "Missing latency HELP"
    assert "cugar_latency_ms{percentile=\"p50\"}" in prometheus_output, "Missing P50 latency"
    assert "cugar_latency_ms{percentile=\"p95\"}" in prometheus_output, "Missing P95 latency"
    assert "cugar_latency_ms{percentile=\"p99\"}" in prometheus_output, "Missing P99 latency"
    
    assert "# TYPE cugar_executions_total counter" in prometheus_output, "Missing executions TYPE"
    assert "cugar_executions_total" in prometheus_output, "Missing executions metric"
    
    assert "# HELP cugar_budget_used_total" in prometheus_output, "Missing budget HELP"
    assert "cugar_budget_used_total" in prometheus_output, "Missing budget metric"
    
    assert "# HELP cugar_domain_usage_total" in prometheus_output, "Missing domain usage HELP"
    assert "cugar_domain_usage_total{domain=" in prometheus_output, "Missing domain labels"
    
    print("  ✓ All required Prometheus metric types present")
    print("  ✓ HELP and TYPE annotations correct")
    print("  ✓ Metric labels formatted properly")
    
    print("✅ PASSED: Prometheus export format is valid")
    return True


async def test_golden_signals_tracking():
    """Test golden signals (success rate, latency, error rate) tracking."""
    print("\n🧪 TEST: Golden Signals Tracking")
    
    reset_metrics()
    aggregator = get_metrics_aggregator()
    
    # Record successful executions
    for i in range(9):
        aggregator.record_execution(
            trace_id=f"success-{i}",
            success=True,
            duration_ms=1000 + i * 100,  # Varying latencies
            steps=4,
            budget_used=2.7,
            budget_limit=100,
            approvals=[],
            results=[{"tool": "test", "domain": "test", "status": "success"}],
        )
    
    # Record 1 failed execution
    aggregator.record_execution(
        trace_id="failure-1",
        success=False,
        duration_ms=500,
        steps=2,
        budget_used=1.0,
        budget_limit=100,
        approvals=[],
        results=[{"tool": "test", "domain": "test", "status": "error"}],
    )
    
    summary = aggregator.get_summary()
    
    # Verify golden signals
    assert summary.total_executions == 10, "Should have 10 executions"
    assert summary.successful_executions == 9, "Should have 9 successes"
    assert summary.failed_executions == 1, "Should have 1 failure"
    assert summary.success_rate == 0.9, f"Success rate should be 90%, got {summary.success_rate}"
    assert summary.error_rate == 0.1, f"Error rate should be 10%, got {summary.error_rate}"
    
    # Verify latency percentiles
    assert summary.latency_p50 > 0, "P50 should be positive"
    assert summary.latency_p95 > 0, "P95 should be positive"
    assert summary.latency_p99 > 0, "P99 should be positive"
    assert summary.latency_p99 >= summary.latency_p95 >= summary.latency_p50, \
        "Percentiles should be ordered: P99 >= P95 >= P50"
    
    print(f"  🎯 Success Rate: {summary.success_rate:.1%} (expected 90%)")
    print(f"  🎯 Error Rate: {summary.error_rate:.1%} (expected 10%)")
    print(f"  🎯 Latency P50: {summary.latency_p50:.0f}ms")
    print(f"  🎯 Latency P95: {summary.latency_p95:.0f}ms")
    print(f"  🎯 Latency P99: {summary.latency_p99:.0f}ms")
    
    print("✅ PASSED: Golden signals tracked correctly")
    return True


async def test_budget_tracking():
    """Test budget utilization tracking."""
    print("\n🧪 TEST: Budget Tracking")
    
    reset_metrics()
    aggregator = get_metrics_aggregator()
    
    # Record executions with varying budget usage
    aggregator.record_execution(
        trace_id="low-budget",
        success=True,
        duration_ms=1000,
        steps=2,
        budget_used=2.0,
        budget_limit=100,
        approvals=[],
        results=[],
    )
    
    aggregator.record_execution(
        trace_id="high-budget",
        success=True,
        duration_ms=1000,
        steps=4,
        budget_used=5.0,
        budget_limit=100,
        approvals=[],
        results=[],
    )
    
    aggregator.record_execution(
        trace_id="exceeded-budget",
        success=False,
        duration_ms=1000,
        steps=10,
        budget_used=150.0,  # Exceeded!
        budget_limit=100,
        approvals=[],
        results=[],
    )
    
    summary = aggregator.get_summary()
    
    assert summary.total_budget_used == 157.0, f"Total budget should be 157, got {summary.total_budget_used}"
    assert summary.mean_budget_per_execution == 157.0 / 3, \
        f"Mean budget should be {157.0/3:.1f}, got {summary.mean_budget_per_execution}"
    assert summary.budget_exceeded_count == 1, f"Budget exceeded count should be 1, got {summary.budget_exceeded_count}"
    
    print(f"  💰 Total Budget Used: {summary.total_budget_used:.1f}")
    print(f"  💰 Mean Budget/Execution: {summary.mean_budget_per_execution:.1f}")
    print(f"  💰 Budget Exceeded: {summary.budget_exceeded_count} times")
    
    print("✅ PASSED: Budget tracking works correctly")
    return True


async def test_approval_metrics():
    """Test approval flow metrics tracking."""
    print("\n🧪 TEST: Approval Metrics")
    
    reset_metrics()
    aggregator = get_metrics_aggregator()
    
    # Record executions with approvals
    aggregator.record_execution(
        trace_id="approval-1",
        success=True,
        duration_ms=1000,
        steps=2,
        budget_used=1.0,
        budget_limit=100,
        approvals=[
            {"tool": "draft_message", "status": "approved", "wait_time": 2000}
        ],
        results=[],
    )
    
    aggregator.record_execution(
        trace_id="approval-2",
        success=True,
        duration_ms=1000,
        steps=2,
        budget_used=1.0,
        budget_limit=100,
        approvals=[
            {"tool": "draft_message", "status": "approved", "wait_time": 3000}
        ],
        results=[],
    )
    
    aggregator.record_execution(
        trace_id="approval-denied",
        success=False,
        duration_ms=1000,
        steps=1,
        budget_used=0.5,
        budget_limit=100,
        approvals=[
            {"tool": "draft_message", "status": "denied", "wait_time": 1000}
        ],
        results=[],
    )
    
    summary = aggregator.get_summary()
    
    assert summary.total_approvals == 3, f"Should have 3 approvals, got {summary.total_approvals}"
    assert summary.approval_denied_count == 1, f"Should have 1 denial, got {summary.approval_denied_count}"
    
    # Mean wait time should be (2000 + 3000 + 1000) / 3 = 2000ms
    expected_mean_wait = 2000.0
    assert abs(summary.approval_wait_time_mean - expected_mean_wait) < 1, \
        f"Mean wait should be ~{expected_mean_wait}ms, got {summary.approval_wait_time_mean}ms"
    
    print(f"  🔐 Total Approvals: {summary.total_approvals}")
    print(f"  🔐 Mean Wait Time: {summary.approval_wait_time_mean:.0f}ms")
    print(f"  🔐 Denied: {summary.approval_denied_count}")
    
    print("✅ PASSED: Approval metrics tracked correctly")
    return True


async def run_all_tests():
    """Run all observability integration tests."""
    print("=" * 80)
    print("🔬 OBSERVABILITY INTEGRATION TESTS")
    print("=" * 80)
    
    tests = [
        test_metrics_aggregator_initialization,
        test_single_execution_metrics,
        test_multiple_execution_aggregation,
        test_prometheus_export_format,
        test_golden_signals_tracking,
        test_budget_tracking,
        test_approval_metrics,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print("\n✅ ALL OBSERVABILITY TESTS PASSED")
        return 0
    else:
        print(f"\n❌ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
