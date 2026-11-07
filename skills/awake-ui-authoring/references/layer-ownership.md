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

> **ui-headless holds zero visual policy.** Every colour, radius and inset arrives as a
> parameter, or nothing is drawn. Sizes still follow the size rule in `SKILL.md` — derivable from
> content, never from a theme.

Audited 2026-08-21: 31 ambient fallbacks and 14 ambient overrides. The overrides are why a
shadcn skin cannot currently restyle a checkbox's checkmark, its indeterminate dash, a radio
dot, or a toggle's on/off colours. `verifyUiHeadlessAmbientTheme` fails the build on any new
one; its exemption list is the existing debt and only ever shrinks.

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

`ui-headless` has no reference today, which is why `combobox` accumulated five defects and
`select` three before anyone rendered them open. Use two, for different things — and take the
*runtime* shape from neither, because Awake is immediate-mode and both references are retained:

| Take | From | Why it transfers |
|---|---|---|
| Part anatomy, roles, keyboard, state attributes | **Radix / Base UI**, and WAI-ARIA APG for behaviour | A decomposition is not a state model, so it is mode-independent |
| Tokens, variant/size enums, Tailwind-class translations | **`shadcn-compose`** (same author, already-solved Kotlin translation) | Pure data |
| *Nothing* | either one's `remember`/recomposition/callback shape | Awake resolves state by explicit `id` and returns the outcome; see `kmp-api-mimicry`'s "mimic shape, not runtime" |

Material is not the model for this layer: its signatures fuse `colors`/`elevation` into the
control, which is the ambient-override defect above promoted to API. It stays useful only as a
checklist of which controls ought to exist.

## Behaviour belongs underneath, even when only one skin exists today

If a component owns real structure -- measurement, selection resolution, open/close state,
traversal -- that behaviour belongs in `ui-headless` even if `ui-designsystem` is its only
current caller. Several components (Tabs, Collapsible, Dialog, DropdownMenu) were built
styled-first and now own behaviour that cannot be reused or reskinned without dragging shadcn
in. That is a debt, not a pattern to copy.

The exception is genuine *composition*: a branded arrangement of existing primitives with no new
behaviour is correctly design-system-only.

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

## Design System may use Core infrastructure, never Core widget primitives

`ui-designsystem` may have an **internal** (`implementation`) dependency on `ui-core` for
`Style`, theme/text providers, CompositionLocal mechanics, and runtime-free value adapters. It
must not expose Core types from its public API.

A design-system recipe still calls Headless widgets for behavior. It must not claim slots, draw,
hit-test, record semantics, or call Core layout/control primitives directly. If a recipe needs
that, extend Headless with the missing generic behavior or slot API; duplicated behavior is a
Headless API gap, not a reason to bypass it.

## Do not add a per-component style registry to `:awake:compose:*`

A per-component size/recipe registry is visual policy and inevitably turns Core into a hidden
design system. Headless may accept a generic visual-state contract; `ui-designsystem` supplies the
actual branded sizes, colours, and radii by mapping its named variant to that neutral contract. A
Headless fallback must remain content-derived, metric-derived, or a physical constraint.
