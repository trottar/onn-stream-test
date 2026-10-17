---
memory_schema: 1
as_of: 2026-10-17
status: TASK HANDOFF — G5-S3/S4 LAN smoke (session A): one 10-min PS1-STREAM on the LAN with `PRIVYHUB_REMOTE_LADDER=1`, `PRIVYHUB_REMOTE_RUNG_CAP=4000` and `PRIVYHUB_WAN_TELEMETRY=1` in the drop-in — the first live run of B's G5-S3 and G5-S4 code. The expected result is "nothing changes on the LAN": `path_class` reads `lan`, no 4000, the cap logs no effect. Host gates; everything else reported. Flags removed at teardown. Nothing adopted; nothing committed. Session B starts only after this session exits
---

# G5-S3 / G5-S4 — the LAN smoke

Read first: `G5_S3_REMOTE_LADDER_2026-10-17.md` (what the flag does; `path_class`; the remote-only 4000; what is "pending on the stream"), `G5_S4_REMOTE_RUNG_CAP_2026-10-17.md` (the cap needs G5-S3; no effect on the LAN, logged once), `CL_B3_…` §R1/§W (the reference LAN run and the telemetry flag's cost), E4-S2's constraint discipline.

## 1. Pre-registration (hashed before the run)

- **Run:** `tools/e1_suite.py run --e2 --window 600`, one E1-PS1-STREAM, E2's warm-up, an idle gap of 120 s, `e3_flag.conf` carrying exactly `PRIVYHUB_REMOTE_LADDER=1`, `PRIVYHUB_REMOTE_RUNG_CAP=4000`, `PRIVYHUB_WAN_TELEMETRY=1`; written, read back under load (ten environ lines), removed at teardown with `flags_absent` true.
- **Validity:** E3-A3B's reading (PLAYING; replaced ≤ 2× if not).
- **Gates (host):** RetroArch ≥ 59.9; capture 60 ± 0.1; dup+drop ≤ 0.2/min; `flags_absent` after.
- **Expected and checked, reported as met / not met (not gates — a miss is a finding about B's code, written up, nothing else):**
  1. every `decisions.jsonl` row carries `path_class: lan` (G5-S3: the games plugin's routing class reached the ladder, and it is `lan` on the LAN);
  2. no actuation to 4000, no `remote_cap` row, and the cap's "no effect on a LAN path" line logged once (G5-S4);
  3. the ladder's rung path as the adopted ladder would do (compare with CL-B3 R1 and the G8-S1 `none` cells: 7000 held unless the link forces a step);
  4. the companion's and the ladder's cost with the three flags vs CL-B3 W (reported).
- **Reported:** loss, rendered, stale, resyncs, the `wan` class, the link's own state tonight.

## 2. Steps

1. Precondition: seven lines, `--check` ok (adb to the onn as before), no `e3_flag.conf`, no game, one device paired, the G8-S1 unit collected; the tree committed (name HEAD).
2. The pre-registration written to `evidence/g5_s3_smoke_2026-10-17/preregistration.txt`, hashed, the hashes of `companion/remote_ladder.py`, `companion/remote_cap.py`, `companion/wan_adaptation.py`, `companion/adaptive_bitrate_live.py`, `companion/plugins/games.py` beside it.
3. The drop-in, restart, read back (ten lines). The run. Teardown: drop-in removed, restart, `flags_absent` true, `--check` ok.
4. `evidence/G5_S3_LAN_SMOKE_2026-10-17.md` + the directory (the suite's output, `decisions.jsonl` read: the `path_class` count, any 4000 or `remote_cap` row, the cap's log line; the gates; the comparison table; `redact_check.txt`, `manifest.sha256`, `validity.json`); `docs/WAN_ADAPTATION_RULES.md` status lines ("LAN smoke done; off-site pending"); ROADMAP §G5; `logs/g5_s3_smoke_git_status.txt`; `CURRENT.md` Next Action (G4-S2 off-site with the flags; G8-S2 from session B). **Exit.** Then the user starts session B.

No sudo, no nft, the Opal read-only, adb only to read state, no addresses or identifiers; nothing fetched, nothing deleted; nothing adopted; nothing committed.
