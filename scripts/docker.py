import subprocess
import sys
import os


def build():
    """Build Docker image"""
    project_name = "uictlapi"
    version = "0.1.0"  # You might want to extract this from pyproject.toml

    # Build the image
    cmd = [
        "docker", "build",
        "-t", f"akinfold/{project_name}:latest",
        "-t", f"akinfold/{project_name}:{version}",
        "."
    ]

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def push():
    """Push Docker image to Docker Hub"""
    project_name = "uictlapi"
    version = "0.1.0"

    # Push both tags
    tags = [f"akinfold/{project_name}:latest", f"akinfold/{project_name}:{version}"]

    for tag in tags:
        cmd = ["docker", "push", tag]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            sys.exit(result.returncode)
