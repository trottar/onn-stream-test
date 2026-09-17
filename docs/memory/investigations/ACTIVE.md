---
memory_schema: 2
as_of: 2026-09-17
---

# Active Investigations and Queued Work

## Active — D-137 TV-state probe schema-v2 projection repair

D-136 failed only at D-122 TV-state parity. Source inspection proves D-122's
D-116 projection is stale relative to TV user-state schema v2: it omits
`guide_incorrect`, `rejected_guide_source_key`, and `guide_incorrect_at_ms`.

D-137 updates diagnostic projection only. Production TV-state code remains
unchanged.

## Queued after D-137

1. rerun D-136;
2. if automated pass, short manual Live TV / guide / VOD smoke;
3. D5 closeout.
