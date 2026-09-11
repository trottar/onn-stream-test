---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B4.1 exact Games source-context result

Fresh classification:

`B4_1_GAMES_SOURCE_CONTEXT_CAPTURED`

Authoritative source:
- path: `companion/plugins/games.py`;
- SHA-256: `3fe502bda2f85706855e6f4e2f38ae0421f7c5de63136efae908d32393c30c77`;
- bytes: 96176;
- lines: 3536;
- BOM: none;
- newline: CRLF.

Structural counts:
- legacy import: 1;
- legacy constructor assignment: 1;
- legacy catalog dict: 1;
- legacy action if: 3;
- legacy payload assignments: 5;
- legacy stream calls: 8;
- StreamHostError handlers: 2;
- AST probe initially reports two launch-try ancestors because the outer request
  try contains the nested launch try; the production transform therefore
  selects only a Try with a *direct Name(StreamHostError) handler*, which is the
  nested launch try.

Exact context block hashes:
- lines 8-18: `9b5b4bbddcd1758db6fc16e48c8fc38d5c123f1a7da7c1001653ee7718de8c56`;
- lines 67-79: `8a79c97a241e121c666d3292d6eafaf3d036f9ca38e0107745d665ff6e475905`;
- lines 1663-1680: `4d3cb5263604f64ced70c3bcb72792e1d0628235cddf378aff1ff379462a4645`;
- lines 2782-2797: `996ee818d6f38614efcd2bbaa1e72d22a5539340eeee2a1d92adb818c073fdfb`;
- lines 3092-3536: `642d3f77a1f3e619b3b90823162e699fe1c28c72f69f935864bac2183e0a6f7d`.

Disposition:
`USE_EXACT_AST_SPANS_AND_CAPTURED_CONTEXT_FOR_B4_1_REBUILD`.
