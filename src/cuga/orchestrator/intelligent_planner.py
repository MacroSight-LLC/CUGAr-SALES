"""
Intelligent planner with LLM-driven goal decomposition.

Following AGENTS.md principles:
- Capability-first: Works without adapters (falls back to rule-based)
- Registry-driven: Tools from registry.yaml
- Budget-aware: Estimates costs
- Explainable: Natural language reasoning

Usage:
    planner = IntelligentPlanner(registry, profile)
    plan = await planner.create_plan(goal, context, prospect_data)
"""

import logging
from typing import Any, Dict, List, Optional

from cuga.adapters.openai_adapter import OpenAIAdapter, create_openai_adapter
from cuga.orchestrator.protocol import ExecutionContext
from cuga.orchestrator.planning import Plan, PlanStep, PlanningStage, ToolBudget

logger = logging.getLogger(__name__)


class IntelligentPlanner:
    """
    LLM-driven planner with fallback to rule-based decomposition.
    
    Capabilities:
    - Goal decomposition using LLM
    - Semantic tool ranking
    - Cross-domain orchestration
    - Explainable plans
    
    Graceful degradation:
    - If LLM unavailable → rule-based planning
    - If tool ranking fails → registry order
    - Always deterministic offline mode available
    """
    
    def __init__(
        self,
        registry: Dict[str, Any],
        profile: str,
        llm_adapter: Optional[OpenAIAdapter] = None,
    ):
        """
        Initialize intelligent planner.
        
        Args:
            registry: Tool registry from registry.yaml
            profile: Execution profile name
            llm_adapter: Optional OpenAI adapter (will try to create if None)
        """
        self.registry = registry
        self.profile = profile
        self.llm_adapter = llm_adapter or create_openai_adapter()
        
        if self.llm_adapter:
            logger.info("IntelligentPlanner initialized with LLM adapter")
        else:
            logger.info("IntelligentPlanner initialized in offline mode (no LLM)")
    
    def is_llm_available(self) -> bool:
        """Check if LLM adapter is available."""
        return self.llm_adapter is not None and self.llm_adapter.is_available()
    
    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Get tools from registry allowed by profile."""
        profile_config = self.registry["profiles"].get(self.profile, {})
        allowed_tools = profile_config.get("allowed_tools", [])
        
        tools = []
        for tool_name, tool_config in self.registry.get("tools", {}).items():
            if not allowed_tools or tool_name in allowed_tools:
                tools.append({
                    "name": tool_name,
                    "description": tool_config.get("description", ""),
                    "domain": tool_config.get("domain", "unknown"),
                    "purpose": tool_config.get("purpose", ""),
                    "side_effects": tool_config.get("side_effects", "read-only"),
                    "inputs": tool_config.get("inputs", {}),
                })
        
        return tools
    
    async def create_plan(
        self,
        goal: str,
        context: ExecutionContext,
        prospect_data: Optional[Dict[str, Any]] = None,
        use_llm: bool = True,
    ) -> Plan:
        """
        Create execution plan from goal.
        
        Args:
            goal: High-level user objective
            context: Execution context with trace_id
            prospect_data: Optional prospect context
            use_llm: Whether to use LLM (False for deterministic testing)
            
        Returns:
            Plan with ordered steps
        """
        logger.info(f"[{context.trace_id}] Creating plan for: {goal}")
        
        available_tools = self._get_available_tools()
        
        if use_llm and self.is_llm_available():
            try:
                return await self._create_llm_plan(
                    goal, context, available_tools, prospect_data
                )
            except Exception as e:
                logger.warning(
                    f"[{context.trace_id}] LLM planning failed: {e}. "
                    "Falling back to rule-based."
                )
                # Fall through to rule-based
        
        # Fallback: rule-based planning
        return self._create_rule_based_plan(goal, context, prospect_data)
    
    async def _create_llm_plan(
        self,
        goal: str,
        context: ExecutionContext,
        available_tools: List[Dict[str, Any]],
        prospect_data: Optional[Dict[str, Any]],
    ) -> Plan:
        """Create plan using LLM decomposition."""
        logger.info(f"[{context.trace_id}] Using LLM for plan generation")
        
        # Decompose goal into steps
        llm_steps = self.llm_adapter.decompose_goal(
            goal=goal,
            available_tools=available_tools,
            context={"prospect": prospect_data, "profile": self.profile},
        )
        
        logger.info(
            f"[{context.trace_id}] LLM generated {len(llm_steps)} steps"
        )
        
        # Convert LLM steps to PlanStep objects
        plan_steps = []
        for i, llm_step in enumerate(llm_steps, 1):
            # Get tool config for metadata
            tool_name = llm_step["tool"]
            tool_config = self.registry["tools"].get(tool_name, {})
            
            plan_steps.append(
                PlanStep(
                    index=i,
                    tool=tool_name,
                    name=tool_config.get("description", tool_name),
                    input=llm_step.get("input", {}),
                    reason=llm_step.get("reason", "LLM-generated step"),
                    estimated_cost=llm_step.get("estimated_cost", 0.5),
                    metadata={
                        "domain": tool_config.get("domain", "unknown"),
                        "side_effect_class": tool_config.get("side_effects", "read-only"),
                        "llm_generated": True,
                    },
                )
            )
        
        # Get plan explanation
        try:
            explanation = self.llm_adapter.explain_plan(llm_steps, goal)
            logger.info(f"[{context.trace_id}] Plan explanation: {explanation}")
        except Exception as e:
            logger.warning(f"[{context.trace_id}] Plan explanation failed: {e}")
            explanation = None
        
        import uuid
        plan = Plan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            goal=goal,
            steps=plan_steps,
            stage=PlanningStage.CREATED,
            budget=ToolBudget(call_ceiling=50),
            trace_id=context.trace_id,
            profile=context.profile,
            metadata={"llm_generated": True, "explanation": explanation},
        )
        
        logger.info(
            f"[{context.trace_id}] LLM plan created: {len(plan_steps)} steps "
            f"across {len(set(s.metadata['domain'] for s in plan_steps))} domains"
        )
        
        return plan
    
    def _create_rule_based_plan(
        self,
        goal: str,
        context: ExecutionContext,
        prospect_data: Optional[Dict[str, Any]],
    ) -> Plan:
        """
        Fallback rule-based planning (deterministic, offline).
        
        Hard-coded scenario: "Prioritize and engage prospect"
        Steps:
          1. Intelligence: Score account fit
          2. Engagement: Draft outreach message
          3. Engagement: Assess message quality
          4. Qualification: Qualify opportunity
        """
        logger.info(f"[{context.trace_id}] Using rule-based planning (offline)")
        
        prospect_data = prospect_data or {}
        
        steps = [
            PlanStep(
                index=1,
                tool="score_account_fit",
                name="Score Account Fit",
                input={
                    "account": {
                        "company": prospect_data.get("company"),
                        "industry": prospect_data.get("industry"),
                        "employee_count": prospect_data.get("employee_count", 500),
                        "revenue": prospect_data.get("revenue", 10000000),
                    },
                    "icp_criteria": {
                        "target_industries": ["Technology", "SaaS", "Financial Services"],
                        "min_employee_count": 100,
                        "min_revenue": 1000000,
                    },
                },
                reason="Score account against ICP to prioritize outreach",
                estimated_cost=0.5,
                metadata={
                    "domain": "intelligence",
                    "side_effect_class": "read-only",
                },
            ),
            PlanStep(
                index=2,
                tool="draft_outbound_message",
                name="Draft Outreach Message",
                input={
                    "template": prospect_data.get("template"),
                    "prospect_data": prospect_data.get("prospect_data"),
                    "channel": "email",
                    "tone": "professional",
                },
                reason="Draft personalized outreach message",
                estimated_cost=1.0,
                metadata={
                    "domain": "engagement",
                    "side_effect_class": "propose",
                },
            ),
            PlanStep(
                index=3,
                tool="assess_message_quality",
                name="Assess Message Quality",
                input={
                    "message": "",
                    "subject": "",
                    "channel": "email",
                },
                reason="Validate message quality before proposing to human",
                estimated_cost=0.5,
                metadata={
                    "domain": "engagement",
                    "side_effect_class": "read-only",
                    "depends_on": 2,
                },
            ),
            PlanStep(
                index=4,
                tool="qualify_opportunity",
                name="Qualify Opportunity",
                input={
                    "opportunity_id": f"opp-{prospect_data.get('company', 'unknown').lower().replace(' ', '-')}",
                    "criteria": {
                        "budget": True,
                        "authority": False,
                        "need": True,
                        "timing": True,
                    },
                    "notes": f"Initial qualification for {prospect_data.get('company')}",
                },
                reason="Assess opportunity quality for prioritization",
                estimated_cost=0.7,
                metadata={
                    "domain": "qualification",
                    "side_effect_class": "read-only",
                },
            ),
        ]
        
        import uuid
        plan = Plan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            goal=goal,
            steps=steps,
            stage=PlanningStage.CREATED,
            budget=ToolBudget(call_ceiling=50),
            trace_id=context.trace_id,
            profile=context.profile,
            metadata={"llm_generated": False, "rule_based": True},
        )
        
        logger.info(
            f"[{context.trace_id}] Rule-based plan created: {len(steps)} steps "
            f"across {len(set(s.metadata['domain'] for s in steps))} domains"
        )
        
        return plan
