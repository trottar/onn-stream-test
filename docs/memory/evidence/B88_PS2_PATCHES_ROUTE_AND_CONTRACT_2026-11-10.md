---
memory_schema: 1
as_of: 2026-11-10
status: BUILT, NOT ADOPTED (session B, queue AF) — ps2-patches served on the onn's POST; and the client ↔ hub contract test: every call the client's source makes (46, kept as data), sent with the client's method through the companion's own HTTP server on loopback. Before: 45 / 46 served; now 46 / 46. Nothing committed. No title, serial, path or identifier in this record
---

# B88 — `ps2-patches` on the onn's route, and the client ↔ hub contract test (2026-11-10)

**Why:** HOME-12R's C48: Patches… → Widescreen → Save → "launch failed with unknown games plugin post action:
ps2-patches". The client POSTs; the hub served it on GET only. B80's and B83's tests called the GET handler directly.

**Baseline:** HEAD `051bb4d0`. **Design** hashed before code at 22:54:03Z (`b88_2026-11-10/design.sha256`).

## What was built (`b88.diff`)

- **`companion/plugins/games.py`:** the save factored into `_ps2_patches_save(query)` (today's code); the GET calls it
  as before; **`handle_post` serves `ps2-patches`** (inside `PRIVYHUB_PS2=1`, as the GET). The reply is the GET's
  (`ps2_patches`: the offer and the toggles now on); the client needs only a 2xx.
- **`tests/client_contract/`:**
  - **`calls.json`** — every hub call in the client's source, **46**: path, method, parameter names, source file; the
    computed actions (`$action` → input-profile-create / update / delete / assign; `$action$query` → recovery-resume /
    copy / discard; `$endpoint` → save-state / load-state; `DiscChange.ENDPOINT` → disc-swap) one row per value; the
    hub's own lazy paths (games/systems, games/details, iptv_org/categories, iptv_org/channels);
  - **`scan.py`** — the source check: every hub path literal in the client's `.kt` sources with the HTTP helper it
    goes through (`httpGet` → GET; `httpPost` / `httpPostBody` / `httpPostJson` → POST; a `requestMethod` near it);
    the identity protocol's path lists skipped (names, not calls);
  - **`test_contract.py`** — the source check both ways (a call in the source the list lacks; a literal the list names
    that the source no longer has; a made-up new call seen); **the server check**: a child on a fixture tree imports
    the companion's own `privyhub_service` (the registry as the companion builds it), serves its
    `PrivyHubRequestHandler` on a `ThreadingHTTPServer` at 127.0.0.1:0, and sends every call with the client's method
    and parameter names — every process the hub would start is a fake `Popen` (the bundles' local `7z` excepted, read
    only), the stream manager answers empty, the network beyond loopback blocked; **asserted: no 404, no 405, no
    "Unknown … action"**; and **the PS2 round trip**: the onn's Save (POST, ws=1) → 200, then `details` → `on: ["ws"]`.

## Served before / now (`served_before_now.md`; HEAD's companion vs B88's, the same check)

| call | method | served before (HEAD) | served now (B88) |
| --- | --- | --- | --- |
| `/plugins/games/ps2-patches` | POST | **no** (400, "Unknown Games plugin POST action") | yes |
| the other 45 | as the client sends them | yes | yes |

- **The PS2 round trip:** HEAD → the Save 400 (unknown action), `details` still `on: []`; B88 → 200, `on: ["ws"]`.
- **No other mismatch found.** The other calls' non-200 answers are the fixture's state ("no session", "one disc",
  "no cheat manifest", a schema the test's empty body lacks) — routed to their real handlers.
- **One finding, not a mismatch:** `/diagnostics/vod-client` (the movie player's retry rows) is served only with
  `PRIVYHUB_VOD_LOG=1`; it is adopted on the hub, so the check runs with it (and the three systems' flags). Without it
  the route does not exist — the client treats its answer as best-effort.

## Switch / absent

No knob: the POST route is new; **the GET answers byte for byte as HEAD's** (`proof_get_unchanged.txt`: the reply and
the `details` read-back SAME).

## Tests

`tests/client_contract/test_contract.py`, 5 (the source check ×2, the server check ×2, the round trip). 3 runs: 5 / 5 each
(`tests_x3.txt`). Mutations **4 / 4 caught** (`tests_mutations.txt`: the POST route removed; a call dropped from the
list; the scanner blind; every call read as POST).

## Disclosed

- The server check stands in fakes for what would start something (processes, the stream's encoder and the virtual
  pads, the guide's fetch); the HTTP server, the routing, the plugins' dispatch and handlers are the companion's own.
- The parameter values are fixture values; the check is about the route and the method, not each handler's outcome.
- The session-identity signatures are not part of the check (the child runs without `PRIVYHUB_SESSION_IDENTITY`).

## Files

`b88_2026-11-10/`: start files, the design + hash, `b88.diff`, `served_before_now.md`, `proof_get_unchanged.txt`,
`tests_x3.txt`, `tests_mutations.txt`, `scripts/`, redact / title checks, `manifest.sha256`. Patch note:
`patches/B88_PS2_PATCHES_ROUTE_AND_CONTRACT.md`.
