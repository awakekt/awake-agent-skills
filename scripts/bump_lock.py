#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
# SPDX-License-Identifier: Apache-2.0
"""Move every source in a consumer lockfile to its newest release tag.

Each moved source gets the commit and archive digest the installer verifies. A maintained bundle
(maintained-core, maintained-studio) is consumed whole, so its skill, command and persona lists
follow the release; a vendor keeps its curated selection, losing only names the release no longer ships, and
reports new ones for a reviewer to adopt. Only stable `vX.Y.Z` tags count; pre-releases are skipped.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


RELEASE_TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
MIRRORED_KINDS = {"maintained-core", "maintained-studio"}
ARRAY_WIDTH = 100


@dataclass
class Report:
    moved: list[str] = field(default_factory=list)
    current: list[str] = field(default_factory=list)
    available: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    def markdown(self) -> str:
        sections = [
            ("Moved", self.moved),
            ("New in a vendor release, not adopted", self.available),
            ("Already current", self.current),
            ("Could not check", self.failed),
        ]
        return "\n\n".join(
            f"### {title}\n\n" + "\n".join(f"- {line}" for line in lines) for title, lines in sections if lines
        ) + "\n"


@dataclass
class Release:
    tag: str
    commit: str
    digest: str
    skills: list[str]
    commands: list[str]
    agents: list[str]


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(("git", *args), cwd=cwd, check=True, text=True, capture_output=True).stdout.strip()


def latest_release(source: str) -> str | None:
    """The highest stable `vX.Y.Z` tag [source] publishes, or None when it has none."""
    tags = [line.rsplit("refs/tags/", 1)[-1] for line in git("ls-remote", "--tags", "--refs", source).splitlines()]
    releases = [(tuple(int(part) for part in match.groups()), tag) for tag in tags if (match := RELEASE_TAG.match(tag))]
    return max(releases)[1] if releases else None


def fetch_release(entry: dict, tag: str, workdir: Path) -> Release:
    """Clones [tag] and reads what the installer would verify and deploy from it."""
    checkout = workdir / entry["id"]
    git("clone", "--quiet", "--no-checkout", "--branch", tag, entry["source"], str(checkout))
    commit = git("rev-list", "-n", "1", tag, cwd=checkout)
    archive = subprocess.check_output(["git", "archive", "--format=tar", commit], cwd=checkout)
    files = git("ls-tree", "-r", "--name-only", commit, cwd=checkout).splitlines()
    skill_root = entry["skill_root"].rstrip("/") + "/"
    skills = sorted(
        path[len(skill_root):].split("/")[0]
        for path in files
        if path.startswith(skill_root) and path.count("/") == skill_root.count("/") + 1 and path.endswith("/SKILL.md")
    )
    commands = top_level_markdown(files, entry.get("command_root", "commands"))
    agents = top_level_markdown(files, entry.get("agent_root", "agents"))
    return Release(tag, commit, hashlib.sha256(archive).hexdigest(), skills, commands, agents)


def top_level_markdown(files: list[str], root: str) -> list[str]:
    """The `.md` files directly under [root]: command and persona names."""
    root = root.rstrip("/") + "/"
    return sorted(path[len(root):] for path in files if path.startswith(root) and "/" not in path[len(root):] and path.endswith(".md"))


def selection(entry: dict, key: str, released: list[str], report: Report) -> list[str]:
    """What [entry] should declare for [key] ("skills", "commands" or "agents") after moving to [released]."""
    declared = entry.get(key, [])
    if entry["kind"] in MIRRORED_KINDS:
        return released
    new = [name for name in released if name not in declared]
    if new:
        report.available.append(f"`{entry['id']}` {key}: {', '.join(new)}")
    return [name for name in declared if name in released]


def render_array(key: str, names: list[str]) -> str:
    lines: list[str] = []
    line = ""
    for item in (f'"{name}",' for name in names):
        if line and len(line) + 1 + len(item) > ARRAY_WIDTH:
            lines.append(line)
            line = ""
        line = f"{line} {item}" if line else f"  {item}"
    if line:
        lines.append(line)
    return f"{key} = [\n" + "\n".join(lines) + "\n]"


def rewrite(block: str, entry: dict, release: Release, lists: dict[str, list[str]]) -> str:
    """[block] with its pin and lists replaced, everything else (comments, order) kept."""
    for key, value in (("tag", release.tag), ("commit", release.commit), ("archive_sha256", release.digest)):
        block = re.sub(rf'^{key} = ".*"$', f'{key} = "{value}"', block, count=1, flags=re.MULTILINE)
    # An unchanged list keeps its hand wrapping, so the diff shows only what moved.
    for key, names in lists.items():
        if key in entry and names != entry[key]:
            block = re.sub(rf"^{key} = \[[^\]]*\]", lambda _: render_array(key, names), block, count=1, flags=re.MULTILINE)
    return block


def bump(lock: Path, report: Report) -> bool:
    """Moves every source in [lock] to its newest release; returns whether the file changed."""
    text = lock.read_text(encoding="utf-8")
    entries = tomllib.loads(text)["source"]
    # Blocks line up with entries: the header and anything before the first source, then one per source.
    parts = re.split(r"(?m)^(?=\[\[source\]\]\s*$)", text)
    header, blocks = parts[0], parts[1:]
    if len(blocks) != len(entries):
        raise ValueError("every [[source]] table must start on its own line")
    with tempfile.TemporaryDirectory() as temp:
        for index, entry in enumerate(entries):
            try:
                tag = latest_release(entry["source"])
                if tag is None or tag == entry["tag"]:
                    report.current.append(f"`{entry['id']}` {entry['tag']}")
                    continue
                release = fetch_release(entry, tag, Path(temp))
            except subprocess.CalledProcessError as error:
                report.failed.append(f"`{entry['id']}`: {(error.stderr or str(error)).strip()}")
                continue
            skills = selection(entry, "skills", release.skills, report)
            lists = {"skills": skills}
            for key, released in (("commands", release.commands), ("agents", release.agents)):
                if key in entry:
                    lists[key] = selection(entry, key, released, report)
            blocks[index] = rewrite(blocks[index], entry, release, lists)
            added = sorted(set(skills) - set(entry["skills"]))
            dropped = sorted(set(entry["skills"]) - set(skills))
            change = "; ".join(filter(None, [f"added {', '.join(added)}" if added else "", f"dropped {', '.join(dropped)}" if dropped else ""]))
            report.moved.append(f"`{entry['id']}` {entry['tag']} → {tag}" + (f" ({change})" if change else ""))
    updated = header + "".join(blocks)
    if updated == text:
        return False
    lock.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".")
    parser.add_argument("--lock", default=".agents/skills.lock.toml")
    parser.add_argument("--summary", help="also write the report as Markdown to this file")
    args = parser.parse_args()
    report = Report()
    try:
        changed = bump(Path(args.project).resolve() / args.lock, report)
    except (OSError, ValueError, KeyError, tomllib.TOMLDecodeError) as error:
        print(f"lockfile bump failed: {error}", file=sys.stderr)
        return 1
    summary = report.markdown()
    print(summary if summary.strip() else "nothing to report")
    if args.summary:
        Path(args.summary).write_text(summary, encoding="utf-8")
    print("lockfile updated" if changed else "lockfile unchanged")
    # A source that could not be checked fails the run, after the reachable ones were moved.
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
