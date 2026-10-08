---
memory_schema: 1
as_of: 2026-10-07
status: TASK HANDOFF — E3-A2 (the user's authorizations in chat, 2026-10-07: "Adopt frame_spin if you think helps" and, after the look by hand, "Sure it ran smoothly from what I can tell"): adopt E3-S5C's audio sender pacing (`frame_spin`) and E3-S4's Snes9x core as the companion's defaults through their own systemd drop-ins; verify on the suite (PS1-STREAM ×2, SNES-STREAM ×1, META ×1); extend the state checks; TOOLS.md, ROADMAP, CURRENT.md. Nothing else adopted; nothing committed
---

# E3-A2 — adopting `frame_spin` and the Snes9x core

**What is adopted, and why.**

1. **`PRIVYHUB_AUDIO_SENDER_PACING=frame_spin`** — E3-S5C, ACCEPTED on
   its pre-registered bar in all three flagged runs
   (`evidence/E3_S5C_AUDIO_SENDER_PACING_SPIN_2026-10-07.md`): sender
   5.9-6.1 % of a core (today 13), companion 17.5-17.6 % (today 24.5),
   socket −0.5 to −3.7 W, underruns 13 / 9 / 5 against controls 17 / 14,
   no loss burst beyond the controls'. The user's words: "Adopt
   frame_spin if you think helps" — Cowork's reading was yes, stated to
   the user before this task was written.
2. **`PRIVYHUB_SNES_CORE=snes9x`** — E3-S4, ACCEPTED and REPEATABLE
   (`evidence/E3_S4_SNES_LIGHTER_CORE_2026-10-07.md`): RetroArch 8-9 % of
   a core (bsnes 436-517), host 7.4-7.9 % (43-50), ~−6.5 W, 60 fps
   everywhere. **The user looked by hand on 2026-10-07 with the record's
   §4 recipe and said: "Sure it ran smoothly from what I can tell".**
   That look is recorded verbatim and is what decides this adoption;
   nothing perceptual was measured. The core is Snes9x 1.63
   (`9b2b6ea9…7a31`), licence "Non-commercial" — noted to the user
   twice; their call.

Read first: both records and their dirs; `E3_S6A_GUIDE_INDEX_ADOPTION_2026-10-07.md`
(the adoption pattern, the state-check patch); `TOOLS.md` (the drop-ins,
kill switches, "The E3 flags"); `tools/e3_state.py`; `tools/e1_suite.py`'s
`ADOPTED`.

## 1. Precondition

The adopted state as E3-S6A left it (environ exactly `live` + `index`;
no other flag; no game; PS1 files identical; APK CONFIRMED). **If the
user's look drop-in `e3_flag.conf` is still present**, remove it,
`daemon-reload`, restart, and record that in the precondition section —
the user's look is over (their words above). Then `e3_state.py` ok.

## 2. The adoption

- Two **separate** drop-ins in
  `~/.config/systemd/user/privyhub-companion.service.d/`:
  - `audio-pacing.conf`: `[Service]` /
    `Environment=PRIVYHUB_AUDIO_SENDER_PACING=frame_spin`;
  - `snes-core.conf`: `[Service]` / `Environment=PRIVYHUB_SNES_CORE=snes9x`.
  `adaptive.conf`, `epg-index.conf` and the unit file untouched.
  `daemon-reload`; restart.
- Verify: the environ carries **exactly four** `PRIVYHUB_*` lines (live,
  index, pacing, snes core); the manager none; `systemctl --user cat`
  lists four drop-ins; `emulators.json` unchanged (the core comes from
  the flag, as E3-S4 ran it).
- **State checks**: `ADOPTED` in `tools/e1_suite.py` / `e3_state.py`
  gains the two names. **Also** `tools/d7_regression.py` and
  `tools/c3_l4_nft_night.py`, which E3-S6A noted still accept only the
  live default: extend each to the same `ADOPTED` list (the one-name
  extension E3-S6A described), no other change, recorded as a patch.
- **Kill switches** in `TOOLS.md`, one line each: delete the file,
  `daemon-reload`, restart. Absent = today's wait / bsnes, byte for byte.
  The `.so` and RetroArch's `Snes9x/` files stay either way. Note the
  per-core saves (`saves/Snes9x/` vs `saves/bsnes/`).

## 3. Verification on the adopted state (pre-registered, hashed before the runs)

No flag is set for these runs; the adopted defaults run.

- **Runs**: E1-PS1-STREAM ×2, E1-SNES-STREAM ×1, E1-META ×1 (E2's windows
  and gaps).
- **Bar — the adoption stands if all hold; otherwise the failing item's
  drop-in is removed, its state-check name reverted, and the record says
  ADOPTION REVERTED for that item (the other may stand):**
  - PS1-STREAM, both runs: sender ≤ 8 % and companion ≤ 20 % of a core;
    audio underruns ≤ 20; rendered ≥ 59.5; within E1's bands of E2's
    PS1-STREAM (host CPU 11.7 ± 2; rendered 59.81 ± 0.5); D-BASE spikes
    < 200/min, stale < 20/min; loss reported;
  - SNES-STREAM: RetroArch ≤ 150 % of a core; host CPU ≤ 20 %; RetroArch
    ≥ 59.9, capture 60 ± 0.5, rendered ≥ 59.5; the window title names
    Snes9x; (the sender/companion clauses above also hold here — both
    adoptions are live in this run);
  - META: companion PSS at the end ≤ 60 MB; grabs failed 0, ok ≥ 205;
    the guide serves (6 channels; programmes ± 5 % of a pre-run read) —
    the index adoption still holds with the others present.
- **Reported:** socket W per row against E2 and the earlier records;
  the per-minute loss lists; the C2 block; Tctl.

## 4. The record

`evidence/E3_A2_FRAME_SPIN_AND_SNES9X_ADOPTION_<date>.md` + `e3_a2_<date>/`
(the two drop-ins' text, environ before/after, the pre-registration +
`.sha256`, 4 runs, `manifest.sha256`, `--check`, table, verdict,
`redact_check.txt`); `patches/` (the state checks) + `PATCH_INDEX.md`;
`TOOLS.md`; `docs/ROADMAP.md` (E3: three adoptions; the E3 list's
status per item); `investigations/ACTIVE.md`; the daily file;
`logs/e3_a2_git_status.txt`; `handoffs/CURRENT_HANDOFF.md`; the redactor
over everything written; **`CURRENT.md` last** — Verified State: the
four-line adopted environ, the four drop-ins, the core; Next Action 1:
the user's commit; 2: what E3 has left (the CONC grab-spawn share —
E3-S1's and S6's remainder — and the grabber's start-up, both untested
as changes; the user's pick, or E4); 3: E4 after that, with the suite
re-run on the adopted state as its base.

**The final state at the end is the four-line adopted state**; no
other flag; no game; PS1 files identical; APK CONFIRMED. No `nft`, no
real `sudo`, the Opal untouched; nothing fetched, nothing deleted.
