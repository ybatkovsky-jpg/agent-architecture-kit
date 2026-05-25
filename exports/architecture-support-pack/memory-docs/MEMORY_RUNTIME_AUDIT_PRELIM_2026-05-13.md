# Memory Runtime Audit (preliminary hybrid audit) — 2026-05-13

## Audit status

This is a preliminary hybrid audit of the **live workspace/deployed contour** based on:
- direct inspection of the deployed workspace code;
- available runtime/tooling signals during this session;
- previous architecture artifacts already present in this environment.

It is **not yet a full runtime-complete audit**, because:
- the spawned bounded subagent died without returning a completion event or artifact;
- `openclaw status` did not return usable output in the available shell path and was killed before yielding a stable status snapshot;
- direct service/database/vector-store inspection is still incomplete.

## Verified findings

### 1) The deployed memory contour is not stock OpenClaw; it includes a custom retrieval system
Verified from `pkm-memory/retrieve_memory.py`.

Observed signs:
- request classification by intent (`current_task_execution`, `resume_reopen_continuation`, `architecture_design_recall`, `meta_evaluation_recall`, etc.);
- per-class serving budgets (`tiny`, `small`, `medium`);
- authority routing and lane-specific source exclusions;
- source-domain tagging (`task_manager_handoffs`, `task_manager_artifacts`, `openclaw_shared_memory`);
- explicit anti-fallthrough and anti-noise heuristics for continuation/meta-evaluation retrieval.

This means the production contour has already evolved from generic memory retrieval into a **policy-routed retrieval orchestrator**.

### 2) Memory is split across multiple semantic source classes, not one flat store
Verified from `pkm-memory/retrieve_memory.py`.

Visible conceptual layers:
- `task_manager_handoffs` → continuation / canonical-handoff state;
- `task_manager_artifacts` → evidence-bearing task artifacts;
- `openclaw_shared_memory` → memory notes / preference / wiki-like memory;
- generic `retrieval_document` fallback lane.

This suggests a layered memory model closer to:
- task-state memory,
- evidence memory,
- durable note memory,
- generic retrieval corpus.

### 3) Retrieval logic is heavily shaped by authority semantics, not only similarity
Verified from `REQUEST_CLASS_SPECS`, routing helpers, and authority aliases.

Important consequence:
- the system is trying to answer "what kind of memory is allowed to answer this question?" before ranking chunks;
- this is stronger than naive semantic search and is a meaningful architectural improvement.

### 4) The current contour contains explicit hardening against known failure modes
Verified from code and recent local architecture artifacts/memory context.

Examples visible in code:
- continuation/handoff suppression in meta-evaluation lanes;
- wrapper/handoff demotion and source-lane hygiene;
- targeted path heuristics for meta-evaluation artifacts and continuation verification docs.

This indicates the memory system is under active corrective iteration against real regressions, not static design.

### 5) The broader workspace also contains architecture-governance tooling around reusable artifacts
Verified from:
- `scripts/architecture/promotion_gate.py`
- `scripts/architecture/verify_promotion_gate_cases.py`

This is not the memory engine itself, but it shows the environment has a parallel architecture-governance contour that likely influences how memory/architecture artifacts are promoted, cited, and stabilized.

## High-confidence hypotheses

### H1) Retrieval quality currently depends significantly on path/title heuristics and curated authority rules
Reason:
- many explicit path markers and artifact-family detectors are present in `retrieve_memory.py`;
- request-class routing appears central to recall quality.

Implication:
- the system is probably effective for known task families and architecture contours,
- but brittle when new artifact naming conventions or source families appear.

### H2) The memory contour is in a transitional state between heuristic retrieval and a cleaner canonical evidence-serving architecture
Reason:
- visible layering and authority semantics are strong;
- but they coexist with many special-case classifiers and path heuristics.

Implication:
- this is likely why regressions can be narrowed without being fully solved: the architecture is improving, but still partially compensatory.

### H3) Token efficiency is being controlled more by pre-routing and budget clamps than by downstream compression quality
Reason:
- visible budget controls (`tiny/small/medium`, bounded item counts, candidate fetch limits);
- not yet enough visible evidence of a dedicated summarization/compression subsystem in this pass.

Implication:
- main token defense seems to be selective retrieval, not deep memory condensation.

## Unknown / not yet verified

Not yet directly verified in this pass:
- which databases/vector stores are actually alive in runtime;
- whether embeddings are generated locally, remotely, or precomputed offline;
- whether Redis/queue/worker infrastructure is in the active memory path;
- whether context assembly happens inside OpenClaw runtime, a sidecar, or a custom prompt builder;
- whether reflection/summarization/compression loops are live, partial, or dormant;
- whether there are dead background jobs or stale services tied to memory.

## Preliminary verdict

### Keep
- request-class-aware retrieval;
- authority-first routing;
- explicit separation of task/handoff/evidence/shared-memory lanes;
- bounded retrieval budgets.

### Simplify
- path/title heuristic sprawl;
- special-case artifact detectors;
- duplicated lane-exclusion logic if it exists elsewhere.

### Rewrite candidates
- candidate generation / corpus admission for meta-evaluation and architecture recall, if current regressions still require narrow hand-tuned markers;
- retrieval scoring into a cleaner two-stage design: candidate admission → authority/rule filter → final ranking.

### Remove or reduce
- wrapper/noise compensation logic once cleaner canonical source boundaries exist;
- generic handoff substitution in lanes where evidence artifacts should dominate.

### Highest-priority refactors
1. Make source families canonical and machine-declared, not inferred from path text.
2. Separate candidate admission from ranking more explicitly.
3. Add runtime observability for retrieval decisions (why a source was included/excluded).
4. Add reproducible eval packs per request class.
5. Verify actual live infra dependencies (DB/vector/cache/worker) and remove dead branches.

## Operational note

This audit is preliminary because runtime observability was partially blocked during this session. A second pass should finish:
- service/process status snapshot;
- active config/env inspection;
- database/vector-store inspection;
- one end-to-end trace from user query → retrieval → context assembly.
