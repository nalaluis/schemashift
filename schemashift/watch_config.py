"""Load and validate a watch configuration file (YAML or JSON)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml  # type: ignore
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


class WatchConfigError(Exception):
    """Raised when a watch config file is missing or malformed."""


_REQUIRED_KEYS = {"baseline", "schema"}


def load_watch_config(path: str | Path) -> Dict[str, Any]:
    """Load a watch configuration from *path* (JSON or YAML).

    The config must contain at least:

    - ``baseline`` – path to the baseline JSON file.
    - ``schema``   – path to the current schema JSON file.

    Optional keys:

    - ``output_format`` – one of ``text``, ``json``, ``markdown`` (default: ``text``).
    - ``fail_on_breaking`` – boolean, default ``true``.

    Returns
    -------
    dict
        Validated configuration mapping.
    """
    p = Path(path)
    if not p.exists():
        raise WatchConfigError(f"Config file not found: {p}")

    suffix = p.suffix.lower()
    raw: Any

    if suffix in (".yaml", ".yml"):
        if not _YAML_AVAILABLE:
            raise WatchConfigError(
                "PyYAML is required to load YAML config files. "
                "Install it with: pip install pyyaml"
            )
        raw = yaml.safe_load(p.read_text())
    elif suffix == ".json":
        try:
            raw = json.loads(p.read_text())
        except json.JSONDecodeError as exc:
            raise WatchConfigError(f"Invalid JSON in config: {exc}") from exc
    else:
        raise WatchConfigError(f"Unsupported config format: '{suffix}'. Use .json or .yaml")

    if not isinstance(raw, dict):
        raise WatchConfigError("Config file must contain a mapping at the top level.")

    missing = _REQUIRED_KEYS - raw.keys()
    if missing:
        raise WatchConfigError(f"Config is missing required keys: {sorted(missing)}")

    config: Dict[str, Any] = {
        "baseline": str(raw["baseline"]),
        "schema": str(raw["schema"]),
        "output_format": str(raw.get("output_format", "text")),
        "fail_on_breaking": bool(raw.get("fail_on_breaking", True)),
    }
    return config
