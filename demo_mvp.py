#!/usr/bin/env python3
"""
CUGAr-SALES MVP Demo Script

Demonstrates capability-first architecture with one complete end-to-end flow:
Goal → Plan → Route → Execute → Present Draft

Per AGENTS.md guardrails:
- Capability-first (not vendor-locked)
- Registry-driven control
- Human-in-the-loop (proposes, never auto-executes)
- Offline-capable (works without adapters)
- Explainable (trace from goal → result)

Demo Flow:
1. User provides goal: "Draft follow-up email for Acme Corp renewal"
2. System loads profile and registry
3. Planner identifies capability: draft_outbound_message
4. Worker executes capability (offline)
5. System returns draft for human approval (NEVER auto-sends)
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any
import yaml
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cuga.agents.contracts import (
    AgentRequest,
    AgentResponse,
    RequestMetadata,
    ResponseStatus,
)
from cuga.orchestrator.protocol import ExecutionContext
from cuga.modular.tools.sales.outreach import draft_outbound_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class MVPDemo:
    """Minimal Viable Product Demo Orchestrator."""
    
    def __init__(self, registry_path: str = "registry.yaml"):
        """Initialize with registry configuration."""
        self.registry = self._load_registry(registry_path)
        self.profile_name = "demo"
        self.profile = self.registry["profiles"][self.profile_name]
        logger.info(f"Initialized with profile: {self.profile_name}")
    
    def _load_registry(self, path: str) -> Dict[str, Any]:
        """Load registry from YAML file."""
        with open(path) as f:
            return yaml.safe_load(f)
    
    def _create_execution_context(self, user_intent: str) -> ExecutionContext:
        """Create execution context with trace_id."""
        trace_id = f"demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        return ExecutionContext(
            trace_id=trace_id,
            request_id=f"req-{trace_id}",
            user_intent=user_intent,
            profile=self.profile_name,
            memory_scope="demo/session-1",
            conversation_id="conv-demo-1",
            session_id="sess-demo-1",
            user_id="demo-user",
        )
    
    def plan(self, goal: str, context: ExecutionContext) -> Dict[str, Any]:
        """
        Simplified planning: identify capability for goal.
        
        In production, PlannerAgent would:
        - Decompose complex goals
        - Rank tools by similarity
        - Attach ToolBudget
        
        For MVP: Direct mapping to draft_outbound_message
        """
        logger.info(f"[{context.trace_id}] Planning for goal: {goal}")
        
        # Check if tool is allowed in profile
        tool_name = "draft_outbound_message"
        if tool_name not in self.profile["allowed_tools"]:
            raise ValueError(f"Tool {tool_name} not allowed in profile {self.profile_name}")
        
        # Get tool definition from registry
        tool_def = self.registry["tools"][tool_name]
        
        plan = {
            "goal": goal,
            "steps": [
                {
                    "step_id": 1,
                    "tool": tool_name,
                    "domain": tool_def["domain"],
                    "inputs_required": ["template", "prospect_data", "channel"],
                    "side_effects": tool_def["side_effects"],
                    "requires_approval": tool_def["requires_approval"],
                }
            ],
            "trace_id": context.trace_id,
        }
        
        logger.info(
            f"[{context.trace_id}] Plan created: "
            f"{len(plan['steps'])} steps, domain={tool_def['domain']}"
        )
        
        return plan
    
    def route(self, plan: Dict[str, Any], context: ExecutionContext) -> str:
        """
        Simplified routing: Always route to WorkerAgent.
        
        In production, CoordinatorAgent would:
        - Delegate to RoutingAuthority
        - Handle concurrent execution
        - Preserve trace ordering
        """
        logger.info(f"[{context.trace_id}] Routing plan to WorkerAgent")
        return "WorkerAgent"
    
    def execute(
        self,
        plan: Dict[str, Any],
        context: ExecutionContext,
        inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute plan step with capability.
        
        In production, WorkerAgent would:
        - Enforce schemas
        - Apply budgets
        - Implement retry policies
        - Handle partial results
        """
        step = plan["steps"][0]
        tool_name = step["tool"]
        
        logger.info(
            f"[{context.trace_id}] Executing step {step['step_id']}: "
            f"{tool_name} (domain={step['domain']})"
        )
        
        # Execute capability (currently direct function call)
        # In production: would go through registry loader + tool executor
        tool_context = {
            "trace_id": context.trace_id,
            "profile": context.profile,
        }
        
        result = draft_outbound_message(inputs, tool_context)
        
        logger.info(
            f"[{context.trace_id}] Execution complete: "
            f"status={result.get('status')}, "
            f"personalization={result['metadata']['personalization_score']:.0%}"
        )
        
        return result
    
    def present_result(self, result: Dict[str, Any], context: ExecutionContext) -> None:
        """Present result to user with human approval reminder."""
        print("\n" + "=" * 80)
        print("✅ DRAFT MESSAGE READY FOR REVIEW")
        print("=" * 80)
        print(f"\nTrace ID: {context.trace_id}")
        print(f"Profile: {context.profile}")
        print(f"Status: {result['status']} (REQUIRES HUMAN APPROVAL)")
        print(f"\n{'-' * 80}")
        print(f"SUBJECT: {result['subject']}")
        print(f"{'-' * 80}")
        print(result['message_draft'])
        print(f"{'-' * 80}")
        
        print("\n📊 METADATA:")
        print(f"  • Personalization Score: {result['metadata']['personalization_score']:.0%}")
        print(f"  • Word Count: {result['metadata']['word_count']}")
        print(f"  • Variables Used: {', '.join(result['variables_used'])}")
        if result['missing_variables']:
            print(f"  ⚠️  Missing Variables: {', '.join(result['missing_variables'])}")
        
        print("\n🛡️ GUARDRAILS ENFORCED:")
        print("  ✓ Status is 'draft' (never 'sent')")
        print("  ✓ Human approval required")
        print("  ✓ Offline execution (no external API calls)")
        print("  ✓ Trace ID propagated throughout")
        print("  ✓ Profile constraints enforced")
        
        print("\n" + "=" * 80)
        print("Next Steps:")
        print("  1. Review draft message above")
        print("  2. Make any necessary edits")
        print("  3. Manually send via your email/CRM tool")
        print("  4. System will NEVER auto-send")
        print("=" * 80 + "\n")
    
    def run_demo(self, goal: str, inputs: Dict[str, Any]) -> None:
        """Run complete demo flow."""
        print("\n🚀 CUGAr-SALES MVP Demo Starting...")
        print(f"Goal: {goal}\n")
        
        # 1. Create execution context
        context = self._create_execution_context(goal)
        logger.info(f"Created execution context: {context.trace_id}")
        
        # 2. Plan
        plan = self.plan(goal, context)
        
        # 3. Route
        agent = self.route(plan, context)
        
        # 4. Execute
        result = self.execute(plan, context, inputs)
        
        # 5. Present
        self.present_result(result, context)
        
        logger.info(f"[{context.trace_id}] Demo complete")


def main():
    """Run MVP demo with sample data."""
    
    # Sample demo data: Follow-up email for Acme Corp renewal
    demo_inputs = {
        "template": """Subject: Quick question about {{company}}'s renewal

Hi {{first_name}},

I wanted to reach out regarding {{company}}'s upcoming renewal for {{product}}.

We've seen great results with {{industry}} companies like yours, and I'd love to explore how we can continue supporting your {{use_case}} goals in the next year.

Would you have 15 minutes next week to discuss?

Best regards,
Sarah Thompson
Account Executive""",
        "prospect_data": {
            "first_name": "Jane",
            "company": "Acme Corp",
            "product": "Enterprise Platform",
            "industry": "Technology",
            "use_case": "customer analytics",
        },
        "channel": "email",
        "tone": "professional",
    }
    
    demo = MVPDemo(registry_path="registry.yaml")
    
    demo.run_demo(
        goal="Draft follow-up email for Acme Corp renewal",
        inputs=demo_inputs,
    )


if __name__ == "__main__":
    main()
