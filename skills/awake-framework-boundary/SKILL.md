---
name: awake-framework-boundary
description: >
  Decide whether a proposed capability belongs in the Awake framework or in a consuming game
  repository, and whether a piece of code belongs in a scene module or in a capability module.
  Use before adding any engine module, before extending or adding an option, field, system or
  behaviour to anything under awake/scene/ (scene components, scene schemas, scene systems),
  before moving code from Awake Studio, a sample or a template into Awake Core, before adding a
  gameplay system or a default tuning value, and before introducing networking, persistence,
  server, or MMO-oriented abstractions.
license: Apache-2.0
metadata:
  author: awake
  last-updated: '2026-10-05'
---

# Awake Framework Boundary

## The Three-Layer Ecosystem Architecture

Awake enforces strict boundaries across three distinct architectural layers:

1. **Layer 1: Awake Core Engine (`awakekt/awake`)** (Apache 2.0):
   Runtime engine libraries required to compile, execute, and ship games on Desktop, iOS, Android, and WASM (`:awake:scene`, `:awake:physics`, `:awake:render`, `:awake:ui:shadcn`, `:awake:project`, etc.).
2. **Layer 2: Awake Core Editor (`awakekt/awake`, `:awake:editor:contract`)** (Apache 2.0):
   Public, vendor-neutral editor contracts and extension points (`com.awakekt.awake.editor:contract`). Enables any developer or toolmaker to author editor plugins without closed-source Studio dependencies.
3. **Layer 3: Awake Studio Pro (`awakekt/awake-studio`)** (Commercial):
   Commercial desktop application (`:app:studio`), visual inspectors, collaborative workflows, and the secure runtime loader (`StudioPluginPipeline`).

## Framework vs Game Boundary Rules

1. A future MMORPG is one consumer, not justification for a new Awake module.
2. Prefer consumer-side composition. Promote only after two credible consumers demonstrate the
   same stable need, or a concrete public-API limitation makes that impossible.
3. Keep accounts, combat, quests, inventories, economy, zones, shards, protocol messages,
   databases, authentication, and live operations in the consuming game.
4. A promoted capability exposes the smallest backend-neutral contract and must not make a
   network library, database, renderer, or UI stack mandatory for ECS/core runtime modules.
5. Record exceptions with consumers, missing API, contract owner, excluded policy, dependency
   direction, and validation plan.
6. Keep water, biomes, vegetation, prop placement, procedural generation, and game assets in a
   consumer/private pack. Awake may supply neutral terrain data and extension seams, never the
   authored world policy.

7. Core ships mechanisms, not feel. Gameplay tuning (move and jump speed, gravity, camera follow
   distance and pitch, input bindings, on-screen control layout) is never a constant in Core code.
   It is a field on a scene component with a neutral default, and the template or game authors the
   value in scene data.
8. Movement that needs ground, slopes or collisions goes through the physics character controller
   binding (`scene:physics`). A hand-rolled gravity or ground-snap system is game code, however
   small.
9. Template and sample art (an arena floor, demo materials, placeholder characters) is a project
   asset the template writes. Core built-ins are neutral primitives only, such as `cube`, `sphere`
   and `plane`.

Use `awake-architecture-auditor` (`skills/awake/agents/awake-architecture-auditor.md`) for the
decision; where that persona is not installed, apply these rules directly and record rule 5 in the
PR. Use implementation skills only after it.

## Where a Capability Lives

| Capability | Home | Examples |
|---|---|---|
| Anything a shipped game needs at runtime, when it is neutral engine capability | Awake Core (`awakekt/awake`, Apache 2.0, Maven Central) | Texture/UV animation on a material, a surface-shader provider seam, scene depth and time inputs, terrain data, navigation |
| Authored world policy and game rules | The consuming game or content pack | A water look, biomes, vegetation, prop placement, importers for a legacy format |
| Authoring productivity, team and cloud workflows | Studio Pro (`awakekt/awake-studio`, commercial) | Visual node editors, generators, river/lake and flow-painting tools. Placement is scored by the private `studio-capability-scoring` skill. |
| Public starting point for a new game | `awake-template` | Build setup and a minimal scene |

- Runtime is never commercial: whatever a Studio scene uses must run from Awake Core or the
  game's own code, and a Pro tool emits data that runtime reads. A capability moves from a pack
  to Core only by rules 2 and 5. Neither Core nor its editor contract depends on Studio Pro.
- There is no separate "starter kits" repository; it was retired unused. Do not route there.

## Promoting Code From Studio, a Sample or a Template

"Runtime is never commercial" moves the *mechanism and its scene data* into Core, never the
template's choices. Before moving a file:

1. Split it into mechanism (a component, its binding, a system that reads the component) and
   values (numbers, layouts, asset names, which systems a template turns on).
2. Move only the mechanism. Give every value a scene-component field, and have the template write
   the value it used to hard-code.
3. If a system only works for one template's world (a flat floor, a fixed arena, one camera
   style), it is template code. Replace it with the general mechanism, or leave it in the template.
4. A module that loads and runs whole projects is composition, not scene binding: it fails the
   admission test below and lives outside `scene:*`, for example under `awake:project`.
5. Record the promotion under rule 5 in the PR, naming what stayed behind as data.

Worked example (2026-09): a first project player moved a third-person template's camera numbers,
a flat-floor jump, a checkered arena mesh and a fixed touch-control layout into
`awake:scene:player`. It was reworked into data-driven scene components (camera rig, character
controller, canvas controls), a thin project runtime, and template-owned assets.

## What Belongs in `awake:scene:*` (The Scene-Binding Boundary)

**`awake:scene:*` = the scene-binding layer only.**
A module belongs under `awake:scene:*` if and only if its primary job is to **bind an engine capability into the ECS scene graph** as components and systems. The capability's own API lives outside `scene/`; the `scene:*` module is only the ECS glue.

### The Admission Test (Two Questions)

1. **Does it manipulate the scene graph or scene document directly?**
   (Transform, Entity hierarchy, scene serialization, scene lifecycle)
2. **Is it the binding layer between `scene-core` and an external capability?**
   (e.g. `scene:physics` = ECS glue between `physics:api` and ECS entities)

- If **yes to either** → belongs in `awake:scene:*` (e.g., `scene:scene-core`, `scene:physics`, `scene:rendering`, `scene:runtime`, `scene:authoring`).
- If **no to both** → top-level module (e.g., `awake:navigation`, `awake:ai`, `awake:ai:behavior`).

```
New capability X:
  Has its own API contract independent of the scene? -> awake:X (top-level)
  Needs to bind X into ECS entities/components?     -> awake:scene:X (scene binding layer)
  Both?                                              -> awake:X:api + awake:scene:X
```

The test places a module. It does not let a capability's logic ride along inside `awake:scene:X`:
the algorithms and state stay in `awake:X`, and the next section sorts every piece of a change.

## Scene Is The Wrapper, Not The Home For Capabilities

Awake is a library first. `awake:scene:*` binds capabilities into the ECS scene graph and the scene
document; a capability's logic must not live there. Run this section before you add to or change
anything under `awake/scene/`: extending a component, adding an option or field to a schema, adding
a system, or adding behaviour to one that exists.

### Sort every piece

- **Scene** (stays in `awake:scene:<x>`): a document schema (`Scene<X>`) and its validation; the
  component binding; the mapping from schema to the capability's types; the system that runs the
  capability over the ECS world; loading a document's assets.
- **Capability** (its own module outside `scene/`): an algorithm, state or behaviour with its own
  API that someone could use without a scene, such as simulation, sampling, culling, clocks and
  curves.

### Rules

1. A capability module depends on no `scene:*` module. `awakekt/awake` enforces this with the
   `verifyCapabilityLayering` Gradle gate.
2. A capability's types never hold a `Scene*` schema type. The scene module maps schema to
   capability types in one mapping file. An exposure test fails when a capability option is neither
   mapped from a scene field nor listed as code-only.
3. To extend a capability that still lives in a scene module, extract it first, or say in the PR
   that it is debt and why.
4. A new option is added in this order: capability type, scene field, mapping, docs, exposure test.

### Before you edit

- Name the thing you are adding and sort it: scene piece or capability piece.
- A capability piece needs a home outside `scene/`. If it has none, extract it or record the debt
  under rule 3.
- A capability piece must compile and be testable with no `scene:*` module on its classpath. If it
  does not, a scene type leaked in: move that type back to the mapping.
- A scene piece needs its schema field, its mapping line, its validation and its docs.
- Add or update the exposure test, and list a code-only option as code-only, never silently.

### Worked example

Particles are the pattern. `awake:particles` is the capability: the simulation and its own emitter
types, with no `scene:*` dependency. `awake:scene:particles` is the wrapper: the `Scene*` schema, the
component, the one mapping file from schema to `awake:particles` types, and the system that steps
emitters over the `World`. A new particle option is a field on the capability's type, a field on the
schema, one mapping line, docs, and a passing exposure test.

`awake:core:audio` plus `awake:scene:audio` is an existing split of the same shape: the player,
clips and decoding live in `core:audio` with no scene dependency, and `scene:audio` holds the
`AudioSource` component and the `AudioSystem` that runs it over the `World`.

