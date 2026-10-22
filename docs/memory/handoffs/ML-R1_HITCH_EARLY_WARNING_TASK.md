---
memory_schema: 1
as_of: 2026-10-22
status: TASK HANDOFF — ML-R1 (session A, overnight, unattended, offline compute only: NO companion restart, NO stream, NO adb, NO edit under companion/ — session B is editing it): the month of logs turned into one per-second feature table, labelled with UX-R3's hitch definition, and a learned early-warning detector ("a hitch is coming within 1-3 s") trained and evaluated on held-out sessions, compared against the hand rules (LAN-R1's T 4 / K 2; the hold's silence threshold). A detector, not a controller. Nothing adopted; nothing committed
---

# ML-R1 — the hitch early-warning detector, from the month on disk

**Why this and not a learned ladder:** the data holds almost no examples of stepping down under loss (the ladder never did), so a policy cannot be learned from it; it holds thousands of labelled seconds, so a *detector* can. If the detector beats the hand thresholds at the same false-alarm rate, it becomes the trigger behind a flag later (session B's work; A's measurement) — not here.

**The user's standard (verbatim):** "This product needs to work at any house especially lan as long as the Internet is over 50mb/s."

Read first: `UX_R3_FIND_THE_DEATHS_2026-10-21.md` §1 (the hitch definition R / C / G / L and its script `ux_r3_seconds.py` — reuse it for the labels, unchanged), `BENCH_R1_…` §2-§4 (the eight cells; cells 1 and 8 as clean references; the room's own gaps), `LAN_R1_…` §2 (the T 4 / K 2 rule, its false-trigger table), `B2_INPUT_HOLD_…` (the 250-ms silence), `MEMORY.md` (which logs exist and their resolutions; LOG_KEEP 3), `docs/memory/evidence/*/runs/**` (every suite run's logs on file), `logs/games/stream_log_archive/`.

## 0. Setup (before the unit)

- `python3 -c "import numpy, sklearn"` — state what is present. **Nothing is fetched.** If scikit-learn is absent: logistic regression in numpy (gradient descent, L2) and a small hand-written gradient-boosted-stump ensemble, or trees omitted with a note; if numpy is absent, stop and write it (the user installs by hand).
- The unit: `systemd-run --user --unit=privyhub-ml-r1 --collect -p Nice=10` running `ml_r1_2026-10-22/ml_r1_pipeline.py`; status file `~/privyhub_ml_r1/status.txt`, `STOP`, **cap 6 h, written in the pre-registration**. Code launches, confirms the inventory stage finished, exits; the record is tomorrow's one-line task (or this task's if the pipeline finishes within Code's own patience, ≤ 45 min of polling).
- **Pre-registration, hashed before training:** the label, the splits, the metrics, the comparison rules, the acceptance bar below — written before any model sees the data.

## 1. The inventory and the table

- **Every session on file since 2026-09-20** with a heartbeat log and a control-gap log (the two the hitch label needs): the evidence copies (`ux_r1/r2/r3`, `bench_r1`, `g8_s1`…`g8_s5`, `cl_b5/6/7`, `g4_s1/s2/s3`, the G5/C3/D-BASE directories, every `runs/**/logs_run1/`), plus the live `logs/games/*` and `stream_log_archive/*`. One row per session: span, system / core, title if known, codec, impairment profile if any (the shim cells), player present or attract, the flags in force, the source paths. **Sessions whose gap log is missing are listed and excluded from the labels** (the heartbeat alone cannot score C).
- **The per-second table** (`features.parquet` or `.npz` + `features_columns.txt`), one row per UTC second per session, **features from the host's view only and only from the past** (nothing in a row is later than its second): the heartbeat interval's rendered frames / fps, post-FEC loss, FEC-recovered, unrecoverable groups, underruns, concealed, prolonged starvation, audio arrival gap max, output age; the control-gap log's count and max of gaps starting in the second and the time since the last controller packet; the frame-size log's frames, packets, bytes, max packets, frames ≥ 40; the ladder's rung and state; the report's decode queue depth / wait and output gap where it covers the second; the shim's dropped counts where present (as context columns, **excluded from the model's inputs** — the model may not see the impairment); rolling sums / maxima over the previous 2, 5, 10 and 30 s of each; seconds since session start; the system (SNES / PS1) as a categorical. Missing = NaN, with a presence flag per source.
- **The label:** `hitch_next_k` for k = 1, 2, 3 s — whether any of the next k seconds is a hitch second by UX-R3's definition (R / C / G / L, the user's own pauses excluded, the first 15 s of each client session excluded from both features and labels).
- Counts per session: seconds, hitch seconds, positive rate per k.

## 2. The models and the evaluation (as pre-registered)

- **Splits by session, never by row:** (a) **held-out evenings** — UX-R1 (Sunday), UX-R2 (the death's night), UX-R3's view of it is the same session; (b) **held-out bench** — BENCH-R1 cells 5 and 8; (c) training = everything else; (d) a 5-fold grouped cross-validation over the training sessions for the hyperparameters, then one fit on all of training.
- **Models:** logistic regression (L2, standardized); gradient-boosted trees (depth ≤ 4, ≤ 300 rounds, early stopping on a grouped fold) if the library allows, else the stump ensemble; **and the two hand rules as baselines scored on the same labels:** LAN-R1's T 4 / K 2 on unrecoverable groups, and the silence rule "time since last controller packet ≥ H" for H = 250 and B6's H if its record has landed.
- **Metrics per held-out set and per k:** AUPRC, and — the one that matters — **recall at the operating point of ≤ 1 false alarm per 10 min on the clean reference sessions** (BENCH-R1 cells 1 and 8, CL-B5/6/7's windows, UX-R2's clean minutes), with the alarm threshold chosen on training data only; lead-time histogram (how many seconds before the hitch the alarm first fires); per-feature importance (coefficients; gain); the same for the baselines.
- **The acceptance bar, written beforehand:** the detector is worth a flag if, at ≤ 1 false alarm / 10 min on the clean references, its recall on the held-out evenings' hitch seconds at k = 2 exceeds the best hand rule's by ≥ 20 points absolute, **and** it fires ≥ 2 s before Sunday's 05:06 burst and before the death's 04:54:55 (or says plainly which it misses). Otherwise: recorded as measured, no flag proposed.
- **What the model is not allowed to learn from:** the shim columns, the session id, the clock time of day, the title. State the exclusion list.

## 3. The artefacts and the record

- `ml_r1_2026-10-22/`: `inventory.md` / `.json`, the feature table and its column list, `label_counts.md`, `ml_r1_preregistration.txt` / `.sha256` / `preregistration_hashed_at.txt`, `ml_r1_pipeline.py`, `results.md` / `.json` (every metric, every baseline, per set, per k), `importance.md`, `lead_times.md`, the fitted model as plain numbers (`model_logreg.json`; the tree ensemble as a JSON dump) and a pure-python scorer `tools/hitch_predictor.py` that reproduces the held-out scores from the table (its self-test), `redact_check.txt`, `manifest.sha256`.
- `evidence/ML_R1_HITCH_EARLY_WARNING_2026-10-23.md`: the inventory in one table; the per-second table's size; the results against the bar, plainly; what the detector looks at (the top features in words); where it fires on Sunday and on the death; what it misses; **"what, if anything, should be built next"** as a proposal, not a change.
- `docs/KNOWN_ISSUES.md` (one line under the top item), `docs/ROADMAP.md` (one line: a detector measured; not built into the companion), `logs/ml_r1_git_status.txt`, `CURRENT.md` Next Action (the user's commit; BENCH-R2 after B's queue; the detector's next step if the bar is met).

Rules: **no edit under `companion/`** (B is in it), no companion restart, no stream, no adb, no sudo, no nft, the Opal read-only; the unit at `Nice=10`; the pipeline reads copies it makes first (`ml_r1_2026-10-22/inputs/`, with a manifest) and never writes under `logs/games/`; no addresses or identifiers in any artefact (the redactor over the directory; session ids masked as the evidence copies mask them); nothing fetched, nothing deleted; nothing adopted; nothing committed.
