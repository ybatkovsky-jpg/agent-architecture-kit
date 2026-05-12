# Evaluation Harness v0.1

## What it provides

A runnable evaluation harness for architecture traces with:
- protected cases;
- sampled cases;
- score reports;
- regression reports.

## Score dimensions

- task success
- constraint compliance
- artifact quality
- tool efficiency
- user fit
- trace clarity

## Fail taxonomy

Examples:
- missing required memory lookup
- unnecessary tool call
- missing requested artifact
- approval bypass

## Important boundary

A harness can be implemented and operational even when the current regression verdict is still non-green.
That means harness readiness is different from promotion readiness.
