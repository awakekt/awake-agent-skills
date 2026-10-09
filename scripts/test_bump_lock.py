#!/usr/bin/env python3
"""Exercise the lockfile bump against disposable local releases, then install what it wrote."""

from __future__ import annotations

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


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    run("git", "init", "--quiet", cwd=path)
    run("git", "config", "user.email", "test@example.invalid", cwd=path)
    run("git", "config", "user.name", "Test", cwd=path)
    run("git", "config", "tag.gpgsign", "false", cwd=path)


def tag_release(path: Path, tag: str, files: dict[str, str]) -> None:
    """Writes [files] into [path], commits everything staged or written, and tags it [tag]."""
    for name, text in files.items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_text(text, encoding="utf-8")
    run("git", "add", "-A", ".", cwd=path)
    run("git", "commit", "--quiet", "-m", tag, cwd=path)
    run("git", "tag", "-a", tag, "-m", tag, cwd=path)


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
        self.write_agent("auditor")
        init_repo(self.source)
        self.release("v0.0.9")
        # The next release adds one skill, retires another, and is followed by a pre-release.
        self.write_skill("added")
        self.write_agent("reviewer")
        run("git", "rm", "-r", "--quiet", "skills/retired", cwd=self.source)
        self.release("v0.0.10")
        run("git", "commit", "--quiet", "--allow-empty", "-m", "candidate", cwd=self.source)
        run("git", "tag", "-a", "v0.0.11-rc.1", "-m", "candidate", cwd=self.source)

    def teardown_method(self, method: object) -> None:
        self.tempdir.cleanup()

    def write_skill(self, name: str) -> None:
        (self.source / "skills" / name).mkdir(parents=True)
        (self.source / "skills" / name / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")

    def write_agent(self, name: str) -> None:
        (self.source / "agents").mkdir(exist_ok=True)
        (self.source / "agents" / f"{name}.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")

    def release(self, tag: str) -> None:
        run("git", "add", ".", cwd=self.source)
        run("git", "commit", "--quiet", "-m", tag, cwd=self.source)
        run("git", "tag", "-a", tag, "-m", tag, cwd=self.source)

    def pin(self, tag: str, source: Path | None = None) -> tuple[str, str]:
        source = source or self.source
        commit = run("git", "rev-list", "-n", "1", tag, cwd=source)
        return commit, installer.archive_digest(source, commit)

    def persona_lock(self, source: Path, agent_root: str | None) -> Path:
        """A lock on [source] v1.0.0 declaring one persona; [agent_root] None leaves the installer default."""
        commit, digest = self.pin("v1.0.0", source)
        lock = self.consumer / "skills.lock.toml"
        lines = [
            "version = 1",
            "",
            "[[source]]",
            'id = "personas"',
            'kind = "maintained-core"',
            f'source = "{source.as_posix()}"',
            'tag = "v1.0.0"',
            f'commit = "{commit}"',
            f'archive_sha256 = "{digest}"',
            'license = "Apache-2.0"',
            'skill_root = "skills"',
            'skills_target = ".agents/skills"',
            'skills = ["example"]',
            *([f'agent_root = "{agent_root}"'] if agent_root else []),
            'agents_target = ".agents/agents"',
            'agents = ["auditor.md"]',
            "",
        ]
        lock.write_text("\n".join(lines), encoding="utf-8")
        return lock

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
                    f'source = "{(source or self.source).as_posix()}"',
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
                    'agent_root = "agents"',
                    'agents_target = ".agents/agents"',
                    'agents = ["auditor.md"]',
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
        assert entry["agents"] == ["auditor.md", "reviewer.md"]
        assert lock.read_text(encoding="utf-8").startswith("# Pinned agent skills.")
        assert report.moved == ["`fixture` v0.0.9 → v0.0.10 (added added; dropped retired)"]
        # The pin the bump wrote is one the installer verifies and deploys.
        installer.install(self.consumer, lock)
        assert (self.consumer / ".claude" / "skills" / "added" / "SKILL.md").is_file()
        assert (self.consumer / ".claude" / "agents" / "reviewer.md").is_file()

    def test_a_vendor_keeps_its_selection_and_reports_new_skills(self) -> None:
        lock = self.lock("vendor")
        report = bumper.Report()

        bumper.bump(lock, report)

        entry = tomllib.loads(lock.read_text(encoding="utf-8"))["source"][0]
        assert entry["tag"] == "v0.0.10"
        assert entry["skills"] == ["example"]
        assert report.available == ["`fixture` skills: added", "`fixture` agents: reviewer.md"]
        installer.install(self.consumer, lock)

    def test_a_current_lock_is_left_byte_for_byte(self) -> None:
        lock = self.lock("maintained-core")
        bumper.bump(lock, bumper.Report())
        before = lock.read_bytes()
        report = bumper.Report()

        assert not bumper.bump(lock, report)
        assert lock.read_bytes() == before
        assert report.current == ["`fixture` v0.0.10"]

    def test_a_release_that_moves_its_personas_out_of_a_skill_moves_the_lock_root(self) -> None:
        source = self.root / "nested"
        init_repo(source)
        tag_release(
            source,
            "v1.0.0",
            {
                "bundle.toml": 'persona_dir = "skills/example/agents"\n',
                "skills/example/SKILL.md": "---\nname: example\n---\n",
                "skills/example/agents/auditor.md": "---\nname: auditor\n---\n",
            },
        )
        run("git", "mv", "skills/example/agents", "agents", cwd=source)
        tag_release(source, "v1.1.0", {"bundle.toml": 'persona_dir = "agents"\ncommand_dir = "commands"\n'})
        lock = self.persona_lock(source, agent_root="skills/example/agents")
        report = bumper.Report()

        assert bumper.bump(lock, report)

        entry = tomllib.loads(lock.read_text(encoding="utf-8"))["source"][0]
        assert entry["agent_root"] == "agents"
        assert entry["agents"] == ["auditor.md"]
        # The lock declares no commands, so the release's command folder is not written into it.
        assert "command_root" not in entry
        assert report.moved == ["`personas` v1.0.0 → v1.1.0 (agents moved to agents/)"]
        installer.install(self.consumer, lock)
        assert (self.consumer / ".claude" / "agents" / "auditor.md").is_file()

    def test_a_lock_on_the_default_root_gets_the_new_root_spelled_out(self) -> None:
        source = self.root / "renamed"
        init_repo(source)
        tag_release(
            source,
            "v1.0.0",
            {"skills/example/SKILL.md": "---\nname: example\n---\n", "agents/auditor.md": "---\nname: auditor\n---\n"},
        )
        run("git", "mv", "agents", "personas", cwd=source)
        tag_release(source, "v1.1.0", {"bundle.toml": 'persona_dir = "personas"\n'})
        lock = self.persona_lock(source, agent_root=None)

        assert bumper.bump(lock, bumper.Report())

        text = lock.read_text(encoding="utf-8")
        assert 'agent_root = "personas"\nagents = [' in text
        entry = tomllib.loads(text)["source"][0]
        assert entry["agents"] == ["auditor.md"]
        installer.install(self.consumer, lock)
        assert (self.consumer / ".agents" / "agents" / "auditor.md").is_file()

    def test_an_unreachable_source_is_reported_not_skipped_silently(self) -> None:
        lock = self.lock("maintained-core", source=self.root / "missing")
        report = bumper.Report()

        assert not bumper.bump(lock, report)
        assert len(report.failed) == 1 and report.failed[0].startswith("`fixture`")
