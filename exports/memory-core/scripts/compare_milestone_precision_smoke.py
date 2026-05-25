#!/usr/bin/env python3
import json
import os

outdir = 'pkm-memory/outputs/smoke-db-retrieval-milestone-pass-2026-04-26'
pairs = [
    ('postgres activation milestone', 'query-postgres-activation-milestone-db.json', 'query-postgres-activation-milestone-local.json'),
    ('postgres activation', 'query-postgres-activation-db.json', 'query-postgres-activation-local.json'),
    ('activation milestone', 'query-activation-milestone-db.json', 'query-activation-milestone-local.json'),
    ('task-107-postgres-activation-and-first-live-ingest', 'query-task-107-db.json', 'query-task-107-local.json'),
]
summary = []
for query, dbf, localf in pairs:
    with open(os.path.join(outdir, dbf), encoding='utf-8') as f:
        db = json.load(f)
    with open(os.path.join(outdir, localf), encoding='utf-8') as f:
        local = json.load(f)

    def top3(payload):
        rows = []
        for item in payload.get('items', [])[:3]:
            rows.append({
                'rank': item.get('rank'),
                'title': item['document']['title'],
                'path': item['document']['workspace_path'],
                'score': item['score'],
                'match_reason': item['match_reason'],
            })
        return rows

    summary.append({'query': query, 'db_top3': top3(db), 'local_top3': top3(local)})

with open(os.path.join(outdir, 'comparison-summary.json'), 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(json.dumps(summary, ensure_ascii=False, indent=2))
