---
name: awake-ui-verification
description: Verify Awake UI behavior, rendered output, and source parity. Use when testing a UI change, investigating visual or interaction drift, comparing with a pinned reference, or deciding whether a snapshot baseline may be updated.
---

# Verify Awake UI changes

A passing snapshot proves that output did not change; it does not prove that the output is correct.
Use an oracle appropriate to the claim, inspect the evidence, and report anything that remains
unmeasured.

## Choose the relevant workflow

| Task | Read |
|---|---|
| Component tests, semantics, bounds, input, and test placement | [Component tests](references/component-tests.md) |
| Official reference comparison, parity claims, or snapshot updates | [Visual parity and baselines](references/visual-parity.md) |
| A click, render, or CPU preview does not behave as expected | [UI debugging](references/ui-debugging.md) |
| Commands, reports, and comparison artifacts | [Tool reference](references/tool-reference.md) |

For shadcn components, also follow [awake-shadcn-parity-workflow](../awake-shadcn-parity-workflow/SKILL.md).
The Awake repository's UI policy is documented in
[ui-validation.md](https://github.com/awakekt/awake/blob/main/docs/reference/ui-validation.md);
the command sequence is in
[ui-parity-tool.md](https://github.com/awakekt/awake/blob/main/docs/reference/ui-parity-tool.md).

## Rules for claims and baselines

- Keep “did output change?” separate from “is the result correct?” Snapshots detect regressions;
  semantic, geometry, behavior, style, and source-reference evidence answer correctness questions.
- Treat the pinned upstream capture and source as authority, not memory, an old screenshot, or a
  plausible-looking result. Check provenance before trusting an artifact.
- Report a named parity scope and its coverage. Do not claim universal pixel parity; mark missing
  or unsupported evidence as unmeasured.
- Never record a baseline to make a failure pass. First run without recording, inspect and explain
  the diff, then update the PNG and any separate signature maps together.
- Before calling a visual or behavioral change complete, inspect fresh artifacts and run the
  relevant focused tests. Use a real backend capture only when the question involves GPU behavior.
