---
name: awake-ui-performance
description: What makes an Awake UI frame expensive, and the traps that make a change silently cost more than it looks. Read before writing anything that runs inside a `Row`/`Column`/`Box` content lambda, world-anchored canvas HUD system, or draw block, before adding a per-frame allocation, and before claiming a UI performance improvement. Trigger keywords - per-frame allocation, garbage, GC, frame time, ms per frame, wasm vs desktop performance, intrinsic queries, LayoutStats, ComposeFrameProbe, TextFrameProbe, ComposeHost, measureTextWidth, perfStatsEnabled, F2 overlay, slow UI, jank, optimize UI.
license: Apache-2.0
metadata:
  author: awake
  last-updated: '2026-11-22'
---

# Awake UI performance

## Why this exists

`awake-core-math` Rule 2 bans allocation inside `System.update`. UI needs the same rule and did
not have it. Measured 2026-08-21 on the old `ui-core` engine, before any of the fixes below:

- **1,151,016 bytes allocated per frame** for 60 plain surfaces (~68 MB/s at 60fps)
- **15.09 ms/frame** for `samples:ui-showcase`'s shell — the whole 16.67 ms budget, UI alone,
  before a single 3D frame

Most of that came from `ui-core` measuring a container by re-running its content. Core now runs
the retained `:awake:compose` engine: layout is single-pass, `Constraints` in and a measured node
out. Two things did not change, and they are why the rules below still apply. The whole tree
composes every frame (`ComposeHost.frame`): nothing skips and nothing is observed. And every node
is measured, placed and drawn every frame: nothing is skipped because it did not change.

## Rule 1 - a composable is per-frame code

Anything reachable from a composable body, a `MeasurePolicy` or a draw block runs at least once
per frame, forever. Apply the same discipline `System.update` gets.

Non-obvious allocators found in this codebase, all of them in hot paths:

| Trap | Cost | Fix |
|---|---|---|
| `val x get() = Thing()` on a value read every frame | one object per *read* | share one immutable instance |
| `copy(x = value)` when `value` is already `x` | full data-class copy | identity guard, return `this` |
| `list.filter { }.forEach { }` | list + iterator per call | indexed `for (i in list.indices)` |
| `listA + listB` | new backing array | append into one reused list |
| `addAll(collection)` | copies through `toArray()` | indexed add loop |
| `for (x in list)` on a `List` | `Iterator` object | indexed loop |
| `Style { … }` built in a composable body | a style object per call | hoist a constant style to a `val`; key a derived one with `remember` |
| `map.clear()` followed by re-putting entries every frame | fresh node object (~32 B) per inserted entry | scan a small cached `ArrayList` (`<= 32` items) or update entries in place |
| `measureTextWidth(...)` or `queryEach(Name::class, CanvasElement::class)` every frame | repeated glyph metrics and full-HUD scans | cache element refs once; re-measure only when `(text, look)` changes |

None of these read as expensive. Every one was a measurable share of the frame.

## Rule 2 - intrinsics are the extra walk, and they are silent

A node is measured once per frame. An intrinsic query, such as `Modifier.width(IntrinsicSize.Min)`
or a policy asking its children how wide they would like to be, walks the subtree again first.
Compose never tells you when you paid for one.

Count them: set `LayoutStats.enabled = true`, run some frames, and read
`LayoutStats.intrinsicQueries`. It costs nothing while off. Put an intrinsic size as close to the
leaves as you can: one near the root walks everything beneath it again.

## Rule 3 - build what draws once, not every frame

The tree composes every frame, so an object built in a composable body is built every frame. Hold
on to what does not change:

- A value derived from inputs: `remember(key) { }`, or `remember(key1, key2) { }`.
- A path, gradient or matrix used to draw: `Modifier.drawWithCache { }`. It rebuilds when the
  node's size, density or layout direction changes, and replays the recorded drawing in between.

Text already does this: each text node keeps its last measurement and glyph run in a
`TextLayoutCache` and reuses them while nothing that shapes the text has changed. Do not shape or
measure text yourself in a composable body.

## Rule 4 - a `remember` key is a cache key, and silent when wrong

`remember` returns the old value until a key changes, by `==`. A key that leaves out an input
ships **silently stale** output. A shadcn style reads the theme *and* switches on a variant, so it
keys on both: `remember(theme, variant) { }`. Keyed on the theme alone, a variant change returns
the last variant's style. Widget-local state is an input too.

The opposite mistake costs time instead: a key that changes every frame, such as a fresh object or
an animating float, rebuilds every frame and the `remember` buys nothing.

There is no vararg `remember`, on purpose: an array per call per frame is the cost it exists to
avoid. Test a cached value by changing each input between two frames and asserting the output
moved.

## Rule 5 - measure, and distrust the measurement's shape

Pick the probe by the question. None of them answers another one's question.

**Bytes and ms per frame, desktop only.** `ComposeFrameProbe` holds a byte ceiling that ratchets
down as fixes land, prints ms/frame beside the total, and splits the bytes by phase.
`TextFrameProbe` does the same for text that does not change. `ConstraintsAllocationProbe` and
`InputAdapterAllocationProbe` in `:awake:compose:ui` cover one subsystem each.

```bash
./gradlew :awake:compose:foundation:desktopTest --tests "*ComposeFrameProbe*" --rerun-tasks -i
```

Desktop-only on purpose: they count with `ThreadMXBean.currentThreadAllocatedBytes`, a JVM API
with no wasm or Native equivalent.

**Bytes per frame in a browser.** The JVM figure does not transfer: Kotlin/Wasm allocates for
calls the JVM runs free (about 28 B for a call that leaves a default to a function of four or more
parameters, the same for a lambda converted to a `fun interface` or a `Comparator`). The WebGPU
backend's stage heap tests (`MovingCameraStageHeapBrowserTest`, `PrepareHeapBreakdownBrowserTest`)
and scene3d's `PlanningHeapBreakdownBrowserTest` measure JS heap growth per stage in Chromium; a
per-item path is cleared there, not by a JVM probe. `ComposeHost.frameCounts` reports what a frame
composed, measured and drew, and `ComposeHost.explainMeasure` names what invalidated a measure.

**Geometry per frame.** `UiFrameCostRatchetTest` (`:awake:ui:shadcn`, `commonTest`) counts mesh
vertices and draw runs for one fixed frame of real shadcn widgets. Counts, not milliseconds: they
are exact, and the backend's upload work is proportional to them. `UiUploadCostBenchmark`
(`:awake:backend:vulkan`) carries the one loose time bound.

**Layout throughput.** `:awake:ui:benchmark` holds kotlinx-benchmark suites
(`FlexLayoutBenchmark`, `LayoutNestingBenchmark`) for the JVM.

**Where a real frame's milliseconds went — running app.** `SceneAppLifecycleRuntime.perfStatsEnabled`
(**F2**, `fn+F2` on a Mac keyboard; not F3/F5, which are browser Find and reload) splits the frame
into UI build, UI wait, UI staging, and sim+render, and turns on the renderer's draw stats.
`ComposeFrameStats` times one host's composition passes on their own. Studio prints the split in
its status bar. This is the only tool that can tell a layout problem from a GPU one.

**Whole-page ms — headless.** Studio's `StudioFramePerfProbeTest` measures its shell.
`FrameSpans` (`:awake:engine:render:testing`) records named spans for a probe like it, so CPU and
GPU timings come out as comparable label-to-ms maps.

Three ways this went wrong in practice:

1. **The scene shape decides what you can see.** `ComposeFrameProbe` has no text in it, so text
   cost went unmeasured until a node-graph canvas at rest turned out to spend most of its frame
   there. Similarly, an empty-HUD probe with zero open signs, badges, or stacked labels reads
   0 B/frame while a crowded town allocates per-frame wrappers and re-measures text every tick.
   Always probe a populated scene shape alongside the empty control.
2. **The ranking reorders after every fix.** Re-profile between changes. The site predicted to
   dominate (draw primitives) never appeared in the profile at all; the real top site was a map
   copy nobody suspected.
3. **Desktop JVM is the forgiving platform — for allocation.** Its young generation is hundreds
   of MB; ART and Kotlin/Native are where allocation rate actually costs pauses. It also hides
   allocation that exists only on Kotlin/Wasm (see "Bytes per frame in a browser" below): a JVM
   probe that reads zero clears nothing for the browser, so go to the browser heap test first for
   a web complaint. But do not
   extend that intuition to CPU time without measuring it. On the old engine the same layout
   scene ran on desktop JVM and in real headless Chrome only **1.23×** apart (0.66 vs 0.82
   ms/frame). A whole-frame regression bigger than that was not coming from layout, whatever the
   platform folklore said.

**Always print a total alongside a per-frame average.** The first desktop run of a frame probe
reported 0.26 ms/frame; the total elapsed contradicted it, and it was a warm-up artifact. Without
the second number a 3× claim would have shipped and sent the next person at the wrong subsystem.

Targets: **≤16 KB/frame** is the ship gate (~1 MB/s, roughly one GC every few seconds on ART).
Dear ImGui and Nuklear run effectively zero steady-state allocation, so this is not aspirational.

## What this does not fix

The retained engine was the rewrite the old rules pointed at: single-pass measurement removed
trial passes, and the opt-in layout cache went with them. By default it does not skip: every
composable runs and every node is measured each frame, so a screen that is slow because it is big
stays slow. The runtime section of Core's `docs/reference/compose-engine/15-compose-parity.md`
says what skipping cost when it was first tried.

Skipping is opt-in and whole-frame. `ComposeHost.skipUnchangedComposition` skips a frame's
composition when no snapshot state it read has changed, and `skipUnchangedMeasure` skips the
measure pass too, but only with composition skipping on and only while nothing read during the
last measure changed. One changed read recomposes or re-measures the whole tree. Two things defeat
it silently:

- **State the snapshot system cannot see.** A composable that reads a plain field or a polled
  getter looks unchanged, and the frame is skipped with stale content. Hold it in `mutableStateOf`,
  or wrap a value owned elsewhere in a `PolledState`. Do not turn the switches on for an app until
  `verifySkippedCompositions` is clean on it.
- **Composing inside measure, and reading the frame clock.** A subcomposition that runs during
  measure (`BoxWithConstraints`) and reads `LocalFrameClock` invalidates measure every frame. Size
  from placement instead, and read the clock in draw, only while something moves.

And do not reach for an engine change to fix a *platform* gap. Web frame time measured ~2.5×
desktop while UI layout measured only 1.23× — so the extra milliseconds were downstream of layout
(GPU submission, buffer uploads, present). Attribute the frame with F2 before choosing a
subsystem. The most expensive mistake available here is a correct fix applied to the wrong layer.
