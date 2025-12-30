"""Watsonx provider with deterministic defaults and simple audit logging.

This module intentionally avoids network calls in tests by allowing injection of a mock
client. It prefers deterministic generation using greedy decoding and bounded tokens.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

try:
    from pydantic import BaseModel, ValidationError
except Exception:  # pragma: no cover - soft dependency fallback
    class BaseModel:  # type: ignore
        @classmethod
        def model_validate(cls, value: Any) -> Any:
            return value

    class ValidationError(Exception):
        ...

try:  # optional dependency for environments without the SDK
    from ibm_watsonx_ai.foundation_models import Model
except Exception:  # pragma: no cover - defensive import guard
    Model = None  # type: ignore

DEFAULT_MODEL = os.getenv("MODEL_NAME", "ibm/granite-3-3-8b-instruct")
DEFAULT_CONFIG_PATH = Path(os.getenv("AGENT_SETTING_CONFIG", "settings.watsonx.toml"))


@dataclass
class WatsonxProvider:
    """Minimal Watsonx provider focused on deterministic responses.

    The provider is intentionally lightweight to keep compatibility with existing
    CUGA entrypoints while making it easy to swap in real SDK calls in production.
    """

    model_id: str = DEFAULT_MODEL
    decoding_method: str = "greedy"
    temperature: float = 0.0
    max_new_tokens: int = 256
    repetition_penalty: float = 1.0
    project_id: Optional[str] = field(default_factory=lambda: os.getenv("WATSONX_PROJECT_ID"))
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("WATSONX_API_KEY"))
    url: Optional[str] = field(default_factory=lambda: os.getenv("WATSONX_URL"))
    audit_path: Path = field(default_factory=lambda: Path("logs/audit/model_calls.jsonl"))
    client: Any | None = None

    def __post_init__(self) -> None:
        self.max_new_tokens = min(max(self.max_new_tokens, 16), 2048)
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "decoding_method": self.decoding_method,
            "temperature": self.temperature,
            "max_new_tokens": self.max_new_tokens,
            "repetition_penalty": self.repetition_penalty,
        }

    def _build_client(self) -> Any:
        if self.client is not None:
            return self.client
        if Model is None:
            raise RuntimeError("ibm-watsonx-ai is not installed")
        return Model(
            model_id=self.model_id,
            params=self.parameters,
            credentials={"apikey": self.api_key},
            project_id=self.project_id,
            url=self.url,
        )

    def generate(self, prompt: str, *, seed: int | None = None) -> Dict[str, Any]:
        payload = {
            "prompt": prompt,
            "model_id": self.model_id,
            "parameters": self.parameters,
            "seed": seed,
        }
        response: Dict[str, Any]
        if self.client is None and Model is None:
            response = {"output_text": prompt, "usage": {"input_tokens": len(prompt)}}
        else:
            client = self._build_client()
            response = client.generate_text(prompt=prompt, seed=seed)
        self._write_audit(payload, response)
        return response

    def function_call(self, functions: Iterable[type[BaseModel]], prompt: str) -> Dict[str, Any]:
        errors: list[str] = []
        for fn_model in functions:
            try:
                fn_model.model_validate({})
            except ValidationError as exc:  # pragma: no cover - defensive
                errors.append(str(exc))
        response = self.generate(prompt)
        return {"response": response, "validation": errors}

    def to_langchain(self) -> Any:
        """Return a lightweight adapter that mimics a LangChain LLM."""

        provider = self

        class _LCWrapper:
            def __call__(self, prompt: str, **_: Any) -> str:
                return provider.generate(prompt).get("output_text", "")

        return _LCWrapper()

    def _write_audit(self, payload: Dict[str, Any], response: Dict[str, Any]) -> None:
        record = {
            "model_id": payload["model_id"],
            "parameters": payload["parameters"],
            "seed": payload.get("seed"),
            "prompt_preview": payload["prompt"][:200],
            "usage": response.get("usage", {}),
        }
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")


__all__ = ["WatsonxProvider", "DEFAULT_MODEL", "DEFAULT_CONFIG_PATH"]
