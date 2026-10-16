---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 92e388e (G3-S3 uncommitted beside it, not touched)
---

# CL-B3 — G3-S3's hardened APK on the onn, on the seven-line state

**Classification: OPEN, awaiting the user.**

- **The APK:** INSTALLED and CONFIRMED (`59f736d2…f65f`).
- **The signed path on the LAN: PASSED** (R1, every host gate held).
- **The G5-S1 live smoke (W):** the `wan` object was live and every host gate held, but **two W gates were NOT
  MET:**
  - the companion's CPU cost was **+0.633 point** of a core, against ≤ 0.5;
  - **no `logs/wan_sessions.jsonl` line** was written.
- **The VOD play: PENDING.** The user was away; they chose to run W now and do VOD later.
- The pre-registration says "if a gate fails: stop and say so — the user decides". Nothing was rerun, and nothing
  was adopted beyond G-A1's three adoptions and the APK.

Task: `handoffs/G-A1_ADOPTION_AND_CL-B3_TASK.md` §2-3, session A. Files: `cl_b3_2026-10-16/`. Pre-registration:
`cl_b3_preregistration.txt`, sha256 `c9973200…0802`. It was hashed at 17:26Z (`preregistration_hashed_at.txt`),
after the install, the hash patch and the setting, and before any run. The G-A1 record is
`G_A1_OVERLAY_AND_IDENTITY_ADOPTION_2026-10-16.md`.

## 1. The install

- **Before** (`device_apk_before.txt`, `client_before_install.json`): the onn ran `77011eef…7d9d` (CL-B2), with
  `identity_v2` false, the hub host empty, the device secret present, and the identity prefs holding `device_id`,
  `display_name` and `permissions` (key names only; `cl_b3_client_read.py` never writes values).
- **`adb install -r`** of G3-S3's `app-debug.apk` (sha256 `59f736d29b96700253a178efa5efd0cd8846858a89d32848a0994586712bf65f`,
  the same as `g3_s3_2026-10-16/apk_sha256.txt`) at 17:24Z: `Success` (`install.log`). The device read back
  `59f736d2…` (`device_apk_after.txt`).
- **The pairing survived** (`client_after_install.json`, `pairing_survived.json`):
  - the device secret and the prefs are unchanged;
  - the client's device id **is in the hub's store** (compared in process; only the boolean is written);
  - the store holds 1 device.

  No re-pair was needed.
- **The pinned hash** (patch `patches/CL-B3_HARDENED_APK_HASH.md`; `cl_b3_hash.diff`, `predecessors/`):
  - `tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`, and its test;
  - 33 / 33 tests passed (`tests_nft_night.txt`).
  - `--check` (`check_after_install.json`): ok on the seven lines, APK CONFIRMED.
- **Rollback (written, not applied):** `adb install -r PrivyHub/app/build/g3_s3_preserved/app-debug.apk`
  (`77011eef…`, its hash re-read: `rollback_apk_sha256.txt`), then copy the three predecessors back.

## 2. The client setting

- **The user turned `identity_v2` on** on the onn's Settings screen (asked and confirmed), with "Hub host" left
  empty (home, LAN).
- Read back through `run-as` at 17:26:08Z (`client_setting_on.json`): `identity_v2` true, `hub_host_set` false.
- The client set up at once: `token_issued` at 17:26:00Z, **`sig_v` 2**, permissions **games, tv, vod,
  diagnostics**, `media_token_issued` true, `overlay_declared` false, routing `lan` (`audit_setting_on.jsonl`).
  The client then stored `diagnostics` in its pairing (`pairing_end.json`).

## 3. The two PS1-STREAM runs (`tools/e1_suite.py --e2`, gap 120 s, 10 min)

| run | what | window (UTC) | capture fps | dup+drop /min | RetroArch | host CPU %† | rung kbps (polls) | ladder acted | companion / RetroArch / encoder % of a core | flags_absent | rendered* | loss/min* | resyncs* |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | seven lines, `identity_v2` on | 17:30:55-17:40:55 | 59.988 | 0.10 | 59.999 | 11.569 | 7000-7000 (×69) | 0 | 24.80 / 34.39 / 36.01 | true | 59.67 | 80 | 0 |
| W | R1 + `PRIVYHUB_WAN_TELEMETRY=1` (the suite's per-run drop-in) | 17:48:59-17:58:59 | 60.036 | 0.10 | 59.999 | 11.593 | 7000-7000 (×69) | 0 | 25.44 / 35.74 / 35.38 | true | 59.80 | 60 | 3 |

† Reported, not gated: the CL-B2 bar lesson. Both runs held the same rung with no ladder action, and the encoder
sat at its usual ~36 %. \* The link: reported, not gated. It was the cleanest since 10-09.

- **Host gates (RetroArch ≥ 59.9, capture 60 ± 0.1, dup+drop ≤ 0.2/min, flags_absent): ALL HOLD** in both runs
  (`cl_b3_analysis.py` → `cl_b3_table.md`, `cl_b3_verdict.json`; `validity.json`: both OK).
- **The signed path in R1** (`audit_r1.jsonl`, `access_r1_identity.txt`, `poll_r1.jsonl`):
  - 17:29:06Z `host_local_setup` on `/plugins/games/launch`: the suite launches from the hub.
  - 17:29:10-11Z `POST /session/nonce` 200 → `POST /session/setup` 200 → `token_issued` for the paired device,
    `sig_v` 2, media token issued.
  - **17:29:21Z `POST /plugins/games/native-stream-start?port=48100` → 200.** Under a token, G3-S3 refuses any
    port other than the signed `video_port` with a 403 `endpoint-port-mismatch`, audited with `port_kind`. The 200
    with no such audit row is the binding holding: the stream-start port equals the signed one, 48100.
  - **No `legacy_setup`, no `session_refused`, no `endpoint-*` refusal** in the run.
  - The declared target: `overlay_declared` false and routing `lan`, so the host chose the declared LAN
    `media_host` (G3-S3's class rule). PLAYING came in 3.0 s.
  - `/session/status` while PLAYING (from 17:29:33Z): one session, `kind` session, permissions games / tv / vod /
    diagnostics, **`media_token_live` true**.
- **W's audit** (`audit_w.jsonl`, `access_w_identity.txt`): the same shape (`sig_v` 2, `?port=48100` → 200, no
  refusal). After the teardown's restart, the client set up again at 17:59:17Z.

## 4. The G5-S1 live smoke (W)

- **The flag:** the suite wrote `e3_flag.conf` = `PRIVYHUB_WAN_TELEMETRY=1` and restarted, ran W, then removed it,
  ran daemon-reload and restarted again (`runs/final_state.json`: seven lines, `flags_absent` true). Afterwards the
  drop-in directory holds the seven adopted drop-ins only.
- **The `wan` object** (`poll_w.jsonl`: every 30 s, `wan` only; `wan_excerpt_last.json`):
  - Present on **`/status` and `/diagnostics/stream-telemetry` in 23 of the 24 polls while the game was active**.
    The first poll came 11 s before PLAYING and read null, as no client report had come in yet.
  - The address and long-hex check matched 0 times.
  - **The eleven measures**, all present, each with its `source`:
    - delivered goodput, ~7,059 kbit/s;
    - packet loss, post- and pre-FEC;
    - FEC groups (*not classified; G5-S2*);
    - jitter p50 / p95 (*not classified; G5-S2*; no per-packet times carried);
    - RTT p50 / p95 (*not classified; G5-S2*);
    - sender pacing; queue depth;
    - decoder starvation (its audio counter *not recorded*);
    - overlay path `no-peer`;
    - MTU 1280 (oversize drops *not observed*; *not classified; G5-S2*);
    - path-change events, 0.
  - **A primary class per window.** At 17:58:49Z: 341 reports, 68 windows; the primary counts were clean 42,
    lossy 25, starved 1, and the rest 0. The session class was **lossy** (it read clean early in the session).
- **The session report — NOT MET:**
  - **`logs/wan_sessions.jsonl` was not written.**
  - G5-S1 writes a session's summary line only when the *next* stream session starts in the same process
    (`_close_session_locked` from `observe`).
  - W was the process's only session, and the teardown restart ended the process first. So no line was written.
    The design does this every time a run ends with a restart.
  - The live `wan` on `/diagnostics/stream-telemetry` is the per-session object while the session lasts. G5-S1's
    record already treats it as "the report", since the client's own report is the games plugin's. It was
    present.
  - For G5-S2: write the summary at stream stop and at shutdown.
- **The cost — CPU NOT MET, memory met:**
  - The companion's mean CPU in W minus R1 was **+0.633 point of a core**, against ≤ 0.5. Its PSS was
    **+0.35 MB**, against ≤ 2.
  - This is **two separate runs, not paired arms.** Both held the same 7000 rung with no ladder action.
  - RetroArch was also +1.35 points in W, so part of the difference is run-to-run.
  - W's poller made two extra loopback reads every 30 s (`/status`, `/diagnostics/stream-telemetry`) that R1's
    did not.
  - The provider's own cost was not measured in isolation. A G1-S2-style idle A/B (`g1_s2_cost.py`) would need the
    flag on and two more restarts, which were not pre-registered.
- **After the flag:** `/status` (791 bytes) is **byte for byte equal to G-A1's** `status_after_adoption.json`,
  **except `server.pid`**, with no `wan` key (`status_compare_after_w.json`). `--check` was ok on the seven lines
  (`check_end.json`).

## 5. The VOD play (PENDING)

- Asked at 17:42Z (`vod_asked_at.txt`). The user was away from home and chose: run W now, VOD later.
- **To finish CL-B3:**
  1. Play a movie on the onn (VOD → MOVIES) for ≥ 60 s.
  2. Reduce the audit from that time (`cl_b3_audit.py vod <since>`). Expect `media_session` for `paired-device`,
     `media_token_used` false (the header), routing `lan`, with no `legacy-*` and no `media-token-unknown`.
  3. Count the range server's 200 / 206 `GET /vod/…` lines in `logs/server.log` after line 16,921
     (`vod_serverlog_offset.txt`), keeping the status codes only.
  4. Add §5 here.

## 6. State at the end (18:00Z)

- **Seven adopted lines; no `e3_flag.conf`, no `e4_constraint.conf`; no game; APK `59f736d2…` CONFIRMED**
  (`check_end.json`).
- **The device is paired:** 1 device, the client's id in the store, the stored permissions games, tv, vod,
  diagnostics (`pairing_end.json`). `/session/status` reads mode v2, `legacy_unpaired_lan` true
  (`session_status_end.json`).
- **`identity_v2` on, hub host empty** (`client_end.json`).
- Nothing committed.

## 7. Files

- **`cl_b3_2026-10-16/`:**
  - `baseline_head.txt`; the pre-registration and its hash;
  - `cl_b3_client_read.py`, `cl_b3_poll.py`, `cl_b3_audit.py`, `cl_b3_analysis.py`;
  - `runs/` (R1 under `E1-PS1-STREAM/run1`, W under `E1-PS1-STREAM_flag/run1`; `suite.log`, `final_state.json`);
  - `runs_r1_console.log`, `runs_w_console.log`;
  - `cl_b3_table.md`, `cl_b3_verdict.json`, `validity.json`;
  - the `audit_*.jsonl` excerpts (event, reason, routing, path, sig_v, port_kind, permissions, media-token
    booleans, `paired-device` / `host-local`; no device id, token_ref or address);
  - `access_r1_identity.txt`, `access_w_identity.txt` (time, request line and status; no source address);
  - `poll_r1.jsonl`, `poll_w.jsonl`, `wan_excerpt_last.json`;
  - the hashes, the client reads, the `--check` readings, `status_*.json`, `status_compare_after_w.json`;
  - `predecessors/`, `cl_b3_hash.diff`, `tests_nft_night.txt`;
  - `redact_check.txt`, `manifest.sha256`, `manifest_check.txt`.
- Patch `patches/CL-B3_HARDENED_APK_HASH.md`; `logs/cl_b3_git_status.txt`.
- No sudo, no nft, no Tailscale change, no Opal access. No address, token, media token, key or pairing code in any
  file in the repo.
- The two systemd drop-ins (G-A1) were written by the user by hand, after this session's own write was refused by
  its permission check. The suite then wrote and removed W's `e3_flag.conf` itself, unrefused.
