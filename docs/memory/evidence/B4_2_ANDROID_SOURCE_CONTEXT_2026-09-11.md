---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B4.2 exact Android Moonlight source-context result

Classification: `B4_2_ANDROID_SOURCE_CONTEXT_CAPTURED`

Authoritative MainActivity:
- SHA-256 `bce727b866c1901aa7e8eeb8cd288b701fe1a0b4317a4db3b88b86ad7054e36e`;
- 377170 bytes / 14471 lines;
- no BOM / CRLF.

Authoritative AndroidManifest:
- SHA-256 `c34751d9ebf89786efbbb255d50f182a8f6e5986b490c0055d1dc2616fd29ee1`;
- 2596 bytes / 77 lines;
- no BOM / LF.

Exact function hashes:
- buildGameCatalogMessage `aea6325a50573697d7e3559c6e9affb893fe7d665116614abb43ae3258f54588`;
- launchGameOnCompanion `2443d64e57ae1940f7ee0b9b28c1a33441b6b453352f5c5b86ba69e5561a6ba3`;
- openGameStreamClient `c04882f29afabe79f8150ca6ffe54dc0d2027aa4b4317f88e95919058eb1051c`;
- showGameDetails `83c5c46ed779598b39823bc711750a743ab2d064d8e27861d2e97a540f902da0`.

Manifest context:
`4a06d73207552f16ebd79d5e7dcd1c99d337455f2397f591415a7b2777c3b543`.

Observed edge:
- Sunshine catalog wording;
- full Moonlight/com.limelight launcher;
- three direct launcher calls;
- stale stream_host/stream_warning parsing after B4.1;
- unreachable stream_host game-details branches;
- manifest com.limelight package query.

B4.2 removes only these evidenced edges. Uncaptured helper definitions and
runtime/download/setup artifacts remain until a post-B4.2 orphan audit.
