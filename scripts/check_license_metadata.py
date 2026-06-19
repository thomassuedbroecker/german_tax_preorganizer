#!/usr/bin/env python3
"""Verify repository license metadata and notice coverage."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SPDX = "BSD-2-Clause"
REQUIRED_FILES = (
    "LICENSE",
    "LICENSE_POLICY.md",
    "THIRD_PARTY_NOTICES.md",
    "CONTENT_PROVENANCE.md",
)


def _dependency_name(requirement: str) -> str:
    match = re.match(r"[A-Za-z0-9_.-]+", requirement)
    return match.group(0) if match else requirement


def main() -> int:
    errors: list[str] = []
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject.get("project", {})

    if project.get("license") != EXPECTED_SPDX:
        errors.append(
            f"pyproject.toml project.license must be {EXPECTED_SPDX!r}"
        )

    license_files = project.get("license-files", [])
    if "LICENSE" not in license_files:
        errors.append("pyproject.toml project.license-files must include LICENSE")

    for relative_path in REQUIRED_FILES:
        if not (ROOT / relative_path).is_file():
            errors.append(f"missing required licensing file: {relative_path}")

    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    if not license_text.startswith("BSD 2-Clause License"):
        errors.append("LICENSE does not contain the expected BSD 2-Clause text")

    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8").lower()
    dependency_groups = [project.get("dependencies", [])]
    dependency_groups.extend(project.get("optional-dependencies", {}).values())
    dependencies = {
        _dependency_name(requirement)
        for group in dependency_groups
        for requirement in group
    }
    for dependency in sorted(dependencies, key=str.lower):
        if dependency.lower() not in notices:
            errors.append(
                f"direct dependency missing from THIRD_PARTY_NOTICES.md: {dependency}"
            )

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for relative_path in REQUIRED_FILES:
        if relative_path not in readme:
            errors.append(f"README.md does not link to {relative_path}")

    if errors:
        print("License metadata check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"License metadata OK: {EXPECTED_SPDX}; "
        f"{len(dependencies)} direct dependencies/extras covered."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
