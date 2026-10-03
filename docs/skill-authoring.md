# Writing an Awake skill

One standard for every Awake skill bundle: `awake-agent-skills`, `awake-game-agent-skills` and
`awake-studio-agent-skills`. `scripts/verify_bundle.py` enforces the rules marked **(checked)**.

## Pick the bundle

| The skill helps someone... | Bundle | Namespace |
|---|---|---|
| build a game, tool or editor plugin on Awake | `awake-game-agent-skills` | `awake-*` |
| change Awake Core itself | `awake-agent-skills` | `awake-*` |
| make Studio product or creative-production decisions | `awake-studio-agent-skills` (private) | `studio-*` |

A skill lives in exactly one bundle. If it serves two readers, split it by reader, as
`awake-core-editor` (maintaining the contract) and `awake-editor-plugin-authoring` (writing a plugin)
do.

## Frontmatter

```yaml
---
name: awake-example            # (checked) matches the directory, lowercase-hyphen, bundle namespace
description: >                 # (checked) 1-1024 chars: what it does, then "Use before/when ..."
  Do X with Y. Use before adding Z or changing W.
license: Apache-2.0            # (checked) the bundle's license
metadata:
  author: awake
  last-updated: '2026-10-03'   # (checked) ISO date, never in the future
---
```

The description is what an agent reads to decide whether to load the skill, so lead with the task
and name its trigger.

## Body

- Start with one `# Title` **(checked)**, then the rules. Imperative, short, specific to Awake.
- Keep `SKILL.md` under 250 lines **(checked)**. Move long tables, worked examples and source notes
  to `references/<topic>.md` and link them.
- Links stay inside the bundle or use a full URL **(checked)**. Link to another bundle's skill by
  its GitHub URL. Never reference a local path or a deployed `.agents/` copy **(checked)**.
- Cite real module, type and file names from the current code. A skill that describes code which
  moved is a bug; fix it in the same change that moves the code.
- No investigation narration, dated incident stories, or competitor and third-party game names.

## Register it

Add a row to the bundle README's skill table **(checked: every skill listed once, nothing
stale)**. Consumers pick it up on their next lock bump.
