# Memory Stack v2

## Core idea

The right move is not one giant memory product.
The right move is a layered memory stack where each memory class has its own authority boundary.

## Recommended layers

1. **Lossless capture layer**
   - raw transcripts;
   - artifacts;
   - logs;
   - execution traces.

2. **Operational retrieval backbone**
   - bounded evidence retrieval;
   - indexed documents/chunks/provenance;
   - lexical-first by default.

3. **Distilled durable memory**
   - decisions;
   - patterns;
   - anti-patterns;
   - blockers;
   - durable references.

4. **Canonical wiki / knowledge layer**
   - stable topic pages;
   - runbooks;
   - architecture summaries.

5. **Graph / semantic augmentation**
   - optional;
   - only after lexical retrieval plateaus.

6. **Agent/session shell**
   - wake-up continuity;
   - episodic local recall;
   - not the global source of truth.

## Main rule

Only the smallest necessary layer should participate in default runtime context.
The rest should be retrieved or referenced on demand.
