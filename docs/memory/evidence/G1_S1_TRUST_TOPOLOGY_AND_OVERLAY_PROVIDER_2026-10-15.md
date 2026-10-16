---
memory_schema: 1
as_of: 2026-10-15
baseline_commit: 3107fb5
---

# G1-S1 — trust topology, the source-address audit, the overlay provider boundary

**Classification: BUILT behind its flag; verified by tests; NOT ADOPTED.**
`PRIVYHUB_OVERLAY_PROVIDER` is absent on the running companion, so nothing
it runs changed. The live smoke (the status endpoint with the flag on the
running companion) is **pending on the stream** (session A). Tailscale is
**not installed** on the hub, so the `tailscale` provider was exercised with
fixtures and reads `binary-absent` on the host.

- Task: `handoffs/G1-S1_TRUST_TOPOLOGY_AND_OVERLAY_PROVIDER_TASK.md`, queue
  `handoffs/QUEUE_2026-10-15B.md` item 1, session B.
- **Baseline: `3107fb5`** (`git log --oneline -1` at the start; the tree then
  carried only the link watch's own files uncommitted —
  `g1_s1_2026-10-15/git_status_at_start.txt`).
- The link watch (`privyhub-link-watch.service`) was running throughout.
  This session did not restart the companion, start a stream or a game, or
  touch `~/privyhub_link_watch/` or `e4_s4d_2026-10-15/`.

## 1. G0 — `docs/REMOTE_TRUST.md` (new)

The two topologies quoted from ROADMAP §G0; the **threat model** (the visited
network, the household LAN, an overlay member without a paired identity, a
request's source address, a lost handheld — what each must never get); the
**fail-closed rules** (overlay absent → remote absent, local unchanged;
identity unknown → no session; permission unknown → denied; a failed
credential never falls back). Every statement is a ROADMAP quote or marked
"G1-S1 proposal".

## 2. The source-address audit (`g1_s1_2026-10-15/source_address_audit.md`)

- Pattern: `client_address|client_ip|clientIp|remote_addr|getpeername|X-Forwarded|x-forwarded|recvfrom|source\[0\]|peername|REMOTE_ADDR`
  over `companion/*.py` and the client's `*.kt` / `*.java`. **80 lines in 11
  companion files, 0 in the client; every one listed.**
- **The finding.** One value decides almost everything: the HTTP source
  (`privyhub_service.py:2377`) becomes `games.handle_post_request`'s
  `client_ip`, which sets **the video target** (the FEC relay,
  `native_fec_relay.py:288`), **the audio target**
  (`native_session_io.py:511`), **the controller's only allowed source**
  (`native_session_io.py:2533`, which is today the controller's whole
  authorization), and the target a recovery restart reuses
  (`games.py:3740` → `:232`). The client sends **no identity and no
  address** at setup — only `?port=` (`NativeStreamActivity.kt:719`).
- **Stays as is:** the loopback-only test tools (`games.py:3405`…`:3510`,
  `adaptive_bitrate_live.py:1162`: host-local authorization), the access-log
  line (`privyhub_service.py:1856`: routing evidence), the internal peers
  (RetroArch's command reply, the relay's loopback input).
- `X-Forwarded-*`, `REMOTE_ADDR`, `getpeername`: 0 hits.

## 3. The overlay provider boundary (`companion/overlay/`, new)

| file | what |
| --- | --- |
| `provider.py` | the contract: `OverlayState` (connected, available, path direct / relayed / no-peer / none, peer readiness, MTU, reason; the endpoint **opaque**, never exported; diagnostics provider-internal) and `public()` (endpoint → `present` / `absent` + an 8-hex hash, no diagnostics) |
| `none.py` | always absent (the default) |
| `tailscale.py` | `tailscale status --json`, and `tailscale netcheck --format=json` only while Running, **only if the binary exists**; never installs, never runs `up` / `down` / `set`; 10-s cache; binary absent → `available: false`, reason `binary-absent` |
| `__init__.py` | `select_provider` / `reporter_from_environ` by `PRIVYHUB_OVERLAY_PROVIDER=none\|tailscale`; absent / empty → None; unknown → `none` with reason `unknown-provider` (fail closed); `OverlayStatusReporter`: the status field + one log line per state change (no endpoint value) |
| `__main__.py` | `python3 -m companion.overlay --state [--provider …] [--diagnostics]` |

**The companion (`companion/privyhub_service.py`, predecessor
`27d31b58…5fbc`, after G1-S1 `79041797…`):** two edits.

- Module level: `OVERLAY_STATUS = None`; **only if**
  `PRIVYHUB_OVERLAY_PROVIDER` is non-empty, `from overlay import …` and the
  reporter is built. Absent: nothing imported, constructed or called; no
  thread.
- `PrivyHubController.status()`: the document is built as before into
  `payload`; after the lock, `if OVERLAY_STATUS is not None:
  payload["overlay"] = …`; return. Absent: the same bytes (§4).

## 4. Verification (`g1_s1_2026-10-15/tests_output.txt`)

`python3 -m unittest discover -s tests/overlay -v` → **17 tests, OK**:

- selection: absent / empty / blank → None (today); `none`, `tailscale`,
  case and spaces; an unknown name → `none`, reason `unknown-provider`;
- the `none` provider's public form, exactly;
- `tailscale` with fixtures (`tests/overlay/fixtures/`, no addresses — the
  endpoint is a placeholder): **connected-direct, connected-relayed,
  connected-no-peer, stopped, needs-login, daemon-down, binary-absent** (no
  process run at all); every argv the provider ran is one of the two
  read-only subcommands; netcheck only while Running; the cache;
- the endpoint never appears in `public()`, in `repr`, or in a log line; one
  log line per state change;
- **the status document, byte for byte:** the baseline's `status()` (kept as
  `fixtures/status_method_predecessor.py.txt`, from `git show 3107fb5`) and
  the edited one, both run on the same fake controller with the flag absent →
  identical JSON bytes; with a reporter set → the only new key is `overlay`;
- the service imports `overlay` only inside the flag's `if` (AST check).

**The one-shot read on this host** (`g1_s1_2026-10-15/overlay_state.txt`):
default → `none`, absent; `--provider tailscale` → `binary-absent`,
`tailscale_binary_installed: false`. Nothing was run against the companion.

## 5. Pending, and for the user

- **The user, by hand:** install Tailscale on the hub (their sudo; ROADMAP
  §G1's first provider) and log it in. Nothing here installs it.
- **Session A, then:** the live smoke — the companion restarted with
  `PRIVYHUB_OVERLAY_PROVIDER=tailscale` (a drop-in), `GET /status` shows the
  `overlay` object, the journal shows one `overlay:` line; then the drop-in
  removed. **Pending on the stream** (the watch owns the companion until
  2026-10-20T04:00Z).
- Not adopted; the flag is absent.

## 6. Files; disclosures

- `g1_s1_2026-10-15/`: `baseline_commit.txt`, `git_status_at_start.txt`,
  `predecessor_sha256.txt`, `after_sha256.txt`, `source_address_audit.md`,
  `tests_output.txt`, `overlay_state.txt`, `g1_s1.diff` (the service diff
  and the new files), `redact_check.txt`, `manifest.sha256`.
- Patch record: `patches/G1-S1_OVERLAY_PROVIDER_BOUNDARY.md`
  (`PATCH_INDEX.md` is not session B's file this queue; not updated).
- Running the tests let Python write bytecode caches (`__pycache__/`,
  gitignored) under `companion/overlay/` and `tests/overlay/`; kept.
- No sudo, no nft, the Opal untouched; nothing fetched or installed;
  nothing deleted. Git status: `logs/g1_s1_git_status.txt`.
