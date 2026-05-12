# Truth Boundary Contract

## Core rule

If a worker, helper surface, or operator output cannot point to the correct authority layer, the claim is not complete.

## Truth classes

### Lifecycle truth
Canonical authority:
- task state/events

### Continuation truth
Canonical authority:
- runtime continuation state / resume basis

### Result truth
Canonical authority:
- durable artifacts and evidence files

### Human decision truth
Canonical authority:
- explicit human decision reflected into canonical state

### Legibility truth
Projection only.
Useful to read, never enough by itself.

## Mapping rule

Every operationally important statement should map back to exactly one canonical authority class.
If a helper surface shows state from another layer, it must behave as a projection and include the canonical reference.
