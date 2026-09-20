#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
# SPDX-License-Identifier: Apache-2.0
"""Validate the public Awake skill package without an Awake engine checkout."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_PATTERN = re.compile(r"\]\(([^)]+)\)")


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}

    fields: dict[str, str] = {}
    index = 1
    while index < end:
        match = re.match(r"^([a-zA-Z0-9_-]+):\s*(.*)$", lines[index])
        if not match:
            index += 1
            continue
        key, value = match.groups()
        if value in {">", ">-", ">+", "|", "|-", "|+"}:
            parts: list[str] = []
            index += 1
            while index < end and (not lines[index] or lines[index][0].isspace()):
                if lines[index].strip():
                    parts.append(lines[index].strip())
                index += 1
            fields[key] = " ".join(parts)
            continue
        fields[key] = value.strip().strip("\"'")
        index += 1
    return fields


def validate_links(path: Path, text: str, errors: list[str]) -> None:
    for match in LINK_PATTERN.finditer(text):
        target = match.group(1).strip().split(maxsplit=1)[0].strip("<>")
        if not target or target.startswith(("#", "/", "//")):
            continue
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
            continue
        local_target = unquote(target.split("#", 1)[0].split("?", 1)[0])
        if not local_target:
            continue
        resolved = (path.parent / local_target).resolve()
        if ROOT not in resolved.parents and resolved != ROOT:
            errors.append(f"{path.relative_to(ROOT)}: relative link escapes bundle: {target}")
        elif not resolved.exists():
            errors.append(f"{path.relative_to(ROOT)}: broken relative link: {target}")


def validate_skill(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    relative = path.relative_to(ROOT)
    fields = parse_frontmatter(text)
    name = fields.get("name", "")
    description = fields.get("description", "")

    if not fields:
        errors.append(f"{relative}: missing or invalid YAML frontmatter")
        return
    if len(name) > 64 or not NAME_PATTERN.fullmatch(name):
        errors.append(f"{relative}: name must use lowercase letters, digits, and single hyphens (max 64)")
    if name != path.parent.name:
        errors.append(f"{relative}: name must match its skill directory")
    if not description or len(description) > 1024:
        errors.append(f"{relative}: description must contain 1 to 1024 characters")
    if not (name == "awake" or name.startswith("awake-")):
        errors.append(f"{relative}: maintained Core skills must use the awake namespace")
    validate_links(path, text, errors)


def validate_agents(errors: list[str]) -> int:
    agents = sorted((SKILLS / "awake" / "agents").glob("*.md"))
    catalog_path = ROOT / "docs" / "agent-catalog.md"
    catalog = catalog_path.read_text(encoding="utf-8") if catalog_path.is_file() else ""
    if not catalog:
        errors.append("docs/agent-catalog.md: missing public persona catalog")
    for path in agents:
        relative = path.relative_to(ROOT)
        fields = parse_frontmatter(path.read_text(encoding="utf-8"))
        name = fields.get("name", "")
        if name != path.stem:
            errors.append(f"{relative}: persona name must match its filename")
        if not name.startswith("awake-"):
            errors.append(f"{relative}: public persona names must use the awake namespace")
        if not fields.get("description"):
            errors.append(f"{relative}: persona description is required")
        if not fields.get("tools") or not fields.get("model"):
            errors.append(f"{relative}: preserve explicit tools and model metadata")
        if name not in catalog:
            errors.append(f"{relative}: persona is missing from docs/agent-catalog.md")
        validate_links(path, path.read_text(encoding="utf-8"), errors)
    return len(agents)


def main() -> int:
    errors: list[str] = []
    skill_paths = sorted(SKILLS.glob("*/SKILL.md"))
    for path in skill_paths:
        validate_skill(path, errors)

    for path in sorted(SKILLS.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        if ".agents/" in text or "~/.agents" in text or "file://" in text:
            errors.append(f"{path.relative_to(ROOT)}: references a deployment or local-machine path")

    agent_count = validate_agents(errors)
    if errors:
        print("Public skill package verification failed:", *errors, sep="\n", file=sys.stderr)
        return 1
    print(f"Public skill package verification passed ({len(skill_paths)} skills, {agent_count} personas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
