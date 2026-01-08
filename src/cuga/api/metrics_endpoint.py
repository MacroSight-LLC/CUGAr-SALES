"""
Prometheus metrics endpoint for CUGAr-SALES.

Exposes aggregated metrics in Prometheus format for scraping.
Enables real-time monitoring with Prometheus + Grafana.

Usage:
    # Development server
    python3 -m uvicorn cuga.api.metrics_endpoint:app --reload --port 8000
    
    # Production server
    uvicorn cuga.api.metrics_endpoint:app --host 0.0.0.0 --port 8000 --workers 4
    
    # Access metrics
    curl http://localhost:8000/metrics
    curl http://localhost:8000/health
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse, JSONResponse

from cuga.orchestrator.metrics import get_metrics_aggregator

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CUGAr-SALES Metrics API",
    description="Prometheus metrics endpoint for sales automation observability",
    version="1.0.0",
)


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns aggregated metrics in Prometheus text format:
    - Golden signals (success_rate, error_rate, latency percentiles)
    - Execution counters (total, successful, failed)
    - Budget metrics (total, mean, exceeded count)
    - Approval metrics (total, wait times, denied/timeout)
    - Tool metrics (calls, errors, success rate)
    - Domain usage (calls by domain)
    
    This endpoint is designed to be scraped by Prometheus at regular intervals.
    
    Returns:
        Plain text in Prometheus exposition format
    """
    try:
        aggregator = get_metrics_aggregator()
        prometheus_output = aggregator.get_prometheus_metrics()
        
        logger.info("Metrics endpoint scraped successfully")
        return prometheus_output
        
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        # Return empty metrics on error (Prometheus expects 200 OK)
        return "# Error generating metrics\n"


@app.get("/health")
async def health():
    """
    Health check endpoint.
    
    Returns system health status including:
    - Service status (healthy/unhealthy)
    - Metrics aggregator status
    - Current metrics summary
    
    Returns:
        JSON with health status and basic metrics
    """
    try:
        aggregator = get_metrics_aggregator()
        summary = aggregator.get_summary()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "cugar-sales-metrics",
                "version": "1.0.0",
                "metrics": {
                    "total_executions": summary.total_executions,
                    "success_rate": summary.success_rate,
                    "error_rate": summary.error_rate,
                    "latency_p95_ms": summary.latency_p95,
                },
            },
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "cugar-sales-metrics",
                "error": str(e),
            },
        )


@app.get("/")
async def root():
    """
    Root endpoint with API documentation.
    
    Returns:
        JSON with available endpoints and documentation links
    """
    return {
        "service": "CUGAr-SALES Metrics API",
        "version": "1.0.0",
        "endpoints": {
            "/metrics": "Prometheus metrics in text format",
            "/health": "Health check with current metrics summary",
            "/docs": "Interactive API documentation (Swagger UI)",
            "/redoc": "Alternative API documentation (ReDoc)",
        },
        "documentation": {
            "prometheus": "Configure Prometheus to scrape /metrics endpoint",
            "grafana": "Import metrics to visualize golden signals and trends",
        },
    }


@app.get("/dashboard")
async def dashboard():
    """
    Human-readable metrics dashboard.
    
    Returns aggregated metrics in JSON format for web dashboards.
    This is an alternative to the console dashboard in MetricsAggregator.
    
    Returns:
        JSON with complete metrics summary
    """
    try:
        aggregator = get_metrics_aggregator()
        summary = aggregator.get_summary()
        
        return {
            "golden_signals": {
                "success_rate": summary.success_rate,
                "error_rate": summary.error_rate,
                "latency_p50_ms": summary.latency_p50,
                "latency_p95_ms": summary.latency_p95,
                "latency_p99_ms": summary.latency_p99,
                "mean_latency_ms": summary.mean_latency,
            },
            "executions": {
                "total": summary.total_executions,
                "successful": summary.successful_executions,
                "failed": summary.failed_executions,
                "total_steps": summary.total_steps,
                "mean_steps_per_execution": summary.mean_steps_per_execution,
            },
            "budget": {
                "total_used": summary.total_budget_used,
                "mean_per_execution": summary.mean_budget_per_execution,
                "exceeded_count": summary.budget_exceeded_count,
            },
            "approvals": {
                "total": summary.total_approvals,
                "wait_time_total_ms": summary.approval_wait_time_total,
                "wait_time_mean_ms": summary.approval_wait_time_mean,
                "denied_count": summary.approval_denied_count,
                "timeout_count": summary.approval_timeout_count,
            },
            "tools": {
                "total_calls": summary.tool_call_count,
                "errors": summary.tool_error_count,
                "success_rate": summary.tool_success_rate,
            },
            "domains": dict(summary.domain_usage),
            "time_range": {
                "first_execution": summary.first_execution,
                "last_execution": summary.last_execution,
            },
        }
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )


if __name__ == "__main__":
    # Development server
    import uvicorn
    
    print("🚀 Starting CUGAr-SALES Metrics API...")
    print("📊 Metrics endpoint: http://localhost:8000/metrics")
    print("💚 Health check: http://localhost:8000/health")
    print("📈 Dashboard: http://localhost:8000/dashboard")
    print("📚 API docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
