# Failure Modes and Hardening

## Executive lesson

A system can produce a plausible answer envelope while grounding on the wrong evidence underneath.
That is a real failure, not a cosmetic one.

## Major failure families observed

1. **Classifier misses natural phrasing**
   - especially multilingual operator phrasing.

2. **Meta-artifact self-hit contamination**
   - evaluation/meta docs outrank the underlying domain evidence.

3. **Continuation freshness drift**
   - resume queries fail to prefer the immediate predecessor state strongly enough.

4. **Audit envelope with wrong proving files**
   - correct-looking trace output points to the wrong artifacts.

5. **Preference recall not anchored tightly enough**
   - retrieval wanders across adjacent notes instead of targeting durable preference memory.

## Hardening rule

Fix upstream selection and routing first.
Do not confuse better explanation of wrong candidates with a real fix.
