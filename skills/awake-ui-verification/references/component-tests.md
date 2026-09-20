# Component tests

Use the lowest-level test harness that expresses the behavior. Extend an existing matrix or
component fixture before adding a new test file.

## Retained Compose test surface

- Use composeFrame for one frame and composeTestSession for interaction across frames.
- Assert semantics and exact bounds with onNode/onNodeWithTag, assert, and
  assertBoundsInRoot. Use onAllNodes only for intentional collection assertions.
- Use stable, owner-scoped Modifier.testTag values for production nodes that tests must target.
- Use session gestures for ordinary pointer input. Use an explicit UiInputState frame for wheel,
  keyboard, or custom input.
- Use captureImage for an intentional CPU-rendered snapshot. Use captureSemantics as structured
  evidence, not as a screenshot substitute.
- Use rasterizeDebugOverlay for semantic bounds and rasterizeLayoutOverlay for all placed layout
  nodes. These diagnose geometry; they do not prove paint correctness or hit-testing.
- Use raw UiContext only when the low-level lifecycle or renderer itself is under test. Mark such
  fixtures with UiLowLevelTest and a reason.

The CPU rasterizer is deterministic and useful for component tests, but it is not a GPU-fidelity
oracle. For backend rendering questions, use the real offscreen backend capture.

## Test design and ownership

1. A data-driven matrix owns combinations of inputs and expected measurements; add a row before
   creating a new test.
2. A regression test owns one shipped invariant and must fail when its fix is removed.
3. Keep pixel snapshots separate from semantic, geometry, and behavior tests because intentional
   design changes require reviewed baseline updates.

| Concern | Preferred owner |
|---|---|
| Retained Compose semantics, bounds, and input | compose:ui-testing |
| Sizing, scrolling, and measurement | compose:foundation |
| Whether a recipe applies the right modifiers | ui-shadcn |
| Geometry against shadcn | ui-showcase geometry tests |
| Paint comparison against shadcn | ui-showcase reference comparison |

Before adding a case, check that it asserts an exact contract, belongs in the lowest module that
can express it, and is not already covered by an owning fixture. Text-field tests should prove
focus routes typing to the field, insertion uses the saved caret, deletion/navigation preserve
valid caret bounds, and disabled fields neither focus nor mutate. Add explicit selection or IME
cases when those capabilities are enabled. Cursor-blink pixels are not a stable oracle.
