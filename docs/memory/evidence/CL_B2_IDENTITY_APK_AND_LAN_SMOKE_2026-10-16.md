---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 3107fb5 (G1-S1 / G3-S1 / G3-S2 uncommitted beside it, not touched)
---

# CL-B2 — the identity APK on the onn; G3 end to end on the LAN

**Classification: CLOSED. The APK is INSTALLED and stays (CONFIRMED).
Every identity gate passed on the LAN. One host gate FAILED: R3's host CPU
was 12.963 %, against the band 10.9 ± 2, so 0.06 point over. The host
flag and the client setting are NOT ADOPTED.**

- **The user's decision on the failed gate (2026-10-16):** the APK stays
  and CL-B2 closes, with the gate recorded as FAILED by 0.06. The
  pre-registration says "if a gate fails: stop and say so; the user
  decides". This is that decision. The rollback in §1 stays written and
  not applied.
- **The cause, from the files (§2a):**
  - Against R1, the companion and RetroArch were within a point. The
    encoder was **46.65 against 35.75 %** of a core.
  - The ladder polled **7000-7000** in R3, against **5000-7000** in R1.
  - However, the E4-S1 reference and R2 both also held 7000 throughout,
    at about 36 % encoder. So the rung mix does not explain R3's +10.9
    points, and the cause is not located.
  - The bar lesson is in §2a.

- **The APK:** G3-S2's debug APK `77011eef…7d9d` is now the onn's
  CONFIRMED APK. It is the same flavour CL-B1 installed; G3-S2 did not
  build a release APK, by the user's decision. The APK adoption is the
  user's.
- **The handshake:** with the host flag on and the setting on, the paired
  onn ran a real 20-min PS1-STREAM through its own signed setup and token,
  and every host gate held.
- **Refusals:** a forged token and an unpaired device were both refused
  and audited.
- **Off again:** with the flag and the setting off, the stream is today's.
  Its host CPU, 12.963 %, was 0.06 over the band (§2a).

Task: `handoffs/CL-B2_IDENTITY_APK_INSTALL_AND_LAN_SMOKE_TASK.md`, session
A item 3 of `QUEUE_2026-10-16.md`. It ran across two sittings:
2026-10-16 02:14-03:16Z (stopped at the re-pair, below) and 13:49Z onward.
Files: `cl_b2_2026-10-16/`. Pre-registration:
`cl_b2_preregistration.txt`, sha256 `848c87ad…5b17`, hashed before the
install.

## 1. The install (step 1-2)

- **Precondition:** the link watch was inactive (stopped, E4-S4C).
  `tools/e3_state.py` read ok on five lines. The onn ran `de072762…835e`,
  CL-B1's CONFIRMED APK (`device_apk_before.txt`).
- **Install:** `adb install -r` of `PrivyHub/app/build/outputs/apk/debug/app-debug.apk`
  (`77011eefa538fb965e46ad1f25ddac99036e1d77557ba7b7a677dc5947807d9d`).
  It reported `Success` (`install.log`), and the device read back the same
  hash (`device_apk_after.txt`).
- **The state tools' pinned hash:** patch
  `patches/CL-B2_IDENTITY_APK_HASH.md`.
  - The edits: `tools/e1_suite.py` `EXPECT_APK`,
    `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`, and its test.
  - The diff is `cl_b2_hash.diff`; the predecessors are in
    `predecessors/`.
  - 33 / 33 tests passed; `e3_state.py` read `apk: CONFIRMED`
    (`check_after_install.json`).
- **Rollback (written, not applied):**
  1. `adb install -r PrivyHub/app/build/g3_s2_preserved/app-debug.apk`
     (`de072762…`, preserved by G3-S2).
  2. Copy the three predecessors back.

## 2. The three PS1-STREAM runs (`tools/e1_suite.py --e2`, gap 120 s)

| run | what | window (UTC) | capture fps | dup+drop /min | RetroArch | host CPU % (band 10.9 ± 2) | flags_absent after | rendered* | loss/min* | resyncs* |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | setting off, flag absent, 10 min | 02:20-02:30 | 59.942 | 0.10 | 59.999 | 12.20 | true | 57.32 | 1,249 | 35 |
| R2 | paired, `identity_v2` on, host flag on (the suite's per-run drop-in), 20 min | 02:50-03:10 | 59.989 | 0.10 | 59.999 | 11.22 | true | 58.53 | 731 | 49 |
| R3 | flag off, setting off, 10 min (second sitting) | 13:54-14:04 | 59.990 | 0.10 | 59.999 | **12.96 (FAILED, +0.06)** | true | 59.48 | 216 | 3 |

\* The link: reported, not gated. It was lossy on 10-16 as on every
night since 10-09.

- **Host gates:** each run's are E4-S1 PS1-STREAM's (RetroArch ≥ 59.9,
  capture 60.0 ± 0.1 segment-aware, dup+drop ≤ 0.2/min, host CPU ±2 of
  10.9 %). R1 and R2 held every gate. **R3 held all but host CPU: 12.963 %
  against a ceiling of 12.9, FAILED by 0.06** (§2a). `cl_b2_verdict.json`
  reads `FAILED (runs/E1-PS1-STREAM/run2:host_cpu_pm_2_of_10.9)`, and
  `validity.json` reads all three runs `OK` (valid runs, not passes).
  (`cl_b2_analysis.py` → `cl_b2_table.md`, `cl_b2_verdict.json`,
  `validity.json`).
- **R1 and R3 match today:** with the host flag absent, the G3-S1 gate is
  not constructed, and R1 wrote no audit line (the audit log did not yet
  exist). The client with the setting off sends today's bytes (G3-S2's
  `WireRequestTest`).

## 2a. The failed gate: R3's host CPU (the reading; the user's decision)

- **The gate:** host CPU ±2 points of E4-S1's PS1-STREAM 10.9 %, so at
  most 12.9. R3 read **12.963, FAILED by 0.06**. R3's other four gates
  held.
- **From the files** (`cl_b2_cpu_split.py` → `cl_b2_cpu_split.json`; the
  sampler's per-process means as % of one core, the polled
  `bitrate_kbps`, the ladder's acted decisions):

  | run | host CPU % | companion | RetroArch | encoder (min-max) | Xorg | `bitrate_kbps` polled | ladder acted |
  | --- | --- | --- | --- | --- | --- | --- | --- |
  | E4-S1 reference (10-09) | 10.922 | 25.04 | 33.52 | 36.04 (31-39) | 9.70 | 7000 ×129 | none |
  | R1 | 12.198 | 24.59 | 34.00 | 35.75 (0-49) | 9.70 | 5000-7000 (7000 ×55, 5000 ×14) | 7000 → 5000 at 02:28:06Z |
  | R2 (flag) | 11.223 | 25.02 | 34.09 | 35.64 (31-39) | 9.61 | 7000 ×129 | none |
  | R3 | **12.963** | 25.36 | 35.89 | **46.65 (37-56)** | 11.07 | 7000 ×69 | none |

  - The companion and RetroArch were within a point of R1 in R3 (+0.76,
    +1.89). The encoder was **46.65 against 35.75 %** of a core
    (+10.9). Xorg was +1.4.
  - R3's polled ladder read **7000-7000** for the whole window. R1's read
    **5000-7000**: one drop to 5000 at 02:28:06Z, for the run's last
    ~2.5 min.
- **What the files do not support (said plainly):** the user's reading is
  that the cleaner link held the ladder at 7000, while E4-S1's 10.9 was
  measured with rung drops. The files contradict the second half:
  - **E4-S1's reference run held 7000 for all 129 polls, with no ladder
    action.** Its encoder used 36.04 %.
  - **R2 also held 7000 for its whole 20 min, with no action.** Its
    encoder used 35.64 %.
  - So at the same constant 7000 rung, the encoder used about 36 % in the
    reference and in R2, and 46.65 % in R3. The rung mix does not account
    for R3's +10.9 points. R1's single drop came late and was short, and
    R1's encoder mean (35.75) matches the 7000-only runs.
- **What differed in R3, recorded and not tested:**
  - It was the second sitting, about 10.7 h after R2, in daytime.
  - It had the cleanest link of the three: 216 loss/min and 3 resyncs,
    against 731-1,249 and 35-49.
  - The mean core clock was higher: 3,515 MHz, against 3,199-3,423.
  - The encoder's floor was 37 %, above every other run's typical value.

  The cause of the encoder's +10.9 is **not located**. No further run
  was made: this close runs nothing.
- **The decision (the user's, 2026-10-16):** the gate is recorded as
  **FAILED by 0.06**. The APK stays, and CL-B2 closes. Nothing else is
  adopted.
- **The bar lesson:**
  - **As the user wrote it:** a host-CPU band must compare runs at an
    equal rung mix, or report the encoder together with its rung.
  - **As written here:** the second half is what made this reading
    possible. A host-CPU band gate should report the encoder's % of a
    core beside the polled rung mix, both for the run and for the
    reference.
  - R3 shows that an equal rung mix is necessary but not sufficient: at
    an equal rung, the encoder still moved by 11 points. A gate that
    fails within ~0.1 point of its edge should be read through that
    split before the cause is named.
  - For a future bar (not applied here), the user could choose to gate
    the encoder's share at the rung, or to widen the band. Either is the
    user's call.

## 3. Pairing (step 3)

- **The flag:** `e3_flag.conf` = `PRIVYHUB_SESSION_IDENTITY=v2`
  (`e3_flag_pairing.conf.txt`), then `daemon-reload` and a restart.
  `/session/status` read: mode v2, 0 devices, `legacy_unpaired_lan` true.
- **The window:** opened on the hub (`POST /session/pairing/open`,
  loopback) at 02:44:04Z. The user typed the code on the onn, and the
  hub held **1 device** at 02:44:51Z.
- **The audit** (`audit_pairing.jsonl`): `pairing_open` (host_local),
  then `pairing_ok` for `dev-381e…`, permissions games, tv and vod,
  routing `lan`.
- **The store** `~/.config/privyhub/paired_devices.json` is mode 0600 and
  holds one device and its key. Its directory is **0775**, not the 0700
  G3-S1 describes. The directory already existed (it holds
  `android-signing`), so the store's own 0600 is what protects the key.
  This is noted for G3-S3.
- **The setting:** the user turned `identity_v2` on at 02:45:48Z (read
  through `run-as`, that one setting only). The flag drop-in was then
  removed and the companion restarted, because the suite's preflight
  needs it absent; the suite sets the flag itself for R2.

## 4. End to end (step 4)

- **The audit over R2** (`audit_r2.jsonl`, 02:46:10-03:10:27Z), in order:
  1. `session_refused token-unknown` on `/sources` (02:46:19Z): the
     client's token was from before the restart.
  2. `token_issued` for `dev-381e…` the same second: the designed single
     fresh setup and retry (nonce → signed setup → token).
  3. `host_local_setup` on `/plugins/games/launch` (02:48:19Z): the suite
     launches the title from the hub itself.
  4. `token_issued` for `dev-381e…` (02:48:24Z): the stream activity's
     setup.
  - **No `legacy_setup`** in the whole run. `native-stream-start` is a
    setup path, so a call without a header from the LAN would have been
    audited `legacy_setup`. The client's stream calls therefore carried
    the token (`X-PrivyHub-Session`).
  - Two `token_issued` for the one device: the client set up twice within
    two minutes, recorded as seen.
- **Declared endpoints** (`declared_target_r2.json`):
  - For a session, the companion hands the native-stream handler
    `SESSION_IDENTITY.client_target(self)`, which is the declared
    `media_host`. The source is used only as routing evidence.
  - `endpoint-port-mismatch` (the signed `video_port` against the call's
    port) did not fire.
  - **The wire destination was not observable unprivileged:** the encoder
    sends to the loopback FEC sender, every UDP socket in the companion's
    cgroup is unconnected, and a capture needs privileges, which were not
    used.
  - On the LAN the client declares its own address on the route to the
    hub, the same as the source. The stream reached the onn: PLAYING in
    3.0 s, and R2's gates held.
- **The client's log:** `PrivyHubIdentity` lines from R2 had rotated out
  of the onn's 256-KiB main buffer before they were read, so
  `logcat_r2.txt` is empty. The refusal lines below were read at once.
- **A forged token, from the hub** (03:11:17Z, flag on again):
  `curl -H "X-PrivyHub-Session: <forged>" /plugins/games/status` returned
  **HTTP 401**, `{"reason": "token-unknown"}` (`forged_token_response.txt`).
  It was audited as `session_refused token-unknown` (`audit_forged.jsonl`)
  and did not fall back.
- **The pairing removed** (by 03:11:30Z):
  - The store was backed up beside itself first
    (`paired_devices.json.cl_b2_before_unpair`, 0600, outside the repo).
  - Its device list was emptied; the hub read 0 devices.
  - The client was relaunched (`am force-stop` + launcher).
  - Its setup was **refused `unknown-device`**, audited on `/session/setup`
    at 03:11:34Z (`audit_unpaired.jsonl`). The host's code is
    `unknown-device`; the task wrote `device-unknown`.
  - The client logged `identity: refused, reason=unknown-device`
    (`logcat_unpaired.txt`). On that path its code shows the toast
    "PrivyHub session refused: unknown-device". This session read the log
    line; it did not see the screen.
- **Re-paired:**
  - The first sitting's two windows (03:11:56Z and 03:14:09Z) expired
    with no attempt reaching the hub: only `pairing_open` in the audit
    (`audit_repair.jsonl`). The session stopped and said so.
  - On resumption, the window opened at 13:49:24Z gave **1 device** at
    13:49:56Z, `pairing_ok` for a **new** device id `dev-2fb1…`, routing
    `lan` (`audit_repaired.jsonl`, `session_status_after_repair.json`).

## 4a. The audit excerpts (as written in `cl_b2_2026-10-16/`; no address, no token)

The excerpts are reduced by `cl_b2_audit.py` to the event, reason,
routing, path, permissions and a device-id prefix of 4 hex digits, as
the pre-registration set. `token_ref`, the source address and any key
are not written.

- **Pairing** (`audit_pairing.jsonl`):
  - `02:44:04Z pairing_open host_local=true routing=lan`
  - `02:44:50Z pairing_ok client=dev-381e… permissions=games,tv,vod routing=lan host_local=false`
- **R2** (`audit_r2.jsonl`):
  - `02:46:19Z session_refused token-unknown path=/sources`
  - `02:46:19Z token_issued dev-381e… expires_in_s=28800`
  - `02:48:19Z host_local_setup path=/plugins/games/launch`
  - `02:48:24Z token_issued dev-381e…`
  - No `legacy_setup`.
- **The forged token** (`audit_forged.jsonl`, `forged_token_response.txt`):
  - `03:11:17Z session_refused token-unknown path=/plugins/games/status host_local=true`
  - The response was **HTTP 401** `{"ok": false, "error": "session refused", "reason": "token-unknown"}`.
- **The unpaired device** (`audit_unpaired.jsonl`, `logcat_unpaired.txt`):
  - `03:11:34Z session_refused unknown-device path=/session/setup host_local=false`
  - The client logged `03:11:33.800 PrivyHubIdentity: identity: refused, reason=unknown-device`.
- **The re-pair:**
  - The first sitting (`audit_repair1.jsonl`, `audit_repair.jsonl`):
    `03:11:56Z pairing_open` and `03:14:09Z pairing_open`. Both expired
    with no attempt.
  - On resumption (`audit_repaired.jsonl`): `13:49:31Z pairing_open`,
    then `13:49:52Z pairing_ok client=dev-2fb1… permissions=games,tv,vod routing=lan`.
  - `session_status_after_repair.json` read mode v2, 1 device, no window
    open.
  - `logcat_repair.txt` holds only the 03:11:33 refusal line: the re-pair
    wrote no `PrivyHubIdentity` line that was captured.
- **R1 and R3:** no audit line. R1 ran before the log existed; for R3,
  `audit_r3.jsonl` has 0 rows.

## 4b. The APK hashes

| what | sha256 | file |
| --- | --- | --- |
| on the onn before (CL-B1's CONFIRMED) | `de072762e55122c3060086f6f10b1bff54633d9165d0c475f17699127841835e` | `device_apk_before.txt` |
| installed (G3-S2's debug APK) | `77011eefa538fb965e46ad1f25ddac99036e1d77557ba7b7a677dc5947807d9d` | `install.log` (`Success`) |
| on the onn after (read back) | `77011eefa538fb965e46ad1f25ddac99036e1d77557ba7b7a677dc5947807d9d` | `device_apk_after.txt` |
| the pre-registration | `848c87ad7b1966a0a4f91f8a7ea5cf256abf07a69c4114a5704fe86fa90a5b17` | `cl_b2_preregistration.sha256` (re-hashed at close: the same) |

- **`e3_state.py --check`** read `ok`, `apk: CONFIRMED`, five lines, no
  `e3_flag.conf`, no `e4_constraint.conf`. That held at three points:
  - after the install, 02:16:19Z (`check_after_install.json`);
  - before R3, 13:50:15Z (`check_before_r3.json`);
  - the suite's end state, 14:04:41Z (`runs/final_state.json`,
    `flags_absent` true).
- This close ran no `--check` of its own: it runs nothing against the
  host.

## 5. Flag off, setting off (step 5)

- **The setting:** `identity_v2` read **false** at 13:50Z
  (`client_setting_before_r3.txt`). It was already off when step 5
  began, so the user had nothing to change.
- **The flag:** `e3_flag.conf` removed, `daemon-reload`, restart
  (`restart_before_r3.json`: the five lines).
  `e3_state.py --check`: ok, `apk: CONFIRMED`, five lines
  (`check_before_r3.json`).
- **R3** (§2), 13:54-14:04Z: PLAYING in 3.1 s; capture 59.990, dup+drop
  0.10/min, RetroArch 59.999, `flags_absent` true. Host CPU was 12.963 %,
  FAILED by 0.06 (§2a). The audit log gained **no line** over R3
  (`audit_r3.jsonl` is empty, `audit_r3_counts.json` 0 rows since
  13:50:15Z), as in R1: with the flag absent, the gate is not
  constructed. The link was the cleanest of the three runs (216 loss/min,
  3 resyncs).
- The pairing (`dev-2fb1…`) stays in the hub's store. With the flag
  absent, the store is not read.

## 6. Follow-ups for G3-S3 (not acted on)

- **The declared ports (the G3-S3 follow-up from this smoke):**
  - The client declares `video_port` 48100, which is signed and checked
    against `native-stream-start`'s port, and `audio_port` 48101, which
    is declared, unsigned and **ignored** by the host.
  - The video leaves the encoder for the loopback FEC sender (port 48110),
    and that sender's sends are unconnected, so the host's chosen
    destination is not visible from outside the process.
  - G3-S3 could sign and check `audio_port`, and report the chosen
    target's class and hash in `/status` or the audit (no address), so a
    smoke can compare it with the declaration.
- The store's directory mode (§3).
- The client sets up twice per stream entry (§4).
- **Already on G3-S3's list (not from this smoke):**
  - the range server over the overlay;
  - tokens on the TV-sync, EPG and diagnostics paths.

## 7. The adoption lines (written, not applied; the user's call)

- **The host flag:**
  `~/.config/systemd/user/privyhub-companion.service.d/session-identity.conf`:

  ```
  [Service]
  Environment=PRIVYHUB_SESSION_IDENTITY=v2
  ```

  Then `systemctl --user daemon-reload`, restart the companion, and add
  `PRIVYHUB_SESSION_IDENTITY=v2` to `tools/e1_suite.py`'s `ADOPTED`.
  Revert: delete the file, `daemon-reload`, restart, and take the line
  out.
- **The client setting:** on the onn, Settings → "Use paired identity
  (identity v2)" → on. The device is paired (`dev-2fb1…`). Revert: the
  same switch off.
- **The order:** the flag first, then the setting. With the flag off, a
  client with the setting on falls back to today's requests (`/session/nonce`
  → 404). With the flag on and the setting off, the onn plays on the
  legacy LAN path (`legacy_unpaired_lan` true).
- **The APK:** CONFIRMED in the state tools (§1), and **kept**: the user
  decided it stays, with R3's host-CPU gate recorded FAILED by 0.06
  (§2a). It is the only adoption in CL-B2. The rollback in §1 stays
  written and not applied.

## 8. Files; state

- **`cl_b2_2026-10-16/`:**
  - the pre-registration and its hash;
  - `runs/` (R1 and R3 under `E1-PS1-STREAM/run1-2`, R2 under
    `E1-PS1-STREAM_flag/run1`; `suite.log`, `final_state.json`,
    `absent.json`);
  - `cl_b2_analysis.py`, `cl_b2_table.md`, `cl_b2_verdict.json`,
    `validity.json`;
  - `cl_b2_cpu_split.py` → `cl_b2_cpu_split.json` (§2a, written at the
    close from the run files);
  - the `--check` readings: `check_after_install.json`,
    `check_before_r3.json`, `runs/final_state.json`;
  - `cl_b2_audit.py` and the `audit_*.jsonl` excerpts (event, reason,
    routing, path, permissions, device-id prefix only; no token_ref, no
    address);
  - `logcat_*.txt` (`PrivyHubIdentity` lines, addresses and long hex
    replaced before writing);
  - the hashes, the restarts and session statuses, `declared_target_r2.json`,
    `forged_token_response.txt`, `predecessors/`, `cl_b2_hash.diff`;
  - `redact_check.txt`: the redactor over everything written in this
    queue and last night's (G5-S1, G4-P1).
    - 245 files: 233 OK, 12 HIT.
    - Every HIT is benign only: the loopback or bind address in
      `companion/privyhub_service.py`, `tools/e1_suite.py` and its
      predecessor; the Beetle PSX core's version string in the runs' and
      the watch probes' `title.txt`.
    - Each HIT re-checked OK with those strings masked.
    - A grep for `token_ref`, token or header values and pairing codes
      found none;
  - `manifest.sha256`: all 122 files in the directory except itself and
    `manifest_check.txt`, written last;
  - `manifest_check.txt` (`sha256sum --check`: 122 OK, rc 0).
- `logs/cl_b2_git_status.txt`.
- **State at the end:** the five-line adopted state; no flag, no
  constraint; APK `77011eef…` CONFIRMED; one paired device; `identity_v2`
  off. Nothing committed. This close ran nothing against the host or the
  onn, restarted nothing, and changed no flag or setting.
- No sudo, no nft. No address, token, key or pairing code in any file in
  the repo; the pairing codes went only to the chat.
