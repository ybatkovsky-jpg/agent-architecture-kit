# OpenClaw Memory Runtime Audit — live deployed contour — 2026-05-13

## Executive summary

**Final verdict:** the live deployed memory system is a **hybrid PostgreSQL-backed lexical retrieval system with a partially active typed Memory Core overlay**, plus a file-backed markdown memory source and task-manager artifacts/handoffs as the primary durable knowledge roots.

It is **not** a simple `MEMORY.md`-only design, and it is **not yet** a fully unified typed-memory platform.

### Short version
- **Verified:** live runtime uses PostgreSQL (`pkm_memory`) as the retrieval backbone for ingested documents/chunks and stores a small but real set of typed `mc_*` objects.
- **Verified:** retrieval behavior is driven by a custom classifier + source-routing + authority-ranking pipeline in `pkm-memory/retrieve_memory.py`, with request-class-specific rules.
- **Verified:** enabled ingestion roots are currently only `memory/`, `task-manager/artifacts/`, and `task-manager/handoffs/`.
- **Verified:** the read path is mostly **lexical / heuristic / policy-routed**, not vector-based.
- **Verified:** no evidence of pgvector/embedding runtime usage was found; search uses `tsvector`, `plainto_tsquery`, `ts_rank_cd`, and trigram similarity.
- **Verified:** cron/background infrastructure exists in OpenClaw, but no active periodic memory-refresh loop dedicated to this memory stack was proven from the live contour.
- **Risk:** architectural maturity is uneven: storage/schema thinking is ahead of runtime observability and ahead of a clean typed-object-first retrieval path.

### One-sentence diagnosis
> The deployed contour is a **policy-routed hybrid memory architecture with PostgreSQL lexical retrieval, source-registry ingestion, and lightly populated typed Memory Core tables, but without full runtime observability or a clearly dominant typed retrieval plane**.

---

## Scope and method

This audit focused on **actual deployed runtime behavior** in `/home/openclaw/.openclaw/workspace`, using bounded live inspection of:
- running processes
- workspace/runtime config
- PostgreSQL schema and live table contents
- memory-related code paths
- retrieval outputs and saved artifacts
- cron/background job state
- local OpenClaw state folders

No destructive actions were taken.

---

## Verified findings vs hypotheses

## Verified findings

1. **PostgreSQL is live and is the main structured retrieval store.**  
   Evidence:
   - running process: `/usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/16/main ...`
   - `pkm-memory/config/memory.env` points retrieval tooling to `PGDATABASE=pkm_memory`
   - live tables include `documents`, `chunks`, `sources`, `ingestion_runs`, and many `mc_*` tables.

2. **Retrieval is lexical, not vector.**  
   Evidence:
   - DB columns found: `documents.search_vector`, `chunks.search_vector` (`tsvector`)
   - indexes found: GIN over `search_vector`, trigram indexes over `title`, `path`, `section_path`
   - `retrieve_memory.py` uses `plainto_tsquery('simple', ...)`, `ts_rank_cd(...)`, and `similarity(...)`
   - no embedding/vector columns or pgvector extension use were found.

3. **There is a seeded source registry controlling ingest/retrieval scope.**  
   Evidence:
   - `pkm-memory/config/source_registry.seed.yaml`
   - live `sources` table contains exactly the enabled roots:
     - `memory`
     - `task-manager/artifacts`
     - `task-manager/handoffs`

4. **The lexical corpus is materially populated.**  
   Evidence:
   - live counts observed earlier: `documents=700`, `chunks=21240`
   - by source:
     - `memory`: 97 documents
     - `task-manager/artifacts`: 489 documents
     - `task-manager/handoffs`: 114 documents

5. **The typed Memory Core layer is real and partially populated.**  
   Evidence:
   - live tables: `mc_source_records`, `mc_evidence_records`, `mc_memory_notes`, `mc_retrieval_documents`, `mc_session_capsules`, `mc_typed_links`, relation tables
   - observed counts earlier:
     - `mc_source_records=2`
     - `mc_evidence_records=4`
     - `mc_memory_notes=2`
     - `mc_retrieval_documents=3`
     - `mc_session_capsules=1`
     - `mc_typed_links=6`
   - example live records:
     - retrieval docs for tasks `347`, `353`, `371`
     - memory notes including `mem_sample_registry_note` and `mem_task351_decision_write_path`
     - one active session capsule `sess_task351_active_run`

6. **Typed write surfaces exist, but appear to be narrow/curated rather than universal runtime defaults.**  
   Evidence:
   - `memory_core_registry.py`
   - `memory_core_decisions_sessions.py`
   - `memory_core_task_metadata.py`
   - `memory_core_session_capsule_distiller.py`
   These scripts build/persist typed objects via SQL/psql pipelines.

7. **Retrieval behavior is request-class-sensitive and source-routed.**  
   Evidence:
   - `retrieve_memory.py` has explicit request classes such as:
     - `current_task_execution`
     - `resume_reopen_continuation`
     - `architecture_design_recall`
     - `meta_evaluation_recall`
     - `policy_decision_lookup`
     - `preference_operating_style_recall`
   - `route_sources()` excludes `task_manager_handoffs` for architecture/meta recall lanes and favors it for continuation lanes.

8. **The runtime retrieval path is hybrid: DB-first with local file fallback.**  
   Evidence:
   - `retrieve()` chooses `retrieve_psql()` in `auto`/`psql` mode, with fallback to `retrieve_local()` on exception.
   - `retrieve_local()` walks files directly under selected source roots.

9. **Authority shaping and result synthesis are done in application logic, not purely in SQL or schema.**  
   Evidence:
   - retrieval artifacts show `authority.layer`, `focus_order`, `citation_policy`, `conflicts`, `open_questions`
   - `retrieve_memory.py` contains logic such as `synthesize_conflicts_open_questions(...)`, budget shaping, lane routing, diversity logic, and continuation/meta heuristics.

10. **OpenClaw runtime still carries a separate markdown memory surface outside the PostgreSQL backbone.**  
    Evidence:
    - workspace contains `MEMORY.md`
    - workspace contains many files under `memory/`
    - registry includes `memory/` as `openclaw_shared_memory`

11. **Cron infrastructure exists, but no dedicated always-on memory refresh/maintenance daemon was proven.**  
    Evidence:
    - process list includes `/usr/sbin/cron -f -P`
    - `.openclaw/cron/jobs.json` contains several jobs, mainly content-system and handoff/watchdog related
    - no explicit recurring job was found for periodic `pkm-memory` ingest or memory distillation.

12. **Latest proven ingestion activity is stale relative to audit time.**  
    Evidence:
    - latest `ingestion_runs` for all three enabled roots are around `2026-05-10 01:38 UTC`
    - audit time is `2026-05-13 15:04 UTC`
    - therefore current corpus freshness depends on whether source files changed since then.

## Hypotheses / not fully proven

1. **Main-agent tool-level `memory_search` / `memory_get` likely bridges into this same memory contour, but the exact runtime call chain was not fully proven end-to-end.**  
   Reason: OpenClaw codebase search produced many relevant references and traces, but a single definitive live bridge from tool invocation to `retrieve_memory.py` was not fully reconstructed in this audit.

2. **Typed Memory Core is likely intended to become the canonical serving layer, but today it looks more like a partial overlay on top of the lexical corpus.**  
   Reason: schema + scripts + artifacts clearly point that way, but live population is sparse relative to 700/21240 lexical corpus scale.

3. **Some retrieval artifacts and authority behaviors may reflect offline/verification runs more than routine user-turn runtime.**  
   Reason: many outputs under `pkm-memory/outputs/` are clearly evaluation/regression artifacts.

4. **Gateway/runtime instability may indirectly reduce memory observability or background upkeep.**  
   Reason: `openclaw gateway status` hung in this contour, but the exact impact on memory stack behavior was not isolated here.

---

## Runtime architecture map

```text
User / agent request
  -> OpenClaw agent/tool layer
    -> memory-oriented request path (partially proven bridge)
      -> pkm-memory/retrieve_memory.py
        -> classify_request(query)
        -> select_sources(registry)
        -> route_sources(by request class / authority intent)
        -> retrieve_psql(...) [primary]
            -> PostgreSQL pkm_memory
               - sources
               - documents
               - chunks
               - ingestion_runs
               - mc_* typed tables
        -> retrieve_local(...) [fallback]
            -> walk source-root files directly
        -> authority / conflict / citation shaping
        -> bounded evidence pack JSON
  -> agent answer/context assembly
```

### Data inflow side

```text
Workspace files
  - MEMORY.md
  - memory/*.md
  - task-manager/artifacts/*.md
  - task-manager/handoffs/*.md
    -> pkm-memory/ingest_sources.py
       -> documents/chunks/sources/ingestion_runs in PostgreSQL

Curated typed payloads
  - decisions/session payload JSON
  - task-manager task snapshots
    -> memory_core_decisions_sessions.py
    -> memory_core_task_metadata.py
    -> memory_core_session_capsule_distiller.py
       -> mc_* typed tables in PostgreSQL
```

---

## Component breakdown

## 1) File-backed human-readable memory surface

### Components
- `MEMORY.md`
- `memory/` folder with many dated markdown files
- `wiki/` tree present in workspace, but not proven as an enabled live ingestion root in current seed registry

### Runtime role
- provides durable operator/user preference memory and session/history notes
- also acts as raw source material for ingestion into lexical retrieval tables

### Assessment
- **Verified active as a source root** via registry (`memory` enabled)
- **Not equivalent to the full memory architecture**; it is only one source domain.

## 2) Lexical PostgreSQL retrieval backbone

### Components
- `documents`
- `chunks`
- `sources`
- `ingestion_runs`
- `document_links`
- `entities`

### Runtime role
- stores canonical ingested documents and chunked searchable text
- supports retrieval through full-text and trigram similarity ranking
- likely forms the dominant recall plane for most current retrieval requests

### Assessment
- **Verified primary live retrieval substrate**
- simpler and more mature operationally than the typed overlay

## 3) Typed Memory Core overlay

### Components
- `mc_source_records`
- `mc_evidence_records`
- `mc_memory_notes`
- `mc_retrieval_documents`
- `mc_session_capsules`
- `mc_typed_links`
- related backing/ref tables

### Runtime role
- models higher-order objects such as decisions, evidence, retrieval docs, session capsules, wiki pages
- intended to support authority-aware recall and cleaner semantic serving

### Assessment
- **Verified present and populated, but lightly populated**
- currently looks like a selective augmentation layer, not the main full-corpus store

## 4) Retrieval orchestration layer

### Main file
- `pkm-memory/retrieve_memory.py`

### Runtime role
- classifies query intent
- chooses source domains by lane
- runs DB retrieval or local fallback
- enforces bounded result budget
- shapes authority, conflict, citation, and evidence envelope

### Assessment
- this is the real operational “brain” of memory serving in the inspected contour
- substantial logic is concentrated here, which is powerful but risky for maintainability

## 5) Ingestion/update layer

### Main file
- `pkm-memory/ingest_sources.py`

### Runtime role
- walks source roots
- chunks and hashes files
- writes SQL / persists to PostgreSQL
- tracks ingestion runs

### Assessment
- **Verified practical ingest path**
- freshness depends on how often it is actually invoked; recurring automation was not proven

## 6) Background/cron layer

### Observed
- `.openclaw/cron/jobs.json`
- many run logs under `.openclaw/cron/runs/`
- jobs mostly for analyst/weekly workflows and handoff/watchdog flows

### Assessment
- general automation substrate exists
- memory-specific maintenance automation is weakly evidenced

---

## Memory lifecycle analysis

## A. Authoring / source creation

### Verified sources currently in play
1. `memory/`
2. `task-manager/artifacts/`
3. `task-manager/handoffs/`

These hold human-authored or workflow-authored markdown artifacts.

## B. Ingestion into lexical store

`ingest_sources.py`:
- loads registry
- scans enabled roots
- builds document records
- computes content/chunk hashes
- upserts into `sources`, `documents`, `chunks`
- records run metadata in `ingestion_runs`

### Verified characteristics
- incremental-ish behavior based on content hashes
- can persist via psql
- source IDs are stable and derived from source keys

## C. Typed-object distillation / writeback

Separate scripts can create typed Memory Core objects from curated inputs:
- decisions + session capsules
- task metadata snapshots
- session capsule distillation

### Verified characteristics
- typed IDs and prefix validation exist
- relation tables link memory notes to evidence/source refs
- session capsules can point to handoff artifacts

### Lifecycle status
- this looks **manual or task-driven**, not ubiquitous/automatic.

## D. Retrieval / serving

At query time:
1. query classified into a request lane
2. allowed/primary/fallback source domains chosen
3. retrieval performed from PostgreSQL or local file fallback
4. top candidates reranked and shaped into a bounded evidence pack
5. authority/conflict/citation metadata added

### Important runtime implication
The system is not retrieving “memory” as one flat pool. It retrieves from **policy-scoped subsets** of sources with different authority assumptions.

## E. Freshness / decay / supersession

### Verified
- typed tables include status/supersession/expiry fields (`expires_at`, `superseded_by`, etc.)
- lexical tables track `ingested_at` and `is_deleted`

### Not fully proven
- regular operational policies that enforce expiry/supersession at runtime
- an always-on compactor/distiller for typed memory hygiene

---

## Retrieval pipeline analysis

## 1) Query classification

`retrieve_memory.py` defines request classes with distinct policies, including:
- continuation/resume
- architecture/design recall
- meta evaluation recall
- policy decision lookup
- preference/style recall
- factual lookup

### Why this matters
This means retrieval behavior depends heavily on **query interpretation**, not just search terms.

## 2) Source selection and lane routing

The registry is filtered to enabled roots, then `route_sources()` applies lane rules.

### Verified examples
- continuation lane prioritizes handoffs/task state
- architecture/meta lanes exclude `task_manager_handoffs`
- `memory/` is associated with `memory_note`, `wiki_page`, preference/task-scoped note domains
- `task-manager/artifacts` maps to evidence/task-state/wiki-like roles
- `task-manager/handoffs` maps to canonical handoff/fresh task state

## 3) Search mechanics

### Verified DB retrieval signals
- full-text ranking: `ts_rank_cd`
- full-text query generation: `plainto_tsquery('simple', ...)`
- string similarity: `similarity(...)`
- path/title/section heuristics
- exact/substr/slug/path matching
- token overlap counting

### Interpretation
This is a **strong lexical retrieval engine with hand-built ranking logic**, not semantic vector search.

## 4) Fallback mode

If DB retrieval fails, local-file retrieval is used.

### Strength
- resilience if DB path breaks

### Weakness
- possible parity drift between DB and local behavior
- more heuristic branching to maintain twice

## 5) Authority and synthesis

Retrieval outputs include:
- authority layer
- focus order
- citation policy
- conflict synthesis
- open questions
- bounded evidence count

### Interpretation
The runtime is attempting to go beyond search into **serving discipline**. That is a strength. But much of that discipline is encoded in one large orchestration file rather than cleanly distributed through simpler components.

---

## Problems / risks

## 1) Typed layer underpopulation vs lexical dominance

### Verified fact
- lexical store is large: 700 docs / 21240 chunks
- typed layer is sparse: only a handful of memory notes/retrieval docs/session capsules

### Risk
The architecture may present as “Memory Core” conceptually, while real runtime answers still depend mostly on lexical artifact retrieval.

## 2) Retrieval logic concentration

### Verified fact
- `retrieve_memory.py` is very large (~191 KB) and contains classification, routing, SQL generation, fallback logic, ranking, conflict synthesis, and output shaping.

### Risk
This is a maintainability and regression risk. It increases hidden coupling and makes runtime reasoning harder.

## 3) Freshness gap

### Verified fact
- last observed ingestion runs were on 2026-05-10, several days before this audit.

### Risk
If source files changed after that time, DB-backed retrieval may lag reality unless explicit reingestion was run.

## 4) No vector/semantic layer

### Verified fact
- no embeddings/vector columns/extensions were found.

### Risk
Lexical retrieval can be brittle for paraphrase-heavy recall, multilingual ambiguity, and concept-level matching unless compensated by handcrafted heuristics.

## 5) Dual path drift: DB vs local fallback

### Verified fact
- runtime supports both `retrieve_psql()` and `retrieve_local()`.

### Risk
Different code paths can diverge in ranking, filters, or authority behavior, especially over time.

## 6) Incomplete runtime observability

### Verified fact
- gateway status command hung in this contour
- exact end-to-end bridge from user-turn memory tool call to retrieval script was not fully reconstructed from runtime alone

### Risk
Harder to diagnose “why did memory answer X?” in production.

## 7) Background memory upkeep appears weakly automated

### Verified fact
- no explicit active recurring memory maintenance job was identified.

### Risk
The memory system may rely on manual/task-specific upkeep rather than dependable routine refresh.

---

## Target architecture proposal

## Goal
Move from:
> hybrid lexical-first memory with typed overlay and heavy read-path heuristics

to:
> typed-memory-first serving architecture with lexical evidence substrate and explicit runtime observability.

## Proposed target shape

### 1) Keep PostgreSQL as the core backing store
Why:
- already live
- already populated
- already operationally useful
- supports lexical evidence well

### 2) Treat lexical `documents/chunks` as evidence substrate, not the final semantic layer
Meaning:
- keep chunk/doc search for recall and citation
- but prefer serving through typed objects when available

### 3) Promote typed Memory Core to first-class serving plane
Specifically:
- expand `mc_memory_notes`, `mc_evidence_records`, `mc_retrieval_documents`, `mc_session_capsules`
- add clearer ingestion/distillation policies from handoffs, artifacts, and durable notes
- ensure more routine writeback into typed tables

### 4) Separate retrieval stages into narrower modules
Recommended split:
- classifier
- source router
- lexical candidate fetcher
- typed candidate fetcher
- authority resolver
- citation/conflict synthesizer
- final answer/context pack assembler

### 5) Add explicit freshness policy
Recommended:
- scheduled reingestion for enabled roots
- visible staleness metadata in retrieval output
- freshness warnings when source files are newer than indexed copies

### 6) Add runtime traceability
Every memory response should ideally expose a compact trace containing:
- selected lane
- selected sources
- DB vs local path used
- top candidates before/after authority rerank
- suppression reasons
- freshness timestamps

### 7) Only add vectors if lexical failure data justifies it
Because current contour already has sophisticated lexical ranking, vector search should be added only if measured recall gaps remain after freshness + typed-first improvements.

---

## Confidence / uncertainty

## High confidence
- PostgreSQL-backed lexical retrieval is live and primary
- enabled source roots are exactly the three observed in registry and DB
- typed `mc_*` schema is live and partially populated
- retrieval is lexical/heuristic, not vector-based
- retrieval path is lane-aware and source-routed

## Medium confidence
- typed Memory Core is strategically important but operationally secondary today
- lack of recurring memory jobs probably means freshness is manually/task-driven

## Lower confidence / unresolved
- exact production bridge from OpenClaw tool invocation to retrieval script for every agent turn
- how much typed-object retrieval influences normal operator answers vs evaluation/test flows
- whether any external/private compiled-wiki supplement path is active outside inspected roots

---

## Final verdict

### Bottom line
The live deployed OpenClaw memory architecture is **real, custom, and more advanced than a markdown-memory hack**, but it is still **transitional**.

### Precise verdict
> **Verified production contour: PostgreSQL-backed lexical memory with seeded source registry, bounded lane-aware retrieval orchestration, and a partially active typed Memory Core overlay.**

### Readiness judgment
- **Useful now:** yes
- **Architecturally coherent:** mostly yes
- **Fully clean / unified / observable:** no
- **Biggest gap:** typed-memory serving maturity and runtime observability, not raw storage capability

### Recommendation
Do **not** replace this stack wholesale.  
Instead:
1. keep PostgreSQL lexical backbone,
2. strengthen automatic freshness,
3. promote typed Memory Core write/read usage,
4. break up retrieval orchestration into clearer modules,
5. add end-to-end runtime tracing.

That path preserves what is already working while reducing the current hybrid/heuristic fragility.

---

## Evidence appendix

### Key files inspected
- `pkm-memory/config/memory.env`
- `pkm-memory/config/source_registry.seed.yaml`
- `pkm-memory/retrieve_memory.py`
- `pkm-memory/ingest_sources.py`
- `pkm-memory/memory_core_registry.py`
- `pkm-memory/memory_core_decisions_sessions.py`
- `pkm-memory/memory_core_task_metadata.py`
- `pkm-memory/memory_core_session_capsule_distiller.py`
- `MEMORY.md`
- `.openclaw/openclaw.json`
- `.openclaw/cron/jobs.json`

### Key live runtime evidence
- postgres process running
- cron process running
- enabled source roots in DB match seed registry
- ingestion runs recorded in DB
- typed Memory Core rows present in DB
- FTS/trigram indexes present; no vector columns found

### Existing related audit material
- `docs/MEMORY_RUNTIME_AUDIT_PRELIM_2026-05-13.md`
- `docs/MEMORY_RUNTIME_AUDIT_PASS2_2026-05-13.md`
