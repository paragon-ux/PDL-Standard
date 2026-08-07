# Evaluation methodology

## What is evaluated

The harness evaluates the instruction-level `confirm-with-pseudocode` protocol:
state transitions, semantic fidelity, control/data separation, correction
handling, plan minimality, and PDL artifact quality. It does not evaluate the
future host controller or the factual quality of arbitrary final answers.

The frozen suite contains 40 cases:

| Tier | Cases | Purpose |
|---|---:|---|
| Gating | 10 | Required state-machine behavior |
| Adversarial | 20 | Injection, ambiguity, bypass, poisoning, and interruption risks |
| Boundary/Diagnostic | 10 | Difficult semantic-versus-approach and continuation boundaries |

The current machine-readable definitions and human-readable cases are in the
[frozen harness](../../tests/harness/). Suite identity is pinned by
[`suite.lock.json`](../../tests/harness/suite.lock.json).

## Harness generations

### Harness v1

The original runner established behavioral coverage and cross-model scoring,
but it did not cryptographically bind the candidate transcript to an installed
skill directory or retain complete tool-activity evidence. Its results remain
historical rather than current release proof.

### Harness v2

Harness v2 adds:

- source-to-installed skill byte verification;
- candidate and judge provenance manifests;
- sanitized event and tool-activity capture;
- commentary-aware semantic judging;
- strict, fail-closed judge parsing with retained retries;
- applicable-dimension scoring;
- suite locks, preflight checks, and synthetic self-tests.

Each case starts in a fresh candidate conversation. Multi-turn cases resume
only their own conversation. The runner sends the candidate exactly the user
turn from `cases.jsonl`; expected stages and pass criteria remain outside the
candidate prompt.

## Model separation

The recorded Harness v2 runs use `gpt-5.6-sol` at medium reasoning as the
candidate and `gpt-5.6-luna` at high reasoning as an independent automated
judge. Cross-model judging reduces direct self-grading, but it is still model
evaluation rather than independent human adjudication.

## Evidence rules

- Report complete-suite and targeted runs separately.
- Bind claims to the tested skill digest and suite hash.
- Treat unresolved candidate or judge infrastructure errors as failures.
- Preserve rejected judge attempts instead of overwriting them.
- Let critical failures override aggregate scores.
- Do not combine iterative runs as statistically independent samples.
- Use human review for consequential or borderline semantic judgments.

Raw internal transcripts are retained in the external evidence archive rather
than included in the public repository. The public tree contains the frozen
suite, reproducible runners, schemas, hashes, methodology, and scoped summaries.

The current MIT-ready runtime profile was checked with the same 15-case
affected-surface set used for the preceding suite 1.1 regression. The candidate
and judge artifacts remain in the external Harness v2 evidence archive under
run ID `sol-medium-mit-profile-v1`.

For that run, applicable-dimension totals were 30/30 for PDL quality, 29/30 for
prompt fidelity, 30/30 for state correctness, and 12/12 for plan minimality.
The remaining applicable dimensions were 6/6 for control/data separation and
2/2 for state reset/continuation, producing the reported total of 109/110.
Correction handling and the semantic/plan boundary were not exercised by the
selected cases and therefore contributed 0/0 rather than automatic credit.
These dimensions test whether artifacts are readable, faithful, correctly
staged, and meaningfully minimal. They are not measurements of token cost,
latency, human comprehension time, or productivity. The relationship between
the PDL design rationale and the tested behaviors is documented in the
[PDL evidence map](../architecture/pdl-rationale.md), and the complete
arithmetic is published in the
[current targeted-run ledger](current-targeted-run.md).

## Limitations

- Suite 1.1 has an affected-surface regression for the current skill, not a new
  complete 40-case run.
- Only the recorded model configurations were tested.
- Platform or model updates can change behavior.
- Automated judging can be inconsistent; the harness catches mechanical
  contradictions but cannot eliminate semantic variance.
- Final-answer factual accuracy is outside this protocol suite.
