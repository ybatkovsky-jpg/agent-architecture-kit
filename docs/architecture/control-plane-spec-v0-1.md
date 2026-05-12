# Agent Architecture Control Plane Spec v0.1

## Goal

Treat the agent system as a bounded, observable, resumable control plane rather than an endless chat transcript.

The system should:
- keep work bounded and restartable;
- preserve canonical truth outside chat residue;
- separate decision authority, execution authority, and persistence authority;
- expose readable operator surfaces without making them hidden authority layers.

## Layer model

### L1. Human/operator surface
Human-visible intake, approvals, prioritization, review.

### L2. Orchestration surface
Routing, gating, preemption, escalation, lane selection.

### L3. Task control plane
Task lifecycle truth, backlog, sequencing, waiting state.

### L4. Runtime continuity plane
Durable continuation state, resume basis, bounded run metadata.

### L5. Durable knowledge/evidence plane
Artifacts, evidence packs, specs, contracts, proof surfaces.

### L6. Worker plane
Frontier workers, local workers, cheap workers, specialized subagents.

## Truth boundaries

Canonical truth should not live only in chat.
A reasonable chain is:
1. task lifecycle truth;
2. runtime continuity truth;
3. result/evidence truth;
4. human decision truth reflected into canonical state;
5. helper surfaces as readable projections only.

## Architecture rule

No lane should rely on informal transcript memory where a state contract can exist instead.
