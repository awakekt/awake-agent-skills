# Widget identity, and the showcase catalog

Extends `SKILL.md`. Read before adding a stateful widget, a loop that emits widgets, or a
showcase page.

## State follows position: key every list and every branch that remembers

The retained runtime gives a node and its `remember` slots a **positional** identity: the same
index under the same parent, declaring the same type, is the same node as last frame. Hover,
press, focus, scroll and anything a widget remembers live on that node. Two shapes go wrong
silently:

1. **A loop that emits widgets without `key`.** Insert, remove or reorder an item and every
   item after it inherits its neighbour's state: one row's hover shows on another, an expanded
   section collapses, a text field keeps the wrong caret. Wrap each item in
   `key(item.id) { ... }` with a stable id from the data, never the loop index.
2. **A component whose state depends on its caller's layout.** A component that remembers wraps
   its body in `rememberGroup(privateKey) { ... }`, so a sibling that comes or goes beside it
   leaves its state where it was. `ShadcnToggle` and `ShadcnToggleGroup` are the model.

There is no duplicate-id crash to catch these. A `remember` slot that ends up holding a value of
another type is recomputed rather than cast, which hides a shift of a different type and does
nothing for a shift of the same type. Test it: change the list or the branch between two frames
and assert that state stayed with the item. Use `Modifier.testTag` to find a node in a test; a
tag is for lookup, not identity.

See the "State hooks" section of [`compose-parity.md`](compose-parity.md) for the slot model.

## The showcase catalog is the only catalog

`samples:ui-showcase` publishes one list -- `ShowcasePages` in `ShowcaseCatalog.kt`. The app
renders it and every preview/layout-signature fixture is derived from it. Do not maintain a
second list of preview entries in test code.

Three rules keep it honest:

1. **One file per page**, under `ui/pages/<category>/`. The page object owns its own metadata
   *and* its `hero`/`variants`/`states` renderers. A preview function with no page object is
   dead code, not a hidden feature.
2. **`showcasePageOrNull` returns null for an unknown id.** Never reintroduce a fallback to
   `ShowcasePages.first()`. The old fallback let five test fixtures fingerprint the
   Introduction page while claiming to cover Range Slider, State, Shimmer, and Field Demo --
   green tests, zero coverage.
3. **Preview size lives on the page** (`previewWidth`/`previewHeight`), not in a JVM
   annotation. Reading fixture metadata by reflection forces a skip on iOS and wasmJs, so the
   same test silently passes there without asserting anything.

A component shadcn ships that Awake cannot build yet gets a `showcasePlaceholder(...)` entry
naming the missing primitive, not silence.
