# Memory Core v1

## Goal

Turn the layered-memory direction into a serving-oriented memory core that reduces context bloat.

## Core stance

Memory Core v1 is not a new giant storage engine.
It is the minimal schema and serving contract that lets existing memory surfaces behave like one authority-bounded context engine.

## Key object types

### `source_record`
Describes an approved source root or source family.

### `evidence_record`
Points to raw or near-raw factual evidence such as artifacts, transcripts, logs, handoffs, or notes.

### `retrieval_document`
Represents an indexed retrieval document/chunk set.
Derived authority only.

### `memory_note`
The main compact reusable memory object.
Typical subtypes:
- decision
- pattern
- anti_pattern
- blocker
- durable_ref
- preference
- state_summary

### `wiki_page`
Stable synthesized topic page for repeated or mature knowledge.

## Serving policy

Memory objects should be divided into:
- **always-on** candidates;
- **on-demand** retrieval candidates;
- **forbidden ambient injection** objects.

The system should avoid replaying mixed old context when a small canonical memory object would do.
