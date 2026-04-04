# uictlapi
The Ubiquiti Unifi Controller API command line client. Takes care of authentification and CSRF handling and provides convenient curl like interface which makes available use all the features available in the Web UI.

## Installation

### Using pip
```bash
pip install uictlapi
```

### Using Docker
```bash
# Run directly
docker run --rm akinfold/uictlapi:latest --help

# Example usage
docker run --rm akinfold/uictlapi:latest get -a user:pass@controller.local https://controller.local/proxy/network/v2/api/site/default/trafficroutes
```

## Publishing to Docker Hub

The image on Docker Hub is https://hub.docker.com/repository/docker/akinfold/uictlapi  

Releases are built and pushed by GitHub Actions for evry **semantic version tag** (for example `v0.1.0`).

For example:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The workflow publishes version tags (for example `0.1.0`, `0.1`) and updates **`latest`** when the release is the highest non-prerelease semver tag (`latest=auto`).
