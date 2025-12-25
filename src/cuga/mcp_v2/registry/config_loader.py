"""Hydra/OmegaConf adapter for loading registry configuration fragments."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, MutableSequence

from omegaconf import DictConfig, OmegaConf

from .errors import RegistryLoadError, RegistryMergeError, RegistryValidationError


def _load_config(path: Path) -> DictConfig:
    if not path.exists():
        raise RegistryLoadError(f"Registry file not found: {path}")
    try:
        config = OmegaConf.load(path)
    except Exception as exc:  # pragma: no cover - defensive
        raise RegistryValidationError(f"Invalid registry YAML at {path}: {exc}") from exc
    if config is None:
        config = OmegaConf.create({})
    if not isinstance(config, DictConfig):
        raise RegistryValidationError(f"Registry at {path} must be a mapping")
    return config


def _resolve_fragment_paths(document: DictConfig, base_path: Path) -> list[tuple[Path, bool]]:
    fragments: list[tuple[Path, bool]] = []
    fragments_block = document.get("fragments", [])
    if fragments_block is None:
        fragments_block = []
    if not isinstance(fragments_block, MutableSequence):
        raise RegistryValidationError("fragments must be a list of file paths")
    for fragment in fragments_block:
        if not isinstance(fragment, str):
            raise RegistryValidationError("fragment entries must be strings")
        fragments.append(((base_path.parent / fragment).resolve(), False))

    defaults_block = document.get("defaults", [])
    if defaults_block is None:
        defaults_block = []
    if not isinstance(defaults_block, MutableSequence):
        raise RegistryValidationError("defaults must be a list when provided")
    for entry in defaults_block:
        optional = False
        if isinstance(entry, str):
            target = entry
        elif isinstance(entry, Mapping):
            if "optional" in entry:
                optional = True
                target = entry["optional"]
            elif "path" in entry:
                target = entry["path"]
            else:
                continue
        else:
            raise RegistryValidationError("defaults entries must be strings or mappings")
        if target == "_self_":
            continue
        fragment_target = target if str(target).endswith(".yaml") else f"{target}.yaml"
        fragment_path = (base_path.parent / fragment_target).resolve()
        fragments.append((fragment_path, optional))
    return fragments


def _collect_documents(entry_path: Path, *, seen: set[Path] | None = None) -> list[tuple[Path, DictConfig]]:
    seen = seen or set()
    if entry_path in seen:
        raise RegistryMergeError(f"Cycle detected while loading registry fragments: {entry_path}")
    seen.add(entry_path)
    document = _load_config(entry_path)
    documents: list[tuple[Path, DictConfig]] = [(entry_path, document)]
    for fragment_path, optional in _resolve_fragment_paths(document, entry_path):
        if optional and not fragment_path.exists():
            continue
        documents.extend(_collect_documents(fragment_path, seen=seen))
    return documents


def load_registry_config(entry_path: Path) -> list[tuple[Path, DictConfig]]:
    """Load registry documents using OmegaConf with Hydra-style fragments."""

    return _collect_documents(entry_path.resolve())


__all__ = ["load_registry_config"]
