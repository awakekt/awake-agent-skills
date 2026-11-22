# Layer ownership in detail

Extends the three-layer table in `SKILL.md`. Read when deciding which module a piece of code
belongs in, or when a review says something is in the wrong layer.

## Ambient fallback and ambient override

Name the mechanism, not the intent. "Unstyled" is a goal and goals get argued with; these are
greppable.

**Ambient fallback** — reaching for the ambient theme instead of a parameter. Two shapes, same
ban, different severity:

| shape | example | severity |
|---|---|---|
| ambient fallback | `resolved.fill ?: theme.colors.primary` | debt — a skin can still win |
| ambient override | `drawCheckmark(slot, theme.colors.primaryForeground)` | **bug** — a skin cannot win |

> **`:awake:compose:foundation` holds zero visual policy.** Every colour, radius and inset arrives
> through `Style` or an explicit parameter, or nothing is drawn. Sizes still follow the size rule
> in `SKILL.md` — derivable from content, never from a theme.

`verifyUiOwnership` (`com.awakekt.awake.plugin.ui-ownership`, wired into `awakeVerify`) fails the
build if branded tokens, theme locals, or forbidden UI declarations leak across module boundaries.

## Second path

A capability that already has a home getting another one. The repo's audit calls the noun form
"twin nouns"; this is the same defect in behaviour.

> **One canonical mechanism per concern.** Look the registry up before drawing it yourself.

Example, now fixed: the checkbox once hand-built its checkmark from transcribed coordinates
while the icon registry already held a generated vector, and the dropdown chevron beside it
already rendered through the registry. `ShadcnCheckbox` now draws `ShadcnIcons.check` through
`rememberVectorPainter`. The hand-built mark also evaded `awake-ui-icons`' hand-transcription
ban by being typed as a raw path instead of an `ImageVector`, so state that rule by content, not
type: **if it is a glyph, it comes from the registry; being a path is not an exemption.**

## Which reference to check a control against

When designing or auditing a control in `:awake:ui:shadcn` or `:awake:ui:material3`, check two
references for different questions:

| Take | From | Why it transfers |
|---|---|---|
| Part anatomy, roles, keyboard, state attributes | **Radix / Base UI**, and WAI-ARIA APG for behaviour | A decomposition is independent of the rendering backend |
| Tokens, variant/size enums, Tailwind-class translations | **`shadcn-compose`** (same author, already-solved Kotlin translation) | Pure data |
| Layout, modifier, and retained runtime contracts | **AndroidX Compose** (`androidx.compose.runtime`/`ui`/`foundation`) | `:awake:compose:*` mirrors Compose's API surface |

Do not invent non-Compose control APIs inside `:awake:compose:foundation` — if AndroidX Compose
places a control in Material (`Slider`, `Checkbox`, `Switch`), its styled recipe belongs in
`:awake:ui:material3` or `:awake:ui:shadcn`, built on `:awake:compose:foundation`'s neutral
primitives (`Box`, `Row`, `Column`, `Modifier.clickable`, `Modifier.styleable`).

## Reusable layout and interaction primitives belong underneath

If a component needs a generic layout, gesture, or focus primitive that AndroidX Compose Foundation
already ships, implement that primitive in `:awake:compose:foundation` rather than re-deriving it
inside a design-system recipe. Conversely, if a behaviour is specific to a branded control (such as
a shadcn variant style or thumb geometry), keep it in `:awake:ui:shadcn` so foundation stays
skin-neutral and Compose-faithful.

## Foundation consumes `Style`, not a theme recipe

`:awake:compose:foundation` owns the neutral styling contract: `Style`, `StyleState` and
`Modifier.styleable`, with its state rules (hovered, pressed, focused, disabled, selected,
checked). It reads Compose's own locals, such as `LocalDensity` and `LocalTextStyle`, and nothing
branded. It applies the interaction state a style supplies; it never chooses a colour.

`:awake:ui:shadcn` maps a variant (`ShadcnButtonVariant.Default`, `Ghost`, a density) to a
component `Style`. Stateful details such as rest, hover, pressed and disabled live in that
component's style file (`ShadcnButtonStyle.kt`), not in a parallel visual DTO. `Style` is the
only neutral visual contract.

Install the theme with `provideShadcnTheme(values) { ... }`; recipes read it through
`shadcnTheme`. Use `shadcnThemeValues(...)` when only immutable theme values are needed; it
installs nothing. Every shadcn recipe must run inside `provideShadcnTheme`. There is no
Core-theme fallback: `LocalShadcnTheme` defaults to `null` and `shadcnTheme` throws without a
provider, so metrics and branded roles are never silently rebuilt from a generic theme. Do not
add `ShadcnTheme` or other branded APIs to the compose modules.

## Design systems compose `:awake:compose:*` primitives, never raw canvas emitters

`:awake:ui:shadcn` and `:awake:ui:material3` build on `:awake:compose:runtime`, `:awake:compose:ui`,
and `:awake:compose:foundation` (`Box`, `Row`, `Column`, `Spacer`, `Text`, `BasicTextField`,
`Image`, `Style`, `Modifier.styleable`, `CompositionLocal`). Recipes must not drop below
`:awake:compose:ui` to emit raw canvas draw lists, bypass pointer/hit-test dispatch, or duplicate
layout measurement that belongs in `:awake:compose:foundation`.

## Do not add a per-component style registry to `:awake:compose:*`

A per-component size/recipe registry is visual policy and inevitably turns `:awake:compose:*` into
a hidden design system. `:awake:compose:foundation` accepts generic `Style` and `Modifier`;
`:awake:ui:shadcn` and `:awake:ui:material3` supply the branded sizes, colours, and radii by
mapping named variants to that neutral contract. Any fallback in `:awake:compose:foundation` must
remain content-derived, metric-derived, or a physical constraint.
