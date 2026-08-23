# uictlapi

[![PYPI](https://img.shields.io/pypi/v/uictlapi)](https://pypi.org/project/uictlapi/)
[![Docker Image](https://img.shields.io/docker/v/akinfold/uictlapi?label=docker&sort=semver)](https://hub.docker.com/r/akinfold/uictlapi)
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/akinfold/uictlapi/blob/main/LICENSE)

Curl-like CLI for the UniFi Controller / UniFi OS Web UI API — with login and CSRF
handled for you.

Auth and CSRF come from
[`requests-unifi-auth`](https://github.com/akinfold/requests-unifi-auth). This package is
only the HTTP CLI: any Web UI / proxy URL, any method. It is **not** a typed UniFi SDK and
does not invent domain commands (`routes apply`, inventory, multi-controller orchestration).

Live auth/CSRF compatibility against real controllers is tracked in
[`requests-unifi-auth` COMPATIBILITY.md](https://github.com/akinfold/requests-unifi-auth/blob/main/COMPATIBILITY.md).

## Installation

### pip

```bash
pip install uictlapi
```

Requires `requests-unifi-auth>=0.1.5`.

### Docker

```bash
docker run --rm akinfold/uictlapi:latest --help
```

## Usage

Auth (`-a` / `--auth`):

- `user:pass@host`
- three-line file — `username`, `password`, `host` (password may contain `:` and `@`)
- `user:pass` or two-line `user` / `pass` — host from the request URL (less safe;
  prefer an explicit host in the file)
- `@/path/to/file` — file contains any of the forms above

**Host check:** if credentials name a host, it must match the URL hostname
(case-insensitive). On mismatch the CLI exits without sending the request or
credentials.

```bash
mkdir -p ~/.config/uictlapi
printf '%s\n' 'user' 'pass' '192.168.1.1' > ~/.config/uictlapi/auth
chmod 600 ~/.config/uictlapi/auth

uictlapi get -a @$HOME/.config/uictlapi/auth --no-verify \
  'https://192.168.1.1/proxy/network/v2/api/site/default/trafficroutes'
```

```bash
# Inline (host in the auth string)
uictlapi get -a 'user:pass@192.168.1.1' --no-verify \
  'https://192.168.1.1/proxy/network/v2/api/site/default/trafficroutes'

# Same via Docker (mount the auth file)
docker run --rm -v "$HOME/.config/uictlapi/auth:/auth:ro" akinfold/uictlapi:latest \
  get -a @/auth --no-verify \
  'https://192.168.1.1/proxy/network/v2/api/site/default/trafficroutes'

# POST JSON body (from string or @file)
uictlapi post -a @$HOME/.config/uictlapi/auth --no-verify \
  -j '{"enabled":true}' \
  'https://192.168.1.1/proxy/network/v2/api/site/default/some-endpoint'

uictlapi --version
```

Common flags mirror curl-ish habits: `-H` / `-p` / `-d` / `-j` / `-o` / `--show-headers` /
`--status-only` / `--no-verify` / `-t`. Exit status `1` on HTTP ≥ 400, `2` on transport errors.

## Releasing

Version lives in `pyproject.toml` and `src/uictlapi/__init__.py`. Bump on `main` first
(GitHub Actions → **Bump version**, or locally with `bump-my-version`), then:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

The **Publish** workflow runs tests, uploads to PyPI, pushes multi-arch Docker images
(`X.Y.Z`, `X.Y`, and `latest` when appropriate), and creates a GitHub Release.

## License

MIT
