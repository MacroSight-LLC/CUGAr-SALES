"""
Observability metrics aggregator for CUGAr-SALES.

Aggregates canonical events across multiple executions and provides:
- Golden signals (success rate, latency, error rate)
- Real-time metrics dashboard
- Prometheus/Grafana export format
- Historical trend analysis

Following AGENTS.md observability requirements:
- Structured, PII-safe logs
- Canonical events only
- Golden signals tracking
- Trace continuity
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricsSummary:
    """Summary of aggregated metrics."""
    
    # Golden Signals
    success_rate: float = 0.0
    error_rate: float = 0.0
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    mean_latency: float = 0.0
    
    # Execution metrics
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_steps: int = 0
    mean_steps_per_execution: float = 0.0
    
    # Budget metrics
    total_budget_used: float = 0.0
    mean_budget_per_execution: float = 0.0
    budget_exceeded_count: int = 0
    
    # Approval metrics
    total_approvals: int = 0
    approval_wait_time_total: float = 0.0
    approval_wait_time_mean: float = 0.0
    approval_denied_count: int = 0
    approval_timeout_count: int = 0
    
    # Tool metrics
    tool_call_count: int = 0
    tool_error_count: int = 0
    tool_success_rate: float = 0.0
    
    # Domain metrics
    domain_usage: Dict[str, int] = field(default_factory=dict)
    
    # Time range
    first_execution: Optional[str] = None
    last_execution: Optional[str] = None


class MetricsAggregator:
    """
    Aggregates metrics across multiple executions.
    
    Provides:
    - Real-time metrics updates
    - Historical trend analysis
    - Prometheus export format
    - Dashboard visualization data
    """
    
    def __init__(self):
        """Initialize metrics aggregator."""
        self.executions: List[Dict[str, Any]] = []
        self.start_time = time.time()
        
        # Real-time counters
        self._total_executions = 0
        self._successful_executions = 0
        self._failed_executions = 0
        
        # Latency tracking
        self._latencies: List[float] = []
        
        # Budget tracking
        self._budget_used: List[float] = []
        
        # Approval tracking
        self._approval_wait_times: List[float] = []
        self._approval_outcomes: Dict[str, int] = defaultdict(int)
        
        # Tool tracking
        self._tool_calls: Dict[str, int] = defaultdict(int)
        self._tool_errors: Dict[str, int] = defaultdict(int)
        
        # Domain tracking
        self._domain_usage: Dict[str, int] = defaultdict(int)
        
        logger.info("MetricsAggregator initialized")
    
    def record_execution(
        self,
        trace_id: str,
        success: bool,
        duration_ms: float,
        steps: int,
        budget_used: float,
        budget_limit: float,
        approvals: List[Dict[str, Any]],
        results: List[Dict[str, Any]],
    ) -> None:
        """
        Record a single execution's metrics.
        
        Args:
            trace_id: Execution trace ID
            success: Whether execution succeeded
            duration_ms: Total execution time in milliseconds
            steps: Number of steps executed
            budget_used: Budget consumed
            budget_limit: Budget ceiling
            approvals: List of approval requests/responses
            results: Step results with domain information
        """
        execution_data = {
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": success,
            "duration_ms": duration_ms,
            "steps": steps,
            "budget_used": budget_used,
            "budget_limit": budget_limit,
            "budget_exceeded": budget_used > budget_limit,
            "approvals": len(approvals),
            "results": results,
        }
        
        self.executions.append(execution_data)
        
        # Update counters
        self._total_executions += 1
        if success:
            self._successful_executions += 1
        else:
            self._failed_executions += 1
        
        # Track latency
        self._latencies.append(duration_ms)
        
        # Track budget
        self._budget_used.append(budget_used)
        
        # Track approvals
        for approval in approvals:
            wait_time = approval.get("wait_time", 0)
            self._approval_wait_times.append(wait_time)
            status = approval.get("status", "unknown")
            self._approval_outcomes[status] += 1
        
        # Track tools and domains
        for result in results:
            tool = result.get("tool", "unknown")
            domain = result.get("domain", "unknown")
            status = result.get("status", "unknown")
            
            self._tool_calls[tool] += 1
            self._domain_usage[domain] += 1
            
            if status == "error":
                self._tool_errors[tool] += 1
        
        logger.info(
            f"Recorded execution {trace_id}: "
            f"success={success}, duration={duration_ms:.0f}ms, steps={steps}"
        )
    
    def get_summary(self) -> MetricsSummary:
        """Get current metrics summary."""
        if not self.executions:
            return MetricsSummary()
        
        # Calculate latency percentiles
        latencies_sorted = sorted(self._latencies)
        latency_p50 = latencies_sorted[len(latencies_sorted) // 2] if latencies_sorted else 0
        latency_p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)] if latencies_sorted else 0
        latency_p99 = latencies_sorted[int(len(latencies_sorted) * 0.99)] if latencies_sorted else 0
        mean_latency = sum(self._latencies) / len(self._latencies) if self._latencies else 0
        
        # Calculate tool metrics
        total_tool_calls = sum(self._tool_calls.values())
        total_tool_errors = sum(self._tool_errors.values())
        tool_success_rate = (
            (total_tool_calls - total_tool_errors) / total_tool_calls
            if total_tool_calls > 0 else 0.0
        )
        
        # Calculate approval metrics
        total_approvals = sum(self._approval_outcomes.values())
        approval_wait_time_total = sum(self._approval_wait_times)
        approval_wait_time_mean = (
            approval_wait_time_total / total_approvals if total_approvals > 0 else 0.0
        )
        
        return MetricsSummary(
            # Golden Signals
            success_rate=self._successful_executions / self._total_executions,
            error_rate=self._failed_executions / self._total_executions,
            latency_p50=latency_p50,
            latency_p95=latency_p95,
            latency_p99=latency_p99,
            mean_latency=mean_latency,
            
            # Execution metrics
            total_executions=self._total_executions,
            successful_executions=self._successful_executions,
            failed_executions=self._failed_executions,
            total_steps=sum(e["steps"] for e in self.executions),
            mean_steps_per_execution=sum(e["steps"] for e in self.executions) / self._total_executions,
            
            # Budget metrics
            total_budget_used=sum(self._budget_used),
            mean_budget_per_execution=sum(self._budget_used) / self._total_executions,
            budget_exceeded_count=sum(1 for e in self.executions if e.get("budget_exceeded", False)),
            
            # Approval metrics
            total_approvals=total_approvals,
            approval_wait_time_total=approval_wait_time_total,
            approval_wait_time_mean=approval_wait_time_mean,
            approval_denied_count=self._approval_outcomes.get("denied", 0),
            approval_timeout_count=self._approval_outcomes.get("timeout", 0),
            
            # Tool metrics
            tool_call_count=total_tool_calls,
            tool_error_count=total_tool_errors,
            tool_success_rate=tool_success_rate,
            
            # Domain metrics
            domain_usage=dict(self._domain_usage),
            
            # Time range
            first_execution=self.executions[0]["timestamp"] if self.executions else None,
            last_execution=self.executions[-1]["timestamp"] if self.executions else None,
        )
    
    def get_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus format.
        
        Returns:
            String formatted for Prometheus scraping
        """
        summary = self.get_summary()
        
        metrics = []
        
        # Golden Signals
        metrics.append(f"# HELP cugar_success_rate Success rate of executions")
        metrics.append(f"# TYPE cugar_success_rate gauge")
        metrics.append(f"cugar_success_rate {summary.success_rate:.4f}")
        
        metrics.append(f"# HELP cugar_error_rate Error rate of executions")
        metrics.append(f"# TYPE cugar_error_rate gauge")
        metrics.append(f"cugar_error_rate {summary.error_rate:.4f}")
        
        metrics.append(f"# HELP cugar_latency_ms Latency percentiles in milliseconds")
        metrics.append(f"# TYPE cugar_latency_ms gauge")
        metrics.append(f'cugar_latency_ms{{percentile="p50"}} {summary.latency_p50:.2f}')
        metrics.append(f'cugar_latency_ms{{percentile="p95"}} {summary.latency_p95:.2f}')
        metrics.append(f'cugar_latency_ms{{percentile="p99"}} {summary.latency_p99:.2f}')
        
        # Execution counters
        metrics.append(f"# HELP cugar_executions_total Total number of executions")
        metrics.append(f"# TYPE cugar_executions_total counter")
        metrics.append(f"cugar_executions_total {summary.total_executions}")
        
        metrics.append(f"# HELP cugar_executions_successful Successful executions")
        metrics.append(f"# TYPE cugar_executions_successful counter")
        metrics.append(f"cugar_executions_successful {summary.successful_executions}")
        
        metrics.append(f"# HELP cugar_executions_failed Failed executions")
        metrics.append(f"# TYPE cugar_executions_failed counter")
        metrics.append(f"cugar_executions_failed {summary.failed_executions}")
        
        # Tool metrics
        metrics.append(f"# HELP cugar_tool_calls_total Total tool calls")
        metrics.append(f"# TYPE cugar_tool_calls_total counter")
        metrics.append(f"cugar_tool_calls_total {summary.tool_call_count}")
        
        metrics.append(f"# HELP cugar_tool_errors_total Tool errors")
        metrics.append(f"# TYPE cugar_tool_errors_total counter")
        metrics.append(f"cugar_tool_errors_total {summary.tool_error_count}")
        
        # Budget metrics
        metrics.append(f"# HELP cugar_budget_used_total Total budget consumed")
        metrics.append(f"# TYPE cugar_budget_used_total counter")
        metrics.append(f"cugar_budget_used_total {summary.total_budget_used:.2f}")
        
        metrics.append(f"# HELP cugar_budget_exceeded_total Budget exceeded count")
        metrics.append(f"# TYPE cugar_budget_exceeded_total counter")
        metrics.append(f"cugar_budget_exceeded_total {summary.budget_exceeded_count}")
        
        # Approval metrics
        metrics.append(f"# HELP cugar_approvals_total Total approval requests")
        metrics.append(f"# TYPE cugar_approvals_total counter")
        metrics.append(f"cugar_approvals_total {summary.total_approvals}")
        
        metrics.append(f"# HELP cugar_approval_wait_time_ms Mean approval wait time")
        metrics.append(f"# TYPE cugar_approval_wait_time_ms gauge")
        metrics.append(f"cugar_approval_wait_time_ms {summary.approval_wait_time_mean * 1000:.2f}")
        
        # Domain metrics
        metrics.append(f"# HELP cugar_domain_usage_total Tool calls by domain")
        metrics.append(f"# TYPE cugar_domain_usage_total counter")
        for domain, count in summary.domain_usage.items():
            metrics.append(f'cugar_domain_usage_total{{domain="{domain}"}} {count}')
        
        return "\n".join(metrics)
    
    def print_dashboard(self) -> None:
        """Print real-time metrics dashboard to console."""
        summary = self.get_summary()
        
        print("\n" + "=" * 80)
        print("📊 CUGAr-SALES OBSERVABILITY DASHBOARD")
        print("=" * 80)
        
        # Golden Signals
        print("\n🎯 GOLDEN SIGNALS:")
        print(f"  Success Rate: {summary.success_rate:.1%}")
        print(f"  Error Rate: {summary.error_rate:.1%}")
        print(f"  Latency P50: {summary.latency_p50:.0f}ms")
        print(f"  Latency P95: {summary.latency_p95:.0f}ms")
        print(f"  Latency P99: {summary.latency_p99:.0f}ms")
        print(f"  Mean Latency: {summary.mean_latency:.0f}ms")
        
        # Execution Summary
        print("\n📈 EXECUTION SUMMARY:")
        print(f"  Total Executions: {summary.total_executions}")
        print(f"  Successful: {summary.successful_executions}")
        print(f"  Failed: {summary.failed_executions}")
        print(f"  Total Steps: {summary.total_steps}")
        print(f"  Mean Steps/Execution: {summary.mean_steps_per_execution:.1f}")
        
        # Budget Summary
        print("\n💰 BUDGET SUMMARY:")
        print(f"  Total Budget Used: {summary.total_budget_used:.1f}")
        print(f"  Mean Budget/Execution: {summary.mean_budget_per_execution:.1f}")
        print(f"  Budget Exceeded: {summary.budget_exceeded_count} times")
        
        # Approval Summary
        if summary.total_approvals > 0:
            print("\n🔐 APPROVAL SUMMARY:")
            print(f"  Total Approvals: {summary.total_approvals}")
            print(f"  Mean Wait Time: {summary.approval_wait_time_mean:.2f}s")
            print(f"  Denied: {summary.approval_denied_count}")
            print(f"  Timeout: {summary.approval_timeout_count}")
        
        # Tool Summary
        print("\n🛠️  TOOL SUMMARY:")
        print(f"  Total Calls: {summary.tool_call_count}")
        print(f"  Errors: {summary.tool_error_count}")
        print(f"  Success Rate: {summary.tool_success_rate:.1%}")
        
        # Domain Usage
        if summary.domain_usage:
            print("\n📚 DOMAIN USAGE:")
            for domain, count in sorted(summary.domain_usage.items(), key=lambda x: x[1], reverse=True):
                print(f"  {domain}: {count} calls")
        
        # Time Range
        print("\n⏰ TIME RANGE:")
        print(f"  First Execution: {summary.first_execution}")
        print(f"  Last Execution: {summary.last_execution}")
        print(f"  Uptime: {time.time() - self.start_time:.0f}s")
        
        print("\n" + "=" * 80 + "\n")


# Global metrics aggregator instance
_global_aggregator: Optional[MetricsAggregator] = None


def get_metrics_aggregator() -> MetricsAggregator:
    """Get or create global metrics aggregator."""
    global _global_aggregator
    if _global_aggregator is None:
        _global_aggregator = MetricsAggregator()
    return _global_aggregator


def reset_metrics() -> None:
    """Reset global metrics aggregator (for testing)."""
    global _global_aggregator
    _global_aggregator = MetricsAggregator()
