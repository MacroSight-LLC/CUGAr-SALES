# CUGAr-SALES MVP Demo

**Status**: ✅ Demo-Ready (Internal Use)  
**Updated**: January 4, 2026

## What This Demo Shows

A working end-to-end capability-first sales automation flow that demonstrates:

✅ **Capability-First Architecture** - Not vendor-locked  
✅ **Registry-Driven Control** - All tools defined in `registry.yaml`  
✅ **Human-in-the-Loop** - Proposes actions, never auto-executes  
✅ **Offline-Capable** - Works without adapters or external APIs  
✅ **Explainable** - Complete trace from goal → result  
✅ **AGENTS.md Compliant** - Follows all canonical guardrails

## Quick Start

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Run demo
python3 demo_mvp.py
```

**Expected Output**: Draft email message with full traceability and guardrails.

## Demo Flow

```
User Goal: "Draft follow-up email for Acme Corp renewal"
     ↓
1. Create ExecutionContext (trace_id, profile, user_intent)
     ↓
2. Plan: Identify capability → draft_outbound_message
     ↓
3. Route: Delegate to WorkerAgent
     ↓
4. Execute: Run capability with profile constraints
     ↓
5. Present: Show draft with approval reminder (NEVER auto-sends)
```

## What's Implemented

### ✅ Core Infrastructure

- **AgentProtocol** (`src/cuga/agents/contracts.py`)
  - `AgentRequest` / `AgentResponse` standardization
  - Error types and status enums
  - Trace continuity contracts

- **OrchestratorProtocol** (`src/cuga/orchestrator/protocol.py`)
  - `ExecutionContext` with immutable trace_id
  - Lifecycle stages (initialize → plan → route → execute → complete)
  - Failure modes and partial results

- **AgentLifecycleProtocol** (`src/cuga/agents/lifecycle.py`)
  - State ownership rules (agent/memory/orchestrator)
  - Startup/shutdown guarantees
  - Resource cleanup protocols

### ✅ Sales Capability Domains

Implemented under `src/cuga/modular/tools/sales/`:

1. **Territory & Capacity** (`territory.py`)
   - `simulate_territory_change`
   - `assess_capacity_coverage`

2. **Account Intelligence** (`account_intelligence.py`)
   - `normalize_account_record`
   - `score_account_fit`
   - `retrieve_account_signals`

3. **Outreach & Engagement** (`outreach.py`)
   - ✅ **`draft_outbound_message`** (used in demo)
   - `assess_message_quality`
   - `sequence_touchpoints`

4. **Qualification** (`qualification.py`)
   - `qualify_opportunity`
   - `assess_deal_risk`

5. **Analytics & Governance** (`intelligence.py`)
   - `analyze_win_loss_patterns`
   - `extract_buyer_personas`

### ✅ Registry Configuration

[`registry.yaml`](registry.yaml) now includes:

- **Tool Definitions** with capability contracts
  - Purpose, inputs, outputs, guardrails
  - Side-effect classification (read-only, propose, execute)
  - Cost and latency estimates
  - Offline capability flags

- **Execution Profiles** (demo, sales_rep, sales_manager)
  - Allowed tools per profile
  - Budget limits (total calls, per-domain, per-tool)
  - Timeout constraints

- **Adapter Bindings** (optional, disabled by default)
  - Salesforce, Clearbit (can be enabled via env vars)
  - Tools work without adapters

### ✅ Observability Primitives

- Trace ID propagation (`trace_id` in all logs)
- Canonical events (plan_created, tool_call_start, etc.)
- Budget tracking and warnings
- Structured error propagation

## Demo Scenarios

### Scenario 1: Draft Outreach Message (Current)

```python
demo_inputs = {
    "template": "Hi {{first_name}}, regarding {{company}}'s renewal...",
    "prospect_data": {
        "first_name": "Jane",
        "company": "Acme Corp",
        "product": "Enterprise Platform",
    },
    "channel": "email",
}

demo.run_demo(
    goal="Draft follow-up email for Acme Corp renewal",
    inputs=demo_inputs,
)
```

**Output**: Draft email with 100% personalization, ready for human review.

### Scenario 2: Multi-Step Flow (Future)

```python
# Plan with multiple capabilities
# 1. score_account_fit → prioritize prospects
# 2. draft_outbound_message → personalized draft
# 3. assess_message_quality → quality check
```

### Scenario 3: Adapter Integration (Future)

```bash
# Enable Salesforce adapter
export ENABLE_SALESFORCE_ADAPTER=true

# System now enriches with live CRM data
# Still requires human approval before sending
```

## What's NOT Ready

### ⚠️ Limitations (Do NOT Demo Externally Yet)

1. **Single Capability Demo** - Only shows `draft_outbound_message`
   - Full orchestration across multiple domains not wired up
   - Budget enforcement not fully integrated
   - Approval manager exists but not in demo flow

2. **Simplified Planning** - Direct tool mapping
   - Production PlannerAgent would decompose complex goals
   - Tool similarity ranking not implemented
   - No multi-step plan validation

3. **No Full Observability Stack**
   - Events logged but not aggregated
   - Golden Signals defined but not collected
   - No visualization dashboard

4. **Test Coverage Incomplete** - ~60% coverage
   - Need >80% for production readiness
   - Integration tests for multi-agent flows missing
   - Concurrency tests not implemented

5. **No LLM Integration**
   - Currently using direct function calls
   - LLM adapter binding not demonstrated
   - Natural language → capability mapping not shown

## Production Readiness Timeline

### Week 1 (Current)
- ✅ Core protocols implemented
- ✅ One capability end-to-end
- ✅ Registry with contracts
- ✅ Demo script working

### Week 2 (Next Steps)
- 🔲 Multi-domain orchestration
- 🔲 Budget enforcement integration
- 🔲 Approval flow integration
- 🔲 LLM adapter binding

### Week 3 (Hardening)
- 🔲 Test coverage >80%
- 🔲 Observability aggregation
- 🔲 Error recovery flows
- 🔲 Performance benchmarks

### Week 4 (Production)
- 🔲 Security audit
- 🔲 Documentation complete
- 🔲 Deployment automation
- 🔲 External demo ready

## Running the Demo

### Prerequisites

```bash
# Python 3.11+
python3 --version

# Virtual environment with dependencies
source .venv/bin/activate

# Verify imports
python3 -c "from cuga.modular.tools.sales.outreach import draft_outbound_message"
```

### Run Demo

```bash
# Basic demo
python3 demo_mvp.py

# With verbose logging
python3 demo_mvp.py --log-level DEBUG

# Custom inputs (future)
python3 demo_mvp.py --inputs custom_data.json
```

### Expected Output

```
🚀 CUGAr-SALES MVP Demo Starting...
Goal: Draft follow-up email for Acme Corp renewal

[Logs showing trace_id propagation]

================================================================================
✅ DRAFT MESSAGE READY FOR REVIEW
================================================================================

Trace ID: demo-20260104-190229
Profile: demo
Status: draft (REQUIRES HUMAN APPROVAL)

[Draft message content]

📊 METADATA:
  • Personalization Score: 100%
  • Word Count: 57
  • Variables Used: industry, product, first_name, use_case, company

🛡️ GUARDRAILS ENFORCED:
  ✓ Status is 'draft' (never 'sent')
  ✓ Human approval required
  ✓ Offline execution (no external API calls)
  ✓ Trace ID propagated throughout
  ✓ Profile constraints enforced

Next Steps:
  1. Review draft message above
  2. Make any necessary edits
  3. Manually send via your email/CRM tool
  4. System will NEVER auto-send
================================================================================
```

## Key Design Principles Demonstrated

### 1. Capability-First (Not Vendor-First)

```yaml
# registry.yaml
tools:
  draft_outbound_message:
    domain: "engagement"
    purpose: "Scale message personalization"
    offline_capable: true
    
# Vendors are optional adapters
adapters:
  salesforce:
    enabled: false  # System works without it
```

### 2. Human Authority Preserved

```python
# Tool ALWAYS returns status="draft"
result = draft_outbound_message(inputs, context)
assert result["status"] == "draft"  # NEVER "sent"

# Human reviews and approves before sending
```

### 3. Trace Continuity

```python
context = ExecutionContext(
    trace_id="demo-20260104-190229",  # Immutable
    user_intent="Draft follow-up email",
)

# trace_id flows through all operations
plan = planner.plan(goal, context)  # Same trace_id
result = worker.execute(plan, context)  # Same trace_id
```

### 4. Explainable Results

Every result includes:
- What was done (capability name, domain)
- Why (user intent, plan reasoning)
- How (inputs, variables used, personalization score)
- Guardrails enforced (status=draft, approval required)

## Troubleshooting

### Import Errors

```bash
# Ensure src/ is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/home/taylor/CUGAr-SALES/src"

# Or use relative imports
cd /home/taylor/CUGAr-SALES
python3 demo_mvp.py
```

### Registry Not Found

```bash
# Verify registry.yaml exists in project root
ls -l registry.yaml

# Run from project root
cd /home/taylor/CUGAr-SALES
python3 demo_mvp.py
```

### Missing Dependencies

```bash
# Install required packages
pip install pyyaml

# Or use full environment
source .venv/bin/activate
```

## Next Steps

### For Internal Testing

1. Run the demo multiple times
2. Try different templates and prospect data
3. Verify trace_id consistency in logs
4. Check that status is always "draft"

### To Extend the Demo

1. **Add Second Capability**
   - Wire up `assess_message_quality`
   - Show draft → quality check → present

2. **Integrate Budget Enforcement**
   - Use `BudgetEnforcer` from orchestrator
   - Show warnings at 80% usage

3. **Add Approval Flow**
   - Use `ApprovalManager`
   - Simulate approval request/response

4. **Multi-Domain Orchestration**
   - Combine territory, intelligence, engagement
   - Show cross-domain coordination

### To Prepare for External Demo

1. **Test Coverage >80%**
   ```bash
   pytest --cov=src/cuga --cov-report=html
   open htmlcov/index.html
   ```

2. **Performance Benchmarks**
   ```bash
   python3 scripts/benchmark_demo.py
   # Target: <200ms for single capability
   ```

3. **Security Audit**
   ```bash
   python3 scripts/verify_guardrails.py
   # Ensure no auto-send paths exist
   ```

4. **Documentation Polish**
   - Architecture diagrams
   - Video walkthrough
   - FAQ section

## Questions?

See:
- [`AGENTS.md`](AGENTS.md) - Canonical guardrails
- [`registry.yaml`](registry.yaml) - Tool definitions
- [`src/cuga/modular/tools/sales/`](src/cuga/modular/tools/sales/) - Capability implementations
- [`src/cuga/orchestrator/protocol.py`](src/cuga/orchestrator/protocol.py) - Orchestration contracts

---

**Remember**: This is an MVP demo showing one capability end-to-end. It demonstrates the architecture and guardrails, but is not production-ready for external customers yet.
