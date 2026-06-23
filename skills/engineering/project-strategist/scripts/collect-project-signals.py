#!/usr/bin/env python3
"""Collect deterministic project-planning signals for project-strategist.

The script intentionally does not make strategic judgments. It reads local
planning files, git history, and lightweight source signals, then emits JSON for
the agent to interpret.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


MAX_TEXT_CHARS = 12_000
MAX_FILES_PER_SECTION = 200
IGNORED_DIRS = {
    ".scratch",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".uv-cache",
    ".uv-python",
    ".venv",
    "__pycache__",
    "data",
    "node_modules",
    "target",
    "dist",
    "build",
}


@dataclass
class TextDoc:
    path: str
    title: str | None
    chars: int
    excerpt: str


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"command failed: {' '.join(cmd)}")
    return proc.stdout.strip()


def git_root(cwd: Path) -> Path:
    try:
        root = run(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    except RuntimeError as exc:
        raise SystemExit(f"not a git repository: {cwd}") from exc
    return Path(root)


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def first_heading(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or None
    return None


def make_doc(path: Path, root: Path) -> TextDoc:
    text = read_text(path)
    return TextDoc(
        path=rel(path, root),
        title=first_heading(text),
        chars=len(text),
        excerpt=text[:MAX_TEXT_CHARS],
    )


def collect_context(root: Path, warnings: list[str]) -> dict[str, Any]:
    docs: list[TextDoc] = []
    context_map = root / "CONTEXT-MAP.md"
    context = root / "CONTEXT.md"
    if context_map.exists():
        docs.append(make_doc(context_map, root))
    if context.exists():
        docs.append(make_doc(context, root))
    if not docs:
        warnings.append("missing CONTEXT.md or CONTEXT-MAP.md")
    return {"docs": [asdict(doc) for doc in docs]}


def parse_status(text: str) -> str | None:
    lines = text.splitlines()
    for line in lines[:30]:
        if line.lower().startswith("status:"):
            return line.split(":", 1)[1].strip()
    for index, line in enumerate(lines):
        if line.strip().lower() == "## status":
            for candidate in lines[index + 1 : index + 8]:
                stripped = candidate.strip()
                if stripped:
                    return stripped
    return None


def collect_adrs(root: Path, warnings: list[str]) -> dict[str, Any]:
    adr_dir = root / "docs" / "adr"
    if not adr_dir.exists():
        warnings.append("missing docs/adr")
        return {"items": []}
    items: list[dict[str, Any]] = []
    for path in sorted(adr_dir.glob("*.md"))[:MAX_FILES_PER_SECTION]:
        text = read_text(path)
        items.append(
            {
                "path": rel(path, root),
                "title": first_heading(text),
                "status": parse_status(text),
                "excerpt": text[:4_000],
            }
        )
    return {"items": items}


def collect_scratch(root: Path, warnings: list[str]) -> dict[str, Any]:
    scratch = root / ".scratch"
    if not scratch.exists():
        warnings.append("missing .scratch")
        return {
            "issue_status_counts": {},
            "issues": [],
            "backlogs": [],
            "prds": [],
        }

    issues: list[dict[str, Any]] = []
    statuses: Counter[str] = Counter()
    for path in sorted(scratch.glob("**/issues/*.md"))[:MAX_FILES_PER_SECTION]:
        text = read_text(path)
        status = parse_status(text) or "unknown"
        statuses[status] += 1
        issues.append(
            {
                "path": rel(path, root),
                "title": first_heading(text),
                "status": status,
                "excerpt": text[:900],
            }
        )

    backlogs = [
        asdict(make_doc(path, root))
        for path in sorted(scratch.glob("**/backlog.md"))[:MAX_FILES_PER_SECTION]
    ]
    prds = [
        asdict(make_doc(path, root))
        for path in sorted(scratch.glob("**/PRD.md"))[:MAX_FILES_PER_SECTION]
    ]
    return {
        "issue_status_counts": dict(sorted(statuses.items())),
        "issues": issues,
        "backlogs": backlogs,
        "prds": prds,
    }


def collect_git(root: Path, commits: int) -> dict[str, Any]:
    branch = run(["git", "branch", "--show-current"], cwd=root, check=False) or None
    head = run(["git", "rev-parse", "--short", "HEAD"], cwd=root)
    head_subject = run(["git", "log", "-1", "--pretty=%s"], cwd=root, check=False)
    log_oneline = run(
        ["git", "log", "--oneline", "--decorate", "-n", str(commits)], cwd=root
    ).splitlines()
    log_stat = run(
        ["git", "log", "--stat", "--oneline", "-n", str(min(commits, 30))],
        cwd=root,
    )
    names = run(
        ["git", "log", "--name-only", "--pretty=format:", "-n", str(commits)],
        cwd=root,
        check=False,
    ).splitlines()
    churn = Counter(name.strip() for name in names if name.strip())
    high_churn = [
        {"path": path, "commits_touched": count}
        for path, count in churn.most_common(30)
    ]
    return {
        "branch": branch,
        "head": head,
        "head_subject": head_subject,
        "recent_commits": log_oneline,
        "recent_stat": log_stat[:20_000],
        "high_churn_files": high_churn,
    }


def is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def collect_source(root: Path) -> dict[str, Any]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_dir() or is_ignored(path.relative_to(root)):
            continue
        files.append(path)

    ext_counts: Counter[str] = Counter()
    top_dirs: Counter[str] = Counter()
    test_files: list[str] = []
    core_files: list[str] = []

    for path in files:
        relative = path.relative_to(root)
        ext_counts[path.suffix or "[no extension]"] += 1
        top_dirs[relative.parts[0] if relative.parts else "."] += 1
        rel_path = relative.as_posix()
        lower = rel_path.lower()
        if (
            "/test_" in lower
            or lower.startswith("tests/")
            or lower.endswith("_test.py")
            or lower.endswith(".test.ts")
            or lower.endswith(".spec.ts")
            or lower.endswith(".test.tsx")
            or lower.endswith(".spec.tsx")
        ):
            test_files.append(rel_path)
        if relative.parts and relative.parts[0] in {"src", "sdk", "app", "lib"}:
            core_files.append(rel_path)

    tree = source_tree(root)
    return {
        "file_count": len(files),
        "extension_counts": dict(ext_counts.most_common(30)),
        "top_level_file_counts": dict(top_dirs.most_common(30)),
        "test_file_count": len(test_files),
        "test_files_sample": sorted(test_files)[:80],
        "core_files_sample": sorted(core_files)[:120],
        "tree": tree,
    }


def source_tree(root: Path, max_depth: int = 3) -> list[str]:
    lines: list[str] = []
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        relative = current_path.relative_to(root)
        depth = 0 if relative.as_posix() == "." else len(relative.parts)
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
        if depth > max_depth:
            dirs[:] = []
            continue
        indent = "  " * depth
        if depth == 0:
            lines.append(".")
        else:
            lines.append(f"{indent}{current_path.name}/")
        if depth < max_depth:
            for filename in sorted(files)[:40]:
                file_path = current_path / filename
                if is_ignored(file_path.relative_to(root)):
                    continue
                lines.append(f"{indent}  {filename}")
        if len(lines) >= 300:
            lines.append("  ...")
            break
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", help="Path to write JSON output")
    parser.add_argument("--commits", type=int, default=50)
    parser.add_argument("--cwd", default=os.getcwd())
    args = parser.parse_args()

    warnings: list[str] = []
    root = git_root(Path(args.cwd).resolve())
    data: dict[str, Any] = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "repo_root": root.as_posix(),
        "warnings": warnings,
        "context": collect_context(root, warnings),
        "adrs": collect_adrs(root, warnings),
        "scratch": collect_scratch(root, warnings),
        "git": collect_git(root, args.commits),
        "source": collect_source(root),
    }

    payload = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
