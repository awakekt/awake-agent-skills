# Awake Agent Skills

Public Apache-2.0 execution guidance for the Awake engine. Canonical engine architecture remains
in the [Awake repository](https://github.com/awakekt/awake); this repository owns technical
skills, maintainer personas, and the consumer installer.

## Ownership

- Awake engine, renderer, UI, platform, and contributor guidance is maintained here.
- KMP skills and commands remain pinned vendor dependencies; do not edit deployed copies.
- Studio Pro strategy and creative personas live in the separate private
  awake-studio-agent-skills repository and use the studio-* namespace.

## Consumer installation

An Awake checkout pins sources in .agents/skills.lock.toml. Bootstrap the public installer, then
let it verify and materialize the exact lockfile revision:

    git clone https://github.com/awakekt/awake-agent-skills .agents/vendor/awake-agent-skills-bootstrap
    python3 .agents/vendor/awake-agent-skills-bootstrap/scripts/install_consumer.py --project .

The installer caches immutable source checkouts under .agents/vendor/ and deploys only declared
skills and commands into the agent-visible directories: .agents/skills and .agents/commands, mirrored
into .claude/skills and .claude/commands for Claude Code. Consumers keep all four gitignored.

Re-running the installer is safe. It changes nothing when every deployment already matches the
lockfile, relinks entries after a lockfile bump, and removes entries it created for skills that
were dropped from the lockfile. It refuses to replace a directory it did not create.

    install_consumer.py --project . --check   # report drift, exit 1 when an install is needed
    install_consumer.py --project . --force   # re-verify pinned sources even when current

## Validation

Run the package verifier and Agent Skills reference validator for every skill directory:

    python3 scripts/verify_bundle.py
    for skill in skills/*; do [ ! -f "$skill/SKILL.md" ] || uvx --from skills-ref agentskills validate "$skill"; done
    pytest scripts/test_install_consumer.py
