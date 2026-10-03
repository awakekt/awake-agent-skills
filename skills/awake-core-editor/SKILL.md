---
name: awake-core-editor
description: Maintain the vendor-neutral editor plugin contract in Awake Core (:awake:editor:contract): its layer boundary, canonical names and verification. Use before changing an editor extension point or provider contract. Plugin authors use awake-editor-plugin-authoring.
license: Apache-2.0
metadata:
  author: awake
  last-updated: '2026-10-03'
  keywords: Awake, Awake Core Editor, EditorPlugin, PluginManifest, EditorProvider, PluginId, PluginRegistry, ProviderRegistry, 3-layer architecture
---

# Awake Core Editor Architecture & Plugin Contracts

The Awake Engine ecosystem is structured into three strictly decoupled architectural layers:

1. **Layer 1: Awake Core Engine (`awakekt/awake`)** (Apache 2.0):
   Runtime libraries required to compile, execute, and ship games on Desktop, iOS, Android, and WASM (`:awake:scene`, `:awake:physics`, `:awake:render`, `:awake:ui:shadcn`, `:awake:project`, etc.).
2. **Layer 2: Awake Core Editor (`awakekt/awake`, `:awake:editor:contract`)** (Apache 2.0):
   Public, vendor-neutral editor contracts, provider extension points, and project plugin metadata published under `com.awakekt.awake.editor:contract`. Allows third-party developers, community creators, and commercial tools to write plugins against an open-source standard.
3. **Layer 3: Awake Studio Pro (`awakekt/awake-studio`)** (Commercial):
   Commercial desktop authoring application (`:app:studio`), visual inspectors, collaborative workflows, and the secure runtime loader (`StudioPluginPipeline`) that verifies signatures, checks permissions, and hosts plugins.

---

## The Core Editor Contract Boundary

All public plugin interfaces live in `:awake:editor:contract`. They are vendor-neutral and intentionally decoupled from Awake Studio internals:

- **Package**: `com.awakekt.awake.editor.core.plugin`
- **License**: Apache 2.0
- **Publish Coordinates**: `com.awakekt.awake.editor:contract`

### Which side of the line

Decision [D35](https://github.com/awakekt/awake/blob/main/docs/architecture/decisions/D35-editor-boundary.md)
is the rule: if a third-party plugin has to implement or read it, it belongs in this contract; if only
the host calls it, it stays in Studio. Add a new extension point here first, with a test and a row in
the [contract README](https://github.com/awakekt/awake/blob/main/awake/editor/contract/README.md)
provider table, then host it in Studio. A kind with no behaviour stays listed as reserved until it
has one.

### Fundamental Rule: Zero Downward or Horizontal Leaks
- `:awake:editor:contract` **must never** depend on `:app:studio` or any commercial plugin in `awakekt/awake-studio`.
- `:awake:editor:contract` only depends on Awake Core modules (`:awake:project`, `:awake:ecs`, etc.).
- Third-party plugins compile strictly against `com.awakekt.awake.editor:contract`.

---

## Canonical Naming Convention

**Do NOT use** the legacy `Editor*` prefixed names. They exist only as deprecated typealiases for migration.
Always use the **canonical names** below when writing new code:

### Plugin-level types (in `EditorPlugin.kt`)

| Canonical (use this) | Deprecated alias (do NOT introduce) |
|---|---|
| `PluginId` | ~~`EditorPluginId`~~ |
| `PluginApiVersion` | ~~`EditorPluginApiVersion`~~ |
| `PluginApi` | ~~`EditorPluginApi`~~ |
| `PluginMetadata` | ~~`EditorPluginMetadata`~~ |
| `PluginLifecycle` | ~~`EditorPluginLifecycle`~~ |
| `PluginRegistry` | ~~`EditorPluginRegistry`~~ |

The interface `EditorPlugin` **keeps** its `Editor` prefix since it is the named extension point that hosts reference — this name is stable and intentional.

### Provider-level types (in `EditorProviders.kt`)

| Canonical (use this) | Deprecated alias (do NOT introduce) |
|---|---|
| `ProviderId` | ~~`EditorProviderId`~~ |
| `ProviderMetadata` | ~~`EditorProviderMetadata`~~ |
| `ProviderConfiguration` | ~~`EditorProviderConfiguration`~~ |
| `ProviderCodec` | ~~`EditorProviderCodec`~~ |
| `ValidationSeverity` | ~~`EditorValidationSeverity`~~ |
| `ValidationMessage` | ~~`EditorValidationMessage`~~ |
| `ProviderRegistry` | ~~`EditorProviders`~~ |
| `ComponentProvider` | ~~`EditorComponentProvider`~~ |
| `AssetProvider` | ~~`EditorAssetProvider`~~ |
| `EnvironmentProvider` | ~~`EditorEnvironmentProvider`~~ |
| `AnimationProvider` | ~~`EditorAnimationProvider`~~ |
| `BuildProvider` | ~~`EditorBuildProvider`~~ |

The interfaces `EditorProvider` and `EditorProviderKind` **keep** their `Editor` prefix — they are the named extension point interfaces that hosts reference.

---

The plugin-facing API (manifest, lifecycle, providers, registries, asset converters, project plugin
references) is documented for plugin authors in `awake-editor-plugin-authoring`. This skill covers
maintaining the contract itself.

---

## Verification & Architecture Checklist

When adding or modifying editor contracts in Awake Core:

1. **API Tracking**: Run `./gradlew :awake:editor:contract:desktopApiDump` then `desktopApiCheck`.
2. **Tests**: `./gradlew :awake:editor:contract:desktopTest`.
3. **Detekt**: Verify zero violations with `./gradlew :awake:editor:contract:detekt`.
4. **No deprecated shims**: Do not introduce `EditorDock`, `EntityPreset`, `V1` suffixes, `contributesDockTab`, or `dockTabTitle`.
   Do not add a vendor tier flag such as `isPro`; the contract names no product. A host maps
   `requiredLicense` to its own tiers.
5. **No re-introduction of old prefixes**: Use canonical names from the table above.
6. **Payload check**: If `PluginManifest.entrypointClass` is non-blank, the `.awakeplugin` archive must have non-empty `payloadBytes` — enforced by `PluginPreflightChecker` in the Pro pipeline.
7. **License & Provenance**: All files in `:awake:editor:contract` must have the Apache-2.0 header and `Ron June Valdoz` copyright notice.
