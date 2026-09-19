# Awake Agent Skills

Public Apache-2.0 execution guidance for the Awake engine. Canonical engine
architecture remains in the [`awake`](https://github.com/awakekt/awake) repository;
this repository owns the technical agent skills, maintenance personas, and installer.

## Ownership

- `skills/awake-*` and the technical personas in `skills/awake/` are maintained Core content,
  including Awake's portable-platform and conformance guidance.
- `kmp-*` skills and commands are vendor dependencies: pin their upstream release in a consumer
  lockfile, never edit deployed copies.
- Studio Pro strategy and creative personas belong in the private
  `awake-studio-agent-skills` overlay and use the `studio-*` namespace.

## Consumer installation

An Awake checkout pins its sources in `.agents/skills.lock.toml`. Bootstrap the public installer
once, then let it verify and materialize the exact lockfile revision:

```bash
git clone https://github.com/awakekt/awake-agent-skills .agents/vendor/awake-agent-skills-bootstrap
python3 .agents/vendor/awake-agent-skills-bootstrap/scripts/install_consumer.py --project .
```

The installer caches immutable source checkouts under `.agents/vendor/` and deploys only the
declared skill and command names to `.agents/skills` and `.agents/commands`.
