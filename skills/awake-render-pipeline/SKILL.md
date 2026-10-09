---
name: awake-render-pipeline
description: Structure Awake render features, pipelines, materials, and cross-backend rendering. Use before changing Renderer, adding a render pass, modifying draw batching, or moving rendering logic between Vulkan and WebGPU.
license: Apache-2.0
metadata:
  author: awake
  last-updated: '2026-10-09'
---

# Awake render pipeline guidance

Before changing Renderer, a render-contract type, or a backend renderer, read the Awake
[render hardware interface](https://github.com/awakekt/awake/blob/main/docs/reference/render-hardware-interface.md)
and [render extensibility rules](https://github.com/awakekt/awake/blob/main/docs/reference/render-extensibility.md).
The first defines the hardware boundary; the second decides whether a capability belongs in the
shared render graph or an optional authored feature.

## Choose the relevant detail

| Task | Read |
|---|---|
| Shader source, HAL/render-graph ownership, clip space, or unprojection | [Boundaries and shaders](references/boundaries-and-shaders.md) |
| RenderFeature, pipeline/material ownership, batching, or app lifecycle | [Features and composition](references/features-and-composition.md) |
| Module placement, Vulkan/WebGPU sharing, backend invariants, or uniform writes | [Cross-backend rules](references/cross-backend-rules.md) |
| Border, outline, ring, or another draw decoration | [Draw primitives](references/draw-primitives.md) |

## Invariants to keep in view

- Backends implement hardware operations. Scene vocabulary, authored content, and scene-to-GPU
  lowering stay above the HAL; only generic, pre-packed GPU work crosses into a backend.
- Make cross-backend decisions once in a shared layer. A capability may differ by backend, but
  duplicated decisions and algorithms are defects.
- VertexFormat selects the pipeline; Material supplies data and does not choose a pipeline.
- Preserve ordered feature dispatch and UI paint order. Never apply 3D material/pipeline sorting
  to order-sensitive UI draws.
- Derive GPU layout and uniform data from the shared typed schemas and writers; do not hand-code
  sizes, offsets, field indices, or packed arrays.
