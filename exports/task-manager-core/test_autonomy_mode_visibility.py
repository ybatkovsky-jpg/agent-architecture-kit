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
TEST_ROOT = Path(tempfile.mkdtemp(prefix="tm-test-autonomy-mode-"))
os.environ["TASK_MANAGER_ROOT"] = str(TEST_ROOT)
TEST_ENV = dict(os.environ)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run([sys.executable, str(TM), *args], cwd=str(WORKSPACE), env=TEST_ENV, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(args)}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def main() -> int:
    auto_created = json.loads(_run("add", "tmp autonomous mode visibility", "--details", "visibility proof", "--next-action", "Continue bounded slice").stdout)
    auto_id = int(auto_created["task_id"])
    _run("start", str(auto_id), "--note", "Starting visibility proof with evidence artifact task-manager/test_autonomy_mode_visibility.py and verification python3 task-manager/test_autonomy_mode_visibility.py", "--next-action", "Continue bounded slice")
    init_payload = json.loads(_run("autonomy-init", str(auto_id), "--note", "Enter autonomous_until_done mode", "--next-action", "Continue bounded slice").stdout)
    assert init_payload["autonomy_state"]["mode"] == "autonomous_until_done"
    assert init_payload["autonomy_state"]["autonomy_mode"] is True

    shown = json.loads(_run("show", str(auto_id)).stdout)
    assert shown["autonomy"]["mode"] == "autonomous_until_done"
    assert shown["autonomy"]["continuation"]["router_decision"] == "none"
    assert shown["autonomy"]["continuation"]["suppressed_surface_count"] == 0
    assert shown["autonomy"]["continuation"]["goal_complete"] is False
    assert shown["autonomy"]["watchdog"]["eligible_for_resume"] is True

    listed = json.loads(_run("list", "--format", "json", "--limit", "500").stdout)
    listed_row = next(row for row in listed if int(row["id"]) == auto_id)
    assert listed_row["autonomy"]["mode"] == "autonomous_until_done"
    assert listed_row["autonomy"]["surface_allowed"] is False

    watchdog = json.loads(_run("watchdog", "--hours", "999").stdout)
    excluded = next(row for row in watchdog["excluded_autonomy"] if int(row["id"]) == auto_id)
    assert excluded["mode"] == "autonomous_until_done"
    assert excluded["suppressed_surface_count"] == 0

    manual_created = json.loads(_run("add", "tmp manual mode visibility", "--details", "manual visibility proof", "--next-action", "Stay manual").stdout)
    manual_id = int(manual_created["task_id"])
    manual_show = json.loads(_run("show", str(manual_id)).stdout)
    assert manual_show["autonomy"]["mode"] == "manual"
    assert manual_show["autonomy"]["autonomy_mode"] is False
    assert manual_show["autonomy"]["surface_allowed"] is True

    manual_listed = json.loads(_run("list", "--format", "json", "--limit", "500").stdout)
    manual_row = next(row for row in manual_listed if int(row["id"]) == manual_id)
    assert manual_row["autonomy"]["mode"] == "manual"
    assert manual_row["autonomy"]["continuation"]["router_decision"] == "none"

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
