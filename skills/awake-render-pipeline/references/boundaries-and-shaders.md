# Render boundaries and shaders

## Shader source

UI shaders are authored in the shared ASL definitions in awake:asset:shader-pack, not independently
in Vulkan GLSL and WebGPU WGSL. After changing ASL, run
./gradlew :awake:asset:shader-pack:generateAslShaders. Generated shader resources are reviewable
outputs, not authoring locations. Compare uniforms, locations, varyings, bindings, and entrypoints
with live backend resources before changing a definition. If the shared definition cannot preserve
an existing ABI, record the gap instead of silently generating an incompatible shader.

If an existing shader cannot yet be represented without changing its ABI, record the migration
gap instead of generating an incompatible replacement. Fragment derivatives such as fwidth are
valid in generated GPU shaders but not meaningful in the CPU ASL evaluator.

## HAL and render graph

Awake rendering has two layers:

| Layer | Owns |
|---|---|
| Hardware abstraction: render:contract, GpuDevice, Renderer | Pipelines, buffers, textures, samplers, swapchain, command recording, viewport/scissor, readback, and generic GPU pass/draw packets |
| Render graph: render:passes, shader-pack, scene:rendering | Scene lights/cameras, render features, authored content, scene defaults, shadow algorithms, and lowering scene data into generic GPU packets |

The backend must not gain SceneLight, Lens, EnvironmentUniforms, ScenePassDescriptor, shadow
cascade, skybox, particle, fog, or other scene-specific concepts. Pack those values above the HAL
into generic bytes and pass executions. A candidate contract type belongs in render:contract only
if another backend could implement it unchanged without understanding its scene content.

Renderer consumes GpuPassInput; render:passes prepares generic draw requests using GPU resource
handles and draw state. Uniform ABI writes use UniformLayout and UniformWriter with named fields.
The root verifyRenderUniforms task checks production sources, and verifyRenderContractBoundary
protects the contract boundary.

## Clip space and cubemaps

When a shader samples screen-space textures, reconstructs world positions, unprojects rays, or
inspects cubemap faces, use the shared helpers rather than hand-written backend branches:

- Vulkan uses X/Y in [-1, 1], downward Y, and Z in [0, 1]; WebGPU uses X/Y in [-1, 1], upward Y,
  and Z in [0, 1].
- Use ndcToUv or ClipSpace.toNormalizedCoords for NDC-to-UV mapping.
- Use unprojectFarRay for sky/atmospheric rays and unprojectClipToWorld for depth reconstruction.
  Inverse view-projection already accounts for the active projection; do not add a second
  backend-specific Y flip.
- Use CubemapFaces.Faces and CubemapFaces.lens(eye, faceIndex, near, far), which creates the
  square-aspect, 90-degree-FOV lens. Side faces use DOWN as up; +Y uses +Z and -Y uses -Z.
