from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from autonomy_router import route_autonomous_child_completion
from autonomy_state import default_autonomy_state

SCENARIO_MANIFEST_VERSION = "replay_scenario_manifest.v1"


def load_manifest(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_manifest(data)
    return data


def validate_manifest(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict):
        raise ValueError("Scenario manifest must be an object.")
    if str(manifest.get("manifest_version") or "") != SCENARIO_MANIFEST_VERSION:
        raise ValueError(f"Unsupported manifest_version: {manifest.get('manifest_version')!r}")
    scenarios = manifest.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("Scenario manifest must contain a non-empty scenarios list.")
    for i, scenario in enumerate(scenarios, start=1):
        if not isinstance(scenario, dict):
            raise ValueError(f"Scenario #{i} must be an object.")
        for key in (
            "scenario_id",
            "scenario_class",
            "description",
            "task",
            "coach_summary",
            "autonomy_state_patch",
            "child_result",
            "expected",
        ):
            if key not in scenario:
                raise ValueError(f"Scenario {scenario.get('scenario_id', i)!r} missing required key: {key}")
        expected = scenario.get("expected")
        if not isinstance(expected, dict) or not expected:
            raise ValueError(f"Scenario {scenario.get('scenario_id', i)!r} expected must be a non-empty object.")


def _deep_update(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def _build_autonomy_state(task_id: int, patch: dict[str, Any]) -> dict[str, Any]:
    state = default_autonomy_state(task_id=task_id)
    state["autonomy_mode"] = True
    state["delivery_gate"] = "internal_only_until_terminal"
    return _deep_update(state, patch)


def _lookup_path(payload: dict[str, Any], dotted: str) -> Any:
    cur: Any = payload
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(dotted)
        cur = cur[part]
    return cur


def run_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    task = dict(scenario["task"])
    task.setdefault("id", 0)
    task.setdefault("status", "in_progress")
    task.setdefault("next_action", "Continue bounded slice")
    coach_summary = dict(scenario["coach_summary"])
    autonomy_state = _build_autonomy_state(int(task.get("id") or 0), dict(scenario.get("autonomy_state_patch") or {}))
    routed = route_autonomous_child_completion(task, dict(scenario["child_result"]), coach_summary, autonomy_state)

    mismatches: list[dict[str, Any]] = []
    for dotted, expected_value in dict(scenario["expected"]).items():
        actual = _lookup_path(routed, dotted)
        if actual != expected_value:
            mismatches.append({"path": dotted, "expected": expected_value, "actual": actual})

    return {
        "scenario_id": scenario["scenario_id"],
        "scenario_class": scenario["scenario_class"],
        "description": scenario["description"],
        "passed": not mismatches,
        "mismatches": mismatches,
        "routing": routed,
    }


def run_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    results = [run_scenario(s) for s in manifest["scenarios"]]
    passed = sum(1 for item in results if item["passed"])
    failed = len(results) - passed
    return {
        "manifest_version": manifest["manifest_version"],
        "scenario_count": len(results),
        "passed": passed,
        "failed": failed,
        "all_passed": failed == 0,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Replay verifier harness for task-manager autonomy scenarios")
    parser.add_argument("manifest", help="Path to replay scenario manifest JSON")
    parser.add_argument("--write-report", help="Optional path to write JSON report")
    args = parser.parse_args(argv)

    report = run_manifest(load_manifest(args.manifest))
    if args.write_report:
        path = Path(args.write_report)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
