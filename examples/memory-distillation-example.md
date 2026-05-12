# Memory distillation example

Raw discussion:
- long conversation about whether the main chat should host heavy execution
- several examples where context got bloated
- final agreement that bounded work should move into isolated execution

Distilled memory:
- Main should remain a thin orchestration surface.
- Heavy bounded execution should be routed into isolated execution lanes.

Why this is good:
- future sessions do not need the full transcript;
- the reusable decision survives;
- the execution policy becomes portable.
