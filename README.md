# Awake Agent Skills

Agent skills for maintaining Awake Core (`awakekt/awake`): the engine, renderer, UI system,
platform layer and releases. This repository also ships the skill installer and lockfile tools that
every Awake project uses. Building a game on Awake? Use
[awake-game-agent-skills](https://github.com/awakekt/awake-game-agent-skills).

## Awake repositories

| Repository | Visibility | Holds |
|---|---|---|
| [awakekt/awake](https://github.com/awakekt/awake) | Public, Apache-2.0 | Awake Core: the engine runtime and the editor plugin contract |
| [awakekt/awake-template](https://github.com/awakekt/awake-template) | Public | The starting project for a new game |
| awakekt/awake-studio | Private, AGPL-3.0 or commercial | Awake Studio: the editor app, its editor library and commercial plugins |
| [awakekt/awake-agent-skills](https://github.com/awakekt/awake-agent-skills) | Public, Apache-2.0 | Skills for maintaining Awake Core, maintainer personas, and the skill installer |
| [awakekt/awake-game-agent-skills](https://github.com/awakekt/awake-game-agent-skills) | Public, Apache-2.0 | Skills for building games, tools and editor plugins on Awake |
| awakekt/awake-studio-agent-skills | Private | Studio tier placement and creative-production personas |

Each project pins the bundles it needs in `.agents/skills.lock.toml`:

| Project | Bundles |
|---|---|
| awake | agent skills, game skills |
| awake-studio | agent skills, game skills, studio skills |
| awake-template and new games | game skills |

## Skills

| Skill | Use it for |
|---|---|
| `awake` | Route Awake Core maintenance (engine, renderer, UI system, platform, releases) to the right maintainer skill or persona |
| `awake-copyright-provenance` | Record and verify lawful provenance before adapting or copying source into Awake |
| `awake-core-editor` | Maintain the vendor-neutral editor plugin contract in Awake Core (:awake:editor:contract): its layer boundary, canonical names and verification |
| `awake-framework-boundary` | Decide whether a proposed capability belongs in the Awake framework or in a consuming game repository |
| `awake-milestone-workflow` | Repository hygiene, GitHub milestone tracking, and commit squashing workflow for Awake Engine |
| `awake-physics-jolt` | Rules and invariants for Awake's physics system (`awake:physics:api` and `awake:backend:jolt` C++ bridge) |
| `awake-platform-capability-design` | Design, extract and test a portable Awake Core capability (storage, paths, handles, codecs, asset sources, browser persistence), weakest platform first |
| `awake-render-headless-verification` | Verify what the engine actually renders, without a window |
| `awake-render-pipeline` | Structure Awake render features, pipelines, materials, and cross-backend rendering |
| `awake-render-vulkan` | Rules and invariants for Awake's Vulkan rendering backend (`awake:backend:vulkan` and its JNI/C++ bindings) |
| `awake-render-webgpu` | Rules and invariants for Awake's WebGPU rendering backend (`awake:backend:webgpu` and wgpu4k/Dawn integration) |
| `awake-shadcn-parity-workflow` | Verify Awake shadcn components end to end, from the pinned official reference through the standalone recipe and the real showcase/catalog shell |
| `awake-shadcn-recipe-authoring` | Maintainer-facing how-to for BUILDING/EXTENDING shadcn-flavored components inside Awake's ui-designsystem itself -- not for an app/sample that just calls an existing shadcn* component |
| `awake-ui-authoring` | Which UI layer to write in - Compose Foundation, Material 3, or shadcn - and the size/spacing rules that keep them separate |
| `awake-ui-icons` | How icon vector data enters Awake - official SVGs generated into ImageVector objects by the icon-codegen Gradle plugin, never hand-transcribed |
| `awake-ui-performance` | What makes an Awake UI frame expensive, and the traps that make a change silently cost more than it looks |
| `awake-ui-verification` | Verify Awake UI behavior, rendered output, and source parity |

Maintainer personas are listed in [docs/agent-catalog.md](docs/agent-catalog.md). Pinned KMP
vendor skills come from `ronjunevaldoz/kmp-agent-skills`; never edit a deployed copy.

## Install in a project

A project pins its bundles in `.agents/skills.lock.toml`. Bootstrap this installer, then let it
verify and deploy the exact pinned revisions:

    git clone https://github.com/awakekt/awake-agent-skills .agents/vendor/awake-agent-skills-bootstrap
    python3 .agents/vendor/awake-agent-skills-bootstrap/scripts/install_consumer.py --project .

The installer caches each pinned source under `.agents/vendor/`, checks its tag, commit and archive
digest, and deploys only the declared skills, commands and personas to `.agents/skills`,
`.agents/commands` and `.agents/agents`, mirrored into `.claude/` for Claude Code. Keep all six
directories gitignored. A source declares personas with `agent_root`, `agents` and
`agents_target = ".agents/agents"`.

Re-running is safe: it does nothing when every deployment matches the lockfile, relinks after a
bump, removes entries it created for dropped skills, and never replaces a directory it did not
create.

    install_consumer.py --project . --check   # report drift; exit 1 when an install is needed
    install_consumer.py --project . --force   # re-verify pinned sources even when current

## Keep pins current

`bump_lock.py` moves every source to its newest stable `vX.Y.Z` tag and writes the commit and
digest the installer verifies. A maintained bundle's skill, command and persona lists follow the
release; a vendor keeps its selection and reports new names for review. Run it from a scheduled
job that opens a pull request:

    python3 .agents/vendor/awake-agent-skills-bootstrap/scripts/bump_lock.py --project . --summary bump.md

## Write a skill

Follow [docs/skill-authoring.md](docs/skill-authoring.md). It applies to every Awake skill bundle.

## Validate

    python3 scripts/verify_bundle.py
    pytest scripts/test_install_consumer.py scripts/test_bump_lock.py
