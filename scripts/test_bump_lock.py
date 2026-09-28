#!/usr/bin/env python3
"""Exercise the lockfile bump against disposable local releases, then install what it wrote."""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path


def load(name: str):
    path = Path(__file__).resolve().with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module  # dataclasses resolve annotations through the module registry
    spec.loader.exec_module(module)
    return module


bumper = load("bump_lock")
installer = load("install_consumer")


def run(*args: str, cwd: Path) -> str:
    return subprocess.run(args, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE).stdout.strip()


class TestBump:
    def setup_method(self, method: object) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.source = self.root / "source"
        self.consumer = self.root / "consumer"
        self.consumer.mkdir()
        self.write_skill("example")
        self.write_skill("retired")
        (self.source / "commands").mkdir()
        (self.source / "commands" / "example.md").write_text("# example\n", encoding="utf-8")
        run("git", "init", "--quiet", cwd=self.source)
        run("git", "config", "user.email", "test@example.invalid", cwd=self.source)
        run("git", "config", "user.name", "Test", cwd=self.source)
        run("git", "config", "tag.gpgsign", "false", cwd=self.source)
        self.release("v0.0.9")
        # The next release adds one skill, retires another, and is followed by a pre-release.
        self.write_skill("added")
        run("git", "rm", "-r", "--quiet", "skills/retired", cwd=self.source)
        self.release("v0.0.10")
        run("git", "commit", "--quiet", "--allow-empty", "-m", "candidate", cwd=self.source)
        run("git", "tag", "-a", "v0.0.11-rc.1", "-m", "candidate", cwd=self.source)

    def teardown_method(self, method: object) -> None:
        self.tempdir.cleanup()

    def write_skill(self, name: str) -> None:
        (self.source / "skills" / name).mkdir(parents=True)
        (self.source / "skills" / name / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")

    def release(self, tag: str) -> None:
        run("git", "add", ".", cwd=self.source)
        run("git", "commit", "--quiet", "-m", tag, cwd=self.source)
        run("git", "tag", "-a", tag, "-m", tag, cwd=self.source)

    def pin(self, tag: str) -> tuple[str, str]:
        commit = run("git", "rev-list", "-n", "1", tag, cwd=self.source)
        archive = subprocess.check_output(["git", "archive", "--format=tar", commit], cwd=self.source)
        return commit, hashlib.sha256(archive).hexdigest()

    def lock(self, kind: str, source: Path | None = None) -> Path:
        commit, digest = self.pin("v0.0.9")
        lock = self.consumer / "skills.lock.toml"
        lock.write_text(
            "\n".join(
                [
                    "# Pinned agent skills.",
                    "version = 1",
                    "",
                    "[[source]]",
                    'id = "fixture"',
                    f'kind = "{kind}"',
                    f'source = "{source or self.source}"',
                    'tag = "v0.0.9"',
                    f'commit = "{commit}"',
                    f'archive_sha256 = "{digest}"',
                    'license = "Apache-2.0"',
                    'skill_root = "skills"',
                    'skills_target = ".agents/skills"',
                    'skills = ["example", "retired"]',
                    'command_root = "commands"',
                    'commands_target = ".agents/commands"',
                    'commands = ["example.md"]',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return lock

    def test_moves_a_maintained_bundle_to_the_newest_release_and_mirrors_it(self) -> None:
        lock = self.lock("maintained-core")
        report = bumper.Report()

        assert bumper.bump(lock, report)

        entry = tomllib.loads(lock.read_text(encoding="utf-8"))["source"][0]
        assert (entry["tag"], entry["commit"], entry["archive_sha256"]) == ("v0.0.10", *self.pin("v0.0.10"))
        assert entry["skills"] == ["added", "example"]
        assert lock.read_text(encoding="utf-8").startswith("# Pinned agent skills.")
        assert report.moved == ["`fixture` v0.0.9 → v0.0.10 (added added; dropped retired)"]
        # The pin the bump wrote is one the installer verifies and deploys.
        installer.install(self.consumer, lock)
        assert (self.consumer / ".claude" / "skills" / "added" / "SKILL.md").is_file()

    def test_a_vendor_keeps_its_selection_and_reports_new_skills(self) -> None:
        lock = self.lock("vendor")
        report = bumper.Report()

        bumper.bump(lock, report)

        entry = tomllib.loads(lock.read_text(encoding="utf-8"))["source"][0]
        assert entry["tag"] == "v0.0.10"
        assert entry["skills"] == ["example"]
        assert report.available == ["`fixture` skills: added"]
        installer.install(self.consumer, lock)

    def test_a_current_lock_is_left_byte_for_byte(self) -> None:
        lock = self.lock("maintained-core")
        bumper.bump(lock, bumper.Report())
        before = lock.read_bytes()
        report = bumper.Report()

        assert not bumper.bump(lock, report)
        assert lock.read_bytes() == before
        assert report.current == ["`fixture` v0.0.10"]

    def test_an_unreachable_source_is_reported_not_skipped_silently(self) -> None:
        lock = self.lock("maintained-core", source=self.root / "missing")
        report = bumper.Report()

        assert not bumper.bump(lock, report)
        assert len(report.failed) == 1 and report.failed[0].startswith("`fixture`")
