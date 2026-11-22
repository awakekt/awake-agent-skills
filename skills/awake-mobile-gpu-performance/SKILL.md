---
name: awake-mobile-gpu-performance
description: >
  Mobile tile-based GPU (Adreno/Mali) fragment, bandwidth, and render-pass rules for Awake Core
  shaders, materials, and Vulkan/WebGPU passes. Use before editing ASL shaders, shadow sampling,
  terrain shaders, post/outline passes, or auxiliary render targets.
license: Apache-2.0
metadata:
  author: awake
  last-updated: '2026-11-22'
---

# Awake Mobile GPU Performance

Desktop GPUs and Lavapipe hide fragment overdraw, texture bandwidth, and extra render passes that
cut frame rate in half on mobile tile-based deferred renderers (Adreno, Mali). Pair this skill with
[awake-render-pipeline](../awake-render-pipeline/SKILL.md) and
[awake-render-vulkan](../awake-render-vulkan/SKILL.md) before changing shaders or passes.

## Rule 1 — Never pay per-pixel work for inactive features

Every fragment instruction and texture fetch runs across the full scene target every frame. Guard
optional or zero-contribution work before touching memory or transcendentals:

- **Shadows (`cascadeShadowSampling`)**: return `1.0` / `-1` immediately when the active cascade
  count is `< 1` (shadows disabled) or `viewDepth` exceeds the last active cascade's reach — before
  `sqrt`, `textureDimensions`, `normalize`, or the cascade loop — and skip unused cascade slots.
- **Terrain layer blending (`terrainLayersShader`)**: guard each slot's `layerParams` fetch,
  tiling `pow()`, and `albedoLayers` fetch inside a positive-share `iff`, and guard height-blend
  math inside a positive-sharpness `iff` so single-layer pixels and linear palettes
  (`blendSharpness == 0`) do not pay for unused slots.
- **Full-screen overlays and outlines**: skip the pass completely when no drawable uses the style,
  and scissor the draw to affected screen bounds instead of shading every pixel of the frame.

## Rule 2 — Compute UV derivatives once in uniform control flow for guarded fetches

WGSL forbids implicit-derivative `textureSample` inside non-uniform `iff` branches. Do not remove
the `iff` guard to satisfy WGSL validation — instead:

1. Compute `dpdx(uv)` and `dpdy(uv)` once in uniform control flow before the branch.
2. Sample inside `iff(...)` with explicit gradients (`textureSampleGrad` for 2D textures or the
   2D-array gradient builtin in `awake:asset:shader-dsl`), scaling the precomputed derivatives by
   each layer's inverse tiling.

## Rule 3 — Size auxiliary render targets to the scene, never a hardcoded constant

Never allocate full-precision or fixed-size auxiliary buffers (such as `2048×2048` `D32_SFLOAT`
arrays) independent of render scale. On mobile, auxiliary masks and intermediate targets must scale
with the scene render target and use the narrowest format and layer count the feature needs.

## Rule 4 — Minimize native-resolution load/store passes on TBDR

Each separate render pass on the swapchain image forces a tile-based GPU to write the full native
framebuffer out to DRAM and read it back on the next pass:

- Combine consecutive passes targeting the same attachment (for example, drawing a scaled frame's
  upscale and UI in one swapchain render pass rather than clear + upscale + UI passes).
- Prefer `LOAD_OP_DONT_CARE` / `STORE_OP_DONT_CARE` for transient depth and intermediate targets
  whose contents are not needed across passes.
- Keep `Low` mobile quality defaults free of anisotropic filtering and expensive multi-tap PCF.
- **Never let a consumer quality override silently escalate a mobile preset above Core's mobile
  budget**: `RenderQualitySettings.shadowBudgetOverride` and `effectQualityOverride` on mobile
  `Auto` / `Low` / `Medium` presets must stay at or below `ShadowBudget.Reduced` (2 × 1024²) and
  16-bit shadow depth; reserve `ShadowBudget.Default` (3 × 2048²) for explicit `High` or desktop
  presets, and lock mobile tier ceilings with a preset-budget unit test.

## Rule 5 — Guard shader and pass costs with automated tests

Visual parity tests catch wrong pixels, not wasted work. Pair shader and pass changes with tests:

- **Shader WGSL assertions**: verify emitted WGSL contains expected early-outs (`if (cascadeCount < 1)`,
  `if (viewDepth > ...)`), guarded `textureSampleGrad` fetches, and guarded height-blend blocks
  (see `ShadowFadeShaderTest` and `PagedTerrainLayersShaderTest`).
- **Pass-count and RT-size assertions**: verify scaled frames do not add extra swapchain render
  passes or allocate unscaled auxiliary buffers.
