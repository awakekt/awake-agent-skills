---
name: awake
description: Route Awake Core maintenance (engine, renderer, UI system, platform, releases) to the right maintainer skill or persona. Use when changing awakekt/awake itself; building a game, tool or editor plugin on Awake uses the awake-game-agent-skills bundle instead.
license: Apache-2.0
metadata:
  author: awake
  last-updated: '2026-10-09'
---

# Awake Maintainer Routing

Pick the maintainer skill for the area you are changing, or an Awake persona (an `awake-*` agent)
for cross-cutting work; the [agent catalog](../../docs/agent-catalog.md) lists each persona's scope.

- Building a game, tool or editor plugin on Awake: the
  [awake-game-agent-skills](https://github.com/awakekt/awake-game-agent-skills) bundle.
- Studio product and creative-production work: the private `awake-studio-agent-skills` bundle.
- Writing or changing a skill: [docs/skill-authoring.md](../../docs/skill-authoring.md).

Architecture policy lives in the Awake repository's `docs/`; skills carry task guidance only.
