# Monitoring Stack Setup Guide

## Overview

Complete Prometheus + Grafana monitoring stack for CUGAr-SALES with:
- FastAPI metrics endpoint exposing Prometheus format
- Automated scraping every 15 seconds
- Pre-configured Grafana dashboards for golden signals
- Alert rules for performance degradation

---

## Quick Start

### 1. Start Metrics Endpoint (Development)

```bash
# Terminal 1: Start metrics API
cd /home/taylor/CUGAr-SALES
python3 src/cuga/api/metrics_endpoint.py

# Access endpoints:
# - http://localhost:8000/metrics (Prometheus format)
# - http://localhost:8000/health (health check)
# - http://localhost:8000/dashboard (JSON metrics)
# - http://localhost:8000/docs (API documentation)
```

### 2. Run Demo to Generate Metrics

```bash
# Terminal 2: Run observability demo
python3 demo_observability.py

# This will:
# - Execute 3 times with different prospects
# - Record metrics in global aggregator
# - Display dashboard after all runs
```

### 3. Start Full Monitoring Stack (Docker)

```bash
# Build and start all services
docker-compose -f docker-compose.monitoring.yml up -d

# View logs
docker-compose -f docker-compose.monitoring.yml logs -f

# Stop services
docker-compose -f docker-compose.monitoring.yml down
```

**Access Points:**
- **Metrics API**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│ demo_observability.py                                    │
│   - Runs multiple executions                             │
│   - Records metrics via MetricsAggregator                │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────────┐
│ MetricsAggregator (in-memory)                            │
│   - Aggregates metrics across executions                 │
│   - Calculates golden signals                            │
│   - Provides Prometheus export                           │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────────┐
│ FastAPI Metrics Endpoint (port 8000)                     │
│   GET /metrics    → Prometheus text format               │
│   GET /health     → JSON health status                   │
│   GET /dashboard  → JSON metrics summary                 │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ HTTP scrape every 15s
                     ↓
┌──────────────────────────────────────────────────────────┐
│ Prometheus (port 9090)                                   │
│   - Scrapes /metrics endpoint                            │
│   - Stores time-series data                              │
│   - Evaluates alert rules                                │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ PromQL queries
                     ↓
┌──────────────────────────────────────────────────────────┐
│ Grafana (port 3000)                                      │
│   - Visualizes golden signals                            │
│   - Shows domain usage trends                            │
│   - Displays latency percentiles                         │
└──────────────────────────────────────────────────────────┘
```

---

## Metrics Available

### Golden Signals

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `cugar_success_rate` | Gauge | Success percentage (0-1) | >0.90 |
| `cugar_error_rate` | Gauge | Error percentage (0-1) | <0.10 |
| `cugar_latency_ms{percentile="p50"}` | Gauge | Median latency | <1000ms |
| `cugar_latency_ms{percentile="p95"}` | Gauge | P95 latency | <3000ms |
| `cugar_latency_ms{percentile="p99"}` | Gauge | P99 latency | <5000ms |

### Execution Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `cugar_executions_total` | Counter | Total executions |
| `cugar_executions_successful` | Counter | Successful executions |
| `cugar_executions_failed` | Counter | Failed executions |

### Budget Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `cugar_budget_used_total` | Counter | Total budget consumed |
| `cugar_budget_exceeded_total` | Counter | Times budget limit exceeded |

### Approval Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `cugar_approvals_total` | Counter | Total approval requests |
| `cugar_approval_wait_time_ms` | Gauge | Mean approval wait time |

### Tool Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `cugar_tool_calls_total` | Counter | Total tool invocations |
| `cugar_tool_errors_total` | Counter | Tool errors |

### Domain Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `cugar_domain_usage_total{domain="..."}` | Counter | Tool calls per domain |

---

## Alert Rules

Configured in `monitoring/prometheus/rules/golden_signals.yml`:

### Warning Alerts (5-10 minute threshold)

- **LowSuccessRate**: Success rate < 90%
- **HighErrorRate**: Error rate > 10%
- **HighLatencyP95**: P95 latency > 5000ms
- **HighLatencyP99**: P99 latency > 10000ms
- **FrequentBudgetExceeded**: >5 times in 1 hour
- **HighToolErrorRate**: Tool error rate > 5%

### Critical Alerts (1-2 minute threshold)

- **CriticalSuccessRate**: Success rate < 80%
- **ApprovalTimeouts**: Any approval timeouts detected
- **NoRecentExecutions**: No activity for 30 minutes

---

## Grafana Dashboard

Pre-configured dashboard at `monitoring/grafana/dashboards/golden-signals.json` includes:

### Row 1: Golden Signals (Stats)
- Success Rate (gauge with thresholds)
- Error Rate (gauge with thresholds)
- Latency P95 (gauge with thresholds)
- Total Executions (counter)

### Row 2: Trends (Time Series)
- Success/Error Rate Over Time
- Latency Percentiles (P50/P95/P99)

### Row 3: Operations (Gauges/Stats)
- Budget Usage (gauge)
- Approval Wait Time (stat)
- Tool Success Rate (gauge)

### Row 4: Domain Analytics (Bar Chart)
- Tool Calls by Domain

---

## Testing the Stack

### 1. Verify Metrics Endpoint

```bash
# Health check
curl http://localhost:8000/health | jq

# Raw Prometheus metrics
curl http://localhost:8000/metrics

# JSON dashboard
curl http://localhost:8000/dashboard | jq
```

### 2. Verify Prometheus Scraping

```bash
# Open Prometheus UI
open http://localhost:9090

# Run queries:
cugar_success_rate
rate(cugar_executions_total[5m])
cugar_latency_ms{percentile="p95"}
```

### 3. Verify Grafana Dashboard

```bash
# Open Grafana
open http://localhost:3000

# Login: admin / admin
# Navigate to: Dashboards → CUGAr-SALES Golden Signals
```

### 4. Test Alert Rules

```bash
# Check configured alerts in Prometheus
open http://localhost:9090/alerts

# View alert rules
open http://localhost:9090/rules
```

---

## Production Deployment

### Environment Variables

```bash
# Metrics API
export LOG_LEVEL=info
export METRICS_PORT=8000

# Prometheus
export PROMETHEUS_RETENTION=30d
export PROMETHEUS_SCRAPE_INTERVAL=15s

# Grafana
export GF_SECURITY_ADMIN_PASSWORD=<strong-password>
export GF_SERVER_ROOT_URL=https://grafana.yourdomain.com
```

### Kubernetes Deployment

```yaml
# metrics-api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cugar-metrics-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cugar-metrics-api
  template:
    metadata:
      labels:
        app: cugar-metrics-api
    spec:
      containers:
      - name: metrics-api
        image: cugar-sales:metrics-latest
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "info"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
```

### Prometheus ServiceMonitor (Prometheus Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: cugar-sales-metrics
spec:
  selector:
    matchLabels:
      app: cugar-metrics-api
  endpoints:
  - port: http
    interval: 15s
    path: /metrics
```

---

## Troubleshooting

### Metrics Not Appearing

1. **Check metrics endpoint is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Verify MetricsAggregator has data:**
   ```bash
   curl http://localhost:8000/dashboard | jq '.executions.total'
   ```

3. **Check Prometheus scraping:**
   ```bash
   # Prometheus UI → Status → Targets
   # Ensure cugar-sales target is UP
   ```

### Grafana Dashboard Empty

1. **Verify Prometheus datasource:**
   ```bash
   # Grafana → Configuration → Data Sources
   # Test connection to Prometheus
   ```

2. **Check data in Prometheus:**
   ```bash
   # Run query in Prometheus UI:
   cugar_success_rate
   ```

3. **Verify time range:**
   - Dashboard time picker should include recent data
   - Try "Last 15 minutes" or "Last 1 hour"

### High Latency Metrics

Remember P50/P95/P99 include:
- Tool execution time
- Approval wait time (simulated 2s)
- Network overhead (if using live adapters)

For pure execution time, subtract approval wait time:
```promql
cugar_latency_ms{percentile="p95"} - cugar_approval_wait_time_ms
```

### Docker Issues

```bash
# View logs
docker-compose -f docker-compose.monitoring.yml logs cugar-api
docker-compose -f docker-compose.monitoring.yml logs prometheus
docker-compose -f docker-compose.monitoring.yml logs grafana

# Restart services
docker-compose -f docker-compose.monitoring.yml restart

# Rebuild images
docker-compose -f docker-compose.monitoring.yml build --no-cache
```

---

## Next Steps

1. **Add More Dashboards**
   - Tool-specific performance panels
   - Domain comparison charts
   - Budget trend analysis

2. **Configure Alerting**
   - Set up Alertmanager for notifications
   - Configure Slack/PagerDuty webhooks
   - Add runbook links to alerts

3. **Enable Authentication**
   - Configure OAuth for Grafana
   - Add API key authentication for metrics endpoint
   - Set up TLS/HTTPS

4. **Long-Term Storage**
   - Configure Prometheus remote write (e.g., to Thanos)
   - Set up backup for Grafana dashboards
   - Implement metrics retention policy

---

## References

- **Prometheus Documentation**: https://prometheus.io/docs/
- **Grafana Documentation**: https://grafana.com/docs/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **CUGAr AGENTS.md**: Canonical observability requirements
- **WEEK_3_SUMMARY.md**: Observability implementation details
