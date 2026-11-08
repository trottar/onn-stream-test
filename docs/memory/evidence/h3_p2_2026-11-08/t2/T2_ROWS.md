# T2, the rows (2026-11-08 03:02:38-03:09:29Z; the heavy title, after A's audio-wait change)

The user (verbatim): "T2, game started"; "T2 done ( I forgot about the back midway so did one at the end)". No line on
feel was sent with it (asked for at the close).

**The game log:** `PS2 launch: pcsx2 players=2 multitap=false adapter=named` 03:02:38.482Z; `PS2 audio: sink-input
0.1s` 03:02:40.132; `PS2 pause: hotkey` 03:02:40.268; `PS2 resume: hotkey` 03:02:44.674; `PS2 pause: hotkey`
03:09:08.945 (Back); `PS2 resume: hotkey` 03:09:21.330 (Resume); `PS2 pause: hotkey` 03:09:25.042 (Back);
`PS2 exit: sigterm 0.5s` 03:09:29.438 (Stop).

| row | reading | result |
| --- | --- | --- |
| P7a the list | the same node and count as T1 | met (folders: the close) |
| P7b launch | `PS2 launch` 03:02:38.5 → the first heartbeat with frames 03:02:41.0 (**2.5 s**) → `session_started` 03:02:44.7 (**6.2 s**); the line and the `ps2_session` rows present | **met** (margin ~84 s) |
| P7c pads | the same four virtual pads (PCSX2's log); `updates_by_player`: slot 0 24 → 4,629, slot 1 9 → 16 (in the first two minutes only) | **pad 1 met; pad 2 reached the hub, player 2 barely exercised** — not fully shown |
| P7d pause / resume | Backs: `PS2 pause` 0.16 / 0.16 s after `session_ended`; the Resume: `PS2 resume` 0.005 s before `session_started` (the launch's release 0.005 s before); method hotkey; the Back / Resume came at the end (6.4 min), not midway (the user's note) | **met** |
| P7e hitches | the keeper's rows (384 + 3 = 387 s): **4 hitch seconds** (C 3: control gaps of 250-302 ms at 03:05:38 / 03:05:47 / 03:06:47; L 1) → **6.2 per 10 min**; bar 29.7 | **met** (margin 23.5) |
| P7f P2 | the minute-6 capture began 03:08:45.6 and the user's Back came at 03:09:08.6, so it holds 23 s of play, then the paused and exiting picture: the tool on the whole capture reads median 58, corrected minimum 12 (14 static seconds excluded), not a gameplay minute. **On the 23 played seconds:** unique frames 57-60 per second (median 59.5), unique-frame interval p95 16.7 ms, p99 33.4 | **not measured as pre-registered** (the capture overlapped the Back); the played part would pass |
| P7g M2-M6 | over 03:02:44.7-03:09:24.9: no core ≥ 90 % (per-core max 65 %; busiest core median 23 %); threads EE 44 % mean / 64 % max, VU1 30 %, GS 27 %; GPU median **30 %** (p95 33); Tctl max **63.6 °C**; frame-time p95 16.7 ms (the played part); the drive: 453 reads (196 MB), 0 writes, **one stall second: 643 ms at 03:04:57** (2.2 min in; no hitch row then — the hitch seconds came 41-110 s later and were control gaps) | **not met** (the read stall; every other bar met) |
| P7h exit | `PS2 exit: sigterm 0.5s`; nothing left | **met** |
| P7i feel | "It felt really good to play" (sent after "T2 done") | recorded |

**Notes:** play time 6 min 24 s to the Back (+ 3 s after the Resume), short of the 10 minutes; valid (the pads on the
onn; no stream restart). The keeper labels these sessions PS1 (as T1's).
the user (verbatim, after T2 done): "It felt really good to play"
