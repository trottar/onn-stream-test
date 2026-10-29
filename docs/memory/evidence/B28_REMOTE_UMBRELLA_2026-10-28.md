---
memory_schema: 1
as_of: 2026-10-28
baseline_commit: 42a2ab6 (the tree clean at the start; B28 uncommitted)
---

# B28 — `PRIVYHUB_REMOTE=1`: G4-S4's four WAN lines in one, each acting only on a remote-class session; the LAN byte for byte today; G-A9 PREPARED

**Classification: SETTLED + BUILT** behind `PRIVYHUB_REMOTE=1`.
- **Tests:** `tests/remote_umbrella` 10 green (three runs); every suite under `tests/` green; two mutations caught.
- **The replay:** G4-S4 13 / 13 the same under the old and the new readers; the home LAN 16 / 16 today's 7000.
- **Proof:** absent = today, PROVEN.
- **G-A9 PREPARED**, nothing applied. NOT ADOPTED; no live run; nothing committed.

Design `b28_2026-10-28/design_written_before_code.md`, sha256 `986633f8…5742`, hashed **03:06:49Z, before any B28
code**. Precondition checked first: only the companion and `privyhub-link-n1` active.

## 0. Settled: the four lines on a LAN session today (the code; G4-S4's rows)

| line | on a LAN session today | so on the LAN it is |
| --- | --- | --- |
| `PRIVYHUB_START_RUNG=floor` | the start rung picks the **LAN list's floor: 5000**; the remote list (4000-7000) needs the ladder line and an overlay address | **a change:** the stream starts at 5000, not 7000, and the first sample row carries `start_rung` (G8-S2's own `test_floor_starts_at_5000_and_the_status_says_so`) |
| `PRIVYHUB_REMOTE_LADDER=1` | class `lan`: the ladder `base` (no 4000), the actuator adds nothing; the moves are today's | **extra fields:** `path_class` on every ladder row and in the context |
| `PRIVYHUB_REMOTE_RUNG_CAP=7000` | `applies()` false on `lan`, no clamp; at 7000 (the top rung) it never clamps anyway (G4-S4: 0 clamps) | **one extra row:** `remote_cap_config` at the controller's start (once per process) |
| `PRIVYHUB_WAN_TELEMETRY=1` | classification only (never acts): every report observed, a `logs/wan_sessions.jsonl` row per session, `wan` in `/status`, `"wan": …` in stream-telemetry | **extra rows and fields;** a small CPU and file cost, nothing acts |

- **G4-S4 never showed the LAN case.** Its five sessions under the four lines were all over the overlay: floor 4000,
  `path_class` remote. The "7000" LAN sessions in its record ran without the lines.
- **The cost of the floor away from home (G4-S4 §3, not changed):** every new client session starts at 4000,
  including a Home return. The ladder climbs one rung every ~3 min 07 s, so a new session spends ~12-15 min below
  7000 (G4-S4's Home at 21:02:36Z: back at 7000 at 21:17:11Z).

## 1. Built (`b28.diff`)

**`companion/remote_umbrella.py` (new), `RemoteUmbrella`.**
- **The class:** at each `native-stream-start`, before the start, beside B23's call. B23's own readers decide it:
  `link_recovery_wan._default_is_overlay`, G3's overlay test; then `_default_overlay_path`, the provider's path on a
  daemon thread. It is `lan` / `remote-direct` / `remote-relayed` / `remote-unknown`.
- **Remote (any of the three):** the umbrella's own objects go into today's module globals, so the hooks are
  untouched:
  - `RemoteLadder()` into `adaptive_bitrate_live.REMOTE_LADDER` and the actuator probe's;
  - `RemoteCap("7000", ladder)` into `REMOTE_CAP`, its `remote_cap_config` row written once into the ladder log;
  - `StartRung("floor")` into `START_RUNG` in `adaptive_bitrate_live` and `native_stream`, which the
    `restart_fast*` workers read too;
  - a `WanTelemetry` (built at the first remote session from the service's `PROJECT_ROOT` / `OVERLAY_STATUS`) into
    the service's `WAN_TELEMETRY`, with a `/status` wrapper installed once.
  - The ladder's own `note_stream_start` (already in `games.py`, after the start) then sets its class.
  - **These are G4-S4's four exactly.**
- **`remote-unknown` counts as remote for the start rung.** The rung is chosen at the spawn, before the path can be
  read. The overlay address already says the onn is not on the hub's LAN, and the floor is the safe start on an
  unknown path.
- **LAN:** those globals back to None, which is today's code path.
  - The policy's ladder is put back to its base if a remote session left 4000 in it.
  - The telemetry's open remote session is written now.
- **An explicit individual line wins** (present, any value): its module keeps its own object for every class. The
  umbrella sets no environment line.
- **Rows** (the recovery log):
  - `remote_umbrella_config` at the plugin's start: the four `implied` / `explicit`, and the cap's config;
  - **`remote_config` once per session:** `class`, the four `in_force` true / false with `how`, and `why`.
- **`plugins/games.py` (+12):** the guarded import (`== "1"`), the wire after the live controller, and the call
  beside B23's. Nothing else is edited.

## 2. Tests (`tests_remote_umbrella.txt`, `tests_mutations.txt`)

The real `_start_linux_locked` (G8-S2's stub manager) and a real `LiveController` on a temp root; a fake path read
and a fake service; G3's real overlay test on addresses built from integers.
- **LAN:**
  - **the argv and the ladder rows field for field as with no umbrella**; 7000; no `path_class` / `start_rung`;
  - no `remote_cap_config`; no telemetry, no `wan_sessions` row, no `/status` wrapper;
  - one `remote_config` `lan`, all four `in_force` false.
- **Remote direct:**
  - 4000 `floor` with the remote list; `path_class` remote on every row; 4000 in the policy's ladder;
  - the actuator `(4000,)`; `remote_cap_config` once (active, 7000); the climb 4000 → 5000;
  - the telemetry observed, `wan` in `/status`; `remote_config` `remote-direct`, all four in force.
- **Relayed, no-peer, unread:** the start counted remote (4000) before the path read; the rows `remote-relayed` /
  `remote-unknown`.
- **Remote → LAN → remote:**
  - the LAN session today's (globals None, the base ladder, no move to 4000), and the remote session's
    `wan_sessions` row written at the switch;
  - remote again G4-S4's; the cap's row once in all.
- **Explicit lines:**
  - `PRIVYHUB_START_RUNG=5000` is left alone in both classes;
  - `PRIVYHUB_REMOTE_LADDER=0` gives no ladder and the cap inactive (`remote_ladder_flag_absent`);
  - no service: the telemetry `unavailable`, the rest in force.
- **The flag:** `0` / empty / junk = off; the config row; no address in any row; **fresh processes import nothing**
  without `=1`.
- **Mutations:**
  - every session remote: the LAN tests fail (2);
  - the LAN switch a no-op: remote → LAN → remote fails (1).
- **Every suite** (`tests_regression_after_queue_k.txt` against `tests_regression_queue_k_baseline.txt`, in the
  copy): the baseline's outcomes plus the new suites. The four `tools/` tests fail in the copy as at every
  baseline.

## 3. The replay (`replay_remote_umbrella.py`, `replay_output.json`, `replay_table.md`, `replay_run_at.txt`; read-only)

The companion's own readers, on addresses built from integers, at the old (the four explicit, as G4-S4's drop-in)
and the new (`PRIVYHUB_REMOTE=1`):
- **G4-S4's 13 sessions** (all over the overlay):
  - **old and new the same in 13 / 13** (rung, source, list, ladder): 4000 floor, the list 4000-7000;
  - the five that ran under the four started at 4000 floor as logged;
  - `remote_config` would read `remote-direct` where the path was sampled direct and `remote-unknown` where it was
    not sampled.
- **The home LAN of 2026-10-27/28** (CL-B14, G-A7, CL-B15; 16 session starts, a Home return logs two): the new gives
  **today's 7000 with no class in 16 / 16**. The old (the four explicit) would have started every one at **5000**.

## 4. G-A9 PREPARED (`patches/G-A9_REMOTE_ADOPTION_PREPARED.md`, `g_a9_prepared.diff`)

G-A7's applied form:
- `REMOTE = "PRIVYHUB_REMOTE=1"`, **`ADOPTED` to thirteen**, **`drop_in_remote`** and its `ok` term;
- the wording in `e3_state` / `e1_remote` / `test_e1_remote`;
- the drop-in `remote.conf`, the off steps, and the predecessors' sha256 (HEAD `42a2ab6`).

It was checked in /tmp only (`git apply --check`, `e1_suite --self-test`, `ADOPTED` 13). **Nothing applied.**

## 5. Files

- **`b28_2026-10-28/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `started_at.txt`, `units_at_start.txt`;
  - `predecessors/` (the nine modules), `predecessor_sha256.txt`, `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b28.diff`, `proof_flag_absent.py` / `.md`;
  - the replay's four files;
  - `tests_remote_umbrella.txt`, `tests_mutations.txt`, `tests_regression_queue_k_baseline.txt`,
    `tests_regression_after_queue_k.txt`;
  - `g_a9_prepared.diff`, `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:** `companion/remote_umbrella.py` (new), `companion/plugins/games.py`, `tests/remote_umbrella/` (new);
  `patches/B28_REMOTE_UMBRELLA.md`, `patches/G-A9_REMOTE_ADOPTION_PREPARED.md`; `logs/b28_git_status.txt`.
- **Left in /tmp:** `b_q28k` (the copy), `b_q28k_scratch/` (`b28_mut/`, `ga9/`), `b_q28k_*.sh`.
- **The rules held:**
  - no stream, no companion restart, no adb, no sudo, no nft; the Opal untouched;
  - nothing of `privyhub-link-n1`'s files touched;
  - nothing of A's touched; nothing fetched, deleted, adopted or committed.
