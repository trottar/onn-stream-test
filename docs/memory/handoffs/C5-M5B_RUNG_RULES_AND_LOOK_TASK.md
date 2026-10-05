---
memory_schema: 1
as_of: 2026-10-03
status: TASK HANDOFF — C5-M5B: (1) set the 1080p rung's entry threshold and give it a loss-based leave from the recorded data — selection criteria pre-registered before the replays, candidates replayed on every recorded series, the chosen rules built behind the same flag, tests, stop rule, injection, a daytime 30-min hold and one overnight 2-h session; (2) the PS1 look levers (texture filter, dither, PGXP) measured for host cost at 720p and at the rung, and a one-command look helper so the user can judge the picture on the TV. The user accepted C5-M5's R0b deviation. Rung and look presets stay behind flags; nothing adopted
---

# C5-M5B — the rung's rules from the data, and the look

**Why.** C5-M5 built the rung and showed it works mechanically (no
client change; 287-403 ms per sized switch; one real entry overnight,
8.5 min at 1080p at loss 2.0/min). Two rules are wrong for this link:
**the entry** (≥ 435 of 450 clean) was reached once in 2.4 h and on none
of the ten recorded holds with real inputs (best 420-433; S2's best 431);
**the leave** (the mild bar) waits for a sustained fps shortfall that
1080p's bursty loss never gives — S1 sat 2.3 min at 80 lost/min with no
leave, and the replays leave on 1 of 13 recorded 1080p series. The user
accepted C5-M5's R0b deviation (2026-10-03). Both rule changes are
selected here **by criteria written before the replays**, then built and
shown. Separately, the user asked what 4x alone shows: the look levers
Beetle PSX HW offers beyond internal resolution are measured for cost
and put behind a preset so the TV look is one command.

Read first: `evidence/C5_M5_1080P_RUNG_2026-10-03.md` (§3 the replays,
§4 the sessions, §5), `c5_m5_2026-10-03/c5_m5_replays.txt`,
`tools/c5_m5_replay.py`, `patches/C5-M5_1080P_RUNG.md`,
`companion/adaptive_bitrate_live.py`, `C3_L4_N2_MILD_CAPACITY_2026-09-29.md`
(the mild bar's definition and why), `C5_M4_PS1_NATIVE_1080P_SOURCE_2026-10-01.md`
§1 (the core options not proposed: `dither_mode`, `filter`, PGXP keys,
MSAA) and §2 (the host table method, HOLDS 60), `C5_M4A_…` (the adopted
PS1 config and its hashes), `TOOLS.md`, `CURRENT.md`. Live is the
default; the rung flag `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p` is off by
default; APK `de072762…835e`; width 80 MHz.

## 1. Pre-registration — written before any replay

`evidence/c5_m5b_<date>/c5_m5b_preregistration.txt`, hashed. It holds
the candidate grids, the **selection criteria**, and §3's and §4's rows.

**Entry candidates.** Thresholds 405, 410, 415, 420, 425, 430, 435 of
450; and N = 300 at the same clean fraction (≥ 93.3 %). Replayed on
every recorded 720p series at 7000 (the ten with real per-report
inputs first: N1, N2, D1 B3b, LINK-L2 H1-H6, C5-M4A V5; then the
heartbeat-proxy series, marked as proxies; plus C5-M5's S2 and S3's 7000
stretch). For each: entries, minutes to the first entry, and — the
honest part — on the same hold's own later reports, what fraction of the
time after entry the stream would have been "unclean" by the blend.

**Entry selection rule (pre-registered):** the **strictest** threshold
that enters within 20 minutes on **at least 7 of the 10** real-input
holds. If none does, the loosest candidate is reported as not enough and
the entry stays at 435 (the user decides).

**Leave candidates** (rung-only; they never apply at a 720p level):

- **L-A** `lost_packets_delta ≥ 100` on ≥ 2 of the last 10 evaluated
  reports;
- **L-B** the sum of `lost_packets_delta` over the last 15 reports ≥ 300
  (~30 s);
- **L-C** `lost ≥ 50` on ≥ 3 of the last 10 (the mild bar's loss half,
  without its fps half);
- **L-D** L-A or a stale-drop delta ≥ 5 in any report (the client's
  decoder falling behind);
- plus the existing mild bar, strict capacity and the backstop, which
  stay.

Each → ROUTINE one rung down, 12600 → 7000 at 720p, with ROUTINE's
hold-downs and the 10-min re-entry hold. Replayed on the 13 recorded
1080p series, on S1's 2.3-min 1080p stretch and on S3's 8.5-min stretch:
seconds to the leave; and on S3's stretch, whether it fires (a leave
there, at 2.0 lost/min, is a false leave).

**Leave selection rule (pre-registered):** the candidate that leaves
S1's stretch within 60 s, leaves C5-M2 n1r C3 (the rung's own arm) within
120 s, **does not fire on S3's stretch**, and fires on the most of the
13 series; ties → the simplest (L-A before L-B before L-C before L-D).
If none meets all three hard conditions, report the table and keep the
mild bar (the user decides).

## 2. Replays, then the build

`tools/c5_m5_replay.py` extended for the grids; output
`c5_m5b_replays.txt`. Apply the selection rules exactly; write the
chosen numbers and the rows that chose them into the record **before**
changing code.

Then build: the entry threshold and the chosen leave (reason
`rung_loss`, class ROUTINE, visible in status and the rows), behind the
same flag. Tests for the threshold boundary, the leave at and below its
bar, rung-only scope (never at 720p), the 10-min re-entry hold after a
`rung_loss` leave, the oscillation count; mutations caught; the shadow
byte-identical; **the stop rule**: flag absent → 0 differences against
`5005615`'s controller on every series, as C5-M5 ran it.

## 3. Sessions

- **S1b, injection**: entry by the policy path, then the loss leave by
  injecting its bar (not the mild bar); gaps ≤ 450 ms; `any_override`
  false; one SSRC change each; after BACK 7000 / 1280×720.
- **S2b, daytime 30-min hold, flag on** (pre-registered): RUNG SHOWN if
  the controller enters by the new threshold and then either stays or
  leaves by a named rule; every transition named and spaced; 0
  recovery cycles; client rows met; per-level minutes, loss and gap
  reported.
- **S3b, overnight 2-h session, flag on, start 01:00-06:00 local**
  (pre-registered): WORKS AS A RUNG as C5-M5's S3 defined it, plus: time
  at 1080p reported, every leave named, no oscillation HOLD or one with
  its three changes listed, the 1080p minutes' client rows met, loss and
  gap per level reported.
- Teardown after each: flag unset and absent, live default intact,
  stream 7000 at 1280×720, adopted profile and source, no game, 0
  banners, APK confirmed.

## 4. The look: levers measured, presets behind a flag, one command

**The levers**, from Beetle PSX HW's options in the adopted `.opt`:
`beetle_psx_hw_dither_mode` (native → `disabled` or `internal
resolution`), `beetle_psx_hw_filter` (nearest → `bilinear`, `xBR`,
`SABR`, `3-point`, `JINC2`: Code tests each that the core build offers),
PGXP (`pgxp_mode` memory only, `pgxp_texture` on, `pgxp_vertex` on),
`beetle_psx_hw_msaa` (2x/4x if offered). **Not changed in the adopted
files.** They are applied **per session only**, through a core-option
override the companion writes for that launch and removes at BACK (the
mechanism Code chooses must leave `Beetle PSX HW.opt` and the per-title
copies byte-identical; hash before and after every session).

**Cost table** (C5-M4's method and HOLDS 60 bar, 5-min holds, the
adopted 7000 stream, 4x): the baseline 4x; dither disabled; each texture
filter the build offers; PGXP (memory + texture + vertex); MSAA 4x; then
**the full preset** (4x + the best-cost filter + dither disabled + PGXP).
Per hold: HOLDS 60, GPU busy mean/p95, GPU W, RetroArch and encoder % of
a core, Tctl, and the stream's per-second largest frame p50/p90 and cap
hits s/min (a filtered texture changes the encoder's job). Then the
full preset once at the rung (flag on, entry injected, 5 min). A preset
that misses HOLDS 60 is reported and not offered.

**Two presets, behind `PRIVYHUB_PS1_LOOK=`**: `4x` (today's adopted
config, the default when unset) and `remaster` (the full preset that
HOLDS 60, exact option values named in the record). Unset → nothing
changes anywhere.

**The look helper `tools/ps1_look.sh`**, for the user's hand, one
command per look, PowerShell SSH window, the TV showing the stream:

- `tools/ps1_look.sh 4x` / `remaster` / `remaster-1080p`: sets the
  session flags (and for `-1080p` the rung flag), restarts the companion
  through its unit, waits for PLAYING (the user starts the game on the
  TV as usual, or the helper starts the attract title), for `-1080p`
  injects the entry and confirms 1920×1080 in the status, prints **what
  to look at** (edges, textures up close, the dither pattern in
  gradients, polygon wobble; at 1080p the IDR pulse every 250 ms in flat
  areas), and waits for Enter; on Enter it ends the session, unsets
  every flag, restarts the companion, verifies the adopted state (flags
  absent, live, 7000 / 720p, the `.opt` hashes unchanged) and prints it.
- Fake-run tested; the real run is the user's. The user's words after
  each look are recorded in the daily file as their words; nothing
  perceptual is a gate.

## 5. Record and memory

`evidence/C5_M5B_RUNG_RULES_AND_LOOK_<date>.md`, `c5_m5b_<date>/`
(manifest, `--check`); `patches/C5-M5B_*.md`; `PATCH_INDEX.md`;
`architecture/ADAPTIVE_BITRATE.md` (the rung's rules as chosen);
`docs/ROADMAP.md` C5; `decisions/C5_1080P60_CAPABILITY_2026-09-28.md`
(append: the chosen rules and why, the look presets); `TOOLS.md` (the
look helper and both flags, kill switches); `investigations/ACTIVE.md`;
`evidence/RUNTIME_VALIDATION.md`; the daily file;
`check_memory_health.py`; `git status --short` and `git diff --stat` to
`logs/c5_m5b_git_status.txt`; `CURRENT.md` last — Next Action 1: the
user's commit; 2: **the user's look** (the three helper commands, in
order, what to look at, "tell Claude what you saw"); 3: the user's
calls — adopt the rung flag by default or not, the `remaster` preset or
not, the `nft` capacity night for the rung (the user's); 4: Phase E
when C is closed by the user.

Adopted profile, source and APK throughout; the rung and the presets
behind their flags, nothing adopted; the shadow byte-identical; no
`nft`, no real `sudo`, the Opal read-only; no addresses, MACs, SSIDs,
ADB endpoints, serials or credentials anywhere; the two-retry limit;
pre-registered criteria never changed after data. Nothing committed.
