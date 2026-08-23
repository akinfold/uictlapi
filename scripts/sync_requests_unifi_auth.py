#!/usr/bin/env python3
"""Raise the requests-unifi-auth floor to the latest PyPI release if needed.

When the floor moves, bump this package's patch version in pyproject.toml and
src/uictlapi/__init__.py (and tool.bumpversion current_version).

Intended for CI (see .github/workflows/sync-requests-unifi-auth.yml). Exit codes:
0 — success (updated or already current)
1 — error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
INIT_PY = REPO_ROOT / "src" / "uictlapi" / "__init__.py"
DEP_NAME = "requests-unifi-auth"
DEP_RE = re.compile(
    rf'(?P<prefix>"{re.escape(DEP_NAME)}>=)(?P<version>\d+\.\d+\.\d+)(?P<suffix>")'
)
PROJECT_VERSION_RE = re.compile(
    r'(?P<prefix>^version = ")(?P<version>\d+\.\d+\.\d+)(?P<suffix>")',
    re.MULTILINE,
)
BUMPVERSION_RE = re.compile(
    r'(?P<prefix>^current_version = ")(?P<version>\d+\.\d+\.\d+)(?P<suffix>")',
    re.MULTILINE,
)
INIT_VERSION_RE = re.compile(
    r'(?P<prefix>^__version__ = ")(?P<version>\d+\.\d+\.\d+)(?P<suffix>")',
    re.MULTILINE,
)


def fetch_pypi_version(package: str) -> str:
    url = f"https://pypi.org/pypi/{package}/json"
    with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
        payload = json.load(response)
    version = payload["info"]["version"]
    if not isinstance(version, str) or not version:
        raise RuntimeError(f"PyPI returned empty version for {package}")
    return version


def read_dep_floor(pyproject_text: str) -> str:
    match = DEP_RE.search(pyproject_text)
    if not match:
        raise RuntimeError(f"Could not find {DEP_NAME}>=X.Y.Z in pyproject.toml")
    return match.group("version")


def read_project_version(pyproject_text: str) -> str:
    match = PROJECT_VERSION_RE.search(pyproject_text)
    if not match:
        raise RuntimeError("Could not find project version in pyproject.toml")
    return match.group("version")


def bump_patch(version: str) -> str:
    parsed = Version(version)
    if parsed.is_prerelease or parsed.is_devrelease or parsed.epoch:
        raise RuntimeError(f"Refusing to auto-bump non-final version {version!r}")
    major, minor, patch = parsed.release + (0,) * (3 - len(parsed.release))
    return f"{major}.{minor}.{patch + 1}"


def replace_group(pattern: re.Pattern[str], text: str, new_version: str, label: str) -> str:
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"Could not update {label}")
    return pattern.sub(
        f"{match.group('prefix')}{new_version}{match.group('suffix')}",
        text,
        count=1,
    )


def apply_updates(
    *,
    pyproject_text: str,
    init_text: str,
    new_dep_version: str,
    new_package_version: str,
) -> Tuple[str, str]:
    pyproject_text = DEP_RE.sub(
        rf'\g<prefix>{new_dep_version}\g<suffix>',
        pyproject_text,
        count=1,
    )
    pyproject_text = replace_group(
        PROJECT_VERSION_RE, pyproject_text, new_package_version, "project version"
    )
    pyproject_text = replace_group(
        BUMPVERSION_RE, pyproject_text, new_package_version, "bumpversion current_version"
    )
    init_text = replace_group(INIT_VERSION_RE, init_text, new_package_version, "__version__")
    return pyproject_text, init_text


def write_github_output(**values: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def sync(*, dry_run: bool = False) -> int:
    pyproject_text = PYPROJECT.read_text(encoding="utf-8")
    init_text = INIT_PY.read_text(encoding="utf-8")

    current_floor = read_dep_floor(pyproject_text)
    latest = fetch_pypi_version(DEP_NAME)
    package_version = read_project_version(pyproject_text)

    if Version(latest) <= Version(current_floor):
        print(
            f"{DEP_NAME} floor {current_floor} already covers PyPI {latest}; nothing to do."
        )
        write_github_output(
            updated="false",
            dep_version=current_floor,
            package_version=package_version,
        )
        return 0

    new_package_version = bump_patch(package_version)
    print(
        f"Updating {DEP_NAME}>={current_floor} → >={latest}; "
        f"uictlapi {package_version} → {new_package_version}"
    )

    new_pyproject, new_init = apply_updates(
        pyproject_text=pyproject_text,
        init_text=init_text,
        new_dep_version=latest,
        new_package_version=new_package_version,
    )

    if dry_run:
        write_github_output(
            updated="true",
            dep_version=latest,
            package_version=new_package_version,
        )
        return 0

    PYPROJECT.write_text(new_pyproject, encoding="utf-8")
    INIT_PY.write_text(new_init, encoding="utf-8")
    write_github_output(
        updated="true",
        dep_version=latest,
        package_version=new_package_version,
    )
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute updates without writing files",
    )
    args = parser.parse_args(argv)
    try:
        return sync(dry_run=args.dry_run)
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
