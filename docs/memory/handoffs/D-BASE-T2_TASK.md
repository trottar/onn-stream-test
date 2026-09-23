---
memory_schema: 1
as_of: 2026-09-23
status: TASK HANDOFF — D-BASE-T2, (0) adopt the 12/17 audio cushion as the profile default per the user's decision and record their listen; (1) find what accumulates over back-to-back streaming that drives audio loss from ~3/min to ~100/min and resets with idle, and set thermal thresholds from measurement; authorized by the user 2026-09-23
---

# D-BASE-T2 — adopt the cushion; then what builds up while streaming

## Part 0 — adopt 12/17 (the user's decision, 2026-09-23)

`P9a` showed 12/17 passing starvation (-98/-99 %), cost (+33.5/+37.9 ms)
and the underrun noise band in both interleaved arms; the one failed
clause was the hole check against a baseline arm that was itself +28 %
over its sibling — a check on arrivals the cushion cannot move. **The
user's standing decision (2026-09-23) was to spend the +45 ms; it
stands.** Their listen with 12/17 in force, verbatim, user-stated, never a
gate: *"No issues from playing for a minute or two."*

Do: set the profile default to **12 / 17** where `P9` put the default
(`audio_cushion.source: profile`); **unset** `PRIVYHUB_AUDIO_QUEUE_TARGET_PACKETS`
and `PRIVYHUB_AUDIO_QUEUE_CAPACITY_PACKETS` from the user manager
(`systemctl --user unset-environment …`), restart through systemd, and
confirm `native-stream-status` reads 12 / 17 with source `profile` and no
`PRIVYHUB_*` in the MainPID's environ. Compile Python, `git diff --check`;
no client build needed if the default is the companion's — say so. Record
in `decisions/D-BASE-P9_AUDIO_CUSHION.md` (adopted, the measured cost, the
user's words), `docs/PROJECT_STATUS.md` (reference profile block), the
`P9a` record's status line, `RUNTIME_VALIDATION.md`, `MEMORY.md`, `TOOLS.md`.
Patch record + `PATCH_INDEX.md`.

## Part 1 — the loss that builds with streaming time

**The observation (`P9a` §"Audio loss").** Audio `lost_packets` per minute
opened at **3** after a ~40-minute idle and climbed to ~50-60 by minute 12-20;
sessions started a minute after the previous one opened at **30-110** and
stayed there. Cushion-independent (interleaved arms), video loss did not
follow it in the A arms (9.5/9.4 per min) though it doubled in the B arms
(unexplained, noted). `T1` measured the host's hottest sensor ramping
54 → 60 °C over 10 minutes and plateauing; `S3` over three hours saw the
plateau hold. The onn reports thermal status only (0 throughout so far)
and has no readable zones (`T1`). The Opal is read-only over `ssh opal`
(`iw`, `iwinfo`, `/proc`, `/sys`, `logread`; never a write).

Read first: `evidence/D_BASE_P9A_CUSHION_INTERLEAVED_2026-09-23.md`
(§audio loss, the per-minute series), `evidence/D_BASE_T1_THERMAL_TELEMETRY_2026-09-21.md`
(the host sampler, the onn's status-only thermal, what was and was not
readable), `evidence/D_BASE_S3_CAP_SOAK_2026-09-22.md` (three hours: the
hourly loss 380/340/253 — did *audio* loss climb there? check its
heartbeat log), `evidence/O1_OPAL_AIR_VIEW_2026-09-21.md` (what the Opal
exposes and its counter traps), `evidence/D_BASE_R5_HEARTBEAT_LOSS_COUNTERS_2026-09-21.md`,
`tools/` (the host resource sampler `T1` added: interval, fields), `TOOLS.md`.

**One narrow question:** *does audio loss track a host sensor, an onn
signal, or the AP, over back-to-back streaming — and does it reset with
idle?* Not "why is there loss" — `P4`/`O1`/`P5`/`P6` closed the video loss
column; this is the **audio** counter's time trend.

**Design — one run, four back-to-back 20-minute sessions with a 30-minute
idle in the middle, all at the adopted profile and 12/17, no other change:**

| # | session | starts | purpose |
| --- | --- | --- | --- |
| 1 | S-a | after ≥ 40 min host idle (no stream since the previous task — confirm from the recovery log) | cold start: loss should open low |
| 2 | S-b | 1 min after S-a | warm: does it open where S-a ended? |
| 3 | idle | 30 min, nothing streaming, companion up | reset window |
| 4 | S-c | after the idle | does loss open low again? |
| 5 | S-d | 1 min after S-c | warm again |

Throughout (sessions **and** the idle), sample every **10 s** into one
jsonl: host — every `hwmon` temperature (`/sys/class/hwmon/*/temp*_input`
with labels), CPU MHz per core (`/proc/cpuinfo` or `cpufreq`), the
encoder process CPU %, `/proc/net/dev` on the wired interface (rx/tx
drops/errors); onn over adb — `dumpsys thermalservice` (status and any
temperatures it lists), `dumpsys battery` (temperature field, even on a
TV), `cat /sys/class/thermal/thermal_zone*/temp` if any answer (T1 said
none — re-check once, record), and `dumpsys wifi | grep -iE 'rssi|linkspeed|freq'` (link speed and RSSI from the TV's side, no
addresses/SSIDs — filter them out before writing); Opal over `ssh opal` —
`iwinfo <wlan> assoclist` signal/rate for the onn's row **redacted to the
numbers only**, `/proc/loadavg`, the wireless `/sys/class/thermal` or
`/proc` temperature if the SoC exposes one (record "none" otherwise), and
`iw dev <wlan> station dump` retry/failed counters (remembering `O1`'s
`tx failed` copies `tx retries` on this AP — use the rate/MCS instead).
**No writes to the Opal. No addresses, MACs, BSSIDs or SSIDs in any
file — filter at capture, then `h2_prep_redact.py --check`.**

The onn's adb traffic during holds is a diagnostic cost `P8` cleared
(sampler -1 %) — at 10 s it is fine; say so in the record.

**Analysis, raw first.** Per session the per-minute audio and video loss
series; then, over the whole timeline, each sampled signal beside the
audio-loss-per-minute series; Spearman of audio loss/min against each
signal across all four sessions (80 minutes), and separately the *idle*
recovery of each signal against the S-c opening loss.

**Pre-registered reading.**
- **Host thermal / clock** if audio loss tracks a host temperature or a
  CPU-frequency drop with |rho| ≥ 0.6 and that signal is the one that
  reset during the idle while others did not.
- **Onn-side** if the onn's thermal status changes or its link speed /
  RSSI degrades in step (|rho| ≥ 0.6) — then the TV's radio or SoC is the
  accumulator.
- **AP-side** if the Opal's per-station rate/MCS for the onn falls in
  step and the host/onn signals are flat.
- **Time only** if nothing reaches |rho| 0.6 and the idle does not reset
  the loss opening (S-c opens as high as S-b ended) — then it is not
  thermal and the roadmap's `host_link` / AP items get this as their
  first fact.
- **Not reproduced** if S-a and S-b open within 20 % of each other at a
  low level — record that `P9a`'s trend did not recur and stop.

**Thresholds — from the measured curve, proposals only.** If a signal is
implicated: the value at which audio loss/min crossed 30 (≈ the `P9a`
B-arm floor) and 100, as `warn` and `act`; what "act" would be (a
`native-stream-status` flag first; nothing automatic — `C3.L2`: Linux is
`video_only_restart`, not authorized to adapt during play). The user
decides what, if anything, is enforced.

## Record and memory

`evidence/D_BASE_T2_STREAMING_ACCUMULATION_<date>.md` (raw first, the
timeline, the correlations, the reading, the proposed thresholds) with
the jsonl, reports, heartbeat logs and SHA-256s under
`evidence/d_base_t2_<date>/`; `CURRENT.md` (fixed headings, `python3
tools/check_memory_health.py` healthy — trim; Next Action: the user's
threshold decision, then the roadmap list: `host_link`, `B1`/`B3`, Group
C, C6); `MEMORY.md`; `handoffs/CURRENT_HANDOFF.md`;
`investigations/ACTIVE.md`; `KNOWN_ISSUES.md` (the streaming-time loss,
with its cause or "not located"); `TOOLS.md` (the sampler, if kept as a
tool). Teardown per `TOOLS.md`; companion under systemd at 12/17 with no
`PRIVYHUB_*` set; nothing on the Opal changed; no recovery file left.
Never retry a failing action more than twice. No addresses, MACs, SSIDs,
BSSIDs or device identifiers in any memory or evidence file. Nothing
committed.
