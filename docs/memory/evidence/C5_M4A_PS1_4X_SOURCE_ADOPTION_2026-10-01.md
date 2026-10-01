---
memory_schema: 1
as_of: 2026-10-01
baseline_commit: fe8f125
status: C5-M4A DONE — ADOPTED by the pre-registered rows (sha256 18312026…). The PS1 source config C5-M4 proposed is applied — the Beetle PSX HW core override (1920x1080 fullscreen) and internal resolution 4x in the base .opt and the six per-title copies — on the user's authorization of 2026-10-01 ("Yes apply the 4x config"). V1 exactly eight files changed in ~/.config/retroarch; V2 Tekken 3 and Crash Bash (multitap) through the companion's launch route at 1920x1080 / 4096², the multitap write keeps the 4x line (hash-identical after); V3 SNES unchanged (879x672, bsnes.opt equal); V4 D7: P1 8/9 (client discovery FAIL: the client's GET /sources arrived 0.2 s after the row's 3-s window) — retried once under the queue's rule, P2 9/9 PASS on the 4x source; V5 20-min hold on the adopted 7000 stream MET (RetroArch 59.999, capture 60, client 59.94 fps, 27 spikes/min, stale 0.25, underruns 0.70/min; reported loss 4.12/min, max gap 141 ms; 0 transitions, no recovery); V6 no game, stream 7000, any_override false, selector absent, live default intact, APK de072762…835e confirmed, the eight files hashed as the adopted config. Nothing else adopted; nothing committed
---

# C5-M4A — the PS1 source at 4x, adopted

Task: `handoffs/C5-M4A_PS1_4X_SOURCE_ADOPTION_TASK.md`, run unattended
under `handoffs/QUEUE_2026-09-29B.md`'s rules, 2026-10-01 20:15-21:10Z.

- Decision: `../decisions/C5-M4_PS1_4X_SOURCE_ADOPTION_2026-10-01.md`.
- Evidence: `c5_m4a_2026-10-01/` (manifest).
- Pre-registration: `c5_m4a_preregistration.txt`, sha256 `18312026…`,
  written before any change.

**Outcome: ADOPTED.** Every row V1-V6 held. V4 held on its retry; the
first pass's failure is recorded below.

## Before the change

- **The host was idle**: no game, and no `PRIVYHUB_*` in the manager. The
  seven `.opt` files matched C5-M4's `prestate_sha256.txt`.
- **The SNES baseline** for V3: Donkey Kong Country (USA) was launched
  through the companion with no stream. The window was 879×672, and the
  session left `bsnes.opt` (`9a98ff86…`) unchanged.
- **A slip, corrected.** The first run of the listing helper wrote its
  output file inside `~/.config/retroarch/`, because a relative path was
  resolved after a `cd`. The file was deleted at once and the script
  fixed, before any listing was used.

## V1 — the apply (`backup/`, `v1_opt_sha256_before.txt`, `v1_sha256_after.txt`, `listing_*`)

- No game was running.
- The seven `.opt` files were backed up and their hashes verified.
- `Beetle PSX HW.cfg` was copied from C5-M4's `proposal/`.
- One `sed` changed `beetle_psx_hw_internal_resolution = "1x(native)"` →
  `"4x"` in the seven `.opt`. Each `diff` shows exactly that one line, and
  the base is byte-identical to C5-M4's proposed `.opt`.
- **The recursive listing of `~/.config/retroarch/` before and after
  differs in exactly the eight files.** **MET.**

## V2 — through the companion's launch route (`launches/`)

| title | window | render target | config in the log | `.opt` after the session |
| --- | --- | --- | --- | --- |
| Tekken 3 (USA), no multitap | 1920×1080 | 4096² | "Core-specific overrides found … Beetle PSX HW.cfg", "Using windowed fullscreen" | the base, `e409d6c1…` (unchanged) |
| Crash Bash (USA), multitap port 1 | 1920×1080 | 4096² | the same, plus "PS1 multitap: port1", "Game-specific core options found … Crash Bash (USA).opt" | `86a52347…` (unchanged): `"4x"` with port 1 enabled |

- The regenerated `privyhub-session.cfg` carries only `retroarch.cfg`'s
  own `video_fullscreen` / `video_windowed_fullscreen = "false"`, and the
  core override supersedes them, as the window shows.
- **The multitap path's write keeps the 4x line.** **MET.**

## V3 — the 2D cores

- **Donkey Kong Country (USA) after the change:** 879×672, as before. No
  override is loaded, and `bsnes.opt` is `9a98ff86…`, equal to the
  baseline.
- **The other 2D cores:** Genesis and NES have no content on this host,
  so they are shown by their files. No fceumm or blastem options file
  exists before or after, and `retroarch.cfg` is `afab43c6…`, equal.
- **MET.**

## V4 — the D7 regression (`d7/`)

- **P1 (20:29Z): 8 of 9 PASS.**
  - **Client discovery/control FAILED.** In its 3-s window after the
    app's cold start, the row counted 0 `GET /sources` and 0
    `GET /plugins/games/status`.
  - The journal shows the client's `GET /sources` at 16:30:01 local and
    its status poll at 16:30:03, **0.2 s after the row read the
    journal** (the row ended 20:30:01.18Z). The client cold-started more
    slowly than the row waits.
  - It is a client-side start-up timing, not the PS1 source. Every game
    row after it (launch, A/V/controller, pause/resume, Save/Load, End)
    passed through the same client.
- **The retry.** One retry under the queue's rule ("a failing action is
  retried at most twice"). The bar was unchanged: all nine rows.
- **P2 (20:36Z): 9 of 9 PASS.**
  - Boot, discovery, media, Games launch.
  - A/V/controller: 60.0 fps, 89 heartbeats, controller active; feel and
    picture NEEDS USER as always.
  - Pause/resume.
  - Save/Load: scratch slot 3, 2,091,401 B; the hashes restored and the
    54 other state files identical.
  - Profiles, End/teardown.
- **Both passes ran on the 4x source**: every Tekken 3 session log shows
  4096² and 1920×1080.
- **MET on the retry.** P1's FAIL is recorded as it happened.

## V5 — the 20-min hold on the adopted 7000 stream (`runs/`, `c5_m4a_v5_score.txt`)

The hold was 20:42:26-21:02:26Z, attract mode, zero input:

- no `PRIVYHUB_*` in the manager, and the environ exactly the live
  default;
- `any_override` false; T2 at 10 s;
- the counter-only game override (`c5_m4a_counter.sh`) stacked on the
  adopted core override. The session log shows both overrides, 4096² and
  1920×1080. The counter override was deleted at teardown.

| row (pre-registered) | result | |
| --- | --- | --- |
| R1 RetroArch holds 60 | MET | 59.999 fps; longest 256-frame interval 4,272 ms (bar 4,278.7) |
| R2 capture holds 60 | MET | median 60.0 fps; dup+drop 1 frame in ~72,000 |
| capture window 1920×1080 | MET | armcheck `capture_target` |
| spikes ≥ 20 ms < 200/min | MET | 27.2 |
| rendered fps ≥ 59.5 | MET | 59.94 |
| stale drops < 20/min | MET | 0.25 |
| audio underruns < 5/min | MET | 0.70 |

**Reported, not gated:**

- Post-FEC video loss 4.12/min and max gap 141 ms, on a link whose
  LINK-L1 row is MIXED.
- 7.09 Mbit/s.
- The per-second largest frame, p50 / p90 / max, was 49,664 / 86,882 /
  89,590 B. C5-M4's 5-min b_4x read 47,310 / 86,340 / 89,590.
- Cap hits 9.7 s/min (b_4x 6.4; the adopted 720p's usual 9-10 over
  20 min), and 0 frames of ≥ 80 packets.
- **0 controller transitions** (the stop rule stands), and no link-drop
  recovery.
- The host:
  - GPU 22.4 % (p95 28) and CPU 12.1 %;
  - Tctl max 62.9 °C;
  - RetroArch 35.7 % and the encoder 49.2 % of one core (T2).

## V6 — the end state (`c5_m4a_final_state.txt`)

- **The client side:** no game and no RetroArch process; the stream at
  7000 on the adopted profile; `any_override` false; the selector absent.
- **The companion:** no `PRIVYHUB_*` in the manager, and the environ
  exactly the live default. The status reads live / configured live /
  acts true.
- **The onn:** APK `de072762…835e` confirmed. The stale launcher banner
  was cleared by the teardown's force-stop and relaunch.
- **The adopted config** is the eight files with the V1 after-apply
  hashes. There are no measurement files.
- **Unchanged and equal to the pre-state:** `retroarch.cfg`, `bsnes.opt`,
  `emulators.json`, `controller_overrides.json`, the core, the unit and
  the drop-in.
- **MET.**

## Files (`c5_m4a_2026-10-01/`)

- The pre-registration and its sha256.
- `backup/` (the seven pre-change `.opt`), `backup_sha256.txt`, the V1
  hash and listing files.
- **Tools:**
  - `c5_m4a_listing.sh`, `c5_m4a_launch_check.sh`;
  - `c5_m4a_counter.sh`, `c5_m4a_hold.sh`;
  - `c5_m4a_score.py`;
  - C5-M4's `c5_m4_run.sh`, `c5_m4_sampler.py`, `c5_m4_host_table.py`,
    `t2_sample.py`, `ra_cmd.py`, copied.
- **Runs and logs:**
  - `launches/`;
  - `d7/` (P1, P2), `d7_run*.log`;
  - `runs/` (the hold), `c5_m4a_hold.log`;
  - `c5_m4_host_table_runs.{txt,json}`, `c5_m4a_v5_score.{txt,json}`.
- `c5_m4a_final_state.txt`, `redact_check.txt`, `sha256_manifest.txt`.
