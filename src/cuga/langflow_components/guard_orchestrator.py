"""Langflow guard component placeholder."""
from __future__ import annotations

from typing import Any, Dict

try:
    from langflow.custom import custom_component
    from langflow.custom.custom_component.component import Component
except Exception:  # pragma: no cover
    Component = object  # type: ignore
    custom_component = lambda *args, **kwargs: (lambda cls: cls)


@custom_component(component_type="guard", description="Guardrail component")
class GuardComponent(Component):
    display_name = "CUGA Guard"
    description = "Applies lightweight guardrail logic"

    def build_config(self) -> Dict[str, Any]:  # pragma: no cover - UI metadata
        return {"payload": {"type": "dict", "required": True}, "policy": {"type": "str", "required": False}}

    def __call__(self, payload: Dict[str, Any], policy: str | None = None) -> Dict[str, Any]:
        decision = "pass"
        if policy:
            decision = "review"
        return {"decision": decision, "payload": payload}
