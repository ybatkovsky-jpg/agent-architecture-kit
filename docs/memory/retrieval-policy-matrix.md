# Retrieval Policy Matrix

## Purpose

Different request classes should retrieve from different domains with different authority priorities and serving modes.

## Core rule

No transcript-first default behavior.

## Retrieval dimensions

For each request class, define:
- primary domains;
- allowed fallback domains;
- forbidden default domains;
- serving class;
- authority priority focus;
- expected citation shape;
- budget class.

## Why this matters

Without a policy matrix, retrieval becomes noisy and inconsistent.
With a matrix, the system knows:
- where to look first;
- which domains are only fallback;
- what kind of answer envelope should be produced.
