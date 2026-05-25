# Bootstrap Contour for New Agents

## Purpose

This document defines a reusable bootstrap context architecture for **newly created agents and fresh workspaces**.

Goal: avoid heavy flat startup injection and replace it with a layered model:

- thin static bootstrap
- routing manifest
- compact domain capsules
- selective dynamic loading
- deep context only on demand

This contour is intentionally **generic**. It is not tied to one specific main workspace or one specific user's local files.

---

## Design Principles

1. **Thin by default**
   - Startup should include only the minimum needed to orient the agent.

2. **Route, don’t dump**
   - Bootstrap should tell the agent where relevant context lives, not preload everything.

3. **Scope-aware loading**
   - Private, group, project, and task context should load only when appropriate.

4. **Freshness over duplication**
   - Dynamic context should come from current source-of-truth layers, not stale copied markdown.

5. **Evidence-friendly**
   - It should be clear why some context was loaded and why other context was not.

6. **Workspace-agnostic**
   - The architecture must apply to any new agent workspace, not only a single home repo.

---

## Layer Model

### Layer 1 — Static Bootstrap
Small, stable, directly injected context:
- agent identity / role
- behavior rules
- user or owner preferences
- privacy and scope rules
- memory policy
- workspace conventions

### Layer 2 — Bootstrap Routing Manifest
A structured registry telling the agent:
- which context domains exist
- where each domain’s source-of-truth lives
- when it should load
- whether it is always / conditional / on-demand
- scope and privacy boundaries

### Layer 3 — Domain Capsules
Compact current-state summaries for major domains.
Examples:
- active projects
- active tasks
- memory architecture
- current execution map
- topic map
- current architecture state

Capsules should be:
- short
- non-historical
- current-state oriented
- linked to deeper sources

### Layer 4 — Deep Context
Long-form and archival sources:
- historical notes
- raw transcripts
- large docs
- artifacts
- handoffs
- old project trails

This layer should be read only when needed.

---

## Recommended Bootstrap Contract for a New Agent

### Always include
- identity / persona
- behavior rules
- privacy and scope rules
- memory access policy
- bootstrap routing manifest
- task or mission objective for this run

### Conditionally include
- one or more domain capsules when the spawning context already implies a domain
- short curated memory excerpt when the scope allows it
- active task or active project summary when directly relevant

### Must not include by default
- full chat history
- long daily logs
- large project histories
- entire handoff chains
- full artifact collections
- large documentation sets
- broad private memory excerpts unrelated to the task

---

## Selective Loading Flow

1. **Bootstrap load**
   - Load static bootstrap + manifest.

2. **Context classification**
   - Determine workspace type, task domain, privacy scope, and execution mode.

3. **Domain selection**
   - Select only the relevant context domains.

4. **Capsule fetch**
   - Load compact current-state capsules.

5. **Deep fetch on demand**
   - Read artifacts, historical memory, docs, or raw logs only if required.

---

## Why This Matters for New Agents

Fresh agents are the easiest place to enforce clean bootstrap behavior because:
- there is no long main-session tail to inherit
- bounded work naturally benefits from bounded context
- startup cost is easier to measure
- context drift becomes easier to detect

A clean bootstrap contour for new agents also becomes the safest proving ground before retrofitting legacy or main-session startup flows.

---

## Acceptance Criteria

A new-agent bootstrap contour is acceptable when:
- startup context is small and predictable
- heavy history is not injected by default
- relevant context is still discoverable via manifest + capsules
- scope and privacy boundaries are explicit
- dynamic context is fetched from source-of-truth layers
- deep context remains available but on-demand

---

## Practical Rollout Order

1. Define bootstrap manifest schema
2. Define first capsule schema set
3. Audit startup payload of a fresh agent run
4. Map observed payload into keep / conditional / on-demand
5. Add domain loaders
6. Measure token and relevance improvements
