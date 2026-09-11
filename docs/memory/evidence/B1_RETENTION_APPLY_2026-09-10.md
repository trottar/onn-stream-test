---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B1.12 first explicit retention apply

Policy:
`03466dbefde0c3f82fcecfa496009d0fcfdb8573825f6ffb01a4bd95ef012628`

Apply result:
- requested: true;
- automatic: false;
- deleted count: 8;
- deleted bytes: 112,619,830;
- failures: 0.

Post-apply state:
- forward transport: 50 files / 225,071,881 bytes / 214.645 MiB;
- forward limit: 256 MiB;
- forward candidates: 0;
- forward blocked: false;
- reverse transport: 125.393 MiB / candidates 0 / blocked false;
- debug bundles: 23.728 MiB / candidates 0 / blocked false;
- durable memory in retention scope: false;
- patch backups in retention scope: false.

Conclusion:

The first manual retention apply completed exactly as reviewed and left every
managed family under its cap with no pending candidate deletion. Retention
remains manual; automatic cleanup is not enabled.
