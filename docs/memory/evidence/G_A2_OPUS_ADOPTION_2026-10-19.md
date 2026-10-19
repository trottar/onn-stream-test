---
memory_schema: 1
as_of: 2026-10-19
baseline_commit: 263c26d (CL-B5 committed; the tree carried only the user's prompt and this task file)
---

# G-A2 — the Opus audio path adopted: the eighth line

**Classification: ADOPTED (the user's decision, 2026-10-19).** `PRIVYHUB_AUDIO_CODEC=opus` is the eighth adopted
line, through `audio-codec.conf`. The tools read eight lines, and `--check` is ok on eight. **The confirmation run
was VALID**, with every host gate held and Opus on by the drop-in alone.
- **But its client side was worse than CL-B5's:** underruns **78** (50 in the window), against CL-B5 B / L's 11 / 13
  and the bar of interest ≤ 20.
  - Decoder spikes ≥ 50 ms: 138, against 51 / 34.
  - Two host control gaps over 1 s.
  - Not located (§4). Reported to the user, who decides; not a gate here.
- Nothing else adopted; nothing committed.

- **The decision** (`handoffs/G-A2_OPUS_ADOPTION_TASK.md` §1): the user adopts `PRIVYHUB_AUDIO_CODEC=opus` at its
  defaults (128 kbit/s, 10-ms frames) on CL-B5's evidence:
  - underruns 11 / 13 against PCM's 19;
  - −2,910 kbit/s paired;
  - net audio loss comparable;
  - the listen: "No visual or audio problems".

  The decoder-spikes item stays open in `KNOWN_ISSUES.md`, not a blocker (the user's call).
- Task, session A. Pre-registration for the run: `g_a2_2026-10-19/g_a2_preregistration.txt`, sha256 `512dde69…ee95`,
  hashed at 01:49:28Z, before the run.

## 0. Precondition (01:47Z)

`check_start.json`, `client_start.json`:
- the seven lines; `--check` ok (adb to the onn); APK `043891e1…` CONFIRMED;
- no `e3_flag.conf`, no game; one device paired;
- HEAD `263c26d`. The tree carried the user's `_cowork_prompt.txt` and the task file, which were not touched.

## 1. The drop-in

- **`~/.config/systemd/user/privyhub-companion.service.d/audio-codec.conf`**, written at 01:48:30Z (named like the
  others; a copy is `audio-codec.conf`, its sha256 in `audio_codec_dropin_sha256.txt`):

  ```
  [Service]
  Environment=PRIVYHUB_AUDIO_CODEC=opus
  ```
- `systemctl --user daemon-reload`, then `restart privyhub-companion`: active.
- **The environ read back eight lines** (`environ_after_adoption.txt`): the seven plus `PRIVYHUB_AUDIO_CODEC=opus`.
  The user manager has none, and `systemctl --user cat` shows eight `Environment=` lines.
- **The companion's Opus line** is written at the first Opus stream start, not at boot (`AudioCodec.prepare`, once
  per process): `opus 128 kbit/s, 10-ms frames, libopus 1.5.2` at 01:52:03Z (`journal_codec_lines.txt`). At boot it
  logs nothing, as the flag value is valid.

## 2. The tools (each a small patch, listed; `tools.diff`, `predecessors/`)

| file | change |
| --- | --- |
| `tools/e1_suite.py` | `AUDIO_CODEC = "PRIVYHUB_AUDIO_CODEC=opus"` in `ADOPTED` (eight). Its preflight checks the eighth drop-in (`drop_in_audio_codec`) and requires it in `ok`. Every `flags_absent` reader and the restart's `want` read `ADOPTED`, so they now mean eight. |
| `tools/e3_state.py` | the docstring only: "eight". It reads `e1_suite.preflight()` and `ADOPTED`, so `--check` follows with no code change. |
| `tools/e1_remote.py` | `preflight_remote(..., adopted=())`: the two overlay flags plus the adopted set the callers pass (`getattr(E, "ADOPTED", ())`). A missing line refuses, naming it. |
| `tools/test_e1_remote.py` | +1 test: the adopted set required, the refusal names the missing line. |

- **Readers left as they are, listed:**
  - The detached drivers' `"adopted7 ok"` strings live only in past evidence directories:
    `g8_s1_2026-10-16/g8_s1_driver.py:162`, `g8_s3_2026-10-17/g8_s3_driver.py:184`,
    `g4_s2_2026-10-17/g4_s2_driver.py:158-160`.
  - Those are records under their own manifests, so they were not edited. A future driver should print
    `len(E1.ADOPTED)`.
  - Each driver's `ok` comes from `E1.preflight()`, so a copy run today would check eight lines and only print
    "adopted7".
  - `tools/d7_regression.py` and `tools/c3_l4_nft_night.py` `ADOPTED_E3` still list four lines, stale since G-A1
    (CURRENT.md). They were not run or changed.
- **Tests** (`tests.txt`):
  - `test_e1_remote` 21 OK (+1);
  - `test_c3_l4_nft_night` 33 OK;
  - `e1_suite.py --self-test` OK;
  - overlay 17, session_identity 88, audio_codec 20 OK.

  No file in `logs/` was written by them.
- **`--check` on eight lines** (`check_after_tools.json`): ok, APK CONFIRMED, `drop_in_audio_codec` true,
  `e3_dropin_absent` true.

## 3. The confirmation run (`runs/E1-PS1-STREAM/run1`; `g_a2_analysis.py` → `g_a2_verdict.json`)

- **The run:** one E1-PS1-STREAM `--e2 --window 600` on the LAN, the plan without a flag field
  (`E1-PS1-STREAM:1:120`): **no `e3_flag.conf` at any point.** The drop-in directory held the eight adopted files
  only.
- PLAYING at 01:52:12Z (5.1 s; the suite's stream-start wait `attempt: 2`). Window 01:53:42-02:03:42Z.
- At teardown, `flags_absent` true: the eight lines, no `e3_flag.conf`.
- **Valid** (`validity.json`):
  - `token_issued` at **`sig_v` 3, `audio_codecs` opus** (01:51:57Z; `audit_run.jsonl`);
  - the companion's `opus 128 kbit/s` line;
  - **347 heartbeats `audio_codec=opus`, 0 `pcm`**;
  - the report's `codec: opus`;
  - no refusal.

  Opus was on by the drop-in alone.

| | **G-A2 (adopted, no flag file)** | CL-B5 B (Opus, flag file) | CL-B5 L (Opus) | CL-B5 A (PCM) |
| --- | ---: | ---: | ---: | ---: |
| RetroArch / capture / dup+drop (gates) | **59.999 / 59.999 / 0.10** ✓ | 59.999 / 59.998 / 0.10 | 59.999 / 59.999 / 0.10 | 59.999 / 59.998 / 0.10 |
| `flags_absent` after (gate) | **true** ✓ | true | true | true |
| **underruns** (session / heartbeat window) | **78 / 50** | 11 / 7 | 13 / 10 | 19 / 17 |
| net audio loss | **1 frame = 10 ms** (0.9 ms/min; 63 recovered) | 300 ms | 280 ms | 135 ms |
| decode queue depth max / wait max / drops | 36 / 166.8 ms / 0 | 19 / 185.5 ms / 0 | 20 / 86.5 ms / 0 | — |
| decode call avg / max | 3.13 ms / 57.3 ms | 3.16 / 102.3 | 3.14 / 45.5 | — |
| queue residence avg / max | 57.7 / 100 ms | 57.5 / 145 | 58.1 / 94 | 65.3 / 106 |
| stale drops / concealed underruns / prolonged starvation | 1,543 / 1,515 / 161 | 1,001 / 953 / 120 | 845 / 840 / 103 | 868 / 869 / 110 |
| decoder spikes ≥ 20 ms per min / ≥ 50 ms (session) | **163.1 / 138** | 144.0 / 51 | 136.7 / 34 | 100.4 / 54 |
| max output gap (report) | 351 ms | 227 | 310 | 180 |
| host ctrl gaps > 1 s / max | **2 / 1,234 ms** | 0 / 981 | 1 / 1,007 | 0 / 694 |
| video loss / min; rendered fps | 24.2; 59.69 | 25.2; 59.85 | 48.5; 59.85 | 19.9; 59.88 |
| **eno1 tx kbit/s / packets/s** | **8,994.2 / 1,176.6** | 9,003.5 / 1,178.2 | 9,005.6 / 1,178.2 | 11,913.0 / 1,378.9 |
| host CPU %; companion / encoder % of a core | 9.90; 21.05 / 36.30 | 10.10; 21.25 / 36.76 | 11.07; 21.33 / 36.68 | 10.29; 24.76 / 36.18 |
| the onn's thermal status (report) | 0 throughout | 0 | 0 | 0 |

- **The wire is as expected:** ~9,000 kbit/s and ~1,180 packets/s at 7000, which is −2,918.8 / −202.3 against
  CL-B5 A (not paired).
- **The listen: no listen.** No line came from the user during or after the window (`user_report.txt`).

## 4. Read plainly

- **The adoption works:** Opus is on by the drop-in alone, signed and audited, and the saving holds.
- **The client side was worse than in any CL-B5 Opus run.** Underruns 78 (50 in the window), the ≥ 50-ms decoder
  spikes ~3×, the max output gap 351 ms, and two > 1-s host control gaps, while the net audio loss was ~0 and the
  video loss ordinary.
  - That points at the onn, not the path, but it is **not located.** The onn reported thermal status 0 throughout,
    and its CPU was not read (adb only for state reads).
  - **Where the underruns sit:** the report's tick series (its first 400 ticks) has one burst of 22 at ~11 s,
    during start-up and before the window, and a handful of 1-2 elsewhere. The rest of the 78 fall outside the
    series' span.
  - **It does not repeat:** CL-B5 B and L (11 and 13) ran 2-2.5 h earlier, the same APK, the same codec. This is a
    single run.
  - The onn had run five stream sessions since 22:00Z. A long-uptime client-side effect is a candidate, not shown.
- **Not a gate here** (D-BASE-P10's ≤ 20 is the number of interest). The user decided the adoption, and this
  record does not undo it.
  - **To go back to PCM:** see §5.
  - **Proposed, not run:** a repeat of the paired A/B after an onn restart, or the next sessions' underruns
    watched (the E1 row reports them).

## 5. The PCM fallback, and an old client

- **With the drop-in present, an old client** (any APK before CL-B4, or a client with `identity_v2` off: no
  `audio_codecs` declared) **is refused at stream start, with the reason**: "audio codec opus is required by this
  host (PRIVYHUB_AUDIO_CODEC) and the client did not declare it in session/setup".
  - Nothing is stopped or spawned first (G4-W2 §3). It fails closed: it never gets Opus datagrams it would drop
    as silence.
  - The onn runs `043891e1…` (it declares Opus under `sig_v` 3), so it is not affected.
- **Turning Opus off:**
  1. Delete `~/.config/systemd/user/privyhub-companion.service.d/audio-codec.conf`.
  2. Run `systemctl --user daemon-reload && systemctl --user restart privyhub-companion`.
  3. Take `AUDIO_CODEC` out of `tools/e1_suite.py` `ADOPTED` (back to seven), so the preflights expect seven
     again.

  The client then gets PCM 2/4 as before.
- Also written for the user in `docs/REMOTE_TRUST.md` §9.

## 6. State at the end (02:05Z)

- **The eight adopted lines only; no `e3_flag.conf`; no game; APK `043891e1…` CONFIRMED; `--check` ok**
  (`check_end.json`).
- One device paired (`client_end.json`). After the teardown restart, the client set up at `sig_v` 3 / opus
  (02:03:59Z).
- Nothing committed (`logs/g_a2_git_status.txt`).

## 7. Files

**`g_a2_2026-10-19/`:**
- the run's context: `baseline_head.txt`, `git_status_at_start.txt`;
- the drop-in: `audio-codec.conf`, `audio_codec_dropin_sha256.txt`, `dropin_written_at.txt`, `restart_at.txt`,
  `environ_after_adoption.txt`, `companion_opus_line.txt` (empty at boot, by design; the line is in
  `journal_codec_lines.txt`);
- the code: `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`, `tools.diff`, `tests.txt`;
- the `check_*.json` readings and the `client_*.json` reads;
- the run: the pre-registration, its hash and the time it was hashed; `runs/`, `runs_console.log`,
  `audit_offset_before_run.txt`, `audit_run.jsonl`, `journal_codec_lines.txt`, `user_report.txt`;
- the analysis: `g_a2_analysis.py`, `g_a2_analysis_console.json`, `g_a2_verdict.json`, `validity.json`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.

**Elsewhere:** patch `patches/G-A2_OPUS_ADOPTED.md`; `docs/REMOTE_TRUST.md` §9; `docs/CAPABILITY_MODEL.md` (the
wire-rate note); ROADMAP §G4; `KNOWN_ISSUES.md`; `CURRENT.md`; `logs/g_a2_git_status.txt`.

No sudo (only `systemctl --user`), no nft, the Opal untouched, adb only for state reads, nothing fetched, nothing
deleted.
