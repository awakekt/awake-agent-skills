# Awake Core Agent Catalog

This public catalog routes technical Awake maintenance to the right persona. Canonical architecture
policy remains in the [Awake repository](https://github.com/awakekt/awake/tree/main/docs).

## Ownership

Public personas cover engine maintenance only. Public awake-* skills cover engine, renderer, UI,
platform, and contributor guidance. Studio Pro strategy and creative production roles belong to
the separate private Studio bundle; public consumers never pin that private source.

Use names that make the actual capability or professional role discoverable within the awake
namespace. Review every ID by the same standard; retain accurate names and rename only for a
demonstrable ambiguity, mismatch, or specification violation, not cosmetic consistency.

| Persona | Scope |
|---|---|
| awake-engine-core-engineer | Core math, ECS, scene, asset, and engine capabilities |
| awake-render-backend-engineer | Vulkan, WebGPU, physics bridges, and render evidence |
| awake-ui-engineer | Awake UI runtime, shadcn parity, and visual verification |
| awake-game-runtime-engineer | Application composition, runtime lifecycle, and samples |
| awake-platform-release-engineer | KMP targets, build logic, CI, documentation, and releases |
| awake-architecture-auditor | Module boundaries and framework-versus-game decisions |
| awake-docs-maintainer | Documentation, entrypoint, and catalog consistency |

## Model tiers

Use flagship-coding for deep backend and cross-module work, balanced-coding for everyday
implementation and verification, and fast-utility for bounded mechanical tasks. Provider model
identifiers belong to the runner configuration.

## Change process

Add a domain skill before adding a persona. Add a persona only when its ownership, independent
verification, and handoff boundary are clear. Validate with python3 scripts/verify_bundle.py and
update consumer pins through reviewed changes.
