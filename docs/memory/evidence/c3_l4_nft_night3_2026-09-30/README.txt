C3-L4-N3: the user's nft night 3 (2026-09-30 13:14-13:36Z, --only F1), copied from
logs/streaming/c3_l4_nft_night_20260930_131404Z/ on 2026-09-30 by Code, read-only.

Every file went through h2_prep_redact.py on the way in; --check passes on every file. The
redactor replaced address-shaped fields in armcheck_F1.json, status_end_F1.json and report_F1.json
and appended a trailing newline to summary.json, t2_sampler.log and t2_samples.jsonl.stop; every
other file is byte-identical to the original.

source_sha256_before_copy.txt -- the originals' sha256, taken before the copy.
sha256_manifest.txt           -- this directory's files as stored.
Scored by ../c3_l4_n3_2026-09-30/c3_l4_n3_score_night3.py (identical output on the original run
dir and on this copy); record ../C3_L4_NFT_NIGHT3_2026-09-30.md.
