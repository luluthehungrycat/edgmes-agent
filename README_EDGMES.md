# Hermes Agent Edge / Edgmes Agent

This repository is a downstream distribution of [Hermes Agent](https://github.com/NousResearch/hermes-agent) focused on edge devices, local models, and constrained context windows.

## Naming

- **Repository:** `edgmes-agent`
- **Technical/project name:** Edgmes Agent
- **CLI name:** `edgmes` (planned)
- **User-facing product name:** Hermes Agent Edge

Edgmes is intended to preserve the useful stateful, skill-based, profile-aware parts of Hermes while providing an edge-oriented execution policy for smaller models and 16k–64k context windows.

## Current status

The repository currently contains the clean upstream baseline plus the initial Edgmes namespace and project documentation. No upstream runtime files have been forked or modified yet.

Planned areas include:

- model capability profiles
- bounded edge execution loops
- context budgeting and a structured state ledger
- narrow, lazy tool exposure
- deterministic compaction and verification
- edge-specific packaging and smoke tests

## Development principles

1. Keep the upstream filesystem layout intact while boundaries are being established.
2. Put Edgmes-specific behavior under `edgmes/` whenever practical.
3. Prefer generic integration seams that can be proposed upstream.
4. Do not expose the entire Hermes tool and skill universe to small models.
5. Treat persistent state as external data and construct bounded working context.
6. Keep upstream synchronization automated, reviewable, and fail-closed.

See [`docs/edgmes/`](docs/edgmes/) for the architecture and synchronization policy.

## License and lineage

Edgmes retains the upstream MIT license and attribution. It is an independent downstream project and is not an official Nous Research distribution.
