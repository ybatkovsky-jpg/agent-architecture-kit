#!/usr/bin/env bash
set -euo pipefail
python3 -m py_compile \
  task-manager/autonomy_router.py \
  task-manager/task_manager.py \
  task-manager/test_autonomy_router.py \
  task-manager/test_autonomy_state_and_gate.py \
  task-manager/test_autonomy_watchdog.py
python3 task-manager/test_autonomy_router.py
python3 task-manager/test_autonomy_state_and_gate.py
python3 task-manager/test_autonomy_watchdog.py
python3 task-manager/test_autonomy_resume.py
