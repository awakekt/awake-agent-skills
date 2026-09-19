# Awake Repo-Local Skills

This folder contains Awake's public technical skill and agent files. It is published by this
repository and materialized in a consumer only from that consumer's reviewed lockfile.

## What Lives Here

- `agents/*.md`
  - Engine Framework Suite definitions: core, render, UI, runtime, platform, auditor, and documentation
- `commands/*.md`
  - Repo-local operational commands such as audits, review helpers, and semantic UI crop/diff workflows
- `templates/*.md`
  - Reusable starter templates for new repo-local agent docs

## What Does Not Live Here

- canonical architecture policy
- stable module ownership rules
- long-form project technical guidance

Those belong in:

- [architecture](https://github.com/awakekt/awake/blob/main/docs/architecture.md)
- [AI collaboration](https://github.com/awakekt/awake/blob/main/docs/reference/ai-collaboration.md)
- [UI ownership](https://github.com/awakekt/awake/blob/main/docs/reference/ui-ownership.md)
- [game structure](https://github.com/awakekt/awake/blob/main/docs/reference/game-structure.md)

## Agent Naming

Public agent files must follow the naming standard in [the public agent catalog](../../docs/agent-catalog.md):

- `awake-<domain>-<role>.md`
- professional role suffixes only (`engineer`, `auditor`, `director`, `designer`, `producer`)
- no informal names such as `*-dev`

## Agent Model Field

Repo-local agent frontmatter maintains active provider model IDs (e.g. `claude-opus-5`, `claude-sonnet-5`) required by runner tooling (Claude Code dispatch), corresponding to Awake's capability tiers (`flagship-coding`, `balanced-coding`, `fast-utility`).
See [the public agent catalog](../../docs/agent-catalog.md) for provider mappings.

## Working Rule

- `docs/*` is the source of truth
- `skills/*` is execution guidance
- a deployed consumer copy is immutable; change this source repository and release a new pin instead
