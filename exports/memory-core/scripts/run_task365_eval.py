#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path('/home/openclaw/.openclaw/workspace')
OUTDIR = ROOT / 'pkm-memory/outputs/task-365-stage5-2-eval-raw-2026-05-07'
SCRIPT = ROOT / 'pkm-memory/retrieve_memory.py'
OUTDIR.mkdir(parents=True, exist_ok=True)

scenarios = [
    ('mc5-01', 'Где сейчас Memory Core v1 по stage chain и что уже готово после Stage 4?'),
    ('mc5-02', 'Почему в Memory Core v1 решили держать retrieval_document как derived layer, а не как source of truth?'),
    ('mc5-03', 'Продолжи Memory Core evaluation с места после conflict/open-question synthesis и скажи, что делать следующим bounded шагом.'),
    ('mc5-04', 'Как Юрию лучше отвечать по таким technical chain updates: коротко по делу или с длинным разбором?'),
    ('mc5-05', 'Покажи, из каких именно файлов видно, что для Stage 4 уже сделаны routing, authority ranking, citation envelope и conflict synthesis.'),
]

for scenario_id, query in scenarios:
    output = OUTDIR / f'{scenario_id}.json'
    subprocess.run([
        'python3', str(SCRIPT), '--mode', 'local', '--output', str(output), query
    ], check=True, cwd=str(ROOT))
    print(f'{scenario_id}: {output}')
