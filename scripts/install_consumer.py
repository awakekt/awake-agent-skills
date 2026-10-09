#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
# SPDX-License-Identifier: Apache-2.0
"""Install the immutable skill sources declared by a consumer lockfile."""

from __future__ import annotations

import argparse
import filecmp
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from pathlib import Path


COMMIT = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
KINDS = {"vendor", "maintained-core", "maintained-studio"}
SKILL_TARGET = ".agents/skills"
COMMAND_TARGET = ".agents/commands"
AGENT_TARGET = ".agents/agents"
# Agents that do not read .agents/ receive the same deployment in their own project directory.
MIRRORS = {
    SKILL_TARGET: (".claude/skills",),
    COMMAND_TARGET: (".claude/commands",),
    AGENT_TARGET: (".claude/agents",),
}
MARKER = ".agent-source"


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(args, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE).stdout.strip()


def load_lock(path: Path) -> list[dict]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("source"), list):
        raise ValueError("lockfile must declare version = 1 and one or more [[source]] entries")
    entries = data["source"]
    for entry in entries:
        required = ("id", "kind", "source", "tag", "commit", "archive_sha256", "skill_root", "skills", "skills_target")
        if any(not entry.get(key) for key in required):
            raise ValueError(f"source {entry.get('id', '<unknown>')} is missing a required field")
        if entry["kind"] not in KINDS or not COMMIT.fullmatch(entry["commit"]) or not DIGEST.fullmatch(entry["archive_sha256"]):
            raise ValueError(f"source {entry['id']} has invalid kind, commit, or archive digest")
        if entry["kind"] == "maintained-studio" and not entry.get("private", False):
            raise ValueError("maintained-studio entries must explicitly declare private = true")
        if entry["skills_target"] != SKILL_TARGET:
            raise ValueError(f"source {entry['id']}: skills must deploy to {SKILL_TARGET}")
        if entry.get("commands") and entry.get("commands_target") != COMMAND_TARGET:
            raise ValueError(f"source {entry['id']}: commands must deploy to {COMMAND_TARGET}")
        if entry.get("agents") and entry.get("agents_target") != AGENT_TARGET:
            raise ValueError(f"source {entry['id']}: agents must deploy to {AGENT_TARGET}")
    return entries


def archive_digest(repo: Path, commit: str) -> str:
    """The SHA-256 of [commit]'s tar archive, the same on every machine. `git archive` applies the
    local line-ending settings to file contents, and Git for Windows turns core.autocrlf on, so
    both are pinned to the repository's own bytes. bump_lock.py computes it the same way."""
    archive = subprocess.check_output(
        ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "archive", "--format=tar", commit], cwd=repo
    )
    return hashlib.sha256(archive).hexdigest()


def cache_path(project: Path, entry: dict) -> Path:
    return project / ".agents" / "vendor" / f"{entry['id']}@{entry['commit']}"


def cache_source(project: Path, entry: dict) -> Path:
    cache = cache_path(project, entry)
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        run("git", "clone", "--no-checkout", entry["source"], str(cache))
    origin = run("git", "config", "--get", "remote.origin.url", cwd=cache)
    if origin.rstrip("/") != entry["source"].rstrip("/"):
        raise ValueError(f"{entry['id']}: cache origin does not match the lockfile source")
    if run("git", "rev-parse", "HEAD", cwd=cache) != entry["commit"]:
        run("git", "fetch", "--tags", "origin", entry["commit"], cwd=cache)
    # `git clone --no-checkout` may already have the requested HEAD but intentionally leaves the
    # working tree empty. Checkout is therefore required even when the revision already matches.
    run("git", "checkout", "--quiet", "--detach", entry["commit"], cwd=cache)
    if run("git", "rev-parse", "HEAD", cwd=cache) != entry["commit"]:
        raise ValueError(f"{entry['id']}: checkout did not resolve the pinned commit")
    tag_commit = run("git", "rev-list", "-n", "1", entry["tag"], cwd=cache)
    if tag_commit != entry["commit"]:
        raise ValueError(f"{entry['id']}: tag does not resolve to the pinned commit")
    if archive_digest(cache, entry["commit"]) != entry["archive_sha256"]:
        raise ValueError(f"{entry['id']}: archive digest does not match lockfile")
    return cache


def deployments(project: Path, entry: dict) -> list[tuple[Path, Path, list[str]]]:
    """Every (source, destination, names) an entry deploys, agent mirrors included."""
    cache = cache_path(project, entry)
    result = [
        (cache / entry["skill_root"], project / target, entry["skills"])
        for target in (SKILL_TARGET, *MIRRORS[SKILL_TARGET])
    ]
    if entry.get("commands"):
        result += [
            (cache / entry.get("command_root", "commands"), project / target, entry["commands"])
            for target in (COMMAND_TARGET, *MIRRORS[COMMAND_TARGET])
        ]
    if entry.get("agents"):
        result += [
            (cache / entry.get("agent_root", "agents"), project / target, entry["agents"])
            for target in (AGENT_TARGET, *MIRRORS[AGENT_TARGET])
        ]
    return result


def link_target(target: Path) -> Path:
    """Where the symlink [target] points. Windows reports it in extended-length form (\\\\?\\C:\\...),
    which never equals the path it was created with."""
    link = os.readlink(target)
    if link.startswith("\\\\?\\UNC\\"):
        link = "\\\\" + link[len("\\\\?\\UNC\\"):]
    elif link.startswith("\\\\?\\"):
        link = link[len("\\\\?\\"):]
    return Path(link)


def installed_origin(target: Path) -> Path | None:
    """The source an installer-created entry points at, or None for anything else."""
    if target.is_symlink():
        return link_target(target)
    marker = target / MARKER
    if target.is_dir() and marker.is_file():
        return Path(marker.read_text(encoding="utf-8").strip())
    return None


def state(origin: Path, target: Path) -> str:
    if not target.exists() and not target.is_symlink():
        return "missing"
    if target.is_file() and not target.is_symlink():
        # The copy fallback for command and agent files keeps no provenance, so content decides.
        return "ok" if origin.is_file() and filecmp.cmp(origin, target, shallow=False) else "outdated"
    installed = installed_origin(target)
    if installed is None:
        return "unmanaged"
    return "ok" if installed == origin and origin.exists() else "outdated"


def status(project: Path, entries: list[dict]) -> list[tuple[str, Path]]:
    """Every deployed path that differs from the lockfile, as (state, path)."""
    problems: list[tuple[str, Path]] = []
    declared: dict[Path, set[str]] = {}
    for entry in entries:
        for source, destination, names in deployments(project, entry):
            declared.setdefault(destination, set()).update(names)
            for name in names:
                current = state(source / name, destination / name)
                if current != "ok":
                    problems.append((current, destination / name))
    vendor = project / ".agents" / "vendor"
    for target in (
        SKILL_TARGET, *MIRRORS[SKILL_TARGET], COMMAND_TARGET, *MIRRORS[COMMAND_TARGET], AGENT_TARGET, *MIRRORS[AGENT_TARGET]
    ):
        destination = project / target
        if not destination.is_dir():
            continue
        names = declared.get(destination, set())
        for child in sorted(destination.iterdir()):
            origin = installed_origin(child)
            if child.name not in names and origin is not None and origin.is_relative_to(vendor):
                problems.append(("stale", child))
    return problems


def remove(target: Path) -> None:
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)


def deploy(source: Path, destination: Path, names: list[str]) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in names:
        origin = source / name
        target = destination / name
        if not origin.exists():
            raise ValueError(f"declared source is missing: {origin}")
        if state(origin, target) == "ok":
            continue
        remove(target)
        try:
            target.symlink_to(origin)
        except OSError:
            if origin.is_dir():
                shutil.copytree(origin, target)
                (target / MARKER).write_text(str(origin) + "\n", encoding="utf-8")
            else:
                shutil.copy2(origin, target)


def install(project: Path, lock: Path, *, force: bool = False) -> list[tuple[str, Path]]:
    """Bring every deployment in line with the lockfile and return what changed."""
    entries = load_lock(lock)
    problems = status(project, entries)
    conflicts = [str(path) for current, path in problems if current == "unmanaged"]
    if conflicts:
        raise ValueError("refusing to replace entries the installer did not create: " + ", ".join(conflicts))
    if not problems and not force:
        return []
    for entry in entries:
        cache_source(project, entry)
        for source, destination, names in deployments(project, entry):
            deploy(source, destination, names)
    for current, path in problems:
        if current == "stale":
            remove(path)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".")
    parser.add_argument("--lock", default=".agents/skills.lock.toml")
    parser.add_argument("--check", action="store_true", help="report drift without changing anything; exit 1 if an install is needed")
    parser.add_argument("--force", action="store_true", help="re-verify pinned sources even when every deployment is current")
    args = parser.parse_args()
    project = Path(args.project).resolve()
    try:
        if args.check:
            problems = status(project, load_lock(project / args.lock))
        else:
            problems = install(project, project / args.lock, force=args.force)
    except (OSError, ValueError, subprocess.CalledProcessError, tomllib.TOMLDecodeError) as error:
        print(f"agent skill installation failed: {error}", file=sys.stderr)
        return 1
    for current, path in problems:
        action = current if args.check else ("removed" if current == "stale" else "installed")
        print(f"{action:9} {path.relative_to(project)}")
    if not problems:
        print("agent skills are up to date")
    elif args.check:
        print(f"agent skills need an install: {len(problems)} entries differ from the lockfile")
        return 1
    else:
        print(f"agent skill installation complete: {len(problems)} entries updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
