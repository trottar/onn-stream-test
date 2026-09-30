C3-L4-N1: the user's first nft night (2026-09-29 15:19-16:17Z), copied from
logs/streaming/c3_l4_nft_night_20260929_151942Z/ on 2026-09-29 by Code, read-only.

Every file went through h2_prep_redact.py on the way in; --check passes on every
file. The redactor replaced the client address fields in armcheck_*.json,
status_end_*.json and report_*.json; it also appends a trailing newline, which
is the only change to summary.json, t2_sampler.log and t2_samples.jsonl.stop.
Every other file is byte-identical to the original.

source_sha256_before_copy.txt -- the originals' sha256, taken before the copy.
sha256_manifest.txt           -- this directory's files as stored.
Scored by ../c3_l4_n1_2026-09-29/c3_l4_n1_score_night1.py (identical output on
the original run dir and on this copy); record ../C3_L4_NFT_NIGHT1_2026-09-29.md.
