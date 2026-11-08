# B63 — design, written before any B63 code (PS1 multitap vs player 2)

Queue: `handoffs/QUEUE_2026-11-08W.md` §B63. Built after B62 in `/tmp/b_q15w_work` (the diff is against the after-B62
snapshot). **A default-on host change inside the hold-to-join path, disclosed; `PRIVYHUB_PS1_MULTITAP_CAPABILITY=0` =
today.** No title here: T1 is HOME-7's label, and the titles are counted by their metadata only.

## 0. Settled

- **T1 with the port-1 multitap: player 2 is dead.** HOME-7 C17 / its diagnostic: after B54's relaunch, and from boot
  at the next launch, player 2 does nothing although pad 2's changes reach the hub. With the multitap off it works
  (C15; HOME-4+ C7).
  - With Beetle's port-1 multitap, players 1-4 are on 1A-1D and port 2 holds player 5. A title without multitap
    support reads port 1 (1A) and port 2, so **player 2, on 1B, is never read**. This was known in Phase A, which is
    why the multitap was a per-title switch.
- **Which titles are multitap-capable:** the metadata `data/games/retroarch/controller_overrides.json`, which holds 20
  titles.
  - **5 carry `ps1_multitap: "port1"`** (the Phase-A four-player set, D087 / D088's validated path);
  - **3 carry `"off"`**; the rest have no multitap value.
  - **T1's metadata is "off"** (HOME-7's label: "multitap off at its metadata").
  - Today nothing else in the host says "capable"; the system-level `MULTITAP_SYSTEMS` (ps1, snes, ps2) is all B54's
    relaunch checks.
- **The stored count:** B54's client keeps the title's highest joined count in a private preference **on the onn**
  (`privyhub_players_joined`) and sends it as `players_joined` at every launch. The host maps 3 / 4 to the multitap
  (`ports_for_joined`). So T1, stored at 3 since C17, launches with the multitap every time.
  - **The host cannot rewrite the onn's value.** It can cap what that value does at every launch.
- **The client's existing behaviour, read, unchanged:** a hold beyond the session's ports asks for a relaunch only when
  `ports_set.multitap_available` is true. Otherwise it shows its note "No multitap on this system — <n> players" and
  relaunches nothing.

## 1. The rule (host only; no APK)

1. **Capable = the metadata says so:** `ps1_multitap == "port1"`, or a new explicit `ps1_multitap_capable: true` (for a
   four-player title the user wants without the multitap forced on at every launch). **Unknown = not capable.**
   `EmulatorManager.ps1_multitap_capable(game)`; a PS1 title only.
2. **The plan caps it:** `players_session.plan(..., capable=False)` for PS1 → `multitap_available` false, so no
   multitap and 2 ports even for 3 / 4 joined or a 4 pick. `ps1_mode "off"`: the per-content Beetle `.opt` is
   rewritten with the multitap off. `capped_from` records the asked count. The launch passes the capability for PS1.
3. **The echo:**
   - `ports_set` (start response) carries the plan's `multitap_available`. The metadata fallback for PS1 uses the
     capability too.
   - For T1: `players 2, multitap false, multitap_available false`, plus `capable: false` and `capped_from: 4` when it
     was capped.
4. **The client therefore:**
   - for T1, shows its existing note on a third pad's hold, "No multitap on this system — 2 players", and **no
     relaunch**; players 1 and 2 work;
   - for the five capable titles, relaunches with the multitap as B54 (unchanged).
   - **The exact words "This game supports 2 players" need the client:** listed for the next APK, not built.
5. **`relaunch_ports.run`:** a 4-port relaunch of an incapable PS1 title is refused, "This game supports 2 players",
   with nothing stopped (defence: the client does not ask it).
6. **"The stored count never above the title's capability", and the migration:**
   - **On the host:** every launch caps, so a stored 3 on an incapable title starts with 2 ports. The host's own
     per-title state (the per-content `.opt` a join or a relaunch wrote with the multitap on) is rewritten off **at
     that title's next launch**. The game log says `PS1 multitap: off` and the new `PS1 ports capped: 4 -> 2 (not
     multitap-capable)`. That launch is T1's recorded migration (C26 reads it).
   - **The onn's stored value stays 3** until the client changes it. Capping it on the onn (and storing at most the
     capability) is a client change, **listed for the next APK, not built.** Its effect is already neutralised by
     the host's cap.
   - **No one-time host pass:** the host stores no counts, and its `.opt` files are corrected by the launch itself.
     A separate pass would need to map hashed stems to titles for nothing extra.
7. **The knob:** `PRIVYHUB_PS1_MULTITAP_CAPABILITY=0` → every PS1 title counts as capable (today's behaviour).
   Absent / any other value → the rule.

**Default-on, disclosed:**
- a PS1 title not flagged `port1` / `ps1_multitap_capable` never gets the multitap from a join or a pick, so **three
  players on such a title are no longer possible**. Today they would get a dead player 2 anyway;
- the metadata's own `ps1_multitap: port1` titles keep the multitap at launch (D087's path, untouched) and the relaunch.

**Unchanged:** SNES and PS2 multitaps; N64 (four ports); the metadata path D087; B46's `.opt` mechanics.

## 2. Tests (`tests/b63_ps1_multitap/`)

- **`plan`:**
  - PS1 capable with 4 → multitap, ports 4;
  - incapable with 4 → ports 2, `multitap_available` false, `ps1_mode` off, `capped_from` 4;
  - 1 → ports 1 as today;
  - SNES / PS2 / N64 unchanged.
- **`ps1_multitap_capable`:** `port1` → true; `off` / absent / another system → false; `ps1_multitap_capable: true` →
  true; the knob `0` → true for all.
- **`ports_set`:** a join plan for an incapable title → players 2, `multitap_available` false; the metadata fallback
  likewise; a capable title → true.
- **The launch** (the plugin's join path with a fake emulator): `players_joined=3` on an incapable title →
  `players_chosen` 4 asked, the plan capped to 2, `.opt` mode off, the log line; on a capable title → the multitap.
- **`relaunch_ports`:** an incapable PS1 title asked for 4 → `RelaunchRefused("This game supports 2 players")`, no
  pause / stop; a capable one → proceeds as today (B54 / B57's suites).
- **Absent (`=0`) → today:** an incapable title with 3 joined → the multitap, as before.
- **Regression:** `tests/players_session`, `tests/relaunch_ports` (B54 / B57) green. A test that assumed an unknown
  PS1 title relaunches is updated with the capability (disclosed in the record if any).
- **Mutations:** capability always true; the cap removed from `plan`; the relaunch refusal removed; the knob inverted.
