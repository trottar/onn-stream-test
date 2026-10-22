---
memory_schema: 1
as_of: 2026-10-21
status: TASK HANDOFF — UX-R3 (session A, read-only, from UX-R2's preserved copies; no run): find the two moments in last night's Zelda session where the user "literally died because of lag", show what every per-second instrument saw in those seconds, and say whether the instruments can see a death at all. Then define a per-second "hitch" view and count it over both evenings and the September play. Nothing changed; nothing committed
---

# UX-R3 — find the deaths

**The user (2026-10-21):** "It felt better but there were two memorable instances where I literally died because of lag. That is completely unacceptable especially over LAN." Where: "Zelda and no idea probably halfway through to last third of the playthrough." Both evenings were played on a different TV from the usual test TV (a different room, so a different Wi-Fi path to the same router). **The standard the user set, verbatim: "This product needs to work at any house especially lan as long as the Internet is over 50mb/s."**

Read first: `UX_R2_SECOND_EVENING_2026-10-21.md` (Zelda 04:42:26-05:09:21Z, 27.4 min, two client sessions split by a pause at 05:08:58Z; the single-loss step at 04:52Z; decode queue depth max 64 / wait 278 ms in that session), `ux_r2_2026-10-21/session/` (the copies: the heartbeat log, `native_stream_ctrl_gaps.log`, the recovery log, the frame-size log, the decoder reports with their tick series, the audio-timing records, the game log), `UX_R1_…` (Sunday's bursts, for the same view), `D_BASE_R2_STALL_VISIBILITY_2026-09-20.md` and `D_BASE_P1_STALE_THRESHOLD_…` (what a stall looks like in these logs, as it was defined then).

## 1. The window and the per-second view

- **The window:** Zelda's session, with the user's estimate marked: halfway to last third ≈ **04:56-05:03Z** (minutes 13-21 of 27). The whole session is read; the estimate is a highlight, not a filter.
- **Per second, from the copies** (state what each log's real resolution is; where a log is per-minute or per-report, say so and do not interpolate):
  - rendered frames in the second (heartbeat), and the longest output gap the second contains if any log carries it;
  - post-FEC loss, FEC-recovered, unrecoverable groups in the second;
  - **the host's control-gap log: every uplink gap with its start and length** — a controller silence is an input that did not arrive, which is a death in an action game;
  - audio underruns and concealed underruns in the second; the audio arrival gap;
  - the frame-size log's bytes and packets in the second (did a burst of large frames precede the moment?);
  - the ladder's state rows and any decision in the second;
  - the recovery log (any row);
  - the decoder report's tick series if it covers the second (depth, wait, spikes, output gap).
- **Rank the seconds** by a hitch score written before the ranking: a second with rendered < 50 frames, or a control gap ≥ 250 ms starting in it, or an output gap ≥ 200 ms, or post-FEC loss ≥ 30 packets. List the top 15 seconds of the Zelda session and the top 15 of the whole evening, with every column.
- **The answer:** are there two moments in 04:56-05:03Z (or anywhere in Zelda) that stand out as the deaths? If yes, which instrument saw them and what else happened in the ±5 s around them (the onn's uplink, the downlink, the audio, the frame sizes). **If no second in the window stands out, say so plainly: the instruments did not see what the user felt — and name what is missing** (controller-to-screen latency; per-second output gaps on the client; the client's input queue; the Wi-Fi link's own retries).

## 2. The "hitch" view, defined and counted

- Define **hitch seconds** per the score above (write the definition once, with the thresholds), and count them per evening: UX-R1 (Sunday), UX-R2 (last night), and the 2026-09-20 play (from the reports Code already read for H5, as far as they allow — say what they allow). Hitch seconds per 10 minutes of play, and the longest run of consecutive hitch seconds.
- Beside each evening's count, the user's own report of it: Sunday "horrible … not good to terrible"; last night "felt better but … two memorable instances where I literally died because of lag"; September "earlier" (remembered as good).
- **Does the hitch count order the evenings the way the user does?** If it does, it is a candidate gameplay metric for every record from here (proposed, not adopted). If it does not, say what the count misses.

## 3. The ladder, in those seconds

For each of the top-ranked seconds: what the ladder's state was, what its last decision had been, and what the adopted `live` rules would have needed to see to step down. One table. No change proposed here (that is session B's LAN-R1).

## 4. Record

`evidence/UX_R3_FIND_THE_DEATHS_2026-10-21.md` + `ux_r3_2026-10-21/` (the per-second script and its output, the ranked tables, `redact_check.txt`, `manifest.sha256`); `docs/KNOWN_ISSUES.md`'s top item updated with the user's standard verbatim and what the instruments can / cannot see; `logs/ux_r3_git_status.txt`; `CURRENT.md` Next Action (the user's commit; the instrumented evening in the user's own room with the Opal's view and the user's clock marks, as the next run for the user's say-so; LAN-R1 in B). Exit.

No sudo, no nft, the Opal read-only, no adb (nothing on the onn is needed; the copies hold the evening), no addresses or identifiers; nothing fetched, deleted or moved; no restart, no run, no change outside `docs/`, `logs/` and the evidence directory; nothing adopted; nothing committed.
