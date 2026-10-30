---
memory_schema: 1
as_of: 2026-10-29
status: FINAL (2026-10-29, session A, TRIP-PREP) — the user's plain steps for the trip (leaving Friday 2026-10-30 morning; home stays up and staffed). One action per step, with what the screen must show. Placeholders only, no addresses or names - <hub-tailnet-name>, <home-value>, <friend-5ghz-network>. Checked against the adopted state: THIRTEEN lines (PRIVYHUB_REMOTE=1, G-A9, adopted 2026-10-29); the onn's APK fcd924c2… (the loss guard out for the trip); the log-keeper privyhub-trip-log running to 2026-11-01T23:59Z; the trip check's six lines printed at home (evidence/TRIP_PREP_2026-10-29.md). Drafted by session B (B31)
---

# The trip runbook (2026-10-30)

**For the record afterwards:**
- **While you are away, the hub keeps its own notes.** The log-keeper (`privyhub-trip-log`, started Thursday, ending
  by itself Sunday 2026-11-01 23:59 UTC) copies the hub's logs every 5 minutes:
  - the stream's rate and steps, the heartbeats, the pauses and recoveries;
  - the controller gaps, the frame sizes, the hub's load;
  - the onn's session reports, the game logs, the companion's journal.
- **Every minute it notes** whether the onn is reached directly or through a relay, and whether a game is streaming.
- **Everything it keeps has every address and name replaced** before it is written, into
  `docs/memory/evidence/trip_2026-10-30/`.
- You do nothing for it. **Afterwards the read is one line:** "read the trip".

## A. Pack

1. **The onn.** Expect: the small box itself.
2. **Its power supply** (the onn's own adapter and cable). Expect: the plug that fits the onn.
3. **An HDMI cable.** Expect: one cable (the friend's TV needs a free HDMI input).
4. **The controllers** (and their cables or batteries). Expect: every controller you will play with.
5. **The onn's remote.** Expect: the remote that came with it (it has the Home button).
6. **Before you leave, write down the PrivyHub "Hub host" value you use at home** (onn → PrivyHub → SETTINGS, the
   one text field). Expect: `<home-value>` on paper or in a note. You need it in F.

## B. At the friend's

7. **Plug the onn into the TV's HDMI and into power; turn the TV to that input.** Expect: the onn's home screen.
8. **Join their 5 GHz Wi-Fi:** onn Settings → Network → **<friend-5ghz-network>** → their password.
   Expect: "Connected".
   - Pick the 5 GHz one if the router shows two names.
   - **If a box appears in a game saying "Wi-Fi: 2.4 GHz — Use your router's 5 GHz Wi-Fi for this box.",** the onn
     is on the slower band. Back out of the game, choose the 5 GHz network in step 8, and start the game again.
   - If the house has no 5 GHz network, play anyway. The notice shows once a session, and the record will say how
     it went.
9. **Open Tailscale on the onn and press Connect.** Expect: "Connected" (allow the VPN prompt if it asks).
10. **Open PrivyHub → SETTINGS → Hub host = `<hub-tailnet-name>` → Save.** Expect: the game list loads.
    - If the list does not load: in the Tailscale app turn on **Use Tailscale DNS**, then press Save again.
11. **Start a game.** Expect:
    - the game on the TV within a few seconds;
    - the picture at a lower sharpness for the first minutes, getting sharper by itself. The hub starts away-from-home
      streams at a safe rate and climbs, about a step every 3 minutes, to full quality in ~12-15 minutes.

## C. The check (once, after the first game starts)

12. **In Code (over SSH), type exactly:** `Run tools/trip_check.py and show me its six lines`. Expect six short
    lines: adopted, apk, overlay, routing, band, log-keeper.
    - **`path direct`:** the onn reaches the hub straight across the internet. This is the good case (G4-S4 was
      direct throughout).
    - **`path relayed`:** the connection goes through a Tailscale relay because the friend's router does not allow a
      direct one. **There is nothing to fix on their side.** Play anyway; the record says how it went.
    - **`routing: newest token_issued overlay`:** the onn came in over Tailscale (right for the trip).
    - **`band: adb off-LAN`:** normal away from home (the hub cannot read the onn's Wi-Fi from there).
    - **`log-keeper: … running …; unit active`:** the hub's notes are being kept.
    - If a line says **NOT ok** or **unknown**, read it to Code as it is. Do not change anything yourself.

## D. Playing with people

13. **Pair the controllers to the onn as at home** (each controller's own pairing, or plug it in). Expect: each one
    moves in the game.
14. **Play.** Nothing on the link changes with more players; each controller is a few bytes a second.

## E. If it breaks

15. **The stream drops** (the picture freezes or a "Reconnecting" screen). Expect: **the game pauses and comes back on
    its own within seconds.** Wait; do not press anything.
16. **A Home press, or switching apps and back.** Expect: **the picture back in about 2 seconds,** the game where you
    left it.
17. **The picture never comes back** (more than ~30 seconds). Back out of the game (BACK on the remote) and start it
    again from PrivyHub. Expect: the game on the TV again, as after a relaunch at home.
18. **PrivyHub cannot reach the hub** (the game list does not load).
    - Check Tailscale on the onn says **"Connected"** (press Connect if not).
    - Check SETTINGS → Hub host is **`<hub-tailnet-name>`**. Then try again.
19. **Nothing to type into Code unless Code asks you.** The hub keeps its notes either way.

## F. Going home

20. **On the onn, open Tailscale and press Disconnect.** Expect: "Disconnected".
21. **PrivyHub → SETTINGS → Hub host back to `<home-value>`** (the value you wrote down in step 6) → Save.
    Expect: at home, the game list loads.
22. **At home, put the onn back on the home 5 GHz Wi-Fi** (Settings → Network). Expect: "Connected"; in a
    game no 2.4-GHz box.
23. **When home, send 'read the trip' into Code.** Expect: Code reads the hub's notes from the trip and reports.
