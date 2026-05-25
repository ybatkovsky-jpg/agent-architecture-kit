# Task 409 — Memory stack improvement specification

_Date: 2026-05-12_

Primary task:
- **#409 — Memory stack improvement spec: current state, target model, and task-cut basis**

Purpose:
- provide a single execution-facing specification for the current memory stack;
- distinguish real implemented behavior from planned architecture;
- define the target usable memory operating model;
- expose concrete gaps that should be turned into follow-up tasks.

This document is intended to be the **task-cut basis** for future memory-stack improvement work.

---

# 1. Executive summary

The current memory stack is **partially real, partially formalized, and not yet fully closed as an operating system**.

What is already real:
- a file-backed memory layer exists and is actively used;
- a PostgreSQL-based phase-1 retrieval backbone exists and validates successfully;
- retrieval from the database works;
- a Memory Core v1 schema exists in PostgreSQL;
- several bounded writers/verifiers for typed memory objects exist and at least some of them pass verification;
- task metadata can be projected into Memory Core structures.

What is not yet fully true:
- there is no evidence that all memory layers are running as one seamless always-on system;
- promotion/distillation between layers is not yet proven as a stable continuous production loop;
- runtime memory use is not yet clearly unified with the local PKM memory-core contour;
- some important paths exist as designed and partially implemented surfaces, but not as fully operational end-to-end memory behavior.

Core conclusion:

> The memory stack is already a meaningful substrate, but it is not yet a finished memory operating system.

---

# 2. Scope and non-scope

## Scope
This spec covers:
- file memory surfaces;
- PostgreSQL phase-1 retrieval storage;
- Memory Core v1 schema and write surfaces;
- retrieval and serving contours;
- movement between memory layers;
- validation and regression surfaces;
- task-cut implications.

## Non-scope
This spec does not:
- redesign memory from scratch;
- assume vector-first architecture as mandatory;
- claim that every documented layer is already production-ready;
- replace source-level runbooks or low-level schema files.

---

# 3. Current memory architecture by layer

## Layer 0 — Human-readable file memory

### Main components
- `MEMORY.md`
- `memory/YYYY-MM-DD.md`
- `task-manager/artifacts/`
- `task-manager/handoffs/`
- selected docs/notes with memory relevance

### Role
This is the primary human-readable and git-visible memory surface.

### Authority
This layer is the practical source of truth for much of the current memory content.

### Current status
- **Working**
- heavily used in practice
- still central to continuity

### Limitation
- retrieval and serving over this layer are not enough by themselves for structured, scalable recall

---

## Layer 1 — Phase-1 PostgreSQL retrieval backbone

### Main components
Workspace root:
- `pkm-memory/`

Core retrieval schema files:
- `pkm-memory/sql/001_extensions.sql`
- `pkm-memory/sql/010_schema.sql`
- `pkm-memory/sql/020_phase1_backbone_refinements.sql`

Core retrieval scripts:
- `pkm-memory/ingest_sources.py`
- `pkm-memory/retrieve_memory.py`
- `pkm-memory/scripts/bootstrap_storage.sh`
- `pkm-memory/scripts/validate_storage.sh`
- `pkm-memory/scripts/run_live_retrieval_smoke_unified.py`

### Database shape
Verified phase-1 retrieval tables:
- `sources`
- `documents`
- `chunks`
- `entities`
- `document_links`
- `ingestion_runs`

### Role
This layer is the retrieval/index substrate.
It converts selected file-backed sources into searchable structured storage in PostgreSQL.

### Current status
- **Working**
- validation passes
- retrieval works
- incremental ingest exists

### Important characteristics
- lexical-first retrieval backbone
- PostgreSQL is acting as retrieval/index authority, not as the only content authority
- approved-root policy constrains what enters this layer by default

### Limitation
- this layer is mainly retrieval infrastructure, not the full semantic or durable memory model

---

## Layer 2 — Memory Core v1 relational object layer

### Main schema file
- `pkm-memory/sql/040_memory_core_v1_baseline.sql`

### Verified Memory Core tables
- `mc_source_records`
- `mc_evidence_records`
- `mc_memory_notes`
- `mc_wiki_pages`
- `mc_retrieval_documents`
- `mc_session_capsules`
- `mc_typed_links`
- `mc_object_sources`
- `mc_object_evidence`
- `mc_memory_note_supersedes`
- `mc_memory_note_related_refs`
- `mc_wiki_backing_memory`
- `mc_wiki_backing_evidence`
- `mc_retrieval_document_evidence`
- `mc_retrieval_document_chunks`
- `mc_session_capsule_memory_refs`

### Intended object families
- `source_record`
- `evidence_record`
- `memory_note`
- `wiki_page`
- `retrieval_document`
- `session_capsule`
- `typed_link`

### Main scripts
- `pkm-memory/memory_core_registry.py`
- `pkm-memory/memory_core_decisions_sessions.py`
- `pkm-memory/memory_core_typed_links.py`
- `pkm-memory/memory_core_task_metadata.py`
- `pkm-memory/memory_core_session_capsule_distiller.py`

### Role
This layer is the typed memory-object model.
It exists to make memory more structured than “documents and chunks” and to introduce explicit authority-bounded objects.

### Current status
- **Partially working but not fully operationalized as a whole**

What is verified:
- schema exists
- schema conformance verifier passes
- task metadata projection verifier passes
- bounded write surfaces exist

What is not yet fully proven:
- that all object families are populated in real routine use;
- that promotion between evidence -> memory_note -> wiki_page is running as a mature operating loop;
- that session capsules are routinely produced, served, refreshed, and expired in live runtime flow.

---

## Layer 3 — Runtime memory tools and recall surfaces

### Main visible tools
- `memory_search`
- `memory_get`

### Role
These are the runtime recall tools exposed to the assistant.
They are the actual interface used in conversational work to recover prior context.

### Current status
- **Working, but not obviously unified with the whole local memory stack**

Observed practical issue:
- some memory questions are answered better by direct workspace inspection than by runtime memory search alone.

Interpretation:
- tool-level recall exists;
- but the local pkm-memory / memory-core contour is not yet clearly acting as one fully unified recall substrate for runtime.

---

# 4. Current storage model

## 4.1 File storage
Human-editable durable content lives in regular files under the workspace.
This includes curated memory, daily notes, artifacts, and handoff files.

## 4.2 PostgreSQL storage
PostgreSQL stores indexed retrieval data and typed memory-core objects.
It is not a user-edited file tree; it is a database service accessed via SQL/psql/scripts.

## 4.3 Source-of-truth boundary
Current practical boundary:
- files remain major content truth surfaces;
- PostgreSQL acts as retrieval/index/object persistence layer;
- task truth remains in `task-manager/tasks.db` for tasks themselves.

This means the memory system is already **multi-authority**, not monolithic.

---

# 5. Current ingest and movement paths

## 5.1 File sources -> retrieval backbone

### Main path
Approved roots are read by:
- `pkm-memory/ingest_sources.py`

Registry:
- `pkm-memory/config/source_registry.seed.yaml`

Default approved roots currently include:
- `memory/`
- `task-manager/artifacts/`
- `task-manager/handoffs/`

### What happens
- source roots are scanned;
- changed files are identified;
- documents are created/updated;
- chunks are created/updated;
- ingestion run history is recorded;
- local ingestion state is updated.

### Status
- **Working**

---

## 5.2 Retrieval backbone -> query results

### Main path
- `pkm-memory/retrieve_memory.py`

### What happens
- a query is classified/handled;
- retrieval hits are selected from indexed storage;
- bounded result packs are returned;
- citation/authority logic is applied in the serve-pack shape.

### Status
- **Working**

### Caveat
- not yet equivalent to “the whole memory system always remembers correctly”

---

## 5.3 Task system -> Memory Core projection

### Main path
- `pkm-memory/memory_core_task_metadata.py`

### What happens
- task data is read from `task-manager/tasks.db`;
- one task snapshot is emitted;
- a memory-core projection is produced;
- retrieval document and optional typed links are generated;
- reingest/update semantics replace stale relation data.

### Status
- **Verified working as a bounded implementation path**

### Important boundary
- task truth stays in the task system;
- Memory Core stores a projection, not task ownership.

---

## 5.4 Structured object payloads -> Memory Core tables

### Main paths
- `memory_core_registry.py`
- `memory_core_decisions_sessions.py`
- `memory_core_typed_links.py`
- `memory_core_session_capsule_distiller.py`

### What happens
- payloads are validated and expanded;
- SQL or psql writes are generated/executed;
- supported object families are persisted to `mc_*` tables.

### Status
- **Partially verified / bounded-working**

### Caveat
- existence of writers and verifiers does not yet prove routine operational use at scale.

---

# 6. Current validation and verification state

## Confirmed working during recent inspection
- `pkm-memory/scripts/validate_storage.sh` → passed
- `pkm-memory/retrieve_memory.py ... --mode auto ...` → worked
- `pkm-memory/scripts/verify_memory_core_schema_conformance.py` → passed
- `pkm-memory/scripts/verify_memory_core_task_metadata.py` → passed

## Confirmed by repository structure and outputs
There is substantial evidence of prior bounded verification work, including:
- retrieval smoke outputs
- regression fixture packs
- continuation regression packs
- classifier/routing verification outputs
- provenance integrity outputs

## Not fully re-confirmed in this inspection
- every verifier script
- every writer path with live PostgreSQL writes
- every distillation/promote path in continuous production mode
- unified live smoke wrapper as a stable green check in this exact run

Interpretation:
- the stack is not untested;
- but not every claimed path should be treated as freshly re-verified right now.

---

# 7. Current maturity assessment by capability

## 7.1 File memory
- Status: **working**
- Confidence: high

## 7.2 PostgreSQL retrieval backbone
- Status: **working**
- Confidence: high

## 7.3 Retrieval query path
- Status: **working**
- Confidence: medium-high

## 7.4 Memory Core v1 schema
- Status: **working as schema baseline**
- Confidence: high

## 7.5 Memory Core write surfaces
- Status: **partially working / bounded verified**
- Confidence: medium

## 7.6 Task -> memory-core projection
- Status: **working in bounded verification**
- Confidence: medium-high

## 7.7 Evidence -> durable memory_note promotion loop
- Status: **designed / partially surfaced, not proven as routine production loop**
- Confidence: low-medium

## 7.8 Memory_note -> wiki_page distillation loop
- Status: **designed more than operationally proven**
- Confidence: low

## 7.9 Session capsule lifecycle in real runtime
- Status: **partially implemented conceptually and in scripts, not proven as stable daily operating loop**
- Confidence: low-medium

## 7.10 Unified runtime recall across all layers
- Status: **not fully unified**
- Confidence: low

---

# 8. Target memory operating model

The target should not be “one giant magic memory.”
It should be a disciplined layered system with explicit authority and movement rules.

## 8.1 Target layers

### L0 — file-backed canonical human memory
- curated long-term memory
- daily notes
- artifacts
- handoffs

### L1 — retrieval/index substrate
- PostgreSQL-backed searchable document/chunk layer
- approved-root constrained ingest
- repeatable retrieval and citations

### L2 — typed durable memory objects
- evidence records
- memory notes
- wiki pages
- typed links
- retrieval documents
- session capsules

### L3 — serving and prompt policy layer
- always-on vs on-demand vs forbidden ambient injection
- request-class-sensitive serving
- bounded evidence packs

### L4 — distillation and promotion loop
- raw evidence promoted into durable notes only when justified
- durable notes promoted into wiki/canonical synthesis when mature
- stale or superseded memory is marked and not blindly replayed

### L5 — runtime continuity layer
- thin-main compatible resume behavior
- isolated-run startup based on canonical handoff + targeted retrieval
- no dependence on long transcript replay as default continuity source

---

# 9. Required movement contracts between layers

## Contract A — file truth -> retrieval index
Needed behavior:
- reliable incremental ingest
- explicit approved-root control
- no accidental ingestion sprawl

Current status:
- mostly present

## Contract B — source evidence -> typed evidence records
Needed behavior:
- canonical provenance mapping
- stable evidence identifiers
- direct source traceability

Current status:
- partially present

## Contract C — evidence -> memory note promotion
Needed behavior:
- selective promotion rules
- confidence/status fields
- supersede/stale handling
- proof that promotion is not transcript-noise amplification

Current status:
- not yet fully operationalized

## Contract D — memory note -> wiki page distillation
Needed behavior:
- stable synthesis criteria
- backing refs required
- stale refresh logic

Current status:
- mostly designed, not proven as routine loop

## Contract E — active task/run state -> session capsule
Needed behavior:
- bounded continuity package
- explicit expiry / refresh
- usable resume contract

Current status:
- partially implemented, not fully proven in routine runtime practice

## Contract F — memory layers -> runtime serving
Needed behavior:
- assistant can reliably get the best layer for the question type;
- runtime recall is not split-brain between tool memory and local memory surfaces;
- response shaping respects authority and citations.

Current status:
- not yet fully unified

---

# 10. Main gaps

## Gap 1 — No fully proven closed-loop distillation path
We do not yet have strong evidence that the system continuously and reliably promotes:
- raw/source evidence
- into durable memory notes
- into mature wiki/synthesis objects
- with stable lifecycle management.

## Gap 2 — Runtime recall is not clearly unified with local memory-core
The assistant recall surface and the local pkm-memory contour do not yet behave like one clearly unified system.

## Gap 3 — Session-capsule usage is not yet proven as a standard continuity mechanism
The concept exists, scripts exist, but routine operational use is not yet demonstrated strongly enough.

## Gap 4 — Serving policy across memory layers is still more specified than enforced
The target authority/serving rules are articulated, but the real runtime behavior is not yet obviously governed by them end-to-end.

## Gap 5 — Promotion and stale/supersede lifecycle needs stronger operational proof
We need clearer proof that memory objects can evolve without producing clutter, contradiction, or immortal stale context.

## Gap 6 — Validation exists, but fresh green status is not uniformly consolidated
There are many outputs and verifiers, but the overall “memory health dashboard” is still fragmented.

---

# 11. Task fronts to cut from this spec

The follow-up task set should not be one giant rewrite. It should be sliced into bounded fronts.

## Front 1 — Memory runtime reality map and health check
Goal:
- produce one canonical operational status map for the current memory stack
- consolidate what is green / yellow / unverified

Why first:
- avoids planning from stale assumptions

---

## Front 2 — Evidence -> memory_note promotion path
Goal:
- define and implement the first honest bounded promotion loop
- prove it with verifiers and sample data

Why:
- this is the missing bridge between retrieval substrate and durable memory usefulness

---

## Front 3 — Memory_note -> wiki distillation path
Goal:
- define when notes become stable synthesized topic pages
- prevent premature over-summarization

Why:
- otherwise the upper memory layers remain decorative

---

## Front 4 — Session capsule operationalization
Goal:
- make session capsules a real continuity surface for isolated runs and resumptions
- prove refresh/expiry/use paths

Why:
- memory should support thin-main and bounded execution, not fight them

---

## Front 5 — Unified runtime serving bridge
Goal:
- reduce split-brain between runtime memory tools and local pkm-memory / memory-core surfaces
- define one practical routing/serving bridge for recall

Why:
- otherwise the assistant will keep getting better answers from manual inspection than from the memory system itself

---

## Front 6 — Memory health and regression dashboard
Goal:
- collapse scattered verification outputs into one concise repeatable health view

Why:
- makes memory maintenance and decision-making much easier

---

# 12. Suggested sequencing

## Priority 1
Front 1 — current-state operational health map

## Priority 2
Front 2 — evidence -> memory_note promotion loop

## Priority 3
Front 4 — session capsule operationalization

## Priority 4
Front 5 — unified runtime serving bridge

## Priority 5
Front 3 — memory_note -> wiki distillation

## Priority 6
Front 6 — health/regression dashboard

Reasoning:
- first establish truthful current-state visibility;
- then make durable promotion real;
- then improve continuity;
- then unify serving;
- then mature synthesis;
- then make ongoing verification easier.

---

# 13. Definition of success

This memory stack should be considered materially improved when:
- the current stack can be described from one canonical operational doc;
- ingest/retrieval/status are green and easy to verify;
- at least one real promotion path from evidence to durable memory note is operational;
- session capsules are usable as real continuity objects;
- runtime recall is less split-brain and better aligned with local memory-core assets;
- stale/supersede handling is explicit enough to prevent memory clutter from becoming the new problem.

---

# 14. Canonical reference usage

Use this document when asking for memory improvement planning, gap review, or task cutting.

Suggested shorthand:
- **“Task 409 memory stack improvement spec”**

File path:
- `task-manager/artifacts/task-409-memory-stack-improvement-spec-2026-05-12.md`
