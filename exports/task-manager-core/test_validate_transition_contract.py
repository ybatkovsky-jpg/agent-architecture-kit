from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TM = WORKSPACE / "task-manager" / "task_manager.py"
TEST_ROOT = Path(tempfile.mkdtemp(prefix="tm-test-validate-transition-contract-"))
os.environ["TASK_MANAGER_ROOT"] = str(TEST_ROOT)
TEST_ENV = dict(os.environ)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run([sys.executable, str(TM), *args], cwd=str(WORKSPACE), env=TEST_ENV, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(args)}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def main() -> int:
    created = json.loads(
        _run(
            "add",
            "tmp validate/transition contract",
            "--details",
            "Need bounded proof that validate surfaces transition-time fresh proof requirement clearly.",
            "--next-action",
            "Move through lifecycle",
        ).stdout
    )
    task_id = int(created["task_id"])

    _run("start", str(task_id), "--note", "Start validate/transition contract repro", "--next-action", "Add standalone proof note")

    closure_note = (
        "CLAIMED_OUTCOME: representative legacy-style proof note exists before transition. "
        "EVIDENCE: task-manager/test_validate_transition_contract.py records the reproduction path and expected validator surface. "
        "ANCHOR: /home/openclaw/.openclaw/workspace/task-manager/test_validate_transition_contract.py. "
        "VERIFICATION: the test executes validate both with and without inline transition proof and asserts the warning/transition gate behavior."
    )
    _run("note", str(task_id), "--note", closure_note, "--next-action", "Validate review readiness without inline note")

    validate_without_inline_proc = _run("validate", str(task_id), "review", "--next-action", "Close after review")
    validate_without_inline = json.loads(validate_without_inline_proc.stdout)
    assert "validate notice: accumulated proof may look sufficient" in validate_without_inline_proc.stderr, validate_without_inline_proc.stderr
    assert "transition_requires_inline_fresh_proof" in validate_without_inline["warnings"], validate_without_inline
    assert validate_without_inline["gate"]["passed"] is True, validate_without_inline
    assert validate_without_inline["transition_gate"]["passed"] is False, validate_without_inline
    assert "claim" in validate_without_inline["transition_gate"]["missing"], validate_without_inline

    validate_fresh_only = json.loads(
        _run("validate", str(task_id), "review", "--next-action", "Close after review", "--fresh-only").stdout
    )
    assert validate_fresh_only["passed"] is False, validate_fresh_only
    assert validate_fresh_only["transition_gate"] is None, validate_fresh_only
    assert "claim" in validate_fresh_only["missing"], validate_fresh_only
    assert "transition_requires_inline_fresh_proof" not in validate_fresh_only["warnings"], validate_fresh_only

    inline_review_note = (
        "CLAIMED_OUTCOME: representative transition carries fresh inline proof. "
        "EVIDENCE: review command includes closure proof inline while standalone note already exists. "
        "ANCHOR: /home/openclaw/.openclaw/workspace/task-manager/test_validate_transition_contract.py. "
        "VERIFICATION: validate with inline note clears the transition gate warning path."
    )
    validate_with_inline = json.loads(
        _run(
            "validate",
            str(task_id),
            "review",
            "--note",
            inline_review_note,
            "--next-action",
            "Close after review",
        ).stdout
    )
    assert validate_with_inline["passed"] is True, validate_with_inline
    assert "transition_requires_inline_fresh_proof" not in validate_with_inline["warnings"], validate_with_inline
    assert validate_with_inline["transition_gate"]["passed"] is True, validate_with_inline

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
