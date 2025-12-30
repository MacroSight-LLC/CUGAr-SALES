"""Watsonx provider with deterministic defaults and structured auditing."""
from __future__ import annotations

import importlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Type

_pydantic_spec = importlib.util.find_spec("pydantic")
if _pydantic_spec:
    pydantic = importlib.import_module("pydantic")
    BaseModel = pydantic.BaseModel
    ValidationError = pydantic.ValidationError
else:  # pragma: no cover - soft dependency fallback
    class BaseModel:  # type: ignore
        @classmethod
        def model_validate(cls, value: Any) -> Any:
            return value

        @classmethod
        def model_json_schema(cls) -> Dict[str, Any]:
            return {"properties": {}, "required": []}

    class ValidationError(Exception):
        ...

_watsonx_spec = importlib.util.find_spec("ibm_watsonx_ai")
if _watsonx_spec:
    _foundation_spec = importlib.util.find_spec("ibm_watsonx_ai.foundation_models")
    if _foundation_spec:
        Model = importlib.import_module("ibm_watsonx_ai.foundation_models").Model  # type: ignore
    else:  # pragma: no cover
        Model = None  # type: ignore
else:  # pragma: no cover - defensive import guard
    Model = None  # type: ignore

DEFAULT_MODEL = os.getenv("MODEL_NAME", "ibm/granite-3-3-8b-instruct")
DEFAULT_CONFIG_PATH = Path(os.getenv("AGENT_SETTING_CONFIG", "settings.watsonx.toml"))


@dataclass
class WatsonxProvider:
    """Minimal Watsonx provider focused on deterministic responses."""

    model_id: str = DEFAULT_MODEL
    decoding_method: str = "greedy"
    temperature: float = 0.0
    max_new_tokens: int = 256
    repetition_penalty: float = 1.0
    project_id: Optional[str] = field(default_factory=lambda: os.getenv("WATSONX_PROJECT_ID"))
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("WATSONX_API_KEY"))
    url: Optional[str] = field(default_factory=lambda: os.getenv("WATSONX_URL"))
    audit_path: Path | str = field(default_factory=lambda: Path("logs/audit/model_calls.jsonl"))
    actor_id: str = "system"
    client: Any | None = None

    def __post_init__(self) -> None:
        self.max_new_tokens = min(max(self.max_new_tokens, 16), 2048)
        self.audit_path = Path(self.audit_path)
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
        if not self.api_key or not self.project_id or not self.url:
            raise RuntimeError(
                "Missing Watsonx credentials: set WATSONX_API_KEY, WATSONX_PROJECT_ID, and WATSONX_URL"
            )
        return Model(
            model_id=self.model_id,
            params=self.parameters,
            credentials={"apikey": self.api_key},
            project_id=self.project_id,
            url=self.url,
        )

    def generate(self, prompt: str, *, seed: int | None = None) -> Dict[str, Any]:
        if not self.api_key or not self.project_id or not self.url:
            raise RuntimeError(
                "Missing Watsonx credentials: set WATSONX_API_KEY, WATSONX_PROJECT_ID, and WATSONX_URL"
            )

        payload = {
            "prompt": prompt,
            "model_id": self.model_id,
            "parameters": self.parameters,
            "seed": seed,
        }

        if self.client is None and Model is None:
            token_usage = {"input_tokens": len(prompt)}
            response: Dict[str, Any] = {"output_text": prompt, "usage": token_usage, "token_usage": token_usage}
        else:
            client = self._build_client()
            response = client.generate_text(prompt=prompt, seed=seed)
            if "token_usage" not in response and "usage" in response:
                response["token_usage"] = response.get("usage")

        payload["token_usage"] = response.get("token_usage")
        return self._write_audit_and_return(payload, response)

    def function_call(self, functions: Iterable[Type[BaseModel]], prompt: str) -> Dict[str, Any]:
        errors: list[str] = []
        for fn_model in functions:
            try:
                schema = fn_model.model_json_schema()
                props = schema.get("properties", {})
                required = schema.get("required", [])
                if not isinstance(props, dict) or not props:
                    errors.append(f"Model {fn_model.__name__} has no properties.")
                if any(req not in props for req in required):
                    errors.append(f"Model {fn_model.__name__} has invalid required fields: {required}")
            except ValidationError as exc:  # pragma: no cover
                errors.append(f"Invalid Pydantic model {fn_model.__name__}: {exc}")
            except Exception as exc:  # pragma: no cover
                errors.append(f"Invalid Pydantic model {fn_model.__name__}: {exc}")
        response = self.generate(prompt)
        return {"response": response, "validation": errors}

    def to_langchain(self) -> Any:
        """Return a lightweight adapter that mimics a LangChain LLM."""

        provider = self

        class _LCWrapper:
            def __call__(self, prompt: str, **_: Any) -> str:
                return provider.generate(prompt).get("output_text", "")

        return _LCWrapper()

    def _write_audit_and_return(self, payload: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "actor": self.actor_id or "system",
            "model_id": self.model_id,
            "parameters": self.parameters,
            "request": {"prompt": payload.get("prompt"), "seed": payload.get("seed")},
            "response_meta": {"token_usage": payload.get("token_usage")},
            "outcome": {"status": "success"},
        }
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

        combined = dict(response)
        combined["audit"] = record
        return combined


__all__ = ["WatsonxProvider", "DEFAULT_MODEL", "DEFAULT_CONFIG_PATH"]
