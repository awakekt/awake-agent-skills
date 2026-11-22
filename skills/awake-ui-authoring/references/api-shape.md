# Widget API shape

Extends `SKILL.md`. Read before adding a public widget function, an overload, or a new name.

## Naming: Compose is canonical for visual recipe functions; Radix names the concept

A public `context(Composer)` function that returns `Unit` and emits a visible UI element is a
Compose-shaped visual component. Name it as Jetpack Compose does: a PascalCase noun, such as
`ShadcnButton`, `ShadcnDialog`, or `ShadcnButtonGroup`. This applies even though Awake has its
own retained runtime rather than AndroidX's compiler plugin: callers read and compose these APIs
the same way. Android's Compose guidance makes this distinction explicitly: Unit visual
composables are PascalCase nouns; returning helpers retain ordinary Kotlin camelCase.

Use lowercase only for non-visual/returning helpers and modifiers (`remember*`, `shadcnMoveSplit`,
`Modifier.clickable`). Radix remains canonical for *what* a component is called and does --
`ShadcnSelect`, not a "Dropdown"; `ShadcnProgress`, not a "ProgressBar" -- but it does not override Compose's
capitalization convention. Existing lowercase `shadcn*` APIs are compatibility debt. Do not add
new ones; migrate them through PascalCase entry points and explicit deprecations in a dedicated
API-migration change rather than silently breaking consumers.

- `select()`, not `dropdown()` -- it returns a chosen value, it is not a menu.
- `progress()`, not `progressBar()` -- the latter is Android View-era.
- A file's name must match what it exports: `ShadcnButton.kt` exports `ShadcnButton`. A file
  named for a function it does not declare is lying.
- Styled counterparts are `Shadcn<Widget>` over the same base concept, so the pairing remains
  obvious without breaking Compose call-site conventions.

For anything Radix has no name for, the Awake name wins -- `*Slot` overloads are an Awake
invention and a good one; keep them consistent.

## One entry point per widget, not one overload per scope

A widget gets ONE public `context(Composer)` function. Do not add a `RowScope`/`ColumnScope`/
`BoxScope` overload of it. Behaviour that depends on the parent belongs to the scope as a
`Modifier` member, the way `RowScope` declares `Modifier.weight` and `Modifier.align`, and the
caller writes it at the call site.

Why this matters beyond tidiness: overload sets hide capability gaps. Resolution picks the most
specific receiver silently, so a scope that lacks the overload falls through to a base version
that quietly ignores what the caller asked for. One function per widget makes an unsupported
combination a compile error or an explicit `error(...)`, not a silent no-op.

When a widget genuinely needs different behaviour, branch on its parameters inside the one
function. Add an overload only when the signature itself must differ (different parameters, not
different defaults), and say why in a comment.

- An overload that only forwards (`modifier = modifier`) is dead: delete it.
- An overload whose default depends on the static receiver cannot become one function that
  inspects `this`: resolution is static and a `when (this)` is not, so the default would reach
  call sites that never had it. If one stays, write the rule body once and call it from each.

Delete-and-run-the-suite is the check. If nothing moves, the overload was dead.

## Foundation: no separate overload for a content shape -- compose it through the slot

A neutral control or container in `:awake:compose:foundation` gets ONE primary entry point, and it
is the slot/content-lambda form (`context(Composer) () -> Unit`). Do not add a parallel foundation
overload that takes a `label: String` (or any other convenience data shape) and independently
resolves and draws that content itself:

```kotlin
// Wrong -- a second resolution path that styles and draws the label on its own
context(Composer)
fun Control(label: String, modifier: Modifier = Modifier)

// Right -- one slot entry point; the label is composed through its slot
Box(modifier = Modifier.styleable(styleState, style).clickable(onClick = onClick)) {
    Text("Save")
}
```

This is the same principle as "one entry point per widget" above, one level down: neither the
parent scope nor the content shape should fork into two styling/measurement paths. When a `label:`
overload independently re-derives font size, weight, colour, or intrinsic width, it drifts from
the slot path the moment either one changes. One content shape, one resolution path, no drift.

### `:awake:ui:shadcn` MAY offer `label:` / `text:` -- as long as it delegates to the slot overload

The restriction above is on `:awake:compose:foundation`, not on `:awake:ui:shadcn` or
`:awake:ui:material3`. A design-system recipe may offer a `label: String` or `text: String`
convenience overload -- callers expect that sugar -- as long as its body delegates straight into
the recipe's own slot overload rather than duplicating the layout or `Style` resolution:

```kotlin
// Correct: convenience overload delegates straight to the slot entry point
context(Composer)
fun ShadcnButton(text: String, onClick: () -> Unit, modifier: Modifier = Modifier) {
    ShadcnButton(onClick = onClick, modifier = modifier) {
        Text(text)
    }
}
```

## Fill the axis through `Modifier`

Fill is a modifier, as in Compose. Express it at the call site:

```kotlin
Modifier.fillMaxWidth()
Modifier.fillMaxHeight()
Modifier.fillMaxSize()
```

Use `width(48.dp)` or `height(48.dp)` for a fixed authored dimension, and `width(IntrinsicSize.Min)`
to size to content. Do not add a widget parameter or a public sentinel value that means "fill"; a
caller who wants fill says so in the modifier.

## The 4 Closed Foundational Primitives Rule

In Awake's `:awake:compose:*` stack, every UI component is an atomic composition of exactly 4
primitive categories:

1. **Painted Containers**: `Box` (or `Row`/`Column`) styled with `Modifier.styleable(...)`,
   `Modifier.background(...)`, `Modifier.border(...)`, and `Modifier.clip(...)` is how painted
   containers are built — never a bespoke raw-canvas surface primitive.
2. **Spatial Layout Containers**: `Row`, `Column`, `Box`, and `Spacer` (`:awake:compose:foundation`)
   are the spatial layout containers. They distribute bounds without owning visual skin policy.
3. **Content Leaf Nodes**: `Text`, `BasicTextField`, and `Image` (with vector/bitmap painters) are
   the leaf content primitives.
4. **Behavioral Modifiers**: `Modifier.clickable`, `padding`, `size`, `weight`, `align`, `alpha`,
   and `graphicsLayer` attach layout, interaction, and visual effects.

Design-system widgets (`ShadcnButton`, `ShadcnCheckbox`, `ShadcnSwitch`, `ShadcnTabs`,
`ShadcnCollapsible`, etc.) must **never** call raw canvas emitters directly or manually calculate
sibling coordinates; they compose from these 4 `:awake:compose:*` primitive categories.

## Widget event idiom: Compose-shaped callbacks

The retained shadcn controls report events the way Compose does, through callback parameters:
`ShadcnButton(onClick = ...)`, `ShadcnCheckbox`/`ShadcnSwitch(onCheckedChange = ...)`,
`ShadcnSlider(onValueChange = ..., onValueChangeFinished = ...)`,
`ShadcnSelect(onExpandedChange = ..., onItemSelected = ...)`,
`ShadcnToggleGroup(onSelectedChange = ...)`. The caller owns the value and passes it back in. Use
that shape for any new control. `Modifier.clickable(onClick = ...)` is the neutral seam underneath.

One exception: `ShadcnToggle` returns the state after this frame's click instead of taking a
callback. Do not copy it into a new control; a second event shape makes callers learn two idioms.
