---
name: awake-memory-lifecycle
description: >
  Retained heap lifecycle, cache eviction, and CPU-to-GPU release rules for Awake Core resolvers,
  ECS systems, and render backends. Use before adding a cache, map/set field in a System or
  SceneAssetResolver, GPU texture/mesh uploader, or new model/LOD/skinning asset path.
license: Apache-2.0
metadata:
  author: awake
  last-updated: '2026-11-22'
---

# Awake Memory Lifecycle

Per-frame allocation rate is governed by [awake-ui-performance](../awake-ui-performance/SKILL.md)
and [awake-core-math](https://github.com/awakekt/awake-game-agent-skills/blob/main/skills/awake-core-math/SKILL.md).
This skill governs **retained live heap** across streaming load, upload, unload, and teardown
cycles. Android caps `largeHeap` at 512 MiB regardless of device RAM, so unbounded CPU copies or
unpruned runtime maps trigger out-of-memory kills or GC thrashing within minutes of streaming.

## Rule 1 — Every mutable map or set in a `System` or `SceneAssetResolver` names its eviction owner

A `getOrPut`-only cache in a long-lived `System`, `SceneAssetResolver`, or `Renderer` is a leak in
a streamed world. Before adding a map or set field, decide and implement all three:

1. **What removes an entry** (entity removal/destroy, GPU upload completion, refcount reaching 0,
   or an explicit byte/entry LRU cap).
2. **What clears the whole map** (`close()`, `dispose()`, or `forget()`). `close()` must drop
   retained entries, not merely cancel coroutines or close channels.
3. **Who tests the removal path** (a unit test asserting the map returns to empty after unload or
   `close()`).

## Rule 2 — Never key a hash map or hash set by a mutable `data class`

Any Kotlin `data class` with a `var` property in its primary constructor mutates `hashCode()` and
`equals()` after insertion (for example `TerrainComponent.isVisible` and `TerrainComponent.revision`).
Mutating that field strands the entry in its old bucket: subsequent lookups miss, `getOrPut` inserts
a duplicate, and `remove(key)` silently fails.

- Key system side tables by `Entity` or an immutable ID whenever possible.
- If a public binary-compatible map field already keys on a mutable component (such as
  `TerrainClipmapSystem.trackersByTerrain`), fall back to reference-identity lookup (`===`),
  re-bucket on hit, and prune by reference identity against live world components.

## Rule 3 — Drop CPU asset copies once uploaded to the GPU

Decoded pixels (`DecodedImage`, RGBA8 `ByteArray`) and parsed geometry (`MeshGeometry`, `GltfMesh`,
`LoadedPrimitive`) are 4–15× larger than compressed files on disk and duplicate VRAM once uploaded.

- **Decoded 2D images**: wrap file-backed images with `decodeImage(bytes).asReleasingGpuImageSource(bytes)`
  rather than `asGpuImageSource()` (`AssetSourceTextureResolver`, `GltfAssetResolver`). On non-browser
  targets the first `readRgba8()` drops the decoded bitmap immediately; browsers keep their GPU
  `ImageBitmap` path automatically.
- **Releasable glTF models (`GltfAssetResolver.releaseAfterUpload`)**: every asset variant must
  honor release-after-upload — **static meshes, `MSFT_lod` levels, and skinned parts/scenes**:
  - Do not bail out of `dropUploadedGeometry` for LOD models or skinned parts. Normalize `lod<k>:`
    prefixes in `modelPath()` and `GltfReleases`, clear `levelBases` once every level of a base
    mesh uploads, and ensure `SceneAssetLibrary.loadMesh` + `SpawnedModels.mustLoad` reload any
    evicted LOD level before `attachLevels`.
  - Do not parse an unused static fallback mesh into `loadedStaticMeshes` when a `.gltf` already
    has `skinnedNodes`.
  - When releasing a skinned model's images or geometry, strip raw `baseColorImageBytes` /
    `emissiveImageBytes` and vertex/index arrays from `loadedScenes` and `loadedParts` while
    preserving `skeleton`, `skins`, `clips`, and `skinnedNodes` for `getLoadedScene`.
  - Restore the full scene and parts in `adoptLoaded` whenever `loadMesh` or `loadMaterial`
    re-reads a released model.
- **Never opt a new feature out of release silently.** Adding a new glTF extension, PBR map, or
  LOD path requires extending release and reload coverage in the same PR.

## Rule 4 — Verify retention with load → upload → unload → reload tests

Allocation-per-frame probes do not catch live-heap leaks. Any PR that changes a resolver, asset
cache, or streaming system must include a test verifying:

1. Releasable CPU pixels/geometry are dropped after upload (`needsDecode == true`, `isMeshLetGo`,
   `isMaterialLetGo`, or live-heap drop after garbage collection).
2. Unloading entities/cells leaves system/library maps empty and re-spawning reloads cleanly.
3. Calling `close()` / `dispose()` clears internal caches.
