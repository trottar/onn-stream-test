---
memory_schema: 1
as_of: 2026-10-15
status: TASK HANDOFF — G1-S1, queue 2026-10-15B item 1: Phase G's G0 and G1. (a) The trust topology and threat model written down as the project's own document; (b) an audit of every place the companion derives a target, an identity or a permission from a request's source address (G3's input); (c) the overlay provider boundary in the companion — `none` (today) and `tailscale` — behind `PRIVYHUB_OVERLAY_PROVIDER` (absent = today, byte for byte). Software only; no stream; no install; nothing adopted; nothing committed
---

# G1-S1 — trust topology, the source-address audit, the overlay provider boundary

Read first: ROADMAP §G0, §G1, §G3, and "Network trust and remote
authorization boundary" / "Privacy boundary" / "Capability-driven
architecture" (the Guiding principles at the end); `companion/`
(`native_stream.py`, `plugins/games.py`, `native_session_io.py`, the
HTTP layer: where `remote_addr` / peer address / `X-Forwarded-*` are
read), the Android client's session-setup calls (what it sends today),
`docs/TOOLS.md`, `D6_R1_UDP_SUITE_REPLAY_…` (the replay suite),
`CL_B1_…` (the client's report body).

## 1. `docs/REMOTE_TRUST.md` (G0)

The two topologies from ROADMAP §G0 as the project's own document, plus
what the ROADMAP leaves implicit: the **threat model** — who is
untrusted (the visited network; the household LAN; anyone holding the
travel router or the overlay key without a paired PrivyHub identity; a
lost handheld), what each must not get (any PrivyHub service on the
visited LAN; application authority from overlay membership; media or
controller endpoints from a source address), and the **fail-closed
rules** (overlay absent → remote access absent, local unchanged; identity
unknown → no session; permission unknown → denied). One page. Every
sentence either quotes ROADMAP or is marked "G1-S1 proposal".

## 2. The source-address audit (G3's input; no change)

`g1_s1_<date>/source_address_audit.md`: every line in `companion/` and
the client where a request's source address or peer decides something —
file:line, what it decides (media target, controller target, identity,
permission, logging only), and the G3 category it must move to (client
identity / session identity / declared endpoint / authorization /
routing evidence only). Logging-only uses stay. The audit is complete
when `grep` for the address accessors finds nothing unlisted (state the
patterns searched).

## 3. The overlay provider boundary (G1)

- `companion/overlay/`: `provider.py` (the contract: `state()` →
  connected/disconnected, direct vs relayed, reachable overlay endpoint
  (opaque, never an address in logs or records), MTU/path constraint if
  known, peer/session readiness, provider diagnostics kept inside the
  provider), `none.py` (always "absent"; the default), `tailscale.py`
  (reads `tailscale status --json` and `tailscale netcheck --format=json`
  **only if the binary exists**; never installs, never runs `tailscale
  up`; absent binary → state "unavailable" with the reason).
- Selection by **`PRIVYHUB_OVERLAY_PROVIDER=none|tailscale`**, absent =
  `none` = today byte for byte: no new thread, no new call, no new
  status field when absent. With it set: the companion's status endpoint
  gains an `overlay` object (the contract's fields; the endpoint value
  redacted to "present"/"absent" + a short hash); one log line per state
  change.
- **Tests** (`tests/overlay/`): fixtures for `tailscale status` JSON in
  the connected-direct, connected-relayed, stopped, needs-login and
  binary-absent cases; the `none` provider; the selection by flag; the
  byte-for-byte absence (the status document's keys identical to today
  without the flag). Run them; the output in the record.
- **No stream, no restart.** The provider is exercised in-process by the
  tests and by a one-shot `python3 -m companion.overlay --state` (reads
  the host as the running companion would, without touching it).
  Whether the host has `tailscale` installed is reported, not required.
  The live smoke (the status endpoint with the flag on the running
  companion) is "pending on the stream" for session A.

## 4. The record

`evidence/G1_S1_TRUST_TOPOLOGY_AND_OVERLAY_PROVIDER_<date>.md` +
`g1_s1_<date>/` (the audit, the test output, the `--state` output with
the endpoint redacted, the diff, `redact_check.txt`,
`manifest.sha256`); `docs/REMOTE_TRUST.md`; `docs/ROADMAP.md` §G0/§G1
status lines; `patches/G1-S1_…md`; `logs/g1_s1_git_status.txt`. **What the
user must do by hand, listed in the record:** install Tailscale on the
hub (their sudo; the ROADMAP's first provider), then session A runs the
live smoke. Nothing adopted; the flag absent; then queue item 2.
