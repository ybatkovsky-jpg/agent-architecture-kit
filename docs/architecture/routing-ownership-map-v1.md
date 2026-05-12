# Routing and Ownership Map v1

## Routing principle

The conversational surface is not the same as the execution surface.
Routing should happen early, ownership should be explicit, and durable state should be known before work drifts.

## Lanes

### 1. `main-orchestrator`
Role:
- intake;
- routing;
- human interaction;
- short closure.

### 2. `bounded-execution`
Role:
- isolated implementation, analysis, debugging, validation, or synthesis slices.

### 3. `artifact-production`
Role:
- produce durable outputs such as specs, reports, maps, or packages.

### 4. `human-decision`
Role:
- approvals;
- authority decisions;
- prioritization;
- preference selection.

### 5. `background-observation`
Role:
- monitoring;
- timed observation;
- telemetry sampling;
- event waiting under explicit budget.

## Ownership rule

For every lane, the architecture should make clear:
- who executes;
- who decides;
- where state lives;
- where `DONE` lands;
- where `BLOCKED` escalates.
