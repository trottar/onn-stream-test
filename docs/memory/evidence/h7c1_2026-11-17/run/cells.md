# H7-C1 — the cells (`preregistration.md`, sha256 `e23ef8ce…`, hashed 00:31:04Z; the sitting 00:31:12-00:47:08Z)

Four people at the TV with four Sony pads paired to the onn; nothing asked on the hub; no flag, eighteen lines
throughout. Launched from the onn 00:33:45Z (Start Fresh); "ready" 00:35:38Z.

| cell | what was read | met |
| --- | --- | --- |
| **J** — four seats | `launch_ports` four ports (`players` 4); `pad_slots` count 4 joined in every stream session (P4 late once: 00:37:12Z, ~1.7 min after P1-P3 following SAVE 1's RESUME) | **met** |
| **K** — the pictures | 794, one a second 00:33:45-00:46:58Z, **no gap** (largest step 1.01 s); every match's results screen inside the run by the line times; grab 11.0 / save 3.4 ms median; CPU not read (`picture_keeper.md`) | **met** |
| **S** — the stream | no stall row, no recovery act, `launch_orphaned` 2 → 2; **59.8 frames a second median**; the level 7000 throughout, no escalation; loss 113 packets (PP-H3b 57) (`stream_rows.md`) | **met** |
| **V** — the SAVEs kept | two SAVEs (slots 2 and 3 the only empty ones): `begin` `bc8ff296…` (00:35:16Z) and `results_1` `e8efe35f…` (00:38:31Z), each the hub's 200 row and the slot's new hash, **copied with its picture** to `~/privyhub_h7/t89/` with `SHA256SUMS`; the slots left as made (`saves_kept.md`) | **met** |
| **U** — nothing else touched | every other game's 157 files before = after (`02df293c…`); slot 1 unchanged; T89's new files exactly slots 2 and 3 with their pictures; no `.state8`; the drive and the profiles before = after — **but the hub's own `.state` (+ picture) changed** (`55229e83…` → `e8efe35f…`): the hub's SAVE saves to RetroArch's slot 0 and copies it to the slot, so `.state` always mirrors the last SAVE (it equalled slot 1 before for the same reason). The pre-registration said "the hub's own `.state` unchanged" — a wrong prediction of the SAVE's own mechanism; **not met as written**. Recorded, not a cell: the game's in-game `.srm` changed (the game's own records), and the hub's slot index | **not met** (one clause) |

**The finishing orders** (the users' lines, labels to be — not cells): **M1** "1,2,3,4" (asked 1, 2, 3, 4); **M2**
"2,3,4,1" (asked 2, 3, 4, 1); **M3** "3,4,1,2" (asked 3, 4, 1, 2); **M4** "I messed up. / 3,4,2,1 / Want me to redo
it?" (asked 4, 1, 2, 3 — played otherwise, kept as played, not redone); **M5**, all four the same character, "1,3,2,4"
(asked 1, 3, 2, 4).

**NOT MET by one clause of U** — J, K, S and V met.
