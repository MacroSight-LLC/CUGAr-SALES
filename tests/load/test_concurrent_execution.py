"""
Load testing for CUGAr-SALES concurrent execution.

Tests system performance under various concurrent load levels:
- 10 parallel executions
- 50 parallel executions
- 100 parallel executions

Measures:
- Throughput (executions per second)
- Latency (P50/P95/P99)
- Success rate under load
- Memory usage
- Error rate
"""

import asyncio
import sys
import time
import psutil
import statistics
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add src and root to path
root_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_path / "src"))
sys.path.insert(0, str(root_path))

from demo_production import ProductionDemo
from cuga.orchestrator.metrics import get_metrics_aggregator, reset_metrics


class LoadTester:
    """Load testing framework for CUGAr-SALES."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.process = psutil.Process()
        
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    async def run_single_execution(self, execution_id: int) -> Dict[str, Any]:
        """Run a single demo execution and measure performance."""
        start_time = time.time()
        start_memory = self.get_memory_usage_mb()
        
        demo = ProductionDemo(profile="demo")
        
        prospect_data = {
            "company": f"Company-{execution_id}",
            "industry": "Technology",
            "employee_count": 500,
            "revenue": 10000000,
            "template": f"Hi {{{{first_name}}}}, I noticed {{{{company}}}} is doing great work.",
            "prospect_data": {
                "first_name": f"Contact{execution_id}",
                "company": f"Company-{execution_id}",
                "industry": "Technology",
                "role": "VP Engineering",
                "location": "San Francisco",
                "pain_point": "scaling",
            },
        }
        
        try:
            await demo.run_demo(
                goal=f"Load test execution {execution_id}",
                prospect_data=prospect_data,
            )
            
            success = True
            error = None
            
        except Exception as e:
            success = False
            error = str(e)
        
        end_time = time.time()
        end_memory = self.get_memory_usage_mb()
        
        return {
            "execution_id": execution_id,
            "success": success,
            "error": error,
            "duration_ms": (end_time - start_time) * 1000,
            "memory_delta_mb": end_memory - start_memory,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def run_concurrent_batch(
        self,
        batch_size: int,
        batch_name: str
    ) -> Dict[str, Any]:
        """Run a batch of concurrent executions."""
        print(f"\n{'=' * 80}")
        print(f"🚀 LOAD TEST: {batch_name}")
        print(f"{'=' * 80}")
        print(f"Batch Size: {batch_size} parallel executions")
        print(f"Started: {datetime.utcnow().isoformat()}")
        
        # Reset metrics
        reset_metrics()
        
        # Record initial memory
        initial_memory = self.get_memory_usage_mb()
        print(f"Initial Memory: {initial_memory:.1f} MB")
        
        # Start timer
        batch_start = time.time()
        
        # Create tasks for concurrent execution
        tasks = [
            self.run_single_execution(i)
            for i in range(batch_size)
        ]
        
        # Run all tasks concurrently
        print(f"\n⏳ Running {batch_size} executions in parallel...")
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        # Calculate batch metrics
        batch_duration = time.time() - batch_start
        final_memory = self.get_memory_usage_mb()
        memory_delta = final_memory - initial_memory
        
        # Extract latencies
        latencies = [r["duration_ms"] for r in results if r["success"]]
        success_count = sum(1 for r in results if r["success"])
        failure_count = batch_size - success_count
        
        # Calculate statistics
        if latencies:
            latencies_sorted = sorted(latencies)
            p50_idx = int(len(latencies_sorted) * 0.5)
            p95_idx = int(len(latencies_sorted) * 0.95)
            p99_idx = int(len(latencies_sorted) * 0.99)
            
            latency_stats = {
                "min": min(latencies),
                "max": max(latencies),
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p50": latencies_sorted[p50_idx],
                "p95": latencies_sorted[p95_idx],
                "p99": latencies_sorted[p99_idx],
            }
        else:
            latency_stats = {
                "min": 0, "max": 0, "mean": 0, "median": 0,
                "p50": 0, "p95": 0, "p99": 0,
            }
        
        # Calculate throughput
        throughput = batch_size / batch_duration if batch_duration > 0 else 0
        
        batch_summary = {
            "batch_name": batch_name,
            "batch_size": batch_size,
            "duration_seconds": batch_duration,
            "throughput": throughput,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_count / batch_size if batch_size > 0 else 0,
            "latency_stats": latency_stats,
            "memory_initial_mb": initial_memory,
            "memory_final_mb": final_memory,
            "memory_delta_mb": memory_delta,
            "results": results,
        }
        
        # Print summary
        self.print_batch_summary(batch_summary)
        
        return batch_summary
    
    def print_batch_summary(self, summary: Dict[str, Any]) -> None:
        """Print formatted batch summary."""
        print(f"\n{'─' * 80}")
        print("📊 BATCH RESULTS")
        print(f"{'─' * 80}")
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"  Duration: {summary['duration_seconds']:.2f}s")
        print(f"  Throughput: {summary['throughput']:.2f} executions/second")
        
        print(f"\n✅ SUCCESS METRICS:")
        print(f"  Success: {summary['success_count']}/{summary['batch_size']}")
        print(f"  Failure: {summary['failure_count']}/{summary['batch_size']}")
        print(f"  Success Rate: {summary['success_rate']:.1%}")
        
        print(f"\n⚡ LATENCY (ms):")
        stats = summary['latency_stats']
        print(f"  Min: {stats['min']:.0f}ms")
        print(f"  Mean: {stats['mean']:.0f}ms")
        print(f"  Median: {stats['median']:.0f}ms")
        print(f"  P50: {stats['p50']:.0f}ms")
        print(f"  P95: {stats['p95']:.0f}ms")
        print(f"  P99: {stats['p99']:.0f}ms")
        print(f"  Max: {stats['max']:.0f}ms")
        
        print(f"\n💾 MEMORY:")
        print(f"  Initial: {summary['memory_initial_mb']:.1f} MB")
        print(f"  Final: {summary['memory_final_mb']:.1f} MB")
        print(f"  Delta: {summary['memory_delta_mb']:.1f} MB")
        print(f"  Per Execution: {summary['memory_delta_mb'] / summary['batch_size']:.2f} MB")
        
        # Check for failures
        if summary['failure_count'] > 0:
            print(f"\n⚠️  FAILURES:")
            for result in summary['results']:
                if not result['success']:
                    print(f"  Execution {result['execution_id']}: {result['error']}")
    
    def print_comparison(self, all_summaries: List[Dict[str, Any]]) -> None:
        """Print comparison across all batches."""
        print(f"\n{'=' * 80}")
        print("📈 LOAD TEST COMPARISON")
        print(f"{'=' * 80}\n")
        
        print(f"{'Batch':<20} {'Size':<8} {'Success':<10} {'Throughput':<15} {'P95 Latency':<15} {'Memory Δ'}")
        print(f"{'─' * 20} {'─' * 8} {'─' * 10} {'─' * 15} {'─' * 15} {'─' * 10}")
        
        for summary in all_summaries:
            batch_name = summary['batch_name'][:19]
            size = summary['batch_size']
            success_rate = f"{summary['success_rate']:.1%}"
            throughput = f"{summary['throughput']:.2f} ex/s"
            p95 = f"{summary['latency_stats']['p95']:.0f}ms"
            memory = f"+{summary['memory_delta_mb']:.1f} MB"
            
            print(f"{batch_name:<20} {size:<8} {success_rate:<10} {throughput:<15} {p95:<15} {memory}")
        
        print()
    
    def generate_performance_report(
        self,
        all_summaries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        
        # Calculate aggregate metrics
        total_executions = sum(s['batch_size'] for s in all_summaries)
        total_successes = sum(s['success_count'] for s in all_summaries)
        total_failures = sum(s['failure_count'] for s in all_summaries)
        
        overall_success_rate = total_successes / total_executions if total_executions > 0 else 0
        
        # Latency across all batches
        all_latencies = []
        for summary in all_summaries:
            all_latencies.extend([
                r['duration_ms'] for r in summary['results'] if r['success']
            ])
        
        if all_latencies:
            all_latencies_sorted = sorted(all_latencies)
            overall_latency = {
                "min": min(all_latencies),
                "max": max(all_latencies),
                "mean": statistics.mean(all_latencies),
                "p50": all_latencies_sorted[int(len(all_latencies_sorted) * 0.5)],
                "p95": all_latencies_sorted[int(len(all_latencies_sorted) * 0.95)],
                "p99": all_latencies_sorted[int(len(all_latencies_sorted) * 0.99)],
            }
        else:
            overall_latency = {
                "min": 0, "max": 0, "mean": 0,
                "p50": 0, "p95": 0, "p99": 0,
            }
        
        # Memory usage
        total_memory_delta = sum(s['memory_delta_mb'] for s in all_summaries)
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_executions": total_executions,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "overall_success_rate": overall_success_rate,
            "overall_latency": overall_latency,
            "total_memory_delta_mb": total_memory_delta,
            "batches": all_summaries,
        }
        
        return report


async def run_load_tests():
    """Run comprehensive load tests."""
    print("=" * 80)
    print("🔬 CUGAr-SALES LOAD TESTING SUITE")
    print("=" * 80)
    print(f"Started: {datetime.utcnow().isoformat()}")
    print()
    
    tester = LoadTester()
    all_summaries = []
    
    # Test configurations
    test_configs = [
        (5, "Warm-up (5 parallel)"),
        (10, "Light Load (10 parallel)"),
        (25, "Medium Load (25 parallel)"),
        (50, "Heavy Load (50 parallel)"),
    ]
    
    # Run all test batches
    for batch_size, batch_name in test_configs:
        try:
            summary = await tester.run_concurrent_batch(batch_size, batch_name)
            all_summaries.append(summary)
            
            # Cool down between batches
            print(f"\n⏸️  Cooling down for 3 seconds...")
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"\n❌ Batch failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Print comparison
    tester.print_comparison(all_summaries)
    
    # Generate report
    report = tester.generate_performance_report(all_summaries)
    
    # Print final summary
    print("=" * 80)
    print("📊 FINAL PERFORMANCE REPORT")
    print("=" * 80)
    print(f"\nTotal Executions: {report['total_executions']}")
    print(f"Overall Success Rate: {report['overall_success_rate']:.1%}")
    print(f"\nLatency (ms):")
    print(f"  Mean: {report['overall_latency']['mean']:.0f}ms")
    print(f"  P50: {report['overall_latency']['p50']:.0f}ms")
    print(f"  P95: {report['overall_latency']['p95']:.0f}ms")
    print(f"  P99: {report['overall_latency']['p99']:.0f}ms")
    print(f"\nTotal Memory Delta: {report['total_memory_delta_mb']:.1f} MB")
    
    # Performance assessment
    print("\n" + "=" * 80)
    print("✅ PERFORMANCE ASSESSMENT")
    print("=" * 80)
    
    # Check success rate
    if report['overall_success_rate'] >= 0.95:
        print("✅ SUCCESS RATE: EXCELLENT (≥95%)")
    elif report['overall_success_rate'] >= 0.90:
        print("✅ SUCCESS RATE: GOOD (≥90%)")
    else:
        print("⚠️  SUCCESS RATE: NEEDS IMPROVEMENT (<90%)")
    
    # Check P95 latency
    if report['overall_latency']['p95'] < 3000:
        print("✅ LATENCY P95: EXCELLENT (<3000ms)")
    elif report['overall_latency']['p95'] < 5000:
        print("✅ LATENCY P95: GOOD (<5000ms)")
    else:
        print("⚠️  LATENCY P95: HIGH (>5000ms)")
    
    # Check memory usage
    avg_memory_per_exec = report['total_memory_delta_mb'] / report['total_executions']
    if avg_memory_per_exec < 1.0:
        print("✅ MEMORY USAGE: EXCELLENT (<1MB/execution)")
    elif avg_memory_per_exec < 5.0:
        print("✅ MEMORY USAGE: GOOD (<5MB/execution)")
    else:
        print("⚠️  MEMORY USAGE: HIGH (>5MB/execution)")
    
    print("\n" + "=" * 80)
    print("✅ LOAD TESTING COMPLETE")
    print("=" * 80)
    
    return report


if __name__ == "__main__":
    report = asyncio.run(run_load_tests())
    sys.exit(0)
