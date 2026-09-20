# Cross-backend rendering rules

## Module placement

| Module | Owns | Excludes |
|---|---|---|
| render:contract | Stable backend-neutral contracts, GPU data shapes, vertex semantics/formats, resource handles, low-level layout vocabulary | Driver types/calls, rendering policy, source draw packets, scene lowering, filesystem output, test helpers |
| render:passes | Shared render algorithms, features, draw preparation, vertex/uniform writers, batching, pass ordering | Backend types, UI framework vocabulary, desktop/platform I/O |
| render:passes2d | Shared 2D coalescing, mesh upload/recording ports, and algorithms | Widgets, layout/state/theme, backend objects, paint-order sorting |
| render:testing | Cross-platform pixel buffers, offscreen-capture lifetime, assertions, and diagnostic writers | Production renderer APIs, backend construction, application/game content |
| Vulkan/WebGPU backends | Driver bindings, GPU resource allocation/recording, backend-specific caches and fixtures | Shared decisions, CPU render algorithms, UI/game content, reusable cross-backend tests |

Put a stable shape or port in contract, an algorithm using it in passes, and a diagnostic in
render:testing. Backend code is for behavior that must name a specific driver.

## Shared data and backend invariants

- Make common or symmetric rendering decisions once. If both backends decide the same thing,
  move that decision to the shared layer.
- Derive vertex locations, formats, strides, and offsets from VertexFormat/GpuDataShape;
  uniform size and contents from UniformLayout/UniformFields/UniformWriter; colors from the
  shared Color type. Never duplicate typed values as numeric constants, field indices, or
  concatenated FloatArrays.
- Shared APIs must be implementable by a third backend and use the common capability intersection.
  Vulkan-only features belong behind optional capability interfaces; the shared core must not
  require raw Vk types, descriptor indices, or explicit barriers.
- Backend source handles hardware only. Scene/content concepts and scene defaults stay above the
  HAL. Keep the backend-layering and render-contract verification gates passing; do not grow
  exemptions to accommodate new content knowledge.
- A one-backend capability can be valid when the gap is explicit. A one-backend decision about
  shared pipeline/feature selection is duplication and must be moved up or documented at its
  declaration.
- Do not use expect/actual to require matching backend algorithms. Use shared algorithms and
  backend-implemented ports; reserve expect/actual for platform primitives.

Before adding an adapter or indirection, verify that the shared RHI already has the necessary
hardware primitive. An adapter cannot remove duplication if the underlying contract cannot express
the operation.

## Review checklist

- Shared algorithms and feature order are not duplicated between backends.
- Backend declarations contain no authored scene vocabulary or defaults.
- GPU layouts are derived from canonical schemas; uniform writes use named shared fields.
- UI paint order is preserved; material sorting applies only where order is not observable.
- New capabilities pass the third-backend test and document any genuine backend gap.
- Run verifyRenderUniforms, verifyRenderContractBoundary, verifyBackendLayering, and the relevant
  backend tests before review.
