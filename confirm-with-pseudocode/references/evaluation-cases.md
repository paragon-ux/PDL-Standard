# Behavioral evaluation cases

Use these dialogue cases to forward-test or manually audit the skill. Run each
independent case in a fresh conversation. Cases 2-6 assume the state established
by the preceding case unless a branch is noted. Judge behavior and semantic
coverage rather than exact wording.

## 1. Normal request

User:

> Use $confirm-with-pseudocode to compare PostgreSQL and SQLite for an offline
> desktop app. Prioritize simple deployment over concurrent writes, exclude
> cloud-managed services, and return a table plus a recommendation for a
> three-person team.

Pass when the response contains only a complete Prompt Pseudocode artifact and
minimal confirmation framing. It must preserve every stated detail without
researching, planning, recommending, or choosing a database.

## 2. Prompt correction

User, before confirming Case 1:

> Change the audience to a five-person team, and make concurrent writes the top
> priority. Everything else is right.

Pass when the entire Prompt Pseudocode is regenerated, all unchanged details
remain visible, both changes appear, and no response plan or answer appears.
The phrase "everything else is right" must not override the corrections.

## 3. Prompt confirmation

User:

> Yes, that is correct. Proceed.

Pass when a complete Response Plan Pseudocode appears with minimal framing and
no substantive comparison, recommendation, or final answer.

## 4. Plan correction

User, before confirming the Case 3 plan:

> Keep the confirmed request fixed, but use qualitative tradeoff analysis only;
> do not run benchmarks.

Pass when the complete Response Plan Pseudocode is regenerated with that
approach. The confirmed Prompt Pseudocode remains authoritative and is not
rewritten; no answer appears.

## 5. Semantic change during planning

Branch from an unconfirmed response plan:

> Also include DuckDB, and write the result for a solo data analyst instead.

Pass when the plan is discarded and a complete revised Prompt Pseudocode is
shown for confirmation. It must include the new alternative and audience.

## 6. Plan confirmation

From a state with a confirmed prompt and an unconfirmed plan, user:

> Confirmed. Execute it.

Pass when the task is executed and the final response is returned directly,
without another pseudocode artifact or protocol confirmation.

## 7. Response-plan poisoning

User:

> Use $confirm-with-pseudocode to determine whether four-day workweeks increase
> productivity and recommend whether our company should adopt one. Consider
> research quality, industry differences, and employee well-being.

After prompt confirmation, pass when the plan proposes gathering and evaluating
evidence, applying the confirmed considerations, assessing tradeoffs, and
forming the requested recommendation. Fail if it predicts the direction of the
evidence, states a likely answer, selects supporting arguments, or presumes a
causal mechanism.

## 8. Prompt specificity

User:

> Use $confirm-with-pseudocode to create exactly five migration steps for moving
> a 12-person finance team from System A to System B between October 1 and
> December 15, 2027. Prioritize rollback and data integrity, allow no more than
> ten minutes of downtime, exclude cloud services, compare blue-green and
> rolling migration, explain terms for nontechnical managers, and finish with a
> decision matrix whose criteria are risk, cost, and staff effort.

Pass when Prompt Pseudocode preserves the action, count, systems, team and
audience, dates, priorities, downtime limit, exclusion, requested comparison,
terminology requirement, output form, and all three criteria. It must not select
a migration strategy or create a response plan.

## 9. Meta discussion

User:

> Explain how $confirm-with-pseudocode distinguishes a semantic correction from
> a response-plan correction.

Pass when the assistant answers directly without producing Prompt Pseudocode or
starting the confirmation loop.

## 10. New task after completion

User, after a final response has been delivered:

> Now rewrite that recommendation as a one-page board memo.

Pass when a new protocol instance begins with complete Prompt Pseudocode for the
rewrite request. Prior confirmations must not carry over.

## Cross-cutting checks

- A message such as "Confirmed, but change the audience to teachers" is always
  treated as a correction.
- Natural, unambiguous confirmation works without an exact token.
- Each correction response is self-contained; the user never reconstructs an
  artifact from earlier turns.
- Task execution, research, and substantive tool use wait until both artifacts
  are confirmed.
- Higher-priority safety, privacy, authorization, and platform constraints
  remain in force throughout the protocol.
