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
docker run --rm akinfold/uictlapi:latest get -a user:pass@controller.local https://controller.local/api/stat/sites
```
