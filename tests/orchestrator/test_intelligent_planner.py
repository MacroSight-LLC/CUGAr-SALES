"""
Test LLM integration for intelligent planning.

Tests both offline fallback and LLM-driven planning (with mocked API).
"""

import asyncio
import json
from unittest.mock import MagicMock, patch

import pytest

from cuga.adapters.openai_adapter import OpenAIAdapter, OpenAIConfig
from cuga.orchestrator.intelligent_planner import IntelligentPlanner
from cuga.orchestrator.protocol import ExecutionContext


def test_openai_adapter_unavailable_without_key():
    """Test graceful degradation when no API key."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="OpenAI API key required"):
            OpenAIConfig()


def test_openai_adapter_with_key():
    """Test adapter initialization with API key."""
    config = OpenAIConfig(api_key="test-key-123")
    adapter = OpenAIAdapter(config)
    
    assert adapter.is_available()
    assert adapter.config.api_key == "test-key-123"
    assert adapter.config.model == "gpt-4"


@patch("httpx.Client")
def test_openai_decompose_goal(mock_client):
    """Test goal decomposition with mocked OpenAI API."""
    # Mock API response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": json.dumps([
                    {
                        "tool": "score_account_fit",
                        "input": {"account": {"company": "Test Co"}},
                        "reason": "Score account against ICP",
                        "estimated_cost": 0.5,
                    },
                    {
                        "tool": "draft_outbound_message",
                        "input": {"template": "Hi {{name}}"},
                        "reason": "Draft personalized message",
                        "estimated_cost": 1.0,
                    },
                ])
            }
        }],
        "usage": {"total_tokens": 100},
    }
    mock_client.return_value.post.return_value = mock_response
    
    config = OpenAIConfig(api_key="test-key")
    adapter = OpenAIAdapter(config)
    
    tools = [
        {"name": "score_account_fit", "description": "Score account fit", "domain": "intelligence"},
        {"name": "draft_outbound_message", "description": "Draft message", "domain": "engagement"},
    ]
    
    steps = adapter.decompose_goal(
        goal="Prioritize and engage prospect",
        available_tools=tools,
    )
    
    assert len(steps) == 2
    assert steps[0]["tool"] == "score_account_fit"
    assert steps[0]["estimated_cost"] == 0.5
    assert steps[1]["tool"] == "draft_outbound_message"


@pytest.mark.asyncio
async def test_intelligent_planner_offline_fallback():
    """Test IntelligentPlanner falls back to rule-based without LLM."""
    registry = {
        "tools": {
            "score_account_fit": {
                "domain": "intelligence",
                "description": "Score account",
                "side_effects": "read-only",
            },
        },
        "profiles": {
            "demo": {"allowed_tools": ["score_account_fit"]},
        },
    }
    
    # Create planner without LLM adapter
    planner = IntelligentPlanner(registry, profile="demo", llm_adapter=None)
    
    assert not planner.is_llm_available()
    
    context = ExecutionContext(
        trace_id="test-trace",
        request_id="test-req",
        user_intent="Test goal",
        profile="demo",
        memory_scope="test",
        conversation_id="test-conv",
        session_id="test-sess",
        user_id="test-user",
    )
    
    # Should use rule-based planning
    plan = await planner.create_plan(
        goal="Prioritize prospect",
        context=context,
        use_llm=True,  # Requested but unavailable
    )
    
    assert plan.plan_id.startswith("plan-")
    assert len(plan.steps) == 4  # Rule-based creates 4 steps
    assert plan.metadata.get("rule_based") is True
    assert plan.metadata.get("llm_generated") is False


@pytest.mark.asyncio
@patch("cuga.adapters.openai_adapter.OpenAIAdapter.decompose_goal")
async def test_intelligent_planner_with_llm(mock_decompose):
    """Test IntelligentPlanner uses LLM when available."""
    registry = {
        "tools": {
            "score_account_fit": {
                "domain": "intelligence",
                "description": "Score account",
                "side_effects": "read-only",
            },
        },
        "profiles": {
            "demo": {"allowed_tools": ["score_account_fit"]},
        },
    }
    
    # Mock LLM response
    mock_decompose.return_value = [
        {
            "tool": "score_account_fit",
            "input": {"account": {"company": "Test"}},
            "reason": "LLM-generated reason",
            "estimated_cost": 0.8,
        }
    ]
    
    # Create adapter with mocked LLM
    config = OpenAIConfig(api_key="test-key")
    adapter = OpenAIAdapter(config)
    
    planner = IntelligentPlanner(registry, profile="demo", llm_adapter=adapter)
    
    assert planner.is_llm_available()
    
    context = ExecutionContext(
        trace_id="test-trace",
        request_id="test-req",
        user_intent="Test goal",
        profile="demo",
        memory_scope="test",
        conversation_id="test-conv",
        session_id="test-sess",
        user_id="test-user",
    )
    
    plan = await planner.create_plan(
        goal="Prioritize prospect",
        context=context,
        use_llm=True,
    )
    
    assert len(plan.steps) == 1  # LLM returned 1 step
    assert plan.steps[0].reason == "LLM-generated reason"
    assert plan.steps[0].estimated_cost == 0.8
    assert plan.metadata.get("llm_generated") is True
    
    # Verify LLM was called
    mock_decompose.assert_called_once()


def test_intelligent_planner_deterministic_mode():
    """Test planner can be forced into deterministic mode."""
    registry = {
        "tools": {},
        "profiles": {"demo": {}},
    }
    
    config = OpenAIConfig(api_key="test-key")
    adapter = OpenAIAdapter(config)
    planner = IntelligentPlanner(registry, profile="demo", llm_adapter=adapter)
    
    context = ExecutionContext(
        trace_id="test-trace",
        request_id="test-req",
        user_intent="Test",
        profile="demo",
        memory_scope="test",
        conversation_id="test-conv",
        session_id="test-sess",
        user_id="test-user",
    )
    
    # Force deterministic mode
    async def run():
        return await planner.create_plan(
            goal="Test goal",
            context=context,
            use_llm=False,  # Explicitly disable LLM
        )
    
    plan = asyncio.run(run())
    
    # Should use rule-based even though LLM available
    assert plan.metadata.get("rule_based") is True
