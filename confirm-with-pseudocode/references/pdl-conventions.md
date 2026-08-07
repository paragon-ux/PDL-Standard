# PDL compatibility conventions

This project-authored runtime profile is designed for compatibility with the
**Pseudocode Standard** attributed to J. Dalbey and published on the Cal Poly
course site at <https://users.csc.calpoly.edu/~jdalbey/SWE/pdl_std.html>.

The profile records only the functional notation and style needed by this
skill. Its wording and examples are original to this project; it does not
redistribute the source page, its prose, or its examples. The local profile is
complete at runtime and must not be supplemented by fetching the source.

## Writing style

- Describe operations in structured English and use terms from the task's
  subject matter rather than implementation-specific mechanics.
- Put each operation on its own line and read equally indented operations from
  top to bottom.
- Indent subordinate operations beneath the construct or action that controls
  them.
- Make control keywords and common action verbs uppercase; write the rest as
  natural language.
- Name the items being processed instead of exposing counters or storage
  details when the domain wording already identifies the iteration.
- State an operation directly instead of imitating assignment syntax.
- Keep the artifact as pseudocode. Do not replace it with a fielded schema or
  invent protocol-specific grammar.

When an artifact describes an algorithm, cover its complete control flow and
refine compound steps until each step contains at most one loop or decision.
Prompt and Response Plan Pseudocode are control artifacts rather than
implementation algorithms: make each complete for its protocol purpose, but do
not add implementation detail merely to satisfy the algorithmic refinement
rule.

## Compatible control forms

### Sequence

Place actions in their required order. For example:

```text
OBTAIN the subtotal for the order
CALCULATE the applicable tax
DISPLAY the final amount
```

Useful action verbs include `READ`, `OBTAIN`, `GET`, `PRINT`, `DISPLAY`,
`SHOW`, `COMPUTE`, `CALCULATE`, `DETERMINE`, `SET`, `INIT`, and `INCREMENT`.
Use a more precise subject-matter verb when one is available.

### Binary decision

```text
IF condition THEN
    actions for the condition
ELSE
    alternative actions
ENDIF
```

Leave out `ELSE` when the false condition requires no action.

### Top-tested loop

```text
WHILE condition
    repeated actions
ENDWHILE
```

### Bottom-tested loop

```text
REPEAT
    repeated actions
UNTIL condition
```

This form performs the actions before its first condition check.

### Bounded or collection loop

```text
FOR each record in the selected group
    repeated actions
ENDFOR
```

Express the bounds with subject-matter terms when possible.

### Multiway decision

```text
CASE selected value OF
    first condition : first actions
    second condition : second actions
    OTHERS : default actions
ENDCASE
```

Leave out `OTHERS` when no default behavior is required.

### Subprocedure

```text
CALL named procedure with inputs RETURNING result
```

Remove the input or result phrase when it does not apply.

## Natural qualification

PDL is readable structured English, not a machine-parsed grammar. Indent
ordinary qualifications when that makes an action easier to inspect:

```text
COMPARE the requested alternatives
    USING the confirmed criteria
    FOR the stated audience

DO NOT include excluded options
```

These qualifications refine an action; they are not new control constructs or
schema fields.
