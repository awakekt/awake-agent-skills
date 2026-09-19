---
name: awake
description: >
  Public execution guidance for technical Awake engine maintenance. Contains core, render, UI, runtime,
  platform, and documentation personas plus review commands and templates. Studio Pro and creative personas
  are supplied only by the private studio overlay.
---

# Awake Repo-Local Skills

See [README.md](README.md) for the full breakdown of what lives here, what doesn't,
agent naming conventions, and the agent model-tier field.

- `agents/*.md` — role-specific execution guidance for Awake's public Engine Framework Suite
- `commands/*.md` — repo-local operational commands (audits, review helpers)
- `templates/*.md` — starter templates for new repo-local agent docs

Canonical architecture policy and module ownership rules live in the Awake checkout's `docs/*`, not here.
This is execution guidance, not the source of truth.

## Release Execution Policy
See the Awake checkout's `docs/release-process.md` for complete branching, versioning, and changelog rules.
To cut a release, run:
```bash
./scripts/release.py cut [--channel dev|alpha|beta|rc|stable]
```
