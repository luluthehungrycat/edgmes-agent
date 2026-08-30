# Dependency security remediation

The OSV scan reports vulnerabilities in dependencies already present on `main`.
Upgrade dependencies with published fixes without mixing application behavior
changes into this remediation. Preserve an explicit limitation for
`extract-zip` because its current upstream line has no patched release.
