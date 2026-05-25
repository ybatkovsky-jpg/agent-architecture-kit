# Meta lane regression mini-pack

Small targeted regression lock for the current `meta_evaluation_recall` behavior.

## Covered scenarios

- explicit `evaluation_summary`
- explicit `hardening_slice`
- explicit `release_recommendation`
- short-query anti-fallthrough (`memory core verdict` must stay meta, not factual, and should still anchor to the Stage 5.4 verdict artifact)
- short alias variants for the same contour: `release rec`, `exec verdict`, `stage 5 summary`, `hardening log`, `go/no-go`
- one negative control proving a real factual lookup stays factual

## What it checks

Checks are intentionally narrow:
- request class
- meta subfamily when applicable
- top result path / authority for the bounded cases where retrieval shape matters, including the short verdict alias pack

## Run

```bash
python3 pkm-memory/scripts/verify_meta_lane_regression_mini_pack.py
```

## Output

- `pkm-memory/outputs/meta-lane-regression-mini-pack-2026-05-07/verification-report.json`
