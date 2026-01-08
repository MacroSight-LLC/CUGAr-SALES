# CUGAr-SALES MVP - Quick Reference

## 🚀 Quick Start (30 seconds)

```bash
source .venv/bin/activate
python3 demo_mvp.py
```

## 📊 What You Get

✅ **Working Demo**: Draft email with full traceability  
✅ **AGENTS.md Compliant**: All guardrails enforced  
✅ **Offline-First**: No external APIs required  
✅ **Human-in-the-Loop**: Proposes, never auto-sends  

## 🎯 Demo Modes

### 1. Automated Demo (Quickest)
```bash
python3 demo_mvp.py
```
Uses pre-configured sample data. Shows complete flow.

### 2. Interactive Demo (Best for Presentations)
```bash
python3 demo_interactive.py
```
Prompts for prospect data. More engaging.

### 3. Custom Demo (Advanced)
```python
from demo_mvp import MVPDemo

demo = MVPDemo()
demo.run_demo(
    goal="Your custom goal here",
    inputs={...}
)
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| [`demo_mvp.py`](demo_mvp.py) | Automated demo script |
| [`demo_interactive.py`](demo_interactive.py) | Interactive demo |
| [`registry.yaml`](registry.yaml) | Tool definitions & profiles |
| [`DEMO_README.md`](DEMO_README.md) | Full documentation |
| [`AGENTS.md`](AGENTS.md) | Canonical guardrails |

## 🛡️ Guardrails Demonstrated

| Guardrail | How Demo Shows It |
|-----------|------------------|
| Capability-first | `draft_outbound_message` works offline |
| Registry-driven | All tools defined in `registry.yaml` |
| Human approval | Status always "draft", never "sent" |
| Trace continuity | `trace_id` propagated throughout |
| Profile enforcement | Budget and tool restrictions applied |
| Explainability | Full metadata and reasoning shown |

## 📈 Current Status

**Demo Readiness**: 20% (Internal) / 5% (External)

### ✅ What Works
- Single capability end-to-end (draft_outbound_message)
- Core protocols (AgentProtocol, OrchestratorProtocol)
- Registry with capability contracts
- Trace ID propagation
- Offline execution

### 🚧 What's Missing
- Multi-domain orchestration
- Budget enforcement integration
- Approval flow in demo
- LLM adapter binding
- Test coverage >80%
- Full observability stack

## ⏱️ Production Timeline

- **Week 1**: ✅ MVP demo complete
- **Week 2**: Multi-domain orchestration
- **Week 3**: Hardening (tests, observability)
- **Week 4**: External demo ready

## 🎭 Demo Script (60 seconds)

1. **Setup** (5s)
   ```bash
   python3 demo_mvp.py
   ```

2. **Highlight Trace ID** (10s)
   "Notice the trace_id flows through every operation..."

3. **Show Draft Output** (20s)
   "System generated a personalized draft with 100% variable substitution..."

4. **Emphasize Guardrails** (15s)
   "Status is 'draft' - system NEVER auto-sends. Human approval required."

5. **Explain Architecture** (10s)
   "Capability-first design means we can swap vendors without changing code..."

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | `export PYTHONPATH="${PWD}/src"` |
| `FileNotFoundError: registry.yaml` | Run from project root |
| Python not found | Use `python3` explicitly |

## 📞 Support

- **Documentation**: [`DEMO_README.md`](DEMO_README.md)
- **Architecture**: [`AGENTS.md`](AGENTS.md)
- **Issues**: Check [`DEMO_README.md`](DEMO_README.md) troubleshooting section

## 💡 Demo Tips

### For Internal Stakeholders
- Focus on architecture and guardrails
- Show registry.yaml structure
- Explain capability contracts
- Demo trace_id propagation in logs

### For Technical Audiences
- Show code in `src/cuga/modular/tools/sales/`
- Explain AgentProtocol standardization
- Walk through ExecutionContext immutability
- Discuss adapter pattern

### What NOT to Say
- ❌ "This is production-ready"
- ❌ "It can auto-send emails"
- ❌ "Full orchestration across all domains"
- ❌ "Complete observability stack"

### What TO Say
- ✅ "Proof-of-concept showing architecture"
- ✅ "One capability end-to-end"
- ✅ "Demonstrates guardrails and safety"
- ✅ "Foundation for multi-domain orchestration"

---

**Version**: MVP 0.1.0 (Internal Demo Only)  
**Last Updated**: January 4, 2026
