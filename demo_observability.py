#!/usr/bin/env python3
"""
Observability demo showing real-time metrics aggregation.

Runs multiple executions and displays:
- Golden signals (success rate, latency, error rate)
- Execution metrics
- Budget tracking
- Approval metrics
- Domain usage
- Prometheus export format
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from demo_production import ProductionDemo
from cuga.orchestrator.metrics import get_metrics_aggregator, reset_metrics


async def run_multiple_executions():
    """Run multiple demo executions to generate metrics."""
    print("\n" + "=" * 80)
    print("🔬 OBSERVABILITY DEMO - Running Multiple Executions")
    print("=" * 80 + "\n")
    
    # Reset metrics for clean demo
    reset_metrics()
    aggregator = get_metrics_aggregator()
    
    # Initialize demo
    demo = ProductionDemo(profile="demo")
    
    # Prospect data variations
    prospects = [
        {
            "company": "Acme Corp",
            "industry": "Technology",
            "employee_count": 500,
            "revenue": 10000000,
            "template": "Hi {{first_name}}, I noticed {{company}} is doing interesting work in {{industry}}.",
            "prospect_data": {
                "first_name": "Jane",
                "company": "Acme Corp",
                "industry": "Technology",
                "role": "VP Engineering",
                "location": "San Francisco",
                "pain_point": "scaling infrastructure",
            },
        },
        {
            "company": "TechStart Inc",
            "industry": "SaaS",
            "employee_count": 200,
            "revenue": 5000000,
            "template": "Hi {{first_name}}, I saw {{company}} is growing fast in {{industry}}.",
            "prospect_data": {
                "first_name": "John",
                "company": "TechStart Inc",
                "industry": "SaaS",
                "role": "CTO",
                "location": "Austin",
                "pain_point": "customer analytics",
            },
        },
        {
            "company": "FinanceFlow",
            "industry": "Financial Services",
            "employee_count": 1000,
            "revenue": 50000000,
            "template": "Hi {{first_name}}, {{company}} is a leader in {{industry}}.",
            "prospect_data": {
                "first_name": "Sarah",
                "company": "FinanceFlow",
                "industry": "Financial Services",
                "role": "VP Product",
                "location": "New York",
                "pain_point": "compliance automation",
            },
        },
    ]
    
    # Run 3 executions
    for i, prospect_data in enumerate(prospects, 1):
        print(f"\n{'─' * 80}")
        print(f"Execution {i}/3: {prospect_data['company']}")
        print(f"{'─' * 80}")
        
        try:
            await demo.run_demo(
                goal="Prioritize prospect and draft personalized outreach",
                prospect_data=prospect_data,
            )
            print(f"✅ Execution {i} completed successfully")
        except Exception as e:
            print(f"❌ Execution {i} failed: {e}")
        
        # Small delay between executions
        await asyncio.sleep(0.5)
    
    # Display aggregated metrics dashboard
    print("\n\n" + "=" * 80)
    print("📊 AGGREGATED METRICS DASHBOARD")
    print("=" * 80)
    
    aggregator.print_dashboard()
    
    # Show Prometheus export
    print("\n" + "=" * 80)
    print("📈 PROMETHEUS EXPORT FORMAT")
    print("=" * 80 + "\n")
    
    prometheus_metrics = aggregator.get_prometheus_metrics()
    print(prometheus_metrics)
    
    print("\n" + "=" * 80)
    print("✅ OBSERVABILITY DEMO COMPLETE")
    print("=" * 80)
    print("\nKey Observability Features Demonstrated:")
    print("  ✓ Real-time metrics aggregation")
    print("  ✓ Golden signals tracking (success rate, latency, error rate)")
    print("  ✓ Budget utilization monitoring")
    print("  ✓ Approval flow metrics")
    print("  ✓ Domain usage analytics")
    print("  ✓ Prometheus export format")
    print("\nPrometheus Scrape Endpoint:")
    print("  In production, expose /metrics endpoint serving aggregator.get_prometheus_metrics()")
    print("\nGrafana Dashboard:")
    print("  Import metrics to visualize trends, percentiles, and domain usage over time\n")


async def main():
    """Run observability demo."""
    try:
        await run_multiple_executions()
        return 0
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
