---
memory_schema: 1
as_of: 2026-10-06
status: TASK HANDOFF — E3-S6, queue B item 2 (the user's go, 2026-10-06): the per-grab parse of the 25.6 MB guide-metadata file inside the companion. A discriminating probe (parse-only vs spawn-only against a live stream), then one change behind a flag: a cached slim channel → source index built once per metadata change. Benchmark E1-META ×2 and E1-CONC ×2 with the flag, E1-PS1-STREAM ×1 as the control. Nothing adopted; nothing committed
---

# E3-S6 — the guide-metadata parse: a cached slim index

**Measured bottleneck (E3-S2 §1, E3-S1 §4).** Every forced refresh
parses the whole 25.6 MB guide-metadata file in the companion's own
Python process (`_fetch_guides_metadata`, `json.loads`): a 147 MB traced
peak, live for the whole grab in a back-to-back cycle. The companion's
stream threads are Python threads in that process. E1-CONC's loss peaks
1 s after each grab starts and did not move when the grabber's CPU was
taken away (E3-S1).

**Narrow hypothesis.** The parse, not the grabber child, is what the
stream feels at each grab's start (it holds the GIL and the memory); a
slim index of what the grab actually needs (channel → source
candidates), built once and reused while the metadata file is unchanged,
removes both the ~110 MB step and the +1 s loss peak.

Read first: `evidence/E3_S2_COMPANION_GUIDE_RETENTION_2026-10-06.md`,
`e3_s2_2026-10-06/probe.md` and `mem_probe.sh`, the probe hook
(`/plugins/epg/memprobe`, `PRIVYHUB_MEM_PROBE=1`),
`evidence/E3_S1_EPG_GRAB_PRIORITY_2026-10-06.md` §4,
`e2_s1_2026-10-05/e2_analysis.py` (the CONC alignment),
`companion/plugins/epg.py`.

## 1. Probe: which half of a grab hurts the stream (before the change)

Extend the dormant probe hook with two operations, served only with
`PRIVYHUB_MEM_PROBE=1`: **`parse`** (run `_fetch_guides_metadata` and
discard the result; no child) and **`spawn`** (run the grabber child
for one channel with a source list prepared beforehand; no parse). With
a PS1 stream PLAYING, the per-second sampler on, trigger each operation
≥ 20 times at ≥ 15-s spacing (parse first, then spawn, then parse
again), and align lost packets/s and the busiest core on the trigger
times as `e2_analysis.py` does for grab bodies.

**Reading rule, written here:** an operation "reproduces the peak" if
its mean lost packets/s at offsets 0-2 s is ≥ 3× the stream's baseline
loss/s (the same window, outside triggers). The probe names **parse**,
**spawn**, **both** or **neither**; also report the parse's wall and CPU
time and the companion's PSS step. `e3_s6_<date>/probe.md`.

## 2. The one change

Behind **`PRIVYHUB_EPG_GUIDE_INDEX=cached`** (absent = today's parse,
byte for byte): the plugin keeps a slim index (per channel id: the
ordered source candidates and whatever else the grab's candidate loop
reads — nothing more) built from the metadata file **once**, keyed by
the file's size + mtime (+ sha256 if cheap), rebuilt only when that key
changes, and the candidate loop reads the index instead of the parsed
list. The index is held in-process (it should be ≤ a few MB; record its
size) and may also be written beside the metadata file as JSON for the
next start. The grab's arguments, the child, the status and the refresh
endpoint's contract are unchanged.

## 3. Pre-registration (hashed before any benchmark run)

- **Runs, in order, E2's windows and gaps:** E1-PS1-STREAM ×1 (no flag;
  the control), E1-META ×2 (flag), E1-CONC ×2 (flag). Drop-in for the
  flagged runs only; removed at each teardown; environ checked.
- **Comparability (else INCONCLUSIVE for the CONC clauses only):** the
  control within E1's bands of E2's PS1-STREAM (host CPU 11.7 ± 2;
  rendered 59.81 ± 0.5).
- **Bar — the memory half, ACCEPTED only if all hold in both META runs:**
  - (a) companion PSS at the window's end ≤ **60 MB** and not "keeps
    growing" (E3-S2's rule, ≤ 5 % over the last 15 min);
  - (b) grabs failed 0, ok ≥ 205, median grab ≤ 1.3× E2's (≤ 6.8 s);
  - (c) the guide still serves: 6 channels, programme count within ± 5 %
    of a pre-run read, and the grab's source candidates per channel
    identical to today's (dumped from both paths in the smoke, diffed);
  - (d) host CPU ≤ E2's META + 2 (≤ 11.8).
- **Bar — the stream half, gated only if the probe named `parse` or
  `both`, otherwise reported; ACCEPTED only if all hold in both CONC runs:**
  - (e) video loss/min ≤ 100 and ≤ 3 × the control's;
  - (f) rendered ≥ 59.5; resyncs ≤ 10 per run;
  - (g) the aligned frame: mean lost packets/s at offsets 0-2 s after
    each grab ≤ 3× the control's baseline loss/s.
- The two halves get separate verdicts in the record (**memory:
  ACCEPTED/REJECTED; stream: ACCEPTED/REJECTED/REPORTED/INCONCLUSIVE**).
  One change, two measured effects — said here before the data.
- **Reported:** the index's size and build time; the companion's PSS per
  minute; the aligned 0-10 s frame for both CONC runs; the busiest
  core; grabs ok/failed and median grab; the EPG child's cost (unchanged
  expected).

## 4. The runs, the record

A flagged smoke first (one forced refresh of each of the six channels;
the candidate dump for clause (c)). Then the runs with the hash checked.
Record `evidence/E3_S6_GUIDE_INDEX_<date>.md` + `e3_s6_<date>/` (the
probe and its aligned tables, the pre-registration + `.sha256`, the
diff, the candidate dumps, 5 runs, `manifest.sha256`, `--check`, the
table and verdict JSON, `redact_check.txt`): both verdicts, the one-line
adoption (`Environment=PRIVYHUB_EPG_GUIDE_INDEX=cached`) and its revert,
and what the probe said about where the CONC loss comes from, whichever
way the runs went. `patches/E3-S6_...md`; `logs/e3_s6_git_status.txt`.
Flag absent; E2's final state restored; then the queue's close.
