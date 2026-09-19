#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023-2026 Ron June Valdoz
# SPDX-License-Identifier: Apache-2.0
"""Validate the public Awake skill package without loading an engine checkout."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def main() -> int:
    errors: list[str] = []
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            errors.append(f"{path.relative_to(ROOT)}: missing frontmatter")
            continue
        match = re.search(r"^name:\s*(\S+)$", text, re.M)
        if not match or match.group(1) != path.parent.name:
            errors.append(f"{path.relative_to(ROOT)}: name must match directory")
        if ".agents/skills/" in text:
            errors.append(f"{path.relative_to(ROOT)}: references deployed paths instead of product tools")
    if errors:
        print("Skill package verification failed:", *errors, sep="\n", file=sys.stderr)
        return 1
    print(f"Skill package verification passed ({len(list(SKILLS.glob('*/SKILL.md')))} skills)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
