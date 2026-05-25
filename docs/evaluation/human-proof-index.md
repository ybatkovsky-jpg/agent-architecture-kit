# Human Proof Index

A human-readable index for the curated proof artifacts exported into this repository.

Purpose:
- explain what each proof artifact is trying to prove;
- avoid forcing readers to infer meaning from raw `verification-report.json` names alone;
- connect proof artifacts to the architectural contours they support.

Primary proof export location:
- `exports/architecture-support-pack/curated-proof-pack/`

---

## 1. How to read these proofs

Each proof entry answers four things:
- **what contour it tests**
- **what claim it supports**
- **what kind of failure it is meant to catch**
- **where the exported artifact lives**

These are not all proofs ever produced in the live workspace.
They are a curated subset chosen because they are architecture-relevant and readable as reusable evidence.

---

## 2. Proof entries

## 2.1 Memory Core schema conformance

**Artifact**
- `exports/architecture-support-pack/curated-proof-pack/memory-core-schema-conformance/verification-report.json`

**Contour**
- Memory Core v1 schema/runtime alignment

**What it proves**
- the declared Memory Core object families and related runtime expectations match the actual schema/baseline contour closely enough to treat the implementation as real, not merely aspirational prose.

**Failure it is meant to catch**
- drift between Memory Core design claims and actual storage/runtime structure.

**Most related docs**
- `docs/memory/memory-core-v1.md`
- `exports/memory-core/sql/040_memory_core_v1_baseline.sql`

---

## 2.2 Memory Core storage smoke

**Artifact**
- `exports/architecture-support-pack/curated-proof-pack/memory-core-storage-smoke/summary.json`

**Contour**
- basic storage path viability

**What it proves**
- the storage contour is not only specified on paper; the core storage path can be exercised in a bounded smoke mode.

**Failure it is meant to catch**
- obviously broken write/read/storage assumptions that would invalidate higher-level memory claims.

**Most related docs**
- `docs/memory/memory-core-v1.md`
- `docs/memory/phased-rollout-and-verification.md`

---

## 2.3 Meta-evaluation routing regression

**Artifact**
- `exports/architecture-support-pack/curated-proof-pack/meta-evaluation-routing-regression-2026-05-12/verification-report.json`

**Contour**
- request-class-aware routing for meta-evaluation retrieval

**What it proves**
- explicit meta-evaluation style requests are routed into the intended retrieval lane rather than falling through to ordinary factual/task retrieval behavior.

**Failure it is meant to catch**
- route confusion where evaluation/meta requests are answered from the wrong source or policy lane.

**Most related docs**
- `docs/memory/retrieval-policy-matrix.md`
- `exports/memory-core/META_EVALUATION_RECALL_CONTRACT_V1.md`

---

## 2.4 Meta-lane regression mini-pack

**Artifact**
- `exports/architecture-support-pack/curated-proof-pack/meta-lane-regression-mini-pack-2026-05-07/verification-report.json`

**Contour**
- meta lane boundary discipline

**What it proves**
- short alias-style or summary/meta prompts still map to the intended meta lane, and negative controls do not accidentally get swept into meta behavior.

**Failure it is meant to catch**
- lane fallthrough, alias confusion, and accidental meta overreach.

**Most related docs**
- `docs/memory/retrieval-policy-matrix.md`
- `exports/memory-core/RETRIEVAL_LANE_CONTRACTS_V1.md`

---

## 2.5 Architecture design recall regression

**Artifact**
- `exports/architecture-support-pack/curated-proof-pack/architecture-design-recall-regression-2026-05-12/verification-report.json`

**Contour**
- architecture-design recall behavior

**What it proves**
- retrieval can surface architecture-design material in the intended lane rather than being dominated by irrelevant nearby artifacts or generic task residue.

**Failure it is meant to catch**
- inability to recover core architectural reasoning or dominance by wrong source classes.

**Most related docs**
- `docs/architecture-overview.md`
- `docs/memory/runtime-serving-architecture.md`

---

## 2.6 Artifact source trace regression

**Artifact**
- `exports/architecture-support-pack/curated-proof-pack/artifact-source-trace-regression-2026-05-12/verification-report.json`

**Contour**
- source traceability and artifact lookup

**What it proves**
- the system can preserve/source the right artifact provenance instead of returning detached answers without a recoverable trace basis.

**Failure it is meant to catch**
- provenance collapse, missing source trace, or incorrect artifact anchoring.

**Most related docs**
- `docs/memory/authority-priority.md`
- `docs/architecture/truth-boundary-contract.md`

---

## 2.7 Provenance link integrity

**Artifact**
- `exports/architecture-support-pack/curated-proof-pack/task-357-provenance-link-integrity/verification-report.json`

**Contour**
- typed provenance linking in Memory Core

**What it proves**
- the provenance-link model is not only declared conceptually; the link integrity contour can be validated with bounded verification.

**Failure it is meant to catch**
- broken or inconsistent evidence/source linkage inside the typed memory model.

**Most related docs**
- `docs/memory/memory-core-v1.md`
- `exports/memory-core/memory_core_typed_links.py`

---

## 2.8 Lifecycle slice verification

**Artifact**
- `exports/architecture-support-pack/curated-proof-pack/task-546-lifecycle-slice-verification-2026-05-21/verification-report.json`

**Contour**
- memory lifecycle loop / production-shape rollout slice

**What it proves**
- the later production-oriented lifecycle contour was bounded and verified as an executable slice, not left only as an intended roadmap.

**Failure it is meant to catch**
- production-lifecycle claims outrunning actual bounded implementation/verification.

**Most related docs**
- `docs/memory/phased-rollout-and-verification.md`
- `task-manager/artifacts/task-546-memory-v1-lifecycle-loop-contract-and-rollout-slice-2026-05-20.md`

---

## 3. What these proofs cover together

Taken together, this curated proof pack covers five major confidence areas:

1. **Schema / storage reality**
   - the memory model has real backing structure
2. **Routing / lane correctness**
   - requests can be steered into the right retrieval behavior
3. **Architecture recall quality**
   - architecture-relevant material can be recovered intentionally
4. **Provenance integrity**
   - answers and artifacts stay source-bound rather than floating free
5. **Lifecycle / rollout credibility**
   - the production path has bounded executable verification support

---

## 4. What this proof pack does not claim

This index should not be overread.
It does **not** claim that:
- every live workspace proof was exported;
- all operational edge cases are solved;
- the memory/runtime contour is fully complete;
- the exported repository is a drop-in production system.

What it does claim is narrower and more useful:
- the most important architectural contours were not exported as empty prose;
- there is real bounded evidence behind them.

---

## 5. Suggested reading order

If you want to connect design and proof:

1. `docs/memory/memory-core-v1.md`
2. `docs/memory/retrieval-policy-matrix.md`
3. `docs/memory/runtime-serving-architecture.md`
4. this file: `docs/evaluation/human-proof-index.md`
5. the corresponding proof artifacts under `exports/architecture-support-pack/curated-proof-pack/`
