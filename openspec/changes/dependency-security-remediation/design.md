# Design

## Scope

- upgrade Electron to a patched release in the desktop workspace and keep the
  electron-builder version aligned with the generated application;
- upgrade the website nanoid override to a patched 3.x release;
- upgrade the resolved Python `h2` package to a patched release when its
  transitive consumer permits it;
- rerun OSV against every tracked lockfile;
- record the remaining `extract-zip` finding and its reachability as an
  explicit follow-up rather than silently suppressing it.

## Safety

Do not add credentials, telemetry, or runtime network behavior. Do not change
Edgmes application logic. Dependency changes must be reproducible from the
lockfiles and verified by the affected workspace checks.
