---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 92e388e (G3-S3 uncommitted beside it, not touched)
---

# G-A1 — the overlay provider and session identity v2 ADOPTED on the host

**Classification: ADOPTED (the user's, 2026-10-16, "yes to all three"). The adopted environ is now SEVEN
`PRIVYHUB_*` lines, in seven drop-ins.** The third adoption, the client's `identity_v2` on, was made on the onn in
CL-B3 (`CL_B3_HARDENED_APK_LAN_2026-10-16.md` §2). Nothing else adopted; nothing committed.

Task: `handoffs/G-A1_ADOPTION_AND_CL-B3_TASK.md` §1, session A. Files: `g_a1_2026-10-16/`.

## 1. Precondition (16:58:40Z, `check_before.json`)

- `tools/e3_state.py`: ok. Five lines, no `e3_flag.conf`, no `e4_constraint.conf`, no game, PS1 files identical,
  APK `77011eef…` CONFIRMED.
- The paired-device store held **1** device. `/session/status` was 404 (the flag absent: the gate not built).
- The link watch: inactive.

## 2. The adoption

- **The drop-ins** (beside `adaptive.conf`, `epg-index.conf`, `snes-core.conf`, `recovery.conf`,
  `snes-capture.conf`):
  - `overlay.conf`: `[Service]` / `Environment=PRIVYHUB_OVERLAY_PROVIDER=tailscale` (`overlay.conf.txt`);
  - `session-identity.conf`: `[Service]` / `Environment=PRIVYHUB_SESSION_IDENTITY=v2`
    (`session-identity.conf.txt`).
  - **Written by the user by hand** at 17:20Z: this session's own write was refused by the session's permission
    check, it stopped and said so, and the user ran the two exact lines (`adopted_at.txt`). The text was read back
    as above.
- `systemctl --user daemon-reload`, then the companion restarted at 17:23:17Z (`restart_adoption.json`): MainPID
  serves 8765, the manager environment holds no `PRIVYHUB_*`, and the process environ reads **seven** lines:

  ```
  PRIVYHUB_ADAPTIVE_BITRATE_MODE=live
  PRIVYHUB_EPG_GUIDE_INDEX=cached
  PRIVYHUB_OVERLAY_PROVIDER=tailscale
  PRIVYHUB_RECOVERY_TRIGGER=v2
  PRIVYHUB_SESSION_IDENTITY=v2
  PRIVYHUB_SNES_CAPTURE_FIX=output_rate
  PRIVYHUB_SNES_CORE=snes9x
  ```

  (`env_before.json` reads the five.)
- **The state tools** (patch `patches/G-A1_OVERLAY_AND_IDENTITY_ADOPTED.md`): `tools/e1_suite.py` `ADOPTED` gains
  both names and `preflight()` checks both drop-ins. `tools/e3_state.py` reads that list, and its docstring says
  seven. Diff: `g_a1_state_tools.diff`.
- **`--check`** (17:23:51Z, `check_after.json`): ok. Seven lines, `drop_in_overlay` and `drop_in_identity` true, no
  flag, no constraint, no game, APK CONFIRMED (still `77011eef…`; CL-B3 then replaced it).

## 3. The status documents

- **`/status`** (`status_after_adoption.json`): the `overlay` object is present.
  - `provider` tailscale; `available` and `connected` true; `path` **`no-peer`**; `peer_ready` false; `mtu` 1280;
    `reason` running; `endpoint` present, `endpoint_hash` `757c5de7` (the same hash as G1-S2).
  - `status_before.json` (547 bytes, five lines) has no `overlay` key.
- **`/session/status`** (`session_status_after_adoption.json`): `mode` **v2**; `paired_devices` **1**;
  `active_sessions` 0; `legacy_unpaired_lan` **true**; no pairing window open.
  - `permissions_known`: games, tv, vod, diagnostics, pairing-admin. `default_paired_permissions`: games, tv, vod,
    diagnostics.
- The host runs this tree's `session_identity.py` (G3-S3's, uncommitted; loaded by the restart), so it accepts the
  v2 canon that G3-S3's APK signs.

## 4. The reverts (written, not applied)

- **The overlay provider:** delete `overlay.conf`, `systemctl --user daemon-reload`, restart the companion, and take
  `OVERLAY` out of `ADOPTED` (and `drop_in_overlay` out of the preflight).
- **Session identity:** delete `session-identity.conf`, then the same reload, restart and edits for `IDENTITY` /
  `drop_in_identity`.
  - With the host flag off, a client with `identity_v2` on falls back to today's requests (`/session/nonce` → 404,
    G3-S2).
  - The paired store stays on disk, unread.
- **Both at once:** delete both drop-ins, one reload and restart, and copy `predecessors/` back.

## 5. Files; state

- `g_a1_2026-10-16/`:
  - `baseline_head.txt` (`92e388e`), `git_status_at_start.txt`;
  - `check_before.json`, `env_before.json`, `status_before.json`;
  - `overlay.conf.txt`, `session-identity.conf.txt`, `adopted_at.txt`;
  - `restart_adoption.json`, `check_after.json`, `status_after_adoption.json`, `session_status_after_adoption.json`;
  - `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`, `g_a1_state_tools.diff`;
  - `redact_check.txt`.
- `logs/g_a1_git_status.txt`.
- No sudo, no nft, no Tailscale command or setting (the provider reads status only). No address, token or
  identifier in any file: the status excerpts carry the endpoint as present / hash only.
