---
memory_schema: 1
as_of: 2026-09-19
baseline_commit: 41bbc6acd3534f79283e328596115a02c3acc296
durable_memory_updated: true
---

# C3-L3R1 — characterization correction and memory sync

## Purpose

The `C3.L2c` / `C3.L3` work of 2026-09-19 left durable memory stating that
run 3's 6000 kbps characterization result was invalid and a rerun was owed.
The rerun had already been taken, was valid, and was on disk when that text
was written. The omission inverted the item's conclusion.

This patch corrects the record, promotes the `C3.L2c` result from its install
record into an evidence record, and brings the files that session did not
touch — `roadmap/STATUS.md`, `MEMORY.md`, the dated record — current.

Durable memory only. No source change, no probe change, no tool change.

## Expected predecessor

`41bbc6acd3534f79283e328596115a02c3acc296`

Per-file SHA-256 is enforced by the installer.

## What was wrong

1. **The 6000 kbps rerun was omitted.** `evidence/C3_L3_..._2026-09-19.md`
   and `CURRENT.md` were written at 06:05 UTC; the rerun finalized at 06:03
   and wrote `logs/streaming/c3_fixed_6000_characterization.json`. The
   handoff, written at 06:09, does reflect it — so memory contradicted
   itself.

2. **The conclusion inverted.** Judged on two samples, 6000 kbps "could not
   be placed with confidence" and 5000 kbps read as the most consistent
   bitrate. With the third sample (307 ms), the `decoder_max_output_gap_ms`
   bands are 5000 kbps 242-367 (125 ms), 5500 kbps 219-584 (365 ms), 6000
   kbps 291-331 (**40 ms**). 6000 kbps is the most consistent.

3. **The decoder-session file was misidentified.**
   `native_decoder_20260919_055703_163.json` was described as "a fresh
   decoder-session file consistent with a real, separate 6000 kbps play
   session ... written 18.8s before the 6000 finalize ran". It is the 5500
   kbps session — 66,638 ms, `max_output_gap_ms` 335, matching the 5500 kbps
   row exactly — and it was written 391 s before the 6000 kbps finalize. It
   is the file the buggy attempt wrongly picked up. The valid 6000 kbps
   session is `native_decoder_20260919_060325_369.json`, 64,840 ms, named by
   the probe itself in `payload.decoder_session_log`, written 9.4 s before
   its finalize.

4. **The finalize defect was overstated as deterministic.** The rerun, in
   the same back-to-back sequence, matched correctly. The defect is
   intermittent and stays open; the data was never lost.

5. **`CURRENT.md` asked for a run that had happened**, and was 13,378 bytes
   against a 10 KB soft limit, carrying implementation narrative that belongs
   in a patch record.

6. **`roadmap/STATUS.md` and `MEMORY.md` were not updated at all** by the
   `C3.L2c`/`C3.L3` session. `STATUS.md` still named `C3.L2c` as the active
   item needing authorization.

7. **No evidence record existed for `C3.L2c`.** Its result lived only in the
   install record, against project practice.

8. **No dated record existed for 2026-09-19.**

9. **`PATCH_INDEX.md` was stale**, missing
   `C3-L3_LINUX_FIXED_BITRATE_PORT.md`. Regenerated here.

## Changed scope

Replaced:

- `docs/memory/evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md`
  — run-3 section corrected in place, rerun added, three-run table and
  reading re-derived, correction notice at the head;
- `docs/memory/CURRENT.md` — work item closed, `C3.L3` and `C3.L2c` results
  recorded, stale Next Action removed, trimmed 13,378 -> 8,856 bytes;
- `docs/memory/handoffs/CURRENT_HANDOFF.md` — finalize defect scoped to the
  one attempt, `C3.L2c` numbers strengthened, `C3.L4` gate restated;
- `docs/memory/PHASE_C_CONTEXT.md` — sub-phase table, new section 6a for
  `C3.L3`, the `max_codec_ms` proxy lesson, the finalize defect in open debt;
- `docs/memory/MEMORY.md` — two durable-fact blocks added;
- `docs/memory/roadmap/STATUS.md` — brought current;
- `docs/KNOWN_ISSUES.md` — finalize-bug entry corrected and scoped; the
  decoder-time entry updated, since `C3.L2c` is no longer its owner.

Added:

- `docs/memory/evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md`;
- `docs/memory/2026-09-19.md`;
- this record.

Generated: `docs/memory/patches/PATCH_INDEX.md`.

Unchanged: all source, all tools, all probe scripts, every other memory file,
the roadmap's sequencing. No work item is unblocked by this patch.

## Where the numbers came from

Every figure was re-derived from raw files, not transcribed from the
summaries being corrected:

- `logs/games/decoder_sessions/native_decoder_20260919_060325_369.json` —
  the valid 6000 kbps session: `duration_ms` 64,840,
  `decoder.max_output_gap_ms` 307, `decoder.max_rx_to_decode_ms` 316,
  `decoder.rendered_frames` 3,651, `decoder.dropped_frames` 19,
  `video.sequence_resyncs` 1, `video.ssrc_changes` 1,
  `video.lost_packets` 26, `video.fec_recovered_packets` 2,
  `video.fec_unrecoverable_groups` 0,
  `video.packets_dropped_waiting_for_idr` 0, `video.resync_to_idr_ms` 26;
- `logs/streaming/c3_fixed_6000_characterization.{json,txt}` — the finalize
  result and `payload.decoder_session_log`;
- `logs/games/decoder_sessions/native_decoder_20260919_055703_163.json` —
  identified as the 5500 kbps session, 66,638 ms, gap 335;
- `logs/games/decoder_sessions/native_decoder_20260919_04*.json` and
  `_03*.json` — the eight-session low-latency comparison, each parsed for
  `low_latency_enabled`, `max_codec_ms`, `max_output_gap_ms` and the spike
  histogram.

## Negative results

- Memory written from a session's own narrative rather than from the files
  on disk inverted a conclusion. The evidence file, `CURRENT.md` and the
  handoff disagreed with each other for four minutes and then stayed that
  way. The standing rule — prefer current local source and fresh measured
  evidence over summaries — is exactly what would have caught it.
- The `C3.L2c` result being recorded only in a patch record is the same
  failure in a smaller form: an install record is not an evidence record,
  and a future session looking under `evidence/` would have found nothing.
- The finalize matching defect is **not** root-caused here. It is scoped and
  given a workaround, nothing more.
- `PATCH_INDEX.md` drifted because a patch record was added without
  regenerating it. The installer's usual pre-check requires the index to
  match a fresh generation; that check would have rejected this patch before
  modification for a defect it is meant to fix, so for the index only it is
  relaxed to a post-write check. Content files keep strict wrong-state
  rejection.

## Validation performed

- installer Python compile;
- payload and installed SHA-256 verification per file;
- predecessor SHA-256 enforced per file, with wrong-state rejection before
  any modification;
- generated index regenerated and verified against a fresh generation after
  writing;
- LF line endings and trailing newline asserted on every written file;
- `tools/check_memory_health.py` executed as a post-write gate, with
  exact-byte rollback on failure;
- `CURRENT.md` re-measured under both soft limits (8,856 bytes, 168 lines)
  and `CURRENT_HANDOFF.md` under its own (7,499 bytes);
- ZIP integrity.

**Deliberately not performed:** no self-test, no synthetic fixture, no
sandbox install. Tier 1 per `patches/PATCH_PROTOCOL.md`. The predecessor
hashes and the health gate decide it on the user's machine.

No runtime validation applies; this patch changes no executable behavior.

## Privacy

No network addresses appear in this patch or in any file it writes.

## Result

Recorded on install.
