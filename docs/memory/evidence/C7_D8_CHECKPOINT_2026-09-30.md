---
memory_schema: 1
as_of: 2026-09-30
baseline_commit: f01c3b2
status: C7 / D8 CHECKPOINT RECORD — every C7 and D8 acceptance item met or explicitly deferred, except "clean checkpoint/push", which is pending the user's commit (Code commits nothing). C3.L4 closed 2026-09-30 (live validated under real loss; behind its flag). The git status for the commit is in logs/c7_d8_git_status_2026-09-30.txt; nothing that must not be committed is outside .gitignore
---

# C7 / D8 — the Phase C and Linux-baseline checkpoint

Task: `handoffs/C3-L4-N3_NFT_NIGHT3_SCORE_AND_C3L4_CLOSE_TASK.md` §3.
The acceptance lists are `docs/ROADMAP.md` "C7 — Phase C checkpoint" and
"D8 — Linux baseline checkpoint". The C7 table there was the starting
point; the corrections are noted.

## C7 — Phase C checkpoint

| item | status | record |
| --- | --- | --- |
| explicit profiles | ✓ | C1: `native_stream_profiles.py`; cap 90 KB, cushion 12/17 and redundancy 2/4 declared and adopted (`C1_STATIC_PROFILE_AND_STATUS_PRIVACY_VALIDATED_2026-09-14.md`, `C1_C2_LINUX_REVALIDATION_2026-09-18.md`, `D_BASE_CLOSEOUT_2026-09-23.md`) |
| transport telemetry contract | ✓ | C2: `privyhub_stream_telemetry_v1`, heartbeat v3, decoder report v2 (`C2_STREAM_TELEMETRY_RUNTIME_VALIDATED_2026-09-14.md`, `C1_C2_LINUX_REVALIDATION_2026-09-18.md`) |
| adaptive bitrate runtime validated | ✓ **`C3.L4` CLOSED 2026-09-30** | Live validated under real loss on three `nft` nights (1 NOT, then 2 and 3 WORKS UNDER LOSS). Live stays behind `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, off by default; turning it on by default is the user's call. `C3_L4_NFT_NIGHT1/2/3_…`, `C3_L4_N1_…`, `C3_L4_N2_…`, `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md` (the close) |
| adaptive FEC validated or explicitly deferred | ✓ explicitly deferred | The user's call, 2026-09-28: adaptive is not supported, static 8+2 NOT SHOWN, 8+1 stays, the arm dormant (`decisions/C4_ADAPTIVE_FEC_2026-09-24.md`, `C4_M1_FEC_ARM_2026-09-25.md`) |
| 1080p60 characterized | ✓ characterized | NOT CAPABLE (stream) at parity; client and host capable; capability-gated. The C5-M2 follow-up arms were INCONCLUSIVE (link), which does not change the characterization (`C5_M1_…`, `C5_M2_…`, `decisions/C5_1080P60_CAPABILITY_2026-09-28.md`) |
| generalized source contract established | ✓ on paper and as an unused interface | `architecture/NATIVE_SOURCE_CONTRACT.md` (`C6_D1_SOURCE_CONTRACT_2026-09-25.md`) |
| Games regression passes | ✓ | D7-R2 all 9 scripted rows PASS; the user's hands-on rows fine (2026-09-28) (`D7_R1_LINUX_REGRESSION_2026-09-25.md`) |
| Phase C artifacts reusable by Phase G remote/WAN | ✓ as a statement, nothing implemented | The contract: a remote transport is another `Transport`. The C5-M3 low-rung data wait under Phase G (`architecture/NATIVE_SOURCE_CONTRACT.md`, `C5_M3_LOW_RUNG_SCREENING_2026-09-29.md`) |
| clean checkpoint/push | **pending the user's commit** | This record; `logs/c7_d8_git_status_2026-09-30.txt` |

**Corrections to the ROADMAP's C7 table:**

- The "reusable by Phase G" row now also points at C5-M3's data.
- The adaptive-bitrate row was "night 3 next". It is now ✓, closed.
- The "1080p60 characterized" row's ✓ is kept. C5-M2 added no outcome.

## D8 — Linux baseline checkpoint

| item | status | record |
| --- | --- | --- |
| Linux is sufficient for normal core server operation | ✓ | D1-D5 closed on Linux: D4 COMPLETE (2026-09-16), D5 COMPLETE (2026-09-17). The companion runs as a systemd user unit (H3). The D-BASE baseline was met cold and warm (`D090_D4_LINUX_GAMES_ACCEPTANCE_2026-09-16.md`, `D5_TV_MEDIA_CLOSEOUT_2026-09-17.md`, `H3_COMPANION_AUTOSTART_DESIGN_2026-09-23.md`, `D_BASE_CLOSEOUT_2026-09-23.md`) |
| PS1-and-below works through Linux-native A/V/input paths | ✓ **with D4's explicit no-fixture skips** | SNES and PS1, including the 4-player multitap, validated. **NES and Genesis had zero local fixtures and are not claimed.** The ROADMAP's wording "PS1-and-below" overstates this by those two systems (`D090_…`, `D7_R1_…`) |
| onn client remains functional | ✓ | D7-R1/R2 scripted rows; the adopted APK in daily use through every C3 / C5 session to 2026-09-30 (`D7_R1_LINUX_REGRESSION_2026-09-25.md`) |
| media / Live TV remain functional | ✓ | D5 closeout: Live TV, EPG, VOD. D7's media row PASS, 2026-09-25 (`D5_TV_MEDIA_CLOSEOUT_2026-09-17.md`, `D7_R1_…`) |
| deferred UDP suite replayed / reclassified | ✓ | NOT REPRODUCED, specific to the old environment (`D6_R1_UDP_SUITE_REPLAY_2026-09-24.md`) |
| no minimum-hardware claim yet | ✓ | None has been made; that is Phase E's |
| clean checkpoint/push | **pending the user's commit** | as C7 |

**Architectural statement** (ROADMAP): *"PrivyHub has a working
Linux-native core suitable for formal resource characterization."* This
holds on the records above, with the NES / Genesis fixture caveat.

**Also open, not a D8 item.** The adopted 720p missed its own post-FEC
loss row in 11 of 16 C5 B holds and in N2's live hold (2026-09-29/30),
with the radio figures unchanged (`investigations/ACTIVE.md`). The
baseline's other rows held. It is worth the user's look before any
further arm is judged on this link.

## For the commit

**Checks on every text file this task wrote.**

- `python3 tools/check_memory_health.py`: **Overall: healthy** (final
  output at the end of this record).
- **`h2_prep_redact.py --check`.** The handoff names
  `tools/h2_prep_redact.py`, which does not exist. The redactor is
  `docs/memory/evidence/h2_prep_2026-09-22/h2_prep_redact.py`, used
  throughout.
  - It passes on every record and memory file.
  - In run files and code copies it flags only the loopback address, the
    any-address bind and the core's version string, as in every earlier
    evidence dir.
  - No private address, MAC, SSID, ADB endpoint, serial or credential was
    found. Checked with a separate grep for private ranges and MACs.

**The git state** is in `logs/c7_d8_git_status_2026-09-30.txt`
(`git status --short`, `git diff --stat`; read-only git). It is
rewritten at the end of the prompt.

**Must NOT be committed.** Every item is already outside git by
`.gitignore`:

| path | why | covered by |
| --- | --- | --- |
| `logs/` (streaming run dirs, companion logs, the git status file itself) | runtime logs; the curated copies live in `docs/memory/evidence/` | `logs/` |
| `runtime/` including `runtime/c5_m3/` (the 120 MB lossless clip and the encodes; hashes in the evidence) | large media | `runtime/` |
| `data/`, `/games/`, `media/`, `cache/` | ROMs, saves, savestates, configs, media | as named |
| `*.apk` (the adopted APK copy `runtime/c4_m1/adopted_app-debug.apk`, any new build) | binaries | `*.apk`, `build/` |
| keys and credentials | secrets | `*.pem`, `*.key`, `.env*`, keystores |
| evidence savestates | game state | `/docs/memory/evidence/**/*.state*` |

**Commit or not, the user's call:**

- **`_cowork_prompt.txt`** is tracked and modified. It is the prompt
  channel, not project state. The user decides whether it belongs in the
  commit.
- **Untracked evidence** is ~127 MB, the largest file 1.3 MB (night 1's
  `frames.jsonl`). Curated evidence `.log` / `.jsonl` files are already
  committed by precedent (175 and 261 tracked), so it is in the same
  class.

## The APK (appended after `CL-B1`, same prompt)

- **The onn client** now runs the adopted **`de072762…835e`**. It was
  adopted 2026-09-30 by its pre-registered rule and carries `CL-B1` plus
  C4-M1's inert v2 decoder.
- A3: the report path works. A4: the client rows are met. A5: its link
  rows match the old APK's in a paired hold.
- So D8's "onn client remains functional" holds on the new APK too
  (`CL_B1_APK_ADOPTION_2026-09-30.md`, `decisions/CL-B1_APK_ADOPTION_2026-09-30.md`).
- The APK binaries stay outside git (`*.apk`, `runtime/`).

## Tool output (final, end of the prompt)

`python3 tools/check_memory_health.py`:

```text
Memory health:

docs/memory/CURRENT.md
  lines: 172
  size: 8885 bytes
  status: healthy

docs/memory/handoffs/CURRENT_HANDOFF.md
  lines: 100
  size: 6755 bytes
  status: healthy

docs/memory/MEMORY.md
  lines: 660
  size: 35818 bytes
  status: healthy

CURRENT.md structure:
  one active objective: True
  one next action: True
  required headings exactly once: True

Overall: healthy
```

**`h2_prep_redact.py --check`**, over the 109 text files the
two tasks wrote (records, memory files, both evidence dirs, the two tool
files):

- **86 pass.**
- **23 are flagged, and every one is one of the known benign classes:**
  - the loopback address, the any-address bind and the core version
    string, in the run files' armcheck / status / report JSON, the
    journals, the alpha logs and the encoder argv;
  - **a new false positive:** the IPv6 pattern matching the driver's
    hold spec (a hold name, two colons, the seconds) on line 3 of
    `cl_b1_run1.log` and `cl_b1_run2.log`.
- A separate grep over the CL-B1 run dirs found **0 private-range
  addresses and 0 MACs**.
- Nothing was fixed, because nothing was an identifier.
