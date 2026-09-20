#!/usr/bin/env python3
"""Exercise the public installer against a disposable, pinned local bundle."""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("install_consumer.py")
SPEC = importlib.util.spec_from_file_location("install_consumer", SCRIPT)
installer = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(installer)


def run(*args: str, cwd: Path) -> str:
    return subprocess.run(args, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE).stdout.strip()


class TestInstaller:
    def setup_method(self, method: object) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.source = self.root / "source"
        self.consumer = self.root / "consumer"
        (self.source / "skills" / "example").mkdir(parents=True)
        (self.source / "commands").mkdir()
        (self.source / "skills" / "example" / "SKILL.md").write_text("---\nname: example\n---\n", encoding="utf-8")
        (self.source / "commands" / "example.md").write_text("# example\n", encoding="utf-8")
        run("git", "init", "--quiet", cwd=self.source)
        run("git", "config", "user.email", "test@example.invalid", cwd=self.source)
        run("git", "config", "user.name", "Test", cwd=self.source)
        run("git", "add", ".", cwd=self.source)
        run("git", "commit", "--quiet", "-m", "fixture", cwd=self.source)
        self.commit = run("git", "rev-parse", "HEAD", cwd=self.source)
        run("git", "tag", "-a", "v0.0.0", "-m", "fixture", cwd=self.source)
        archive = subprocess.check_output(["git", "archive", "--format=tar", self.commit], cwd=self.source)
        self.digest = hashlib.sha256(archive).hexdigest()
        run("git", "commit", "--quiet", "--allow-empty", "-m", "follow-up", cwd=self.source)
        run("git", "tag", "-a", "v0.0.1", "-m", "follow-up", cwd=self.source)
        self.consumer.mkdir()

    def teardown_method(self, method: object) -> None:
        self.tempdir.cleanup()

    def lock(self, *, tag: str = "v0.0.0", commit: str | None = None, digest: str | None = None) -> Path:
        lock = self.consumer / "skills.lock.toml"
        lock.write_text(
            "\n".join(
                [
                    "version = 1",
                    "[[source]]",
                    'id = "fixture"',
                    'kind = "maintained-core"',
                    f'source = "{self.source}"',
                    f'tag = "{tag}"',
                    f'commit = "{commit or self.commit}"',
                    f'archive_sha256 = "{digest or self.digest}"',
                    'license = "Apache-2.0"',
                    'skill_root = "skills"',
                    'skills = ["example"]',
                    'skills_target = ".agents/skills"',
                    'command_root = "commands"',
                    'commands = ["example.md"]',
                    'commands_target = ".agents/commands"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return lock

    def test_installs_exact_source_and_commands(self) -> None:
        installer.install(self.consumer, self.lock())
        assert (self.consumer / ".agents" / "skills" / "example" / "SKILL.md").is_file()
        assert (self.consumer / ".agents" / "commands" / "example.md").is_file()

    def test_rejects_wrong_archive_digest(self) -> None:
        try:
            installer.install(self.consumer, self.lock(digest="0" * 64))
        except ValueError as error:
            assert "archive digest" in str(error)
        else:
            raise AssertionError("installer accepted a wrong archive digest")

    def test_rejects_tag_for_a_different_commit(self) -> None:
        try:
            installer.install(self.consumer, self.lock(tag="v0.0.1"))
        except ValueError as error:
            assert "tag does not resolve" in str(error)
        else:
            raise AssertionError("installer accepted a tag for a different commit")

    def test_rejects_wrong_commit(self) -> None:
        try:
            installer.install(self.consumer, self.lock(commit="0" * 40))
        except subprocess.CalledProcessError:
            pass
        else:
            raise AssertionError("installer accepted a wrong commit")
