# Architecture Overview

## Purpose

This repository captures reusable architecture contours for agent systems that need durable state, bounded execution, and regression discipline.

The main idea is simple:

- keep the conversational surface thin;
- route real work into explicit execution paths;
- preserve only useful memory;
- separate memory from task state;
- evaluate architecture changes as a real system rather than vibes.

---

## Main contours

### 1. Memory contour
Memory is selective continuity, not transcript dumping.

Durable memory should keep:
- decisions;
- patterns;
- anti-patterns;
- blockers with reuse value;
- stable references.

### 2. Task-state contour
Task state is a specialized structured memory layer.

It should answer:
- what work exists;
- what is active;
- what is blocked;
- what depends on what;
- what is next.

### 3. Artifact contour
Artifacts hold detail that is too large or too nuanced for memory summaries.

Examples:
- specs;
- handoffs;
- worked examples;
- implementation notes.

### 4. Execution contour
Main is an orchestration surface.
Heavy or bounded work should move into explicit execution lanes.

### 5. Evaluation contour
Architecture quality is measured through:
- protected cases;
- regression checks;
- comparable coverage;
- contract realism;
- promotion gate discipline.

---

## One-sentence model

**Memory remembers meaning. Task state remembers work. Artifacts remember detail. Evaluation remembers whether the architecture is actually getting better.**
