C3-L4-N2: the user's nft night 2 (2026-09-29 17:42-18:10Z, --only F1,F3), copied from
logs/streaming/c3_l4_nft_night_20260929_174201Z/ on 2026-09-29 by Code, read-only.

Every file went through h2_prep_redact.py on the way in; --check passes on every file. The
redactor replaced address-shaped fields in armcheck_*.json, status_end_*.json and report_*.json
and appended a trailing newline to summary.json, t2_sampler.log and t2_samples.jsonl.stop; every
other file is byte-identical to the original.

source_sha256_before_copy.txt -- the originals' sha256, taken before the copy.
sha256_manifest.txt           -- this directory's files as stored.
Scored by ../c3_l4_n2_2026-09-29/c3_l4_n2_score_night2.py (identical output on the original run
dir and on this copy); record ../C3_L4_NFT_NIGHT2_2026-09-29.md.
