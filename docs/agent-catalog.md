# Awake Core Agent Catalog

This public catalog is the source of truth for the technical personas shipped by
`awakekt/awake-agent-skills`. Awake architecture policy remains in the
[Awake repository](https://github.com/awakekt/awake/tree/main/docs).

## Naming and ownership

Public personas use `awake-<domain>-<role>.md`, use a professional role suffix, and cover
engine maintenance only. Public `awake-*` skills are engine, renderer, UI, platform, or
contributor guidance. They never contain Studio Pro strategy, commercial operations, or creative
game-production personas.

| Persona | Scope |
|---|---|
| `awake-engine-core-engineer` | Core math, ECS, scene, asset, and engine capabilities |
| `awake-render-backend-engineer` | Vulkan, WebGPU, physics bridges, and render evidence |
| `awake-ui-engineer` | Awake UI runtime, shadcn parity, and visual verification |
| `awake-game-runtime-engineer` | Application composition, runtime lifecycle, and samples |
| `awake-platform-release-engineer` | KMP targets, build logic, CI, documentation, and releases |
| `awake-architecture-auditor` | Module boundaries and framework-versus-game decisions |
| `awake-docs-maintainer` | Documentation, entrypoint, and catalog consistency |

The private `awakekt/awake-studio-agent-skills` overlay owns all `studio-*` personas, including
creative roles and Pro scoring. A Studio overlay may extend these public skills but cannot replace
them. Public consumers never list that private source in their lockfile.

## Model tiers

Use `flagship-coding` for deep backends and cross-module audits, `balanced-coding` for everyday
implementation and verification, and `fast-utility` for bounded mechanical work. Provider model
identifiers are runner configuration, not engine architecture policy; keep them valid for the
runner that consumes the bundle.

## Change process

Add a domain skill before adding a persona. Add a persona only when its subsystem ownership,
independent verification harness, and end-to-end handoff boundary are all clear. Validate the
package with `python3 scripts/verify_bundle.py`, release it, and update consumer lockfiles through
reviewed commits.
