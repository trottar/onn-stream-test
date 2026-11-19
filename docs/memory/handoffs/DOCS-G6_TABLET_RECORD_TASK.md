---
memory_schema: 1
as_of: 2026-11-19
status: TASK — session G6, docs only. Records the tablet track (ROADMAP §G6) in repo memory. Nothing adopted; nothing committed.
---

# DOCS-G6 — record the tablet handheld track in repo memory

The tablet work so far lives only in Cowork's notes in the gitignored `Claude outputs/G6_tablet/`. This task copies it
into `docs/memory/`, checking every number against the raw logs it came from. **Docs only.** It writes nothing
under `companion/`, `PrivyHub/` or `tools/`; it restarts no service; it does not stream, run adb or fetch; it writes
nothing to the drive. It reads the hub's logs without changing them.

## Sources (read first)

- `Claude outputs/G6_tablet/G6_TABLET_PLAN_2026-11-19.md`: Cowork's notes (the G6-S1 result, the conflict audit, the
  portrait-mode summary and the user's decisions).
- `Claude outputs/G6_tablet/inputs/G6_TABLET_PROJECT_HANDOFF_2026-11-19.md` and
  `…/inputs/G6_PORTRAIT_INVESTIGATION_HANDOFF_2026-11-19.md`: the user's two briefs, verbatim. Both name an `L:` path.
  The user said to ignore it: the hub's repo is the one.
- Raw: `logs/session_audit.jsonl` (2026-11-19 03:52Z–04:28Z rows), `logs/games/native_stream_recovery.log`
  (sessions 8, 9, 10), `logs/games/decoder_sessions/native_decoder_20261119_035242_129.json`, `…_041013_681.json`,
  `…_042818_218.json`.
- `docs/ROADMAP.md` §G6 and the G9 checkpoint row 10 ("handheld … explicitly pending").

## Rules for every file written

- **Privacy.** No IP, MAC, SSID, BSSID, serial, account, token, `token_ref` value or pairing code. A device id appears
  as its first 4 hex digits and "…" (`dev-954a…`). Run the repo's redaction check over every new file.
- **Ids.** The user's T1–T6 are recorded as **G6-S1 … G6-S6**, because `T1`–`T3` are D-BASE findings and `T88`/`T89` are
  game codes. The portrait stages are **G6-HM1 … G6-HM6**. Cells are never bare `C<n>`. No game title appears in any
  record: the game (title redacted in this copy) is `T88`.
- **Labels.** What was read in code or logs is "verified". What is planned is "proposed". Nothing perceptual is a cell.
- **Public repo.** The user's Claude doc link stays out.

## Steps

0. `git status --short` → `logs/g6_docs_status_before.txt`. Other sessions' uncommitted files may be there: touch none
   of them, and list them in the reply.
1. **Copy in** the task, the two briefs and the notes. This file goes to `docs/memory/handoffs/DOCS-G6_TABLET_RECORD_TASK.md`;
   the briefs go to `docs/memory/handoffs/` under their own names. Each brief gets one first line saying the `L:` path
   is not used and the hub's repo is authoritative (the user, 2026-11-19). The briefs are not otherwise edited.
2. **The G6-S1 record**, `docs/memory/evidence/G6_S1_TABLET_FIRST_INSTALL_2026-11-19.md`. Write it from the notes, but take
   every value from the raw files.
   - The install: the CONFIRMED APK `ca53df0d…`, sideloaded with no adb anywhere.
   - What worked: launch, catalog, touch navigation and a movie (the user's words).
   - The two refused tries: `legacy_setup` rows, no `session_started`, `client_frame` 0, and `host_metadata_error`
     ("audio codec opus is required … did not declare it in session/setup").
   - The pairing: two windows, two `pairing_ok`, and the token issued with `audio_codecs: opus`.
   - Session 10: decoder name, frames, fps, lost and dropped, FEC, IDR, first output, receive-to-decode, Opus, and the link
     notice.
   - The open item: the stale first tablet pairing (`dev-c320…`) in the store, whose removal waits for the user's word.

   Put redacted excerpts and the decoder reports' summary fields in `docs/memory/evidence/g6_s1_2026-11-19/`, with a
   `sha256` manifest.
3. **The plan**, `docs/memory/architecture/G6_HANDHELD_PLAN_2026-11-19.md`:
   - the track, G6-S1 to G6-S6 with each step's aim;
   - the conflict rules from the notes: the tablet never on the hub's adb, because `e1_suite.py` and `c3_l4_nft_night.py`
     call bare `adb`; the prompt file `_cowork_prompt_g6.txt`; G6 runs at secondary priority and never alongside another
     session's run;
   - the portrait-mode result, the decisions (D2: the touch pad is P1 after 5 s with no P1 long-press join; D3: PS1 first;
     D4: keep the fill; D1 partly settled), the open points, and G6-HM1 to G6-HM6, none started.
4. **`docs/ROADMAP.md` §G6**: add a dated status block under the section. G6 opened 2026-11-19 with the SM-P610;
   G6-S1 met; the next steps; the plan file. Do not edit the G9 checkpoint table, which is a record.
5. **`docs/REMOTE_TRUST.md` "Legacy" bullet**: add one sentence. Since G-A2 requires Opus, an unpaired legacy-LAN client
   can browse and play VOD but cannot start a game stream; a new client is paired first. Point to the G6-S1 record.
6. **`docs/memory/MEMORY.md`**: three settled findings, placed by the file's own structure:
   - the legacy path cannot stream games since G-A2;
   - B70's pointer guard consumes the touchscreen during a game;
   - a second adb device on the hub breaks the bare-`adb` tools.
7. **`docs/memory/CURRENT.md`**, keeping its fixed headings:
   - one Active Objective line: G6 OPEN at secondary priority;
   - in Verified State, replace "One device is paired" with the three paired devices (the onn, the tablet, the stale
     tablet pairing awaiting removal), and add that the tablet runs the CONFIRMED APK unchanged;
   - one Next Action item for G6, placed after the existing ones;
   - in the open list, "the handheld (pending)" becomes "the handheld (G6 open)".
8. **`docs/memory/handoffs/README.md`**: rows for the three new handoff files in its index table, in its own format.
9. **Gates**:
   - `tools/check_memory_health.py` passes;
   - `git diff --check` is clean;
   - the redaction check is clean on every new or changed file;
   - `git status --short` shows nothing outside `docs/` and `logs/` from this task.

   Write `logs/g6_docs_git_status.txt` with this task's files only.

Your last reply begins "YOU, now: commit". Then one line each: the files written, the numbers re-read that differ from
the notes (or "none"), the gates, and other sessions' files left untouched. Nothing adopted; nothing committed by you.
