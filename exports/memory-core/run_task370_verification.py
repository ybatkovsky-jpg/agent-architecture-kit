#!/usr/bin/env python3
from pathlib import Path
import subprocess

root = Path('/home/openclaw/.openclaw/workspace')
outdir = root / 'pkm-memory/outputs/task-370-continuation-meta-alignment-verification-2026-05-07'
outdir.mkdir(parents=True, exist_ok=True)
queries = [
    ('q1_continue_conflict_after.json', 'Продолжи Memory Core evaluation с места после conflict/open-question synthesis и скажи, что делать следующим bounded шагом.'),
    ('q2_resume_task363.json', 'Resume Memory Core v1 after task-363 handoff and continue with the next bounded hardening slice.'),
    ('q3_reopen_stage4_chain.json', 'Reopen Memory Core continuation around task-363/task-362 and pick the freshest handoff to continue from.'),
]
for filename, query in queries:
    subprocess.run([
        'python', 'pkm-memory/retrieve_memory.py', '--mode', 'local', '--max-items', '5',
        '--output', str(outdir / filename), query,
    ], cwd=root, check=True)
print(outdir)
