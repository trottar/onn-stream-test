---
memory_schema: 1
as_of: 2026-10-24
status: TASK HANDOFF — G-A4 (session A, ~20 min, unattended): the user's adoption of `PRIVYHUB_LINK_RECOVERY=1` as the TENTH adopted line (the user's decision 2026-10-24, "Adopt", after CL-B12). B's prepared patch applied, the drop-in written, the restart, `--check` ok on ten, one 10-min LAN confirmation window with every client property empty. Nothing else adopted; nothing committed. The user leaves for an off-site session afterwards (G4-S4, a separate prompt) — this must be closed, both units collected, before that
---

# G-A4 — the tenth line

Read first: `patches/G-A4_LINK_RECOVERY_ADOPTION_PREPARED.md` (B20: the diff, `link-recovery.conf`, `ADOPTED` to ten, `drop_in_link_recovery`), `G_A3_LINK_REPORT_ADOPTION_2026-10-23.md` (the adoption form; the two-command drop-in write), `CL_B12_DEFAULTS_AND_UMBRELLA_2026-10-24.md` §5 (the costs; the `link_recovery_config` log defect — **not fixed here**, B's), `LINK_N1_LAUNCH_2026-10-23.md`.

**The user's decision (2026-10-24, verbatim "Adopt").**

1. Precondition: nine lines, `--check` ok (APK `20e3e339…` CONFIRMED), no `e3_flag.conf`, no game, one device paired, no `privyhub-*` unit but the companion and `privyhub-link-n1`, HEAD named (CL-B12 committed), the tree clean but the prompt and this file, the clock outside 04:30-05:30Z, the band 5 GHz, the seven client properties empty.
2. `git apply` the prepared diff (`--check` first); `e1_suite --self-test`, `test_e1_remote`, `test_c3_l4_nft_night`, `tests/link_recovery` green from the tree; **`~/.config/systemd/user/privyhub-companion.service.d/link-recovery.conf`** with `Environment=PRIVYHUB_LINK_RECOVERY=1` (written with the file tool; `daemon-reload` and the restart as a separate command, as G-A3); the environ read back **ten lines**; `--check` ok on ten with `link_recovery.stack` all six `implied 1`.
3. The confirmation window, pre-registered and hashed first: one E1-SNES-STREAM `--e2 --window 600`, **no `e3_flag.conf`, no property set**: `link_recovery_config` and the six module config rows by the drop-in alone; the host gates; 0 `state_saved` and 0 holds outside a real stall (the pad untouched: none expected); silences and hitch s / 10 min on 5 GHz; the teardown's bye and `state_save_skipped`; `flags_absent` after; ten lines; `--check` ok.
4. `evidence/G_A4_LINK_RECOVERY_ADOPTION_2026-10-24.md` + dir (the patch as applied, the drop-in copy, the tests, the window, the redactor, `manifest.sha256`); ROADMAP §G4 / `REMOTE_TRUST.md` where the adopted lines are listed (how to turn it off: delete `link-recovery.conf`, `daemon-reload`, restart; the client halves off with `setprop debug.privyhub.stall_signal 0` / `restart_guard 0`); `logs/g_a4_git_status.txt`; `CURRENT.md`: **the adopted state is TEN lines** (list them). Both units collected; exit.

No sudo, no nft, the Opal read-only, adb for state reads only, no addresses or identifiers; nothing fetched, nothing deleted; nothing but the tenth line adopted; nothing committed.
