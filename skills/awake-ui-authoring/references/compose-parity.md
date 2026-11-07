# Compose parity: modifiers, layout, scoped values, state hooks

Extends `SKILL.md`. Read before adding to the `:awake:compose:*` surface, before adding a
`CompositionLocal`, or before adding or auditing a `remember` hook.

## Nothing enters `:awake:compose:*` that Compose does not have

**The hard rule, and it applies to the whole module group, not just modifiers.**

> A public declaration in `:awake:compose:runtime`, `:awake:compose:ui` or
> `:awake:compose:foundation` must correspond to something `androidx.compose.runtime`,
> `androidx.compose.ui` or `androidx.compose.foundation` actually ships. If it does not, it belongs
> in `ui-designsystem` — or in the consuming module — not here.

These modules exist to *be* Compose's surface on a different runtime. That claim is the entire
reason a Compose-literate reader can predict what they do, and it is what `mirror-map.md` audits.
One local invention with a plausible-looking name spends that credibility everywhere, because a
reader can no longer tell which half of the module they are looking at.

**The test is upstream's package, not your judgement of where it fits.** "This is behaviour, not
styling, so it belongs in foundation" is the reasoning that fails: `Slider` is behaviour, and Compose
still puts it in Material.

Worked example, from a real attempt during Stage 3:

| | |
|---|---|
| Proposed | `sliderTrack()`, `sliderValueAt()`, `nearerThumb()` in `:compose:foundation:gestures` |
| Argument for | Pointer-to-value mapping is behaviour; the recipe should not re-derive it |
| Why it was wrong | Compose Foundation has no slider anything. `Slider` is Material. Foundation ships `draggable`, and Material builds on it |
| Where it went | `ui-designsystem`, as `shadcnSliderTrack`/`shadcnSliderValueAt` — which is also the layer that owns the thumb size those functions take |

A second reason the boundary held here: the old `ui-headless` slider baked in `6.dp` and `16.dp`
with a comment naming their source as shadcn v4. Anything that carries a design-system number, or
takes one as a parameter it then encodes a rule about, is design-system code by the size rule in
`SKILL.md` regardless of how behavioural it looks.

**If Compose genuinely lacks an engine-specific concern** — something with no Compose analog at all,
like a frame clock this runtime needs and Compose gets from the platform — that is the one case for
a non-Compose-shaped declaration. Name it so nobody reads it as parity, and record it in
`mirror-map.md` as **Not implemented in Compose** with the real reason.

### The narrower rule for `Modifier` and the layout DSL

Do **not** extend the naming rule below to controls: Compose Foundation has no
`Button`/`Checkbox`/`Switch`/`Slider` to check against, and Material's own signatures fuse in visual
parameters this layer cannot carry, so "does Compose have it?" has no usable answer there. Check a
control's shape against Radix/Base UI anatomy instead — see `mirror-map.md`'s "Which upstream a given
API mirrors". Note this cuts both ways: a control having no Foundation counterpart is exactly why the
control does not go in foundation.

Before adding a `Modifier` function (`Modifier.kt` and the `draw`, `input` and `layout` packages
in `:awake:compose:ui`; `LayoutModifiers.kt` and its siblings in `:awake:compose:foundation`) or
anything to the layout DSL (`Row`/`Column`/`Box`/`Arrangement`/`Alignment`), check
[`17-modifier-parity.md`](https://github.com/awakekt/awake/blob/main/docs/reference/compose-engine/17-modifier-parity.md)
(every stable Compose modifier, with a verdict) and
[`15-compose-parity.md`](https://github.com/awakekt/awake/blob/main/docs/reference/compose-engine/15-compose-parity.md)
(the capability ledger) first:

- **A real Compose function with this name/shape already exists and Awake doesn't have
  it yet** → implement it matching Compose's real signature and semantics (verify
  against Compose's actual jars or source, not memory; `17-modifier-parity.md` was
  enumerated from the jars with `javap`). Record it there once it lands.
- **Awake needs something Compose genuinely has no equivalent for** (an engine-specific
  concern with no Compose analog) → this is the one case where a new, non-Compose-shaped
  function is legitimate. Name it so it's obviously not attempting Compose parity (avoid
  a name that looks like a Compose function but isn't), and record it in
  `15-compose-parity.md` as an **Upgrade** or **Divergence** with the real reason, so a future
  contributor doesn't assume Compose semantics apply.
- **You're tempted to add a function because it "feels like it should exist" but you
  haven't checked whether Compose actually has it, or whether it behaves the way you're
  about to implement it** → stop, check first. This is how an unrecorded divergence
  happens: a function that looks Compose-shaped, passes a glance-review, then causes a real
  layout or render bug later because its behavior quietly differs from what a
  Compose-literate reader assumes. That is the dangerous category.

Same rule for `Arrangement`/`Alignment`/scroll/graphics-layer helpers: anything on the
`:awake:compose:*` surface, not just `Modifier` itself. Layout is covered by
[`01-layout.md`](https://github.com/awakekt/awake/blob/main/docs/reference/compose-engine/01-layout.md).
Animation (`animateFloat`, `rememberLoopingPhase`, `animateTrailing`, all in
`:awake:compose:foundation`'s `animation` package, driven by `:awake:compose:ui`'s `FrameClock`)
is covered by
[`05-animation.md`](https://github.com/awakekt/awake/blob/main/docs/reference/compose-engine/05-animation.md).
Check the relevant one before adding to either surface.

## Escalate layout-engine defects; do not hide them in a recipe

Treat the following parity evidence as a `:awake:compose:*` `Modifier`/layout contract
investigation, not as an invitation to add component-specific dimensions, offsets, or separators:

- the parent geometry is correct but a child does not receive or honor its allocated bounds;
- `fillMax*` changes meaning during an intrinsic or wrap-content measurement trial, or expands
  to an unbounded viewport instead of the resolved parent axis;
- a recipe needs to inspect a measurement pass, member count, or use negative spacing merely to
  preserve ordinary parent/child layout; or
- a measured pixel slot is converted back into authored `Dp` to force a child into place.

Preserve the parity report's expected/actual/delta evidence. Add the smallest reusable
`:awake:compose:foundation` test matrix first (fixed and wrapping parent bounds, both axes where relevant, density
1 and 2). Fix the generic constraint propagation or modifier behavior, then rerun core,
design-system, and parity verification. Simplify the recipe only after the core contract is
proved. A fixed-width vertical button group whose members become intrinsic during a wrap-height
trial is the canonical cross-axis/intrinsic-sizing example.

**Why core-first, not recipe-first — this is a repeatedly-proven pattern here, not a
preference.** One layout primitive defect surfaces as *many* apparently-unrelated
design-system symptoms, each of which invites its own local workaround:

- The `weight()`+`fillMax*` starvation bug appeared as three separate symptoms (field
  controls, a checkout-form grid row, the toggle group), each patched locally with
  `weight(1f)`. One fix in the old engine's layout code retired the whole class and made all
  three workarounds optional.
- The vertical button-group fill bug was fixed in the row and column fill resolution, not in
  the button-group recipe.

A recipe-local fix for a primitive defect does not just leave the other symptoms broken —
it actively hides the shared root cause and makes the eventual core fix harder, because
each workaround must then be identified and unwound. The parity tool's own triage table
encodes the same rule from the other direction ("child geometry drifts but parent passes →
inspect `fillMax*`, intrinsic measurement, weights, and child modifiers"). A visible shadcn
drift is often a `Modifier` or layout defect wearing a design-system costume. When a recipe
cannot express the source result, record it in
[`docs/reference/ui-parity-core-issues.md`](https://github.com/awakekt/awake/blob/main/docs/reference/ui-parity-core-issues.md)
with the evidence its admission rule asks for.

## Bound-derived interiors must not report intrinsic size

A widget whose interior layout is `fraction x its own resolved bound` (a resizable panel
group, a scroll viewport's content) has **no intrinsic size** -- yet inside a WrapContent
parent's measure trial its children's claims land at trial-inflated positions and register as
phantom content extent. The showcase's preview card grew by the drag delta every frame this
way: the group's handle claim at `fraction x trial-bound` out-measured the card's real text
content, and the re-measured card re-based the panel budget mid-gesture.

Wrap the real content dispatch of such widgets in `boundDerivedContent { ... }`
(`ui-core/scope/UiScopeNesting.kt` -- the stronger sibling of `compositeContent`, isolating
wrap-extent trackers, not just the child list). Scroll viewports already do the equivalent via
`withMeasuredSubtreeIsolated`. Symptom to recognize: "dragging/interacting inside a card
re-sizes the card itself".

## `CompositionLocal`: scoped values, and when NOT to reach for one

`CompositionLocal` (`:awake:compose:runtime`, `CompositionLocal.kt`) carries a value from an
ancestor to any descendant without threading it through every call in between. The spellings are
Compose's own:

```kotlin
val LocalSpacing = compositionLocalOf { 8.dp }            // declare, at file scope

CompositionLocalProvider(LocalSpacing provides 12.dp) {   // provide for a subtree
    val spacing = LocalSpacing.current                    // read anywhere below
}
```

The provider window closes when its content returns, even on a throw.

**Two ways it deliberately differs from Compose. Know both before porting Compose habits:**

1. **No `staticCompositionLocalOf`.** In Compose that variant only decides whether a read
   invalidates a recomposition scope. Here nothing skips and nothing is observed: the whole tree
   composes every frame. One `compositionLocalOf` is the whole API.
2. **No merge hook.** A provided value replaces its parent's. Nesting that should compound does
   so because the *nodes* nest: alpha is `Modifier.alpha` or `Modifier.graphicsLayer` on a node,
   not an ambient value that multiplies. Do not add a merge lambda to a local; that is what once
   let two different composition rules exist side by side.

**Hard rule: declare at file scope, never inside a function or loop.** A local's identity is the
object `compositionLocalOf` returns. One declared inside a function is a new local on every call,
so its readers never find what its provider supplied, and its default is computed again each time.

**When a `CompositionLocal` is the right tool** (all three should be true):

- The value is genuinely *cross-cutting* over a subtree — theme, density, text style — not
  data one specific child needs.
- Threading it as an explicit parameter would mean passing it through widgets that don't
  themselves use it, purely to reach a descendant.
- It has a sensible default that lets a widget render standalone without a provider.

**When it is the wrong tool** — same reasoning Compose gives for using `CompositionLocal`
sparingly: it makes a widget's behavior depend on invisible ambient state, which is harder
to reason about, harder to test in isolation, and harder to reuse. Prefer an explicit
parameter when the caller reasonably needs to control the value, when only one or two levels
separate provider from consumer, or when the value is really *data* rather than *environment*.
An explicit param that's slightly tedious to thread beats an ambient dependency nobody can
see at the call site.

**Layer ownership still applies, and constrains this further:** `:awake:compose:foundation`
reads only Compose's own locals (`LocalDensity`, `LocalTextStyle`, `LocalLayoutDirection`) and
consumes the generic `Style` it is handed (see [`layer-ownership.md`](layer-ownership.md)). The
branded locals (`LocalShadcnTheme`, `LocalShadcnDensity`) live in `:awake:ui:shadcn` *because*
branded ambient state is the design system's to own. A new local in the compose modules that
passes visual policy down is the ownership violation this skill exists to prevent, wearing a
different hat.

Prefer a parameter over a local even inside the design system. `ShadcnButtonGroupSeparator` takes
its orientation as an argument; the old version read it from a group local, so a separator outside
a group silently drew the wrong way.

## State hooks (`remember`): positional, so key what moves

`remember { }`, `remember(key) { }` and `remember(key1, key2) { }` (`:awake:compose:runtime`,
`Remember.kt`) keep a value across frames. State that changes is a plain class held by `remember`,
or `mutableStateOf` with `by` delegation. Nothing observes it, because nothing skips.

The slots live on the enclosing node, so state goes when the node goes. Within a node they are
**positional**, in call order, as Compose's slot table is. That is the part that bites:

1. A call that comes or goes partway through a node shifts the slots of every call after it. A
   slot holding a value of another type is recomputed rather than cast, but a shift between
   calls of the same type hands one call's value to the next **silently**.
2. A list that reorders keeps state with the position, not the item.

So wrap a branch that remembers, and each item of a list, in `key(value) { }`. Its nodes and
its `remember` calls then follow the key. A component that remembers wraps its own body in
`rememberGroup(privateKey) { }`, as `ShadcnToggle` does, so its state does not depend on what its
caller draws around it. A component must not use `key` for this, because that replaces the key its
caller gave the node.

`remember` has one- and two-key overloads and no vararg, on purpose: a vararg array would
allocate on every call, every frame. The full model is in
[`03-composition-locals.md`](https://github.com/awakekt/awake/blob/main/docs/reference/compose-engine/03-composition-locals.md)
and the runtime section of
[`15-compose-parity.md`](https://github.com/awakekt/awake/blob/main/docs/reference/compose-engine/15-compose-parity.md).
