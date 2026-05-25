#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess

ROOT = Path('/home/openclaw/.openclaw/workspace')
OUT = ROOT / 'pkm-memory/outputs/task-445-meta-admission-rerun'
OUT.mkdir(parents=True, exist_ok=True)
queries = [
    ('q1-eval-summary.json', 'show evaluation summary and release recommendation for Memory Core Stage 5'),
    ('q2-explicit-meta-eval.json', 'Покажи evaluation artifacts Stage 5 и из каких файлов видно baseline fail/pass summary.'),
    ('q3-hardening-slice.json', 'Show hardening slice for continuation/meta alignment.'),
]
for filename, query in queries:
    subprocess.run([
        'python3', str(ROOT / 'pkm-memory/retrieve_memory.py'),
        '--mode', 'local',
        '--max-items', '5',
        '--output', str(OUT / filename),
        query,
    ], check=True)
for filename, _query in queries:
    data = json.loads((OUT / filename).read_text())
    print(f'== {filename} ==')
    print('top:', [item['document']['workspace_path'] for item in data['items'][:5]])
    print('selected_sources:', data['routing'].get('selected_source_keys'))
    print('excluded_sources:', data['routing'].get('excluded_source_keys'))
