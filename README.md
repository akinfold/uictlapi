# uictlapi

[![PyPI](https://img.shields.io/pypi/v/uictlapi.svg?logo=pypi&logoColor=white)](https://pypi.org/project/uictlapi/)
[![Docker](https://img.shields.io/docker/v/akinfold/uictlapi/latest?logo=docker&logoColor=white&label=docker)](https://hub.docker.com/r/akinfold/uictlapi)
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/akinfold/uictlapi/blob/main/LICENSE)

Curl-like CLI for the UniFi Controller / UniFi OS Web UI API — with login and CSRF
handled for you.

Auth and CSRF come from
[`requests-unifi-auth`](https://github.com/akinfold/requests-unifi-auth). This package is
only the HTTP CLI: any Web UI / proxy URL, any method. It is **not** a typed UniFi SDK and
does not invent domain commands (`routes apply`, inventory, multi-controller orchestration).

Live auth/CSRF compatibility against real controllers is tracked in
[`requests-unifi-auth` COMPATIBILITY.md](https://github.com/akinfold/requests-unifi-auth/blob/main/COMPATIBILITY.md).
Verified with this CLI: **uictlapi 0.1.3** against **UniFi Network 10.5.67**
(`GET …/trafficroutes` → HTTP 200, 2026-08-24).

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

## Finding API URLs

UniFi does not publish a stable public catalog of every Web UI path. Copy them from the
browser:

1. Open the UniFi Network UI and sign in.
2. Open DevTools → **Network**, filter by Fetch/XHR.
3. Click the screen that does what you want (traffic routes, clients, …).
4. Pick a request to your controller (often under `/proxy/network/...`).
5. Copy the full URL (or path) and reuse it with `uictlapi get|post|…`.

Paths change between UniFi Network versions; treat DevTools as the source of truth.

## Safety

- Create a **dedicated local Admin** for automation (not Owner / Super Admin). Prefer the
  minimum role that can call the endpoints you need.
- Store credentials in a file with mode `600`, not in the shell history:

  ```bash
  mkdir -p ~/.config/uictlapi
  printf '%s\n' 'user' 'pass' '192.168.1.1' > ~/.config/uictlapi/auth
  chmod 600 ~/.config/uictlapi/auth
  ```

- Prefer an auth file that includes the **host** (three-line form or `user:pass@host`).
  The CLI refuses to send credentials when that host does not match the URL hostname.
- `--no-verify` skips TLS certificate checks. Convenient on LAN with the default UniFi
  certificate; for anything beyond a trusted lab network, install/trust a proper CA and
  omit `--no-verify`.
- Never paste passwords, cookies, or CSRF tokens into issues or chat logs.

## Usage

Auth (`-a` / `--auth`):

- `user:pass@host`
- three-line file — `username`, `password`, `host` (password may contain `:` and `@`)
- `user:pass` or two-line `user` / `pass` — host from the request URL (less safe;
  prefer an explicit host in the file)
- `@/path/to/file` — file contains any of the forms above

```bash
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
`--status-only` / `--no-verify` / `-t`. Exit status `1` on HTTP ≥ 400, `2` on transport
errors (including auth host mismatch).

## Releasing

Version lives in `pyproject.toml` and `src/uictlapi/__init__.py`. Bump on `main` first
(GitHub Actions → **Bump version**, or locally with `bump-my-version`), then:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

The **Publish** workflow runs tests, uploads to PyPI, pushes multi-arch Docker images
(`X.Y.Z`, `X.Y`, and `latest` when appropriate), and creates a GitHub Release.

### Auto-sync of `requests-unifi-auth`

The **Sync requests-unifi-auth** workflow (schedule every 6 hours, or manual
`workflow_dispatch`) checks PyPI for a newer `requests-unifi-auth`, raises the
`>=` floor, bumps this package's patch version, pushes `main` + tag, and
dispatches **Publish** on that tag.

## License

MIT
