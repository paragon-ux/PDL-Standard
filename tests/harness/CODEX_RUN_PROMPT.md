# Suggested Codex orchestration prompt

Use this as the goal prompt for the agent orchestrating the evaluation from the
repository root.

```text
Evaluate the `confirm-with-pseudocode` skill under `confirm-with-pseudocode/`
using the Harness v2 hard-test kit under `tests/harness/`.

First run the kit's offline `preflight.py` and `harness_selftest.py`. Do not spend model calls until both pass.

Ensure the installed `confirm-with-pseudocode` skill that Codex resolves is byte-identical to the repo source skill, and pass its actual installed directory to `run_codex_suite.py --installed-skill-path`. Do not use `--skip-skill-verification` for canonical results.

Then:

1. Run the complete 40-case candidate suite with `gpt-5.6-sol` at medium reasoning and write the v2 evidence under `test-results\v2\`.
2. Run `transcript_lint.py` on the candidate results.
3. Judge the complete candidate suite with an independent model/configuration, preferably `gpt-5.6-luna` at high reasoning, using `judge_codex_results.py`.
4. Run `summarize_suite.py` with both the judgments and candidate results.
5. Inspect every critical failure, judge infrastructure error, diagnostic result, and any pre-execution tool activity the semantic judge classifies as substantive.

Run this as an evaluation-only pass. If a behavioral test fails, diagnose and report the underlying general protocol failure, but do not modify the skill or behavioral suite during this run. Preserve the candidate evidence exactly as generated.

Do not weaken, remove, rewrite, special-case, or reinterpret the locked 40 behavioral test vectors to obtain a pass. `suite.lock.json` must remain valid. Do not modify the PDL standard.

If the harness itself fails preflight/self-test or has an infrastructure defect, fix the harness without changing behavioral expectations, rerun its offline checks, and document the harness fix separately from skill changes.

Preserve all v2 JSONL outputs and their `.manifest.json` sidecars in the package. Do not overwrite the historical Harness v1 results.

At completion report:
- candidate model/configuration;
- judge model/configuration;
- skill source and installed-skill verification hashes/status;
- candidate/lint/judge/summary results;
- failures found and root causes;
- skill changes made, if any;
- harness changes made, if any;
- regressions encountered;
- final release-gate status;
- any unresolved concern even if the gate passes.
```
