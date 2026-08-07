# Evaluation results

## Current conclusion

The current instruction-level skill passed a fresh suite 1.1 affected-surface
regression after the PDL compatibility profile was rewritten for MIT release.
It passed both previously residual cases and all selected adjacent cases:

```text
A06  6/6  PASS
A14  8/8  PASS
Adjacent affected surface  13/13 PASS
Total  15/15 cases, 23 turns
```

There were no critical failures, semantic case failures, candidate errors,
structural-lint failures, or unresolved judge errors. The applicable-dimension
score was 109/110; B08 lost one prompt-fidelity point but passed. A14 required
one retained strict-format judge retry. This is targeted evidence and is not a
new post-change 40/40 claim.

The current run's artifact-related dimension totals were:

| Dimension | Applicable score |
|---|---:|
| PDL quality | 30/30 |
| Prompt fidelity | 29/30 |
| State correctness | 30/30 |
| Plan minimality | 12/12 |
| Control/data separation | 6/6 |
| State reset/continuation | 2/2 |
| Correction handling | 0/0 (not exercised) |
| Semantic/plan boundary | 0/0 (not exercised) |
| **Total** | **109/110** |

These results support the tested claims about structured readability, semantic
capture, sequential gating, and non-anchoring plans. They do not measure token
efficiency, latency, or human learning and correction time.

## Evidence generations

| Generation | Suite | Candidate / judge | Scope | Result | Interpretation |
|---|---|---|---|---|---|
| Harness v1 | 1.0 | Sol/medium / Luna/high | Complete 40 cases | 40/40 under the historical rubric | Initial validation; weaker provenance and not the current skill bytes |
| Harness v2 | 1.0 | Sol/medium / Luna/high | Complete 40 cases, 82 turns | 38/40, 0 critical, release gate PASS | Provenance-bound full-suite baseline; A06 and A14 were noncritical failures |
| Harness v2 | 1.1 | Sol/medium / Luna/high | A06, A14, and 13 adjacent cases | 15/15, 0 critical | Pre-release profile affected-surface regression |
| Harness v2 | 1.1 | Sol/medium / Luna/high | Same 15 cases, 23 turns | 15/15, 109/110 applicable points, 0 critical | Current MIT-ready profile refresh |

The current tested skill directory digest is:

```text
d831ebde6e357e10318112c76cbaa8404dc0d5a8cb67eb73c4257f0d7bf6eb5e
```

Suite 1.1 keeps the same 40 case IDs and intentionally changes A14 so plan
completeness is relative to the confirmed request; unrequested remediation is
not required.

## What A06 and A14 established

### A06: task semantics versus current-protocol control

The updated skill excludes an instruction whose only effect is to alter or skip
the active confirmation protocol. The same words remain semantic when the user
asks to quote, analyze, transform, or discuss them as task content.

### A14: coverage before minimality

The updated skill first ensures that every confirmed material requirement is
covered, then removes unnecessary procedural commitment. The resulting
debugging plan reached an evidence-supported diagnosis without selecting a
cause before logs were available.

## Adjacent regression surface

The 13 adjacent cases covered:

- protocol-control words used as quoted data;
- embedded prompt injection;
- requests to collapse stages;
- recommendation and creative-writing plan poisoning;
- vacuous and over-specified plans;
- prompt specificity and non-invention;
- quoted pseudocode as source material;
- deferred execution inputs;
- explicit use of the protocol for a meta-task.

All passed in the current refresh. B08 received a one-point prompt-fidelity
deduction because its Prompt Pseudocode identified the required figures but did
not explicitly preserve that they would arrive after confirmation; its
execution-dependency continuation remained correct. A14's first judge response
was rejected for strict-format inconsistency, retained for audit, and followed
by a valid 8/8 judgment.

The selected IDs, per-case scores, judge-attempt counts, and all dimension
totals are published in the
[current targeted-run score ledger](current-targeted-run.md).

## Public claim boundary

It is accurate to say:

> The project maintains a 40-case adversarial protocol suite, completed a
> provenance-bound full-suite Harness v2 baseline, and passed all 15 selected
> suite 1.1 affected-surface regressions on the current skill.

Do not claim that the current skill passed a fresh 40/40 suite unless a complete
run is performed against the exact current digest.
