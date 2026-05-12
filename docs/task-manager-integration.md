# Task Manager Integration

## Role of the task manager

A task manager is not the whole memory system.
It is a specialized structured layer for operational truth about work.

It should be the primary source of truth for:
- task existence;
- task status;
- active/open/closed state;
- dependencies;
- next-action selection.

## Relationship to memory

Memory and tasks serve different purposes.

- Memory remembers meaning.
- Task state remembers work.
- Artifacts remember detail.

## Correct interaction pattern

### Memory -> Task Manager
Memory can provide:
- why the task matters;
- prior decisions;
- user constraints;
- durable lessons that shape execution.

### Task Manager -> Memory
Task state can provide:
- current operational truth;
- execution status;
- queue visibility;
- closure or blockage signals that deserve distillation.

### Artifact layer <-> both
Artifacts attach deep context, specs, proofs, and handoffs.

## Anti-patterns

- artifact exists but no real task record exists;
- memory says a task exists but the task registry does not;
- raw discussion is treated as task truth;
- task status is inferred from vibes instead of the registry.
