from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import task_manager as tm_mod


def main() -> int:
    def _fake_cron_run(cmd, cwd=None, capture_output=True, text=True):
        assert cmd[:4] == ["openclaw", "cron", "add", "--json"]
        assert "--every" in cmd
        assert cmd[cmd.index("--every") + 1] == "7m"
        assert "--session" in cmd
        assert cmd[cmd.index("--session") + 1] == "isolated"
        assert "--no-deliver" in cmd
        assert "--message" in cmd
        message = cmd[cmd.index("--message") + 1]
        assert "python3 task-manager/task_manager.py watchdog --hours 1.5 --run-resumes --cooldown-minutes 12" in message
        return SimpleNamespace(returncode=0, stdout=json.dumps({"id": "cron-watchdog-1", "name": "autonomy-watchdog-proof"}), stderr="")

    with patch.object(tm_mod.subprocess, "run", side_effect=_fake_cron_run):
        payload = tm_mod.schedule_autonomy_watchdog_cron(
            every="7m",
            hours=1.5,
            cooldown_minutes=12,
            session_target="isolated",
            agent_id="main",
            model="",
            session_key="",
            job_name="autonomy-watchdog-proof",
        )

    assert payload["id"] == "cron-watchdog-1"
    assert payload["name"] == "autonomy-watchdog-proof"
    assert payload["every"] == "7m"
    assert payload["hours"] == 1.5
    assert payload["cooldown_minutes"] == 12
    assert payload["command"][:6] == ["openclaw", "cron", "add", "--json", "--name", "autonomy-watchdog-proof"]
    assert "--no-deliver" in payload["command"]
    assert "--every" in payload["command"]
    assert payload["message"].startswith("Run the local task-manager autonomous watchdog executor.")
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
