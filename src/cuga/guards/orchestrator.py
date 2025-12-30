"""Lightweight guardrail scaffolding."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class GuardResult:
    decision: str
    details: Dict[str, Any]


class BaseGuard:
    def evaluate(self, payload: Dict[str, Any]) -> GuardResult:  # pragma: no cover - interface
        raise NotImplementedError


class InputGuard(BaseGuard):
    def evaluate(self, payload: Dict[str, Any]) -> GuardResult:
        return GuardResult(decision="pass", details={"checked": True, "payload": payload})


class ToolGuard(BaseGuard):
    def evaluate(self, payload: Dict[str, Any]) -> GuardResult:
        decision = "pass" if payload.get("readonly", True) else "review"
        return GuardResult(decision=decision, details={"tool": payload.get("tool")})


class OutputGuard(BaseGuard):
    def evaluate(self, payload: Dict[str, Any]) -> GuardResult:
        return GuardResult(decision="pass", details={"length": len(str(payload))})


class GuardrailOrchestrator:
    def __init__(self, input_guard: InputGuard | None = None, tool_guard: ToolGuard | None = None, output_guard: OutputGuard | None = None) -> None:
        self.input_guard = input_guard or InputGuard()
        self.tool_guard = tool_guard or ToolGuard()
        self.output_guard = output_guard or OutputGuard()

    def route(self, stage: str, payload: Dict[str, Any]) -> GuardResult:
        if stage == "input":
            return self.input_guard.evaluate(payload)
        if stage == "tool":
            return self.tool_guard.evaluate(payload)
        return self.output_guard.evaluate(payload)
