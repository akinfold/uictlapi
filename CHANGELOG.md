# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.4] - 2026-09-13

### Added

- Added a GitHub Pages coverage badge and public project health badges.
- Added a security policy with private vulnerability reporting instructions.
- Expanded root command help with credential formats, host protection, exit codes,
  and a complete example.

## [0.1.3] - 2026-08-23

### Added

- Added a three-line credential-file format with username, password, and host.
- Refuse to send credentials when the credential host does not match the request URL.

## [0.1.2] - 2026-08-23

### Added

- Read credentials from `@file` in `user:password`, `user:password@host`, or
  two-line username/password form.
- Support passwords containing `:` and `@` in the two-line credential format.

## [0.1.1] - 2026-08-23

### Added

- First PyPI release.
- Added `uictlapi --version`.
- Added test, version-bump, and tag-triggered release workflows.
- Publish the same version to PyPI, Docker Hub, and GitHub Releases.

### Changed

- Require `requests-unifi-auth>=0.1.5`.
- Document the curl-like product scope, installation, and common requests.

## [0.1.0] - 2026-04-04

### Added

- Initial curl-like CLI for UniFi Controller and UniFi OS Web UI API requests.
- Support GET, POST, PUT, PATCH, DELETE, HEAD, and OPTIONS requests.
- Added Docker images for AMD64 and ARM64.

[Unreleased]: https://github.com/akinfold/uictlapi/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/akinfold/uictlapi/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/akinfold/uictlapi/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/akinfold/uictlapi/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/akinfold/uictlapi/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/akinfold/uictlapi/releases/tag/v0.1.0
