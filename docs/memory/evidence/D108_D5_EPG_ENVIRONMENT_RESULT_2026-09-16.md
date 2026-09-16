# D-108 — D5 EPG environment result — 2026-09-16

**Status:** runtime-validated diagnostic result

D-108 completed with classification:

`D108_ENVIRONMENT_NODE_UNSUPPORTED`

Measured host environment:

- Git: 2.47.3;
- Node: unavailable;
- npm: unavailable;
- upstream EPG minimum Node requirement: 20.20.0.

Because the environment gate failed, D-108 intentionally stopped before:

- reading the onn TV database;
- fetching current guide metadata;
- checking out the upstream EPG repository;
- installing upstream npm dependencies;
- selecting representative guide sites;
- attempting any guide grab.

No PrivyHub TV/EPG database or production file was modified.

Interpretation:

This result is an environment/toolchain boundary, not evidence that local EPG
programme acquisition fails.

The host should not be modified merely to answer the viability question.
D-109 therefore supplies a checksum-verified portable Node runtime entirely
inside temporary probe state and reuses the exact D-108 acquisition logic.
