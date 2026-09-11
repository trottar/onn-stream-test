---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B4.3 orphan-reference audit

Classification:
`B4_3_ORPHAN_REFERENCE_AUDIT_CAPTURED`

Disposition:
`B4_3_ORPHANS_CONFIRMED_PREPARE_CLEANUP_PATCH`

Exact state:
- MainActivity `d9f7928062a86cdab643ef34b6fa8235a03a2bc900a3d8d7f578cd720d5bc2ea`;
- AndroidManifest `ab1140c3230582f9dbbbf3c179d8fa08363971d9289e08442487f3849c7ac8a2`;
- B4.1 games.py `f1271c865cdf88b971da4116d7eb887bf9855864ce1ae848baafc7a3452e0f9c`;
- stream_manager.py `12ea9b05879c434b85e1c01892d9a7b6020b85efbdc3b7656a95275e47db8e8b`.

Proven code orphans:
- buildStreamHostMessage: definition present, call sites 0,
  body SHA `aae130f2ebf2e4acc197627e2ff70d66dba17e24f088a72a8b339c61a05093d7`;
- setGameStreamHost: definition present, call sites 0,
  body SHA `72183b87617ea57ce106af22eb17483a69c25c41a00da7bc2eae6689dbf6c3ee`;
- stream_manager.py: zero importers outside itself.

Product edges:
- Android Moonlight/Sunshine edge clean;
- Games -> stream_manager edge clean.

Physical legacy groups remain present, but B4.3 captured only paths/counts/bytes
rather than exact content hashes. Therefore physical artifact deletion requires
a separate hash-manifest probe after code-orphan cleanup.
