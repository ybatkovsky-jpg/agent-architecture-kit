#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
OUTDIR = ROOT / 'outputs' / 'task-376-status-handoff-first-hardening-2026-05-10'
OUTDIR.mkdir(parents=True, exist_ok=True)

queries = [
    ('q1-stage-chain-status.json', 'Где сейчас Memory Core v1 по stage chain и что уже готово после Stage 4?'),
    ('q2-task-360-status.json', 'что уже готово по текущей задаче 360 и на каком этапе сейчас'),
    ('q3-next-step-status.json', 'Memory Core v1: что уже сделано, где мы сейчас и что делать дальше после Stage 4?'),
]
summary = []
for filename, query in queries:
    output_path = OUTDIR / filename
    subprocess.run([
        'python', str(ROOT / 'retrieve_memory.py'), '--mode', 'local', '--output', str(output_path), query
    ], check=True, cwd=str(WORKSPACE))
    data = json.loads(output_path.read_text())
    items = data.get('items', [])
    summary.append({
        'query': query,
        'output': str(output_path.relative_to(WORKSPACE)),
        'top_paths': [item.get('document', {}).get('workspace_path') for item in items[:5]],
        'top_titles': [item.get('document', {}).get('title') for item in items[:5]],
        'top_reasons': [item.get('match_reason') for item in items[:3]],
        'request_class': data.get('routing', {}).get('classification', {}).get('request_class'),
        'authority_order': data.get('serve_pack', {}).get('authority_order') or data.get('serve_pack', {}).get('trace', {}).get('authority', {}).get('authority_order'),
    })
(OUTDIR / 'summary.json').write_text(json.dumps({'queries': summary}, ensure_ascii=False, indent=2))
print(json.dumps({'queries': summary}, ensure_ascii=False, indent=2))
