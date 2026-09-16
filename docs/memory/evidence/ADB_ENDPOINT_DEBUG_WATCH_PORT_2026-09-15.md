---
memory_schema: 1
as_of: 2026-09-15
---

# ADB endpoint scan watch-port diagnostic

Runtime endpoint debug showed the recovery probe printing the cached endpoint,
private host, scan range, and ADB validation attempts, but it did not expose
whether a specific known-current TCP port was actually traversed by the
concurrent scanner. The existing debug printed only ports that survived the TCP
open test, so absence from terminal output could not distinguish "not scanned"
from "scanned and classified closed/unreachable".

The next diagnostic adds an opt-in local-only `--debug-watch-port <port>` mode.
For the selected port it reports whether the port is inside the scan range, when
its batch is scheduled, and whether the TCP test returns OPEN or
CLOSED/UNREACHABLE. Literal endpoints remain terminal-only and are excluded from
shareable logs and durable memory.

No production installer, companion, Android application, game, streaming, or
router behavior changes in this diagnostic patch.
