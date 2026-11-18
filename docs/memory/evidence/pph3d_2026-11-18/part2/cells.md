# PP-H3d — the cells (pre-registered `preregistration.md`, hashed 06:32:46Z; nothing perceptual)

| cell | read | met |
| --- | --- | --- |
| **Part 1** | 17 board checks on `e0ce8c4` PASS — the hub's **89**, step25 107, step8 210, and every check changed since `f8d92e38` (`part1/PART1.md`); the rules folder; 228 files; twenty lines; the bench start ready (1.274), PAUSED 5 / 5, no reload, end_P1 [1, 0] | **met** |
| **The self-proof** (after the user's "ok") | ready (1.303), no route / stream before the go, the capture the board's; the go switched (planned, 3.512 s); the end back to the board (3.53 s) | **met** |
| **S** — the sound after every planned switch | switches 2-6: sound 0.6-1.6 s after T, ≤ 3 underruns a row, 0 lost; **switch 1 (the self-proof's, to the title): no row with depth > 0 within 4 s — the switch back began 1.5 s after it** (`sound.md`) | **not met as written (switch 1 only)** |
| **B** — the band | 9 argv lines; the band in the practice's only (`banner.md`) | **met** |
| **L** — the board's log | `cards 1, chose 0`, `practice`, `start`, `scores [1, 0] for seats 1,2` (`board_log.md`) | **met** |
| **P** — Select + R1 in the practice | the user: "Back, all worked as expected" (the press's time not given); 228 files before = after (every sha256) | **met** |
| **LS** — the load screen at the practice's end | `minigame_playing` practice 06:58:56.5Z, 21.5 s before `minigame_practice_end` `start_button` (06:59:18.0Z); then `minigame_stream` board (06:59:20.0Z), `minigame_ready` `after_practice` (06:59:21.2Z), no `minigame_go` before it; the user: "Then went right to load after start" | **met** |
| **F** | PAUSED 9 / 9 and 72 / 72 (and 2 / 2 in the self-proof); no `minigame_reloaded` | **met** |
| **R** | `recognised` true at the first read in every preparation | **met** |
| **S (one card)** | `cards 1, chose 0`; `minigame_start` `players` 2 | **met** |
| **PS** | `"by": "start_button"` (21.474 s); no `minigame_ended` inside | **met** |
| **M** | `minigame_ended` end_P1 [1, 0]; the board's log credits seats 1,2 [1, 0]; the user: "P1, P1" | **met** |
| **E** | END: paused, quit by F10, exit 0; nothing running; `status` idle | **met** |
| **U** | 228 files before = after; no `.state8`; **no in-game save changed** | **met** |
| **W** | the two keys `"false"` at all three party launches (`config_keys.txt`) | **met** |

**NOT MET as pre-registered — S's switch 1 alone.** That switch is the self-proof's own: A ended the title 1.0 s after
`playing`, so the switch back began 1.5 s after it, inside the 1.5-3.5 s a switch's own gap lasts (B143) — no row could
show the title's sound. Every switch the user played through met S. For Cowork: whether S should exclude a switch whose
next switch begins within 4 s.

Recorded, no bar: the user's words (`lines.md`); `mute_ms` 336.6-376.4 (1148.6 on the way back); each switch's
`seconds` 1.769-3.53; `audio_rx_packets` ~100 / s.
