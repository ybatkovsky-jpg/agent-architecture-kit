# Evaluation and Regression Discipline

## Why this matters

Many agent systems improve by intuition and degrade by surprise.
A real architecture needs measurable feedback.

## Key concepts

### Protected cases
Reference scenarios that must not regress below threshold.

### Comparable coverage
A way to compare behavior across equivalent or near-equivalent scenarios.

### Dataset delta checks
A check that new dataset additions or changes did not silently distort the benchmark.

### Promotion gate
A release or adoption threshold that architecture changes must satisfy.

### Reachability realism
If the required score is mathematically unreachable on the sampled dataset, the answer is not endless tuning. The contract or dataset must be recalibrated.

## What to measure

- task success
- memory recall accuracy
- conflict resolution quality
- false-memory rate
- regression count
- protected-case pass rate
- abstention quality when evidence is insufficient

## Bottom line

If a contour matters, it should be testable.
If it is not testable, it is still just a belief.
