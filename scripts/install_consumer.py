#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
# SPDX-License-Identifier: Apache-2.0
"""Install the immutable skill sources declared by a consumer lockfile."""

from __future__ import annotations

import argparse
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


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(args, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE).stdout.strip()


def load_lock(path: Path) -> list[dict]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("source"), list):
        raise ValueError("lockfile must declare version = 1 and one or more [[source]] entries")
    entries = data["source"]
    for entry in entries:
        required = ("id", "kind", "source", "tag", "commit", "archive_sha256", "skill_root", "skills")
        if any(not entry.get(key) for key in required):
            raise ValueError(f"source {entry.get('id', '<unknown>')} is missing a required field")
        if entry["kind"] not in KINDS or not COMMIT.fullmatch(entry["commit"]) or not DIGEST.fullmatch(entry["archive_sha256"]):
            raise ValueError(f"source {entry['id']} has invalid kind, commit, or archive digest")
        if entry["kind"] == "maintained-studio" and not entry.get("private", False):
            raise ValueError("maintained-studio entries must explicitly declare private = true")
    return entries


def cache_source(project: Path, entry: dict) -> Path:
    cache = project / ".agents" / "vendor" / f"{entry['id']}@{entry['commit']}"
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
    run("git", "checkout", "--detach", entry["commit"], cwd=cache)
    if run("git", "rev-parse", "HEAD", cwd=cache) != entry["commit"]:
        raise ValueError(f"{entry['id']}: checkout did not resolve the pinned commit")
    archive = subprocess.check_output(["git", "archive", "--format=tar", entry["commit"]], cwd=cache)
    if hashlib.sha256(archive).hexdigest() != entry["archive_sha256"]:
        raise ValueError(f"{entry['id']}: archive digest does not match lockfile")
    return cache


def deploy(source: Path, destination: Path, names: list[str]) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in names:
        origin = source / name
        target = destination / name
        if not origin.exists():
            raise ValueError(f"declared source is missing: {origin}")
        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.exists():
            shutil.rmtree(target)
        try:
            target.symlink_to(origin)
        except OSError:
            if origin.is_dir():
                shutil.copytree(origin, target)
                (target / ".agent-source").write_text(str(origin) + "\n", encoding="utf-8")
            else:
                shutil.copy2(origin, target)


def install(project: Path, lock: Path) -> None:
    for entry in load_lock(lock):
        cache = cache_source(project, entry)
        deploy(cache / entry["skill_root"], project / ".agents" / "skills", entry["skills"])
        commands = entry.get("commands", [])
        if commands:
            deploy(cache / entry.get("command_root", "commands"), project / ".agents" / "commands", commands)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".")
    parser.add_argument("--lock", default=".agents/skills.lock.toml")
    args = parser.parse_args()
    project = Path(args.project).resolve()
    try:
        install(project, project / args.lock)
    except (OSError, ValueError, subprocess.CalledProcessError, tomllib.TOMLDecodeError) as error:
        print(f"agent skill installation failed: {error}", file=sys.stderr)
        return 1
    print("agent skill installation complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
