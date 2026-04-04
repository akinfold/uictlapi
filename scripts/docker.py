import subprocess
import sys
from pathlib import Path


def _project_version() -> str:
    root = Path(__file__).resolve().parent.parent
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("version = "):
            _, _, rest = stripped.partition("=")
            return rest.strip().strip('"').strip("'")
    raise RuntimeError("Could not find version in pyproject.toml")


def build():
    """Build Docker image"""
    project_name = "uictlapi"
    version = _project_version()

    cmd = [
        "docker",
        "build",
        "-t",
        f"akinfold/{project_name}:latest",
        "-t",
        f"akinfold/{project_name}:{version}",
        ".",
    ]

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def push():
    """Push Docker image to Docker Hub"""
    project_name = "uictlapi"
    version = _project_version()

    tags = [f"akinfold/{project_name}:latest", f"akinfold/{project_name}:{version}"]

    for tag in tags:
        cmd = ["docker", "push", tag]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            sys.exit(result.returncode)
