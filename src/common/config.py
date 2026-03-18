"""Configuration loader with YAML inheritance support."""

import copy
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base, returning a new dict."""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _resolve_extends_path(config_path: Path, extends: str) -> Path:
    """Resolve an extends path from the child config directory or repo ancestors."""
    extends_path = Path(extends)
    if extends_path.is_absolute():
        return extends_path

    checked: set[Path] = set()
    candidates = [config_path.parent, *config_path.parents]
    for base_dir in candidates:
        candidate = (base_dir / extends_path).resolve()
        if candidate in checked:
            continue
        checked.add(candidate)
        if candidate.is_file():
            return candidate

    return (config_path.parent / extends_path).resolve()


def load_config(path: str) -> dict[str, Any]:
    """Load a YAML config file with optional inheritance via 'extends' key.

    If the config contains an 'extends' key, the parent config is loaded
    first and the child values override the parent (deep merge).

    Args:
        path: Path to the YAML configuration file.

    Returns:
        Merged configuration as a plain dict.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the YAML is malformed.
    """
    config_path = Path(path).resolve()
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    logger.info("Loading config from %s", config_path)

    with open(config_path, "r", encoding="utf-8") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh) or {}

    extends = raw.pop("extends", None)
    if extends is not None:
        parent_path = _resolve_extends_path(config_path, extends)
        logger.info("Config extends %s", parent_path)
        parent_cfg = load_config(str(parent_path))
        return _deep_merge(parent_cfg, raw)

    return raw
