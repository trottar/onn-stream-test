# B88 — `ps2-patches` on the onn's route, and the client ↔ hub contract test (design, hashed before code)

**Baseline:** HEAD `051bb4d0`. No knob: the POST route is new (today it answers "Unknown Games plugin POST action");
the GET stays byte for byte.

## Settled (read at HEAD)

- **The client** (`MainActivity.kt`, Patches… → Save): `httpPost("…/plugins/games/ps2-patches?id=…&ws=0|1[&ni=…][&fps60=…]")`;
  any 2xx → "Saved — used the next time this game starts"; an error → "Patches not saved: <message>". The body is not
  read.
- **The hub:** `privyhub_service.PrivyHubRequestHandler` sends GET `/plugins/<plugin>/<action>` to
  `plugin.handle(action, query)` and POST to `handle_post_json_request` / `handle_post_request` / `handle_post`. The
  games plugin serves `ps2-patches` in `handle` (GET) only; its POST dispatch ends in "Unknown Games plugin POST action:
  ps2-patches" — HOME-12R's C48. B80's tests (a plugin built with `object.__new__`, `handle` called) and B83's (the
  plugin as the companion builds it, `handle` called) both stopped one layer short of the HTTP route and the method.

## The fix

`games.py`: the save's body factored into `_ps2_patches_save(query)` (today's GET code, unchanged in effect); `handle`
(GET) calls it as today; **`handle_post` serves `ps2-patches`** with the same call (inside `PRIVYHUB_PS2=1`, as the
GET). The reply is today's GET reply (`ok`, `plugin`, `game_id`, `ps2_patches` = the offer and the toggles now on);
the toggles are stored on the hub (B80's file) and `details` reads them back.

## The contract test (the systemic part)

1. **The list, as data:** `tests/client_contract/calls.json` — every hub call the client's source makes: the path
   (`/plugins/<plugin>/<action>` or a root path), the method (GET / POST, from the helper the call goes through:
   `httpGet` / `httpPost` / `httpPostBody` / `httpPostJson`, or a connection's `requestMethod`), the parameters' names,
   the source file; calls whose action is computed (`$action`, `$endpoint`, `DiscChange.ENDPOINT`, the hub's own lazy
   paths) listed once per value the client can send, with where the values come from.
2. **The source check:** a test scans the client's `.kt` sources for hub paths (string literals with `/plugins/…`,
   the root paths) and fails when one is not in `calls.json`, or when `calls.json` names a literal the source no
   longer has.
3. **The server test:** a child process on a fixture tree (its own `companion/`, B82's fixture library) imports the
   companion's own `privyhub_service` (the registry as the companion builds it), starts **its `PrivyHubRequestHandler`
   on a `ThreadingHTTPServer` at 127.0.0.1:0**, and sends every call in `calls.json` with the client's method and
   parameter names (fixture ids). The side effects that would start something are replaced at their lowest layer
   (RetroArch / PCSX2 / Dolphin processes, the stream's encoder, the guide's fetch); the routing, the plugin's dispatch
   and its handlers run for real. **Asserted for every call: not 404, not 405, and no "Unknown … action" in the reply.**
   Network blocked except loopback.
4. **Any other mismatch found** by the server test: fixed here if it is a route or a method (design addendum hashed
   first), else listed for the next queue with the reason. The record's table: call, method, served before (HEAD's
   server, the same test) / now.

Tests clean their temp dirs; ×3; mutations (the POST route removed; a call dropped from the list; the source check
blind).
