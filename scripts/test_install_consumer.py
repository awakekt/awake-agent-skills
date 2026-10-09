#!/usr/bin/env python3
"""Exercise the public installer against a disposable, pinned local bundle."""

from __future__ import annotations

import hashlib
import importlib.util
import shutil
import stat
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
        for skill in ("example", "other"):
            (self.source / "skills" / skill).mkdir(parents=True)
            (self.source / "skills" / skill / "SKILL.md").write_text(f"---\nname: {skill}\n---\n", encoding="utf-8")
        (self.source / "commands").mkdir()
        (self.source / "commands" / "example.md").write_text("# example\n", encoding="utf-8")
        (self.source / "agents").mkdir()
        (self.source / "agents" / "auditor.md").write_text("---\nname: auditor\n---\n", encoding="utf-8")
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

    def lock(
        self,
        *,
        tag: str = "v0.0.0",
        commit: str | None = None,
        digest: str | None = None,
        skills: tuple[str, ...] = ("example",),
    ) -> Path:
        declared = ", ".join(f'"{skill}"' for skill in skills)
        lock = self.consumer / "skills.lock.toml"
        lock.write_text(
            "\n".join(
                [
                    "version = 1",
                    "[[source]]",
                    'id = "fixture"',
                    'kind = "maintained-core"',
                    f'source = "{self.source.as_posix()}"',
                    f'tag = "{tag}"',
                    f'commit = "{commit or self.commit}"',
                    f'archive_sha256 = "{digest or self.digest}"',
                    'license = "Apache-2.0"',
                    'skill_root = "skills"',
                    f"skills = [{declared}]",
                    'skills_target = ".agents/skills"',
                    'command_root = "commands"',
                    'commands = ["example.md"]',
                    'commands_target = ".agents/commands"',
                    'agent_root = "agents"',
                    'agents = ["auditor.md"]',
                    'agents_target = ".agents/agents"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return lock

    def test_installs_exact_source_and_commands(self) -> None:
        installer.install(self.consumer, self.lock())
        for root in (".agents", ".claude"):
            assert (self.consumer / root / "skills" / "example" / "SKILL.md").is_file()
            assert (self.consumer / root / "commands" / "example.md").is_file()
            assert (self.consumer / root / "agents" / "auditor.md").is_file()

    def test_agents_must_deploy_to_the_agents_directory(self) -> None:
        lock = self.lock()
        lock.write_text(lock.read_text(encoding="utf-8").replace(".agents/agents", ".claude/agents"), encoding="utf-8")
        try:
            installer.load_lock(lock)
        except ValueError as error:
            assert "agents must deploy" in str(error)
        else:
            raise AssertionError("a lockfile deploying agents elsewhere must be refused")

    def test_status_reports_missing_until_installed(self) -> None:
        lock = self.lock()
        before = installer.status(self.consumer, installer.load_lock(lock))
        assert {state for state, _ in before} == {"missing"}
        assert len(before) == 6  # skill, command and agent, each in .agents and .claude
        installer.install(self.consumer, lock)
        assert installer.status(self.consumer, installer.load_lock(lock)) == []

    def test_current_install_skips_source_verification_unless_forced(self) -> None:
        lock = self.lock()
        installer.install(self.consumer, lock)
        cache = installer.cache_path(self.consumer, installer.load_lock(lock)[0])
        # Git writes its objects read-only, and Windows refuses to delete a read-only file.
        for path in (cache / ".git").rglob("*"):
            if path.is_file():
                path.chmod(stat.S_IREAD | stat.S_IWRITE)
        shutil.rmtree(cache / ".git")
        assert installer.install(self.consumer, lock) == []
        try:
            installer.install(self.consumer, lock, force=True)
        except subprocess.CalledProcessError:
            pass
        else:
            raise AssertionError("--force did not re-verify the pinned source")

    def test_new_pinned_commit_is_outdated_until_reinstalled(self) -> None:
        installer.install(self.consumer, self.lock())
        (self.source / "skills" / "example" / "SKILL.md").write_text("---\nname: example\n---\nv2\n", encoding="utf-8")
        run("git", "commit", "--quiet", "-am", "update", cwd=self.source)
        run("git", "tag", "-a", "v0.0.2", "-m", "update", cwd=self.source)
        commit = run("git", "rev-parse", "HEAD", cwd=self.source)
        archive = subprocess.check_output(["git", "archive", "--format=tar", commit], cwd=self.source)
        lock = self.lock(tag="v0.0.2", commit=commit, digest=hashlib.sha256(archive).hexdigest())
        assert {state for state, _ in installer.status(self.consumer, installer.load_lock(lock))} == {"outdated"}
        installer.install(self.consumer, lock)
        assert "v2" in (self.consumer / ".claude" / "skills" / "example" / "SKILL.md").read_text(encoding="utf-8")
        assert installer.status(self.consumer, installer.load_lock(lock)) == []

    def test_removes_skills_dropped_from_the_lock_but_keeps_local_ones(self) -> None:
        installer.install(self.consumer, self.lock(skills=("example", "other")))
        local = self.consumer / ".claude" / "skills" / "local"
        local.mkdir()
        lock = self.lock()
        assert sorted(path.name for state, path in installer.status(self.consumer, installer.load_lock(lock)) if state == "stale") == [
            "other",
            "other",
        ]
        installer.install(self.consumer, lock)
        assert not (self.consumer / ".agents" / "skills" / "other").exists()
        assert not (self.consumer / ".claude" / "skills" / "other").exists()
        assert local.is_dir()

    def test_refuses_to_replace_an_unmanaged_directory(self) -> None:
        own = self.consumer / ".claude" / "skills" / "example"
        own.mkdir(parents=True)
        try:
            installer.install(self.consumer, self.lock())
        except ValueError as error:
            assert "did not create" in str(error)
        else:
            raise AssertionError("installer replaced a directory it did not create")
        assert own.is_dir() and not own.is_symlink()

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


def test_a_windows_link_target_compares_equal_to_the_path_it_was_made_with(monkeypatch) -> None:
    # Windows reports a symlink's target in extended-length form; left as is, every installed
    # entry reads as outdated and no dropped skill is ever found stale.
    monkeypatch.setattr(installer.os, "readlink", lambda _: "\\\\?\\C:\\cache\\skills\\example")
    assert installer.link_target(Path("link")) == Path("C:\\cache\\skills\\example")
    monkeypatch.setattr(installer.os, "readlink", lambda _: "\\\\?\\UNC\\host\\share\\skills\\example")
    assert installer.link_target(Path("link")) == Path("\\\\host\\share\\skills\\example")
    monkeypatch.setattr(installer.os, "readlink", lambda _: "/cache/skills/example")
    assert installer.link_target(Path("link")) == Path("/cache/skills/example")
