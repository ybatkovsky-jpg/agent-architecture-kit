#!/usr/bin/env python3
"""Load architecture formalization config from YAML or JSON.

Stage 2 scaffold: bounded practical loader used by trace/scoring demos.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency handling
    yaml = None


class ArchConfigError(RuntimeError):
    pass


REQUIRED_TOP_LEVEL_KEYS = {
    "architecture",
    "modules",
    "routing",
    "policies",
    "scoring",
    "calibration",
    "protected_cases",
    "update_loop",
}


def load_arch_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise ArchConfigError(f"Config file not found: {config_path}")

    raw = config_path.read_text(encoding="utf-8")
    suffix = config_path.suffix.lower()

    if suffix == ".json":
        data = json.loads(raw)
    elif suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise ArchConfigError("PyYAML is required to load YAML architecture configs")
        data = yaml.safe_load(raw)
    else:
        raise ArchConfigError(f"Unsupported config extension: {suffix}")

    if not isinstance(data, dict):
        raise ArchConfigError("Architecture config root must be an object/map")

    missing = sorted(REQUIRED_TOP_LEVEL_KEYS - set(data.keys()))
    if missing:
        raise ArchConfigError(f"Architecture config missing top-level keys: {', '.join(missing)}")

    return data


def summarize_arch_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "architecture_id": config.get("architecture", {}).get("id"),
        "version": config.get("architecture", {}).get("version"),
        "module_count": len(config.get("modules", [])),
        "policy_count": len(config.get("policies", [])),
        "critic_rule_count": len(config.get("calibration", {}).get("critic_rules", [])),
        "protected_case_count": len(config.get("protected_cases", [])),
        "scoring_metric_count": len(config.get("scoring", {}).get("metrics", {})),
        "learning_loop_phase_count": len(config.get("update_loop", {}).get("learning_loop", {}).get("phases", [])),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load and summarize architecture config")
    parser.add_argument("config", help="Path to architecture YAML/JSON config")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print compact summary output (kept for CLI compatibility)",
    )
    args = parser.parse_args()

    config = load_arch_config(args.config)
    if args.summary:
        print(json.dumps(summarize_arch_config(config), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summarize_arch_config(config), ensure_ascii=False, indent=2))
