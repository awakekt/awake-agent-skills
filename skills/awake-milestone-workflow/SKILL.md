---
name: awake-milestone-workflow
description: >
  Repository hygiene, GitHub milestone tracking, and commit squashing workflow for Awake Engine.
  Use when planning, tracking, or cutting releases to prevent git commit bloat and keep in-repo
  docs separated from ephemeral task checklists.
license: Apache-2.0
metadata:
  author: awake
  last-updated: '2026-10-03'
  keywords: Awake, release, milestones, GitHub, issues, git hygiene, squashing, ADR
---

# Awake Milestone Workflow & Repository Hygiene

This skill defines the operational boundary between **GitHub Milestones & Issues** (ephemeral task tracking) and **In-Repository Documentation** (permanent architectural truth).

---

## The Core Rule of Thumb

> **"Track tasks and burndown in GitHub Milestones; keep architecture, contracts, and ADRs in the repository."**

| Use **GitHub Milestones & Issues** for: | Keep **In-Repo Docs (`docs/`)** for: |
| :--- | :--- |
| 🎯 Release targets (`v0.1.0-alpha.1`, `v0.2.0`, etc.) | 🏛️ **Architecture Decision Records (ADRs)** |
| 📋 To-do items, progress checklists, & burndown | 📐 **Hardware Abstraction Layer (HAL) & Render contracts** |
| 🐛 Bug reports, triage, & fixes | 📖 **API Guides, tutorials, & setup references** |
| 💬 Design discussions before code lands | 📜 **Official release `CHANGELOG.md`** (frozen at release) |
| ⏱️ Ephemeral task lists & assignment | 🤖 **Pinned AI agent skill releases** |

---

## Invariants for AI Agents

1. **No Scratch Checklists in Git & No Issue Spam**:
   - Never create scratch `.md` task checklist files in `docs/` that get committed.
   - Never make a Git commit solely to check off an item or update a markdown task status.
   - **Hierarchy & Granularity**: Never spam top-level root issues for individual rows in an audit matrix, checklist cells, or micro-tweaks.
   - **Parent Epics**: Broad capabilities, audits, or multi-step roadmaps must be filed as a single **Parent Issue** (Epic).
   - **Sub-Issues**: Discrete sub-tasks or follow-up gaps must be linked as **Sub-Issues** under the Parent Issue using `./tools/gh-sub-issue.sh` or tracked as markdown task lists (`- [ ]`) within the Parent Issue description.
   - **Direct PRs**: Micro-fixes resolved immediately in active stacked PRs do not need standalone top-level issues.

2. **Atomic Commits & PR Squashing**:
   - Never push intermediate micro-commits (e.g. `style: reword comment`, `fix typo`, `step 1 of 5`) directly to `main`.
   - Group related modifications into atomic, cohesive commits with conventional commit messages (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`).
   - Enforce PR squashing so each feature lands on `main` as a single, verified commit.

3. **Branch Naming & Stacked PRs**:
   - Use short-lived topic branches formatted as `feat/*`, `fix/*`, `refactor/*`, or `docs/*`.
   - For dependent work, create a linear stack: the bottom branch targets `main`, and every
     branch above it targets the branch immediately below it.
   - Create each higher branch directly from its parent. Do not cherry-pick the parent into a
     separate history, because GitHub may then show the lower layer as part of the upper PR.
   - Keep each PR independently reviewable, review and merge from the bottom upward, and never
     close a middle PR while dependent PRs remain above it.
   - If installed, prefer the official `gh stack` extension:
     `gh stack init`, `gh stack add`, `gh stack submit`, `gh stack rebase`, and `gh stack push`.
     Otherwise set each PR's base branch to the head branch of the PR below it and use
     `git rebase` plus `git push --force-with-lease` carefully.
   - GitHub stacked PRs are public preview; verify the final diff and base branch after every
     rebase. See `docs/release-process.md` for the repository-level workflow.

4. **Querying & Managing Milestones, Epics & Sub-Issues via CLI**:
   - List milestones:
     ```bash
     gh api repos/awakekt/awake/milestones --jq '.[] | "\(.number): \(.title) - \(.description)"'
     ```
   - Create a parent issue / epic linked to a milestone:
     ```bash
     gh issue create --title "feat: <epic title>" --body "<body>" --milestone "<milestone-name>"
     ```
   - Create, attach, and list sub-issues with GitHub's current REST or GraphQL API. Do not
     invoke a helper through a user-local or deployed agent-skill path.
   - Close an issue when work lands:
     ```bash
     gh issue close <issue-number>
     ```

---

## Milestone Sequence

Read the live roadmap with the `gh api .../milestones` command above; never copy milestone names
into a skill or doc, because they go stale as soon as a release is cut. Awake Core milestones
track engine releases only; Studio product milestones belong to the Studio repository.
