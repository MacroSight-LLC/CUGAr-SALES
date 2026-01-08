"""
OpenAI adapter for LLM capabilities.

Following AGENTS.md capability-first architecture:
- Adapters bind vendors to capabilities
- Optional, hot-swappable
- Uses httpx for HTTP with retries
- Secrets enforcement

This adapter provides:
- Text generation (goal decomposition, plan explanation)
- Structured output (JSON plans)
- Tool selection (semantic ranking)

Capabilities remain callable without this adapter (degrades to MockLLM).
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class OpenAIConfig:
    """OpenAI adapter configuration."""
    
    api_key: Optional[str] = None
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: float = 30.0
    base_url: str = "https://api.openai.com/v1"
    
    def __post_init__(self):
        """Load API key from environment if not provided."""
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key parameter."
            )


class OpenAIAdapter:
    """
    OpenAI adapter for LLM capabilities.
    
    Implements capability contracts for:
    - decompose_goal: Break high-level goal into steps
    - rank_tools: Semantic similarity ranking
    - explain_plan: Natural language plan explanation
    """
    
    def __init__(self, config: Optional[OpenAIConfig] = None):
        """Initialize with optional config."""
        self.config = config or OpenAIConfig()
        self.client = httpx.Client(
            timeout=self.config.timeout,
            follow_redirects=True,
        )
        self._available = True
    
    def is_available(self) -> bool:
        """Check if adapter is available."""
        return self._available and bool(self.config.api_key)
    
    def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Call OpenAI API with SafeClient.
        
        Args:
            messages: Chat messages
            temperature: Override config temperature
            max_tokens: Override config max_tokens
            
        Returns:
            Response dict with 'content' and 'usage'
            
        Raises:
            RuntimeError: If API call fails
        """
        if not self.is_available():
            raise RuntimeError("OpenAI adapter not available")
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }
        
        try:
            response = self.client.post(
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data.get("model", self.config.model),
            }
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}") from e
    
    def decompose_goal(
        self,
        goal: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Decompose high-level goal into executable steps.
        
        Capability: Plan generation from natural language goal.
        
        Args:
            goal: User's high-level objective
            available_tools: Tools that can be used
            context: Optional execution context
            
        Returns:
            List of steps with tool, input, reason
        """
        # Format tools for prompt
        tool_descriptions = "\n".join(
            f"- {t['name']}: {t.get('description', 'No description')} (domain: {t.get('domain', 'unknown')})"
            for t in available_tools
        )
        
        system_prompt = """You are a sales automation planning assistant. 
Decompose the user's goal into executable steps using available tools.

Rules:
1. Each step must use exactly one tool
2. Steps should follow logical order (intelligence → engagement → qualification)
3. Specify clear inputs for each tool
4. Provide reasoning for each step
5. Estimate cost (0.1-2.0 based on complexity)

Output JSON array of steps:
[
  {
    "tool": "tool_name",
    "input": {"key": "value"},
    "reason": "why this step is needed",
    "estimated_cost": 0.5
  }
]
"""
        
        user_prompt = f"""Goal: {goal}

Available tools:
{tool_descriptions}

Context: {json.dumps(context or {}, indent=2)}

Decompose into executable steps (JSON array):"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        response = self._call_api(messages, temperature=0.3)
        
        try:
            # Extract JSON from response
            content = response["content"].strip()
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0].strip()
            
            steps = json.loads(content)
            return steps
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse LLM response as JSON: {e}") from e
    
    def rank_tools(
        self,
        goal: str,
        available_tools: List[Dict[str, Any]],
        top_k: int = 10,
    ) -> List[str]:
        """
        Rank tools by semantic relevance to goal.
        
        Capability: Tool selection by similarity.
        
        Args:
            goal: User's objective
            available_tools: All available tools
            top_k: Number of tools to return
            
        Returns:
            List of tool names ranked by relevance
        """
        tool_list = "\n".join(
            f"{i+1}. {t['name']}: {t.get('description', '')}"
            for i, t in enumerate(available_tools)
        )
        
        system_prompt = """You are a tool ranking assistant.
Rank tools by relevance to the user's goal.
Output ONLY the tool names, one per line, in order of relevance (most relevant first)."""
        
        user_prompt = f"""Goal: {goal}

Available tools:
{tool_list}

Rank top {top_k} tools (one name per line):"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        response = self._call_api(messages, temperature=0.0, max_tokens=500)
        
        # Parse ranked tool names
        ranked = []
        for line in response["content"].strip().split("\n"):
            line = line.strip()
            # Remove numbering if present
            if ". " in line:
                line = line.split(". ", 1)[1]
            if line:
                ranked.append(line)
        
        return ranked[:top_k]
    
    def explain_plan(
        self,
        plan_steps: List[Dict[str, Any]],
        goal: str,
    ) -> str:
        """
        Generate natural language explanation of plan.
        
        Capability: Plan explainability.
        
        Args:
            plan_steps: Steps to explain
            goal: Original goal
            
        Returns:
            Natural language explanation
        """
        steps_text = "\n".join(
            f"{i+1}. {s.get('tool', 'unknown')}: {s.get('reason', 'No reason')}"
            for i, s in enumerate(plan_steps)
        )
        
        system_prompt = """You are a plan explanation assistant.
Explain the plan in 2-3 sentences for a sales rep.
Focus on the value and flow, not technical details."""
        
        user_prompt = f"""Goal: {goal}

Plan steps:
{steps_text}

Explain this plan:"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        response = self._call_api(messages, temperature=0.5, max_tokens=200)
        return response["content"].strip()


def create_openai_adapter(
    model: str = "gpt-4",
    temperature: float = 0.7,
) -> Optional[OpenAIAdapter]:
    """
    Factory function to create OpenAI adapter.
    
    Returns None if API key not available (graceful degradation).
    """
    try:
        config = OpenAIConfig(model=model, temperature=temperature)
        return OpenAIAdapter(config)
    except ValueError:
        # No API key - return None for graceful degradation
        return None
