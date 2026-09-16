# Dependency security posture

The August 2026 OSV findings were remediated on the dependency-security branch:

- Website and root 3.x NanoID resolutions are pinned to `3.3.18`, matching the
  upstream fix in commit `8fdda828a8`.
- Python `h2` is resolved to `4.4.1` through `grpclib`.

- Electron is pinned to `41.10.3`, which includes fixes for the reported
  Electron advisories and uses Electron's internal extractor package.
- The vulnerable public `extract-zip@2.0.1` dependency is no longer present in
  the Electron dependency tree. The replacement `@electron-internal/extract-zip`
  package is a separate Electron-maintained package and is not the package
  named by CVE-2026-56876.

The local host is older than the repository's declared Node.js engine and is
not used as release validation.
