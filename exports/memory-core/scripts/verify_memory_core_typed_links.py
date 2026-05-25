#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PAYLOAD = ROOT / "fixtures" / "memory_core_typed_links_payload.sample.json"
SQL_DUMP = ROOT / "state" / "sql-dumps" / "task350-memory-core-typed-links-sample.sql"
REGISTRY_DUMP = ROOT / "state" / "sql-dumps" / "task350-memory-core-typed-links-expanded-payload.json"
WRITER = ROOT / "memory_core_typed_links.py"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT.parent, text=True, capture_output=True, check=True)



def assert_contains(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"Expected to find {needle!r} in generated output")



def expect_failure(payload: dict, expected_substring: str) -> None:
    temp_path = ROOT / "state" / "sql-dumps" / "task350-negative-payload.json"
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(WRITER), str(temp_path), "--persist-mode", "sql-dump", "--sql-dump-path", str(SQL_DUMP)],
        cwd=ROOT.parent,
        text=True,
        capture_output=True,
    )
    if result.returncode == 0:
        raise AssertionError("Expected negative payload to fail validation")
    failure_text = (result.stderr or "") + (result.stdout or "")
    if expected_substring not in failure_text:
        raise AssertionError(f"Expected failure text to include {expected_substring!r}, got: {failure_text}")



def main() -> int:
    SQL_DUMP.parent.mkdir(parents=True, exist_ok=True)
    result = run([
        sys.executable,
        str(WRITER),
        str(SAMPLE_PAYLOAD),
        "--persist-mode",
        "sql-dump",
        "--sql-dump-path",
        str(SQL_DUMP),
        "--emit-registry-payload-path",
        str(REGISTRY_DUMP),
    ])
    output = json.loads(result.stdout)
    if output.get("registry_object_count") != 2:
        raise AssertionError(f"Expected 2 registry objects, got {output.get('registry_object_count')!r}")

    sql_text = SQL_DUMP.read_text(encoding="utf-8")
    assert_contains(sql_text, "INSERT INTO mc_typed_links")
    assert_contains(sql_text, "'provenance'")
    assert_contains(sql_text, "'dependency'")
    assert_contains(sql_text, "'supported_by'")

    expanded = json.loads(REGISTRY_DUMP.read_text(encoding="utf-8"))
    objects = expanded.get("objects", [])
    if len(objects) != 2:
        raise AssertionError("Expanded registry payload must contain exactly 2 objects")
    if any(obj["family"] != "typed_link" for obj in objects):
        raise AssertionError("Expanded registry payload should contain only typed_link families")

    negative_same_ref = json.loads(SAMPLE_PAYLOAD.read_text(encoding="utf-8"))
    negative_same_ref["typed_links"][0]["record"]["to_ref"] = negative_same_ref["typed_links"][0]["record"]["from_ref"]
    expect_failure(negative_same_ref, "typed_link.record.from_ref and typed_link.record.to_ref must differ")

    negative_bad_prefix = json.loads(SAMPLE_PAYLOAD.read_text(encoding="utf-8"))
    negative_bad_prefix["typed_links"][0]["record"]["from_ref"] = "task:350"
    expect_failure(negative_bad_prefix, "typed_link.record.from_ref must start with one of")

    print("task350 verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
