# Observability Documentation Index

Complete documentation for CUGAR agent observability system.

## Quick Start

**Want to get started quickly?**
1. Read [Quick Reference](QUICK_REFERENCE.md) - Common patterns and one-liners
2. Follow [Integration Checklist](INTEGRATION_CHECKLIST.md) - Step-by-step integration
3. Run example: `python examples/observability_example.py`

## Core Documentation

### 📘 [OBSERVABILITY_SLOS.md](OBSERVABILITY_SLOS.md)
**Complete API reference and implementation guide**

Comprehensive documentation covering:
- Architecture overview with diagrams
- Event types (14 types with examples)
- Golden signals (success rate, latency, errors, traffic)
- Configuration (env vars, config files)
- Integration patterns (planner, routing, tools, budget, approval)
- Prometheus metrics endpoint
- Grafana dashboard setup
- Testing guide
- Best practices
- Troubleshooting

**When to use**: Deep dive into observability architecture, complete API reference, implementation details.

### ⚡ [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
**Quick reference for common patterns**

One-page guide with:
- Event emission patterns (copy-paste code snippets)
- Metrics access examples
- Configuration templates
- Common patterns (trace lifecycle, flush, reset)
- Dashboard panel descriptions
- Troubleshooting checklist

**When to use**: Quick lookup for event emission code, metric access, configuration.

### ✅ [INTEGRATION_CHECKLIST.md](INTEGRATION_CHECKLIST.md)
**Step-by-step integration guide**

10-step checklist covering:
1. Initialize collector at startup
2. Emit plan events
3. Emit route events
4. Emit tool call events
5. Emit budget events
6. Emit approval events
7. Add Prometheus endpoint
8. Configure OTEL backend
9. Import Grafana dashboard
10. Verify integration

Each step includes:
- Code snippets with exact integration points
- Files to modify
- Verification commands
- Troubleshooting tips

**When to use**: First-time integration, systematic rollout of observability.

### 📊 [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
**Implementation status and component details**

Summary document with:
- Implementation status (✅ Complete)
- Component inventory (5 modules, 3,500+ lines)
- Event types (14 types documented)
- Golden signals (8 metrics tracked)
- Integration points (5 locations)
- Configuration options
- Testing coverage (30+ tests)
- Files created (11 files)
- Next steps
- Success metrics

**When to use**: Project overview, status check, component inventory.

## Related Documentation

### Agent System
- [AGENTS.md](../../AGENTS.md) - Agent guardrails and contracts (Observability § added)
- [docs/orchestrator/ORCHESTRATOR_CONTRACT.md](../orchestrator/ORCHESTRATOR_CONTRACT.md) - Orchestrator protocol
- [docs/orchestrator/EXECUTION_CONTEXT.md](../orchestrator/EXECUTION_CONTEXT.md) - Execution context with trace_id

### Configuration
- [docs/configuration/CONFIG_RESOLUTION.md](../configuration/CONFIG_RESOLUTION.md) - Config precedence
- [docs/configuration/ENVIRONMENT_MODES.md](../configuration/ENVIRONMENT_MODES.md) - Environment setup

### Testing
- [docs/testing/COVERAGE_MATRIX.md](../testing/COVERAGE_MATRIX.md) - Test coverage requirements
- [docs/testing/SCENARIO_TESTING.md](../testing/SCENARIO_TESTING.md) - Scenario tests

## Files & Locations

### Source Code
```
src/cuga/observability/
├── __init__.py              # Module exports
├── events.py                # Event system (461 lines)
├── golden_signals.py        # Metrics tracking (448 lines)
├── exporters.py             # OTEL/console export (342 lines)
└── collector.py             # Event collection (270 lines)
```

### Configuration
```
configs/observability.yaml   # Observability settings
observability/
├── README.md                # Module overview
└── grafana_dashboard.json   # Pre-built dashboard (400+ lines)
```

### Documentation
```
docs/observability/
├── README.md                       # This index
├── OBSERVABILITY_SLOS.md           # Complete reference (600+ lines)
├── QUICK_REFERENCE.md              # Quick guide (350+ lines)
├── INTEGRATION_CHECKLIST.md        # Step-by-step (500+ lines)
└── IMPLEMENTATION_SUMMARY.md       # Status summary
```

### Examples & Tests
```
examples/observability_example.py           # Integration demo (350+ lines)
tests/observability/test_observability.py   # Test suite (700+ lines)
```

## Reading Order

### For First-Time Users
1. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Get familiar with concepts
2. [INTEGRATION_CHECKLIST.md](INTEGRATION_CHECKLIST.md) - Follow integration steps
3. Run `python examples/observability_example.py` - See it in action
4. [OBSERVABILITY_SLOS.md](OBSERVABILITY_SLOS.md) - Deep dive when needed

### For Implementers
1. [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Understand components
2. [INTEGRATION_CHECKLIST.md](INTEGRATION_CHECKLIST.md) - Follow integration guide
3. [OBSERVABILITY_SLOS.md](OBSERVABILITY_SLOS.md) - Reference API details
4. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick lookup

### For Operators
1. [OBSERVABILITY_SLOS.md](OBSERVABILITY_SLOS.md) - Configuration section
2. Grafana Dashboard - Import `observability/grafana_dashboard.json`
3. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Troubleshooting section
4. Prometheus - Scrape `/metrics` endpoint

## Quick Links

### Common Tasks

**Emit a plan event**:
```python
from cuga.observability import PlanEvent, emit_event
emit_event(PlanEvent.create(trace_id, goal, steps_count, tools_selected, duration_ms))
```
[More examples →](QUICK_REFERENCE.md#event-emission-patterns)

**Get metrics**:
```python
from cuga.observability import get_collector
metrics = get_collector().get_metrics()
print(f"Success rate: {metrics['success_rate']:.2f}%")
```
[Metrics reference →](QUICK_REFERENCE.md#metrics-access)

**Setup OTEL**:
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=cuga-agent
export OTEL_TRACES_EXPORTER=otlp
```
[Configuration guide →](OBSERVABILITY_SLOS.md#configuration)

**Import Grafana dashboard**:
1. Open Grafana → Dashboards → Import
2. Upload `observability/grafana_dashboard.json`
3. Select Prometheus datasource
[Dashboard guide →](OBSERVABILITY_SLOS.md#grafana-dashboard)

## Support

### Troubleshooting
- Events not appearing? → [QUICK_REFERENCE.md#troubleshooting](QUICK_REFERENCE.md#troubleshooting)
- OTEL connection issues? → [OBSERVABILITY_SLOS.md#troubleshooting](OBSERVABILITY_SLOS.md#troubleshooting)
- High memory usage? → [INTEGRATION_CHECKLIST.md#troubleshooting](INTEGRATION_CHECKLIST.md#troubleshooting)

### Testing
- Unit tests: `pytest tests/observability/test_observability.py -v`
- Integration demo: `python examples/observability_example.py`
- Coverage report: See [IMPLEMENTATION_SUMMARY.md#testing](IMPLEMENTATION_SUMMARY.md#testing)

### Questions?
- Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common patterns
- Read [OBSERVABILITY_SLOS.md](OBSERVABILITY_SLOS.md) for complete reference
- Review [INTEGRATION_CHECKLIST.md](INTEGRATION_CHECKLIST.md) for step-by-step guide

---

**Last Updated**: January 1, 2026  
**Status**: ✅ Complete and production-ready  
**Coverage**: 30+ tests, >95% line coverage  
**Lines of Code**: ~3,500 lines across 11 files
