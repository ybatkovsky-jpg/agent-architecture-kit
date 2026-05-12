# Current State and Next Steps

## Current strengths

The architecture already has:
- a thin-main stance;
- explicit execution lanes;
- a small handoff vocabulary;
- bounded retry discipline;
- memory distillation as a first-class concern;
- a named isolated continuation pattern.

## Current limitations

Still under-specified:
- exact runtime mapping into the host system;
- full binding of isolated continuation primitives;
- canonical storage surface mapping;
- chained continuation recovery;
- deeper end-to-end implementation coverage.

## Next practical moves

1. Formal implementation mapping
2. Stronger runtime binding for isolated continuation
3. Canonical storage/anchor policy
4. Broader regression and evaluation coverage
5. Expansion of reference Python implementation
