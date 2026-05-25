#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path('/home/openclaw/.openclaw/workspace')
RETRIEVE = ROOT / 'pkm-memory' / 'retrieve_memory.py'
OUTDIR = ROOT / 'pkm-memory' / 'outputs' / 'task-377-status-handoff-hardening-2026-05-10'
OUTDIR.mkdir(parents=True, exist_ok=True)

QUERIES = {
    'q1-ru-stage-chain-status': 'Где сейчас Memory Core v1 по stage chain и что уже готово после Stage 4?',
    'q2-ru-done-next': 'Что уже сделано по Memory Core v1 и что дальше делать следующим шагом?',
    'q3-en-status-now': 'Where are we now on Memory Core v1 and what is already done?',
    'q4-en-next-based-on-state': 'What next for Memory Core v1 after Stage 4, based on current handoff/state?',
}

results = {}
for key, query in QUERIES.items():
    output_path = OUTDIR / f'{key}.json'
    cmd = ['python3', str(RETRIEVE), query, '--mode', 'local', '--output', str(output_path)]
    subprocess.run(cmd, check=True, cwd=str(ROOT))
    payload = json.loads(output_path.read_text())
    items = payload.get('items', [])
    top_paths = [str(item.get('document', {}).get('workspace_path', '')) for item in items[:4]]
    top_layers = [str(item.get('authority', {}).get('layer', '')) for item in items[:4]]
    top_reasons = [str(item.get('match_reason', '')) for item in items[:4]]
    results[key] = {
        'query': query,
        'request_class': payload.get('request_classification', {}).get('request_class'),
        'top_paths': top_paths,
        'top_layers': top_layers,
        'top_reasons': top_reasons,
        'selected_item_paths': payload.get('serve_pack', {}).get('trace', {}).get('selected_item_paths', []),
    }

summary = {
    'task': 377,
    'date': '2026-05-10',
    'results': results,
}
(OUTDIR / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
