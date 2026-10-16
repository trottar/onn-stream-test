---
memory_schema: 1
as_of: 2026-10-15
baseline_commit: 3107fb5 (plus G1-S1's uncommitted overlay boundary)
---

# G3-S1 — session identity and authorization, host side

*(§1 was written before any G3-S1 code; the sections after it were
written after the tests.)*

## 1. The design (written before the code)

**The rule** (ROADMAP §G3 and the trust boundary): source address is
routing evidence, never identity; overlay membership is transport, never
authorization; session setup fails closed; permissions are auditable. The
places it touches are G1-S1's audit (`g1_s1_2026-10-15/source_address_audit.md`
§6): the media/controller target taken from the source, and the controller
filter as the only authorization.

**One module, `companion/session_identity.py`, behind
`PRIVYHUB_SESSION_IDENTITY=v2`.** Absent = today: nothing imported, no store
read, no audit written, no header, the same response bytes.

### 1.1 Routing evidence (never identity)

Each request's source is classified, in memory only, as:

- `local` — loopback (the hub itself);
- `overlay` — the overlay's address space (the shared CGNAT block and the
  Tailscale IPv6 ULA prefix, built from integers in code, no literal);
- `lan` — inside one of the hub's own on-link IPv4 subnets
  (`/proc/net/route`: routes with no gateway, overlay interfaces excluded;
  re-read every 60 s) — the Opal's LAN as the hub sees it;
- `unknown` — anything else (IPv6 global, a routed public source…).

The audit log records `lan` / `overlay` / `unknown` (`local` is written as
`lan` with `host_local: true`). **No address is stored or logged.**

### 1.2 Client identity and pairing (host side now; client side G3-S2)

- The client generates a long random key (≥ 32 bytes) at first run (G3-S2).
- **Pairing happens once, on the home LAN, through a host action:**
  `POST /session/pairing/open` from the hub itself (loopback) or from a
  session holding `pairing-admin` opens a **120-s window** and returns a
  6-digit one-time code to that caller, which the host shows. The client
  sends `POST /session/pair {code, device_name, key}`; it is accepted only
  from `lan` or `local`, only while the window is open, with the right code
  (constant-time compare), at most 5 attempts per window. Success closes the
  window.
- **The store:** `~/.config/privyhub/paired_devices.json` (outside git; dir
  0700, file 0600, atomic replace): `device_id` (`dev-` + 16 hex), display
  name, the key, `paired_at`, permissions. **No address.** The stdlib has no
  public-key signatures and nothing may be fetched, so the scheme is
  **HMAC-SHA256 with the device key**, which the host must hold (0600, never
  logged). A public-key scheme can replace it in G3-S2 without changing the
  flow.
- **Revocation:** removing a device from the store invalidates its tokens at
  their next use.

### 1.3 Session identity

- `POST /session/nonce` → a single-use nonce, 60-s expiry (at most 256
  outstanding).
- `POST /session/setup {device_id, nonce, media_host, video_port, sig}`,
  `sig` = hex HMAC-SHA256(key, `"privyhub-session-setup-v1\n" + device_id +
  "\n" + nonce + "\n" + media_host + "\n" + video_port`). Checks in order:
  known device → nonce issued / unexpired / unused (a reuse is
  `nonce-replayed`) → signature → endpoints. Success issues a **session
  token** (random, 8-h expiry) bound to the device id, its permissions and
  its declared endpoints.
- Every later call carries `X-PrivyHub-Session: <token>`. A presented token
  that fails (unknown, expired, device revoked) is **refused; it never falls
  back** to the legacy path. `POST /session/end` revokes a token.

### 1.4 Declared endpoints

- The client **declares** `media_host` (its IPv4 address for video, audio
  and controller return) and `video_port`. The host streams there — **not to
  the request's source**: the games plugin's `client_ip` becomes the
  declared host for a token session.
- Today's stream code takes one host for all three, so G3-S1 declares one;
  separate per-stream hosts are G3-S2's (refused until then).
- Validity: IPv4, not loopback / unspecified / multicast; port 1024-65535;
  **its routing class must match the source's** (a `lan` source declares a
  `lan` host, an `overlay` source an `overlay` host; a `local` source may
  declare `lan`). Else `endpoint-invalid` / `endpoint-class-mismatch`.
- `native-stream-start?port=` must equal the declared `video_port`, else
  `endpoint-port-mismatch`.

### 1.5 Authorization

- Permissions: `games`, `tv`, `vod`, `pairing-admin`. A paired device gets
  `games`, `tv`, `vod` by default; an unpaired one nothing.
- Each path needs one: `/plugins/games/*` and `/diagnostics/client-health` →
  `games`; `/plugins/tv_state|epg|iptv_org/*`, `/sources…`, `/stop` → `tv`;
  `/status` and the other `/diagnostics/*` → `diagnostics`, which is **not a
  grantable permission** in v1, so a token session is denied there
  (`permission-unknown`) until G3-S2 decides; any other path → unknown →
  denied. `vod` has no companion route (the range server is a separate
  process, not gated by G3-S1).
- Missing permission → 403 `permission-denied`.

### 1.6 The legacy path (today's client under the flag)

- A request **with no token** is accepted as **legacy only if** the source is
  `lan` and `legacy_unpaired_lan` is on (`~/.config/privyhub/session_identity.json`,
  default **on** for the transition; set `{"legacy_unpaired_lan": false}` to
  turn it off — re-read on change, no restart). It runs exactly as today
  (targets from the source) as synthetic client `legacy-lan`.
- On a session-setup action (`launch`, `native-stream-start`,
  `recovery-resume`, `recovery-copy`) the host issues a token bound to
  `legacy-lan` (response header `X-PrivyHub-Session`; today's client ignores
  it) and audits `legacy_setup`. Other legacy calls are not audited one by
  one (heartbeats would flood the log).
- **Over the overlay, or from an unknown network, the legacy path is never
  allowed** (401 `legacy-overlay` / `legacy-unknown-network`).
- **The hub itself (`local`)** is the operator: always allowed as
  `host-local` (today's loopback tools, the link watch, the suite).
  [G3-S1 proposal] Never put a reverse proxy or `tailscale serve` in front
  of the companion: it would make overlay requests look host-local.

### 1.7 Audit and failure

- `logs/session_audit.jsonl` (gitignored): one JSON line per pairing
  open / close / success / refusal, nonce refusal, setup accept / refuse,
  token issue / expiry / end, permission denial, legacy setup / refusal:
  time, event, client id (never the key or the token; a token is referenced
  by an 8-hex hash), reason code, path (no query), permission,
  `routing_evidence`, `host_local`.
- Refusals answer `{"ok": false, "error": "session refused", "reason":
  <code>}`: 401 for identity, 403 for permission / endpoint.
- **An unrecognised flag value** (not `v2`) fails closed: every non-local
  request is refused (`identity-flag-unknown`).

### 1.8 The glue in `companion/privyhub_service.py`

- `SESSION_IDENTITY` built only when the flag is non-empty (the import inside
  that `if`).
- `do_GET` / `do_POST`: `if SESSION_IDENTITY is not None and
  SESSION_IDENTITY.intercept(self, …): return` (it answers `/session/*` and
  refusals).
- The two plugin calls that pass the source take
  `SESSION_IDENTITY.client_target(self) if SESSION_IDENTITY is not None else
  self.client_address[0]`. The adaptive-bitrate route keeps the source (a
  loopback permission).
- `_send_json` adds the session header only under the flag.

### 1.9 Verification plan (no stream, no restart)

`tests/session_identity/`: every accept / refuse case above; the legacy
path on-LAN accepted and audited, overlay / unknown refused; declared
endpoints used instead of the source; and the **request handler itself run
in-process** (the baseline's `PrivyHubRequestHandler` class against the
edited one, same stubs): the D6-R1 suite's companion requests (`GET
/plugins/games/native-stream-status`, `GET /plugins/games/status`) and the
client's setup calls, **byte for byte with the flag absent**, and with the
flag on the legacy path. The suite's UDP runs need the onn and an idle
stream: **pending on the stream**. The redactor over the audit log.

## 2. Classification

**BUILT behind `PRIVYHUB_SESSION_IDENTITY=v2`; verified in process; NOT
ADOPTED.** The flag is absent on the running companion. **38 tests OK.**
With the flag absent, the request handler's output for the D6-R1 suite's
requests and today's client calls is **byte for byte** the baseline's. The
live smoke and the suite's UDP runs are **pending on the stream** (session A;
the watch owns the companion until 2026-10-20T04:00Z). No companion restart,
stream or game.

- Task: `handoffs/G3-S1_SESSION_IDENTITY_HOST_SIDE_TASK.md`, queue
  `QUEUE_2026-10-15B.md` item 2, session B. **Baseline `3107fb5`**, plus
  G1-S1's uncommitted overlay boundary (`g3_s1_2026-10-15/git_status_at_start.txt`).

## 3. What was built

- **`companion/session_identity.py`** (new): §1 as written. One deviation
  was found while coding and made before the tests: the store and the
  settings are re-read when the file's `(mtime_ns, size)` changes, not its
  float mtime. A rewrite within the same tick must not be missed (a
  revocation, say). A second, smaller one: §1.4 says separate per-stream
  hosts are "refused until then"; the setup in fact reads only `media_host`
  and **ignores** any other endpoint field. It neither refuses nor uses one.
- **`companion/privyhub_service.py`**: predecessor `79041797…` (G1-S1's
  state; the baseline file was `27d31b58…`), after `32a7d2ea…`. Five edits,
  all inert without the flag:
  1. `SESSION_IDENTITY` is built only when the flag is non-empty, with the
     import inside that `if`;
  2. `_send_json` adds the session header only under the flag;
  3. `do_GET` calls `intercept` only under the flag;
  4. `do_POST` calls `intercept` only under the flag;
  5. the two plugin calls that pass the source get the declared target only
     under the flag. The adaptive-bitrate route keeps the source.
- **`tests/session_identity/`** (new): `common.py`, `test_gate.py` (35),
  `test_handler_replay.py` (3), and `fixtures/handler_predecessor.py.txt` (the
  baseline's handler class, from `git show 3107fb5`). No address literal: the
  tests build every address from integers in memory.

## 4. Verification (`g3_s1_2026-10-15/tests_output.txt`)

`python3 -m unittest discover -s tests/session_identity -v` → **38 OK**:

| area | cases (each refused with its reason code, or accepted) |
| --- | --- |
| routing | local, lan, overlay, unknown, not-an-address; the flag absent builds nothing |
| pairing | window closed; open needs the hub or `pairing-admin` (from the LAN, from the overlay); pair OK (the store is 0600 and holds no address; the window closes); over the overlay `pairing-not-lan`; unknown network `network-unknown`; a bad code, then `pairing-attempts-exhausted` at 5, then closed; the window expires; a short key |
| setup | a signed setup is accepted, and the token yields the declared target; wrong signature; **replayed nonce**; expired / unknown nonce; unknown device; **expired token**; a forged token never falls back; `/session/end`; **revoked device**; an overlay session with an overlay endpoint |
| endpoints | class mismatch both ways; invalid (loopback, port 80, not an address); `native-stream-start` port mismatch; `client_target` = declared for a session, the source for legacy |
| permissions | **denied** (a `tv`-only device on games); `/status`, `/diagnostics/*` and an unknown path → `permission-unknown`; `pairing-admin` |
| legacy | **on the LAN: accepted**; setup actions audited `legacy_setup`, with a token header; **overlay and unknown refused**; a legacy token from the overlay refused; turned off; a broken settings file → off (fail closed); the hub itself always `host-local` |
| unknown flag value | non-local refused `identity-flag-unknown`; local allowed |
| audit privacy | no address, key or token in the audit; `routing_evidence` ∈ {lan, overlay, unknown} |
| service glue | `session_identity` imported only inside the flag's `if` (AST) |

**The handler, byte for byte** (`replay_comparison.md`). The baseline's
`PrivyHubRequestHandler` and the edited one ran in process, on raw HTTP
requests, with the same stubs, from a LAN source and from loopback:

- **D6-R1's companion requests** (`GET …/native-stream-status`,
  `GET …/games/status`) and today's client calls (`launch`,
  `native-stream-start`, heartbeat, `GET /status`, an unknown plugin) →
  **14 / 14 identical** with the flag absent (status line, headers, body),
  and the access-log lines identical.
- With `v2` (legacy LAN): 12 identical, and LAN `launch` /
  `native-stream-start` are identical apart from one added
  `X-PrivyHub-Session` header.
- Over HTTP: the overlay without a token → 401 `legacy-overlay`; a token
  session's `native-stream-start` reaches the plugin with **the declared
  target**, a legacy one with the source; a token on `/status` → 403
  `permission-unknown`; the `/session/*` routes answer.

**The comparison catches a change** (`mutation_check.txt`, in memory, no file
edited):

| mutation | requests that differ (of 7) |
| --- | --- |
| the flag-absent target altered | 3 |
| the header sent without its guard | 7 |
| the GET intercept unguarded | 4 |
| unmutated | 0 |

**The D6-R1 suite itself.** Its only companion requests are the two GETs
above, replayed here. Its UDP runs go host → onn and back without the
companion, and need the onn and an idle stream: **pending on the stream**.

**The overlay tests re-run** after these edits: 17 OK
(`tests_overlay_rerun.txt`).

**The audit sample** (`sample_session_audit.jsonl`): the tests' 115 audit
lines, from pairing to legacy refusals; **the redactor passes on it**
(`redact_check.txt`: 0 HIT, over this directory, the record, `REMOTE_TRUST.md`, ROADMAP, the patch,
the module and the tests).

## 5. For the user

- **G3-S2, the client side (an APK change):** key generation at first run,
  the pairing UI (the code entry), the signed setup, the declared endpoints,
  and the token on every call.
- **To decide in G3-S2:** whether `diagnostics` becomes a grantable
  permission (today a paired session cannot read `/status` or
  `/diagnostics/*`), and whether to replace HMAC with a public-key scheme.
  The stdlib has no public-key signatures, and nothing was fetched.
- **Session A, the live smoke** (pending on the stream):
  - restart the companion with `PRIVYHUB_SESSION_IDENTITY=v2` (a drop-in);
  - today's client plays as `legacy-lan`; `logs/session_audit.jsonl` shows
    `legacy_setup`;
  - `curl -s localhost:8765/session/status` reads `paired_devices: 0`;
  - remove the drop-in.
- **Turning legacy off** later:
  `~/.config/privyhub/session_identity.json` → `{"legacy_unpaired_lan": false}`.
  It is re-read on change, no restart.
- Not adopted; the flag is absent.

## 6. Files; disclosures

- **Files** (`g3_s1_2026-10-15/`): `baseline_commit.txt`,
  `git_status_at_start.txt`, `predecessor_sha256.txt`, `after_sha256.txt`,
  `g3_s1.diff` (the service against the baseline, with G1-S1's hunks
  included, then the new files), `tests_output.txt`,
  `tests_overlay_rerun.txt`, `replay_comparison.md`, `mutation_check.txt`,
  `sample_session_audit.jsonl`, `redact_check.txt`, `manifest.sha256`.
- Patch record: `patches/G3-S1_SESSION_IDENTITY_HOST_SIDE.md`
  (`PATCH_INDEX.md` not updated: not session B's file in this queue).
- **The tests' temporary stores** are under the system temp directory
  (`g3_s1_tests_*`) and were left there (nothing deleted). Running them let
  Python write `__pycache__/` (gitignored).
- **A slip, disclosed:** one shell command in this session carried a stray
  `rm -f /dev/null 2>/dev/null`. As a non-root user it cannot succeed (the
  directory is root's). `/dev/null` was checked straight after: still the
  root-owned character device, unchanged. Nothing else was affected.
- No sudo, no nft, the Opal untouched; nothing fetched or installed. Git
  status: `logs/g3_s1_git_status.txt`.
