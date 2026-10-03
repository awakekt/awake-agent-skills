---
name: awake-ui-icons
description: How icon vector data enters Awake - official SVGs turned into ImageVector objects at build time by the com.awakekt.awake.plugin.icon-codegen Gradle plugin, never hand-transcribed. Use before adding an icon, starting an icon pack in a module, changing the generator, or debugging how an icon renders. Trigger keywords - icon, ImageVector, HeroIcons, LucideIcons, ShadcnIcons, SVG, manifest.json, path data, moveTo, cubicTo, chevron, glyph.
license: Apache-2.0
metadata:
  author: awake
  last-updated: '2026-10-03'
---

# Icon Authoring in Awake

One hard rule, one plugin, one seam.

## The Rule: Never Hand-Write Path Coordinates

Every `ImageVector` is generated from an official SVG. Never transcribe path data, never edit
generated output, never derive one glyph from another by rotating or mirroring its coordinates.
Hand-derivation flattens corner arcs into line segments and replicates the error into every
derived glyph; the generator keeps curves as real cubics even where they look negligible.

## Where Icons Live

Core ships no general icon set. Each module vendors only the glyphs it draws, and the plugin
generates them into that module:

| Pack | SVGs | Generated object |
|---|---|---|
| shadcn defaults | `awake/ui/shadcn/src/commonMain/svg/lucide/` | internal `LucideIcons` in `com.awakekt.awake.ui.shadcn.components` |
| shadcn test fixtures | `awake/ui/shadcn/src/commonTest/svg/heroicons/` | internal test `HeroIcons` |
| UI showcase sample | `samples/ui-showcase/src/commonMain/svg/heroicons/` | internal `HeroIcons` |

Recipes and apps read shadcn glyphs through `ShadcnIcons` -- overridable `var` pointers, the brand
seam. Swap an icon there, never by editing a pack. A game or Studio that wants Heroicons vendors
them into its own module the same way.

## Add An Icon To A Pack

1. Copy the SVG, unmodified, from the release the pack's `manifest.json` pins (`source.version`)
   into the matching tier directory. A glyph from another release, or `master`, leaves the pack
   spanning two upstream versions with nothing recording it.
2. Match the tier to the glyphs around it. Heroicons draws 20/solid, 24/solid and 24/outline with
   different weights and detail; a glyph from another tier looks heavier or lighter than its
   neighbours. Never rescale one tier to fake another.
3. Build. The `val` appears automatically, named after the file in camelCase:
   `arrow-down-tray.svg` becomes `arrowDownTray`. A public pack's new `val` is new API, so run the
   module's `desktopApiCheck`.
4. If a shadcn recipe needs it, point a `ShadcnIcons` entry at it.

## Start A Pack In Any Module

Apply the plugin (it needs the Kotlin Multiplatform plugin) and add a pack directory to whichever
source set should see the icons:

```
src/<sourceSet>/svg/<pack>/
  manifest.json
  LICENSE              the upstream licence, verbatim
  <tier-directory>/*.svg
```

```json
{
  "package": "com.example.app.icon",
  "interface": "HeroIcons",
  "visibility": "internal",
  "source": { "name": "Heroicons", "version": "v2.2.0", "license": "MIT" },
  "fileKdoc": ["The Heroicons this module draws."],
  "tiers": [
    { "object": "Solid20Mini", "directory": "20-solid", "dp": 20, "label": "20/solid \"mini\"" },
    { "object": "Outline24", "directory": "24-outline", "dp": 24, "label": "24/outline" }
  ]
}
```

- One pack becomes one file: a `sealed interface` with one nested `object` per tier. Set
  `"flat": true` with a single tier (no `object`) to get a plain `object` instead.
- `visibility` is optional. Use `"internal"` in a library so the pack stays out of its public API
  and consumers go through a pointer object like `ShadcnIcons`.
- `source` is free-form provenance; record the release and, where there is one, its tarball
  SHA-256. `fileKdoc` and a tier's `kdoc` become the generated KDoc.
- Each source set gets a `generate<SourceSet>ImageVectors` task writing to
  `build/generated/imagevector/<sourceSet>`. Output never goes to `src/`: nothing generated is
  committed, detekt and spotless never see it, and every build regenerates it from scratch.
- Each icon is a lazy `val`, built on first use rather than with the whole pack.

## What The Generator Guarantees

- Full SVG path grammar: M/L/H/V/C/S/Q/T/A/Z, absolute and relative, implicit repetition,
  concatenated arc flags such as `a.75.75 0 011.06.02`.
- Arcs become cubic Beziers (W3C endpoint-to-centre parameterisation, at most 90 degrees per
  segment, exact endpoints). Curves are never flattened.
- `<circle>` and rounded `<rect>` become equivalent path commands.
- `fill`, `stroke`, `stroke-width`, `stroke-linecap` and `stroke-linejoin` resolve through
  ancestors, as Heroicons' outline tier declares them on the `<svg>` root. A stroke stays a stroke
  (`DrawStroke`); it is never pre-expanded into a fill.
- `fill-rule="evenodd"` with nested subpaths emits `UiFillRule.EvenOdd`, so holes survive.
- Deterministic output: 4-decimal rounding, trimmed zeros.
- It refuses, and fails the build, rather than approximating: any `transform`, `<ellipse>`,
  `<line>`, `<polyline>` and `<polygon>`, a shape that both fills and strokes, and even-odd
  subpaths that cross instead of nest. It never resolves external entities or DTDs.

Gradients, masks, filters and text are out of scope. Icons are vector paths drawn at the slot's
size; a larger illustration is a bitmap or a separate decision.

## Change The Generator

The generator is `build-logic/src/main/kotlin/com/awakekt/awake/build/icons/SvgImageVectorCodegen.kt`,
wired by `com.awakekt.awake.plugin.icon-codegen.gradle.kts`. The plugin is published, so a change
reaches consumers' generated code on their next Core upgrade.

- Prove it with `./gradlew -p build-logic test --tests '*SvgImageVectorCodegenTest*'`.
- The plugin registers the generate **task** as the source directory, not the directory itself.
  A bare `srcDir(directory)` compiles and never runs the generator, so a clean checkout builds the
  module with no icons.
- A change that alters output for existing SVGs moves every pack. Diff the generated files before
  and after rather than trusting the tests alone.

`packedImageVector` (`awake/compose/ui/.../vector/PackedImageVector.kt`) still decodes a packed
string form, pinned by `PackedImageVectorParityTest`; the generator does not emit it.

## How An Icon Renders

`ShadcnIcon` and `ShadcnCheckbox` draw through `rememberVectorPainter`, so `VectorPainter.draw`:

- `fitTo` scales the viewport into the slot, snaps the centring offset to whole pixels, and
  scales the stroke width with the path. `viewportWidth`/`viewportHeight` must equal the SVG's
  viewBox; `defaultWidth`/`defaultHeight` are per-tier and nothing reads them.
- Fills go through `tessellateFillAa`; strokes through `strokeToSvgFillPath` then
  `tessellateFillAa`, with the anti-aliased fringe centred on the outline as SVG coverage is.
  Both live in `awake/core/graphics2d` (`PathFillTessellation.kt`, `PathStrokeTessellation.kt`).

If a glyph renders wrong, suspect the tessellation or the rasterizer, never the data, and never
compensate by editing path data. Compare against the reference instead:

- `LucideShadcnSpritesheetPreviewTest` writes `lucide-icons.png` and `shadcn-icons.png` to
  `awake/ui/shadcn/build/reports/compose-preview/`.
- `tools/icons/capture_lucide_spritesheet_reference.py --out <png>` renders the same pinned SVGs
  in Chromium at the same positions.
- The Render Evidence workflow captures both on every PR that touches icons and publishes the
  base and head sheets.

## Source-Faithful Defaults

Choose a recipe's glyph family from the visual source it matches. shadcn's pinned recipes import
Lucide, so a visibly compared glyph needs generated Lucide data and a `ShadcnIcons` pointer; never
substitute a similarly named Heroicon because it is already vendored somewhere. Keep recipes on
`ShadcnIcons`, never on a pack directly, so the reference family can change without touching
layout.

An SVG feature the generator or renderer cannot handle is an engine capability finding: record it
with the source SVG and rendered evidence rather than working around it in the data.
