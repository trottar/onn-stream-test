# PrivyHub runbook

These are the plain steps for playing at home and away from home. Each step is one action, followed by what the
screen should show. The names here are placeholders:

- `<home-value>`: the PrivyHub "Hub host" value you use at home;
- `<hub-overlay-name>`: the hub's name on the overlay network;
- `<overlay-account>`: the overlay account the hub uses;
- `<away-5ghz-network>`: the Wi-Fi where you are.

**Write down your `<home-value>` before you leave home.** It is the one text field under onn → PrivyHub → SETTINGS →
Hub host. You need it to go back to home play. The field may be empty, which means the companion host.

## At home

1. **The onn is on the home 5 GHz Wi-Fi** (onn Settings → Network). Expect: "Connected".
2. **PrivyHub → SETTINGS → Hub host = `<home-value>` → Save.** Expect: the game list loads.
3. **Start a game.** Expect: the game on the TV within a few seconds, at full quality from the start.

**The Wi-Fi notice.** In a game a box may say "Wi-Fi: 2.4 GHz — Use your router's 5 GHz Wi-Fi for this box." That
means the onn is on the slower band. Back out of the game, choose the 5 GHz network in onn Settings → Network, and
start the game again. The other two notices, "weak signal" and "slow link", ask you to move the box or the router
closer, use a wired connection, or use the 5 GHz network.

## Away — the first time (once, at home)

1. **The onn is paired with the hub.** In PrivyHub → SETTINGS, "Use paired identity (identity v2)" is ticked and the
   identity line reads `Identity v2: on; paired as "…"`. Expect: no "Last refusal".
   - Pairing happens once, on the home LAN. On the hub, the companion opens a 2-minute pairing window
     (`POST /session/pairing/open` on the control API, from the hub itself) and shows a one-time code. On the onn,
     press "Pair with hub…" and type the code ([`REMOTE_TRUST.md`](REMOTE_TRUST.md) §5–§6).
   - Only a paired onn is let in from away; an unpaired one is never accepted over the overlay.
2. **On the onn, open the Play Store, search for the overlay app (Tailscale) and install it.** Expect: the app on the
   home screen.
3. **Open it and sign in with `<overlay-account>`.** Expect: "Connected". It asks once to allow a VPN connection;
   allow it.
4. **Optional: check from the hub.** Run `python3 -m companion.overlay --state --provider tailscale` from the repo.
   Expect: `"connected": true`.

## Away — each time

1. **Plug the onn into the TV's HDMI and into power, and turn the TV to that input.** Expect: the onn's home screen.
2. **Join the 5 GHz Wi-Fi where you are:** onn Settings → Network → **`<away-5ghz-network>`** → its password. Expect:
   "Connected".
   - If the router shows two names, pick the 5 GHz one.
   - If there is no 5 GHz network, play anyway. The 2.4 GHz notice shows once per session, and the hub's notes will
     say how it went.
3. **Open the overlay app on the onn and press Connect.** Expect: "Connected" (allow the VPN prompt if it asks).
4. **Open PrivyHub → SETTINGS → Hub host = `<hub-overlay-name>` → Save.** Expect: the game list loads.
   - If the list does not load, turn on **Use Tailscale DNS** in the overlay app, then press Save again.
5. **Start a game.** Expect:
   - the game on the TV within a few seconds;
   - the picture a little softer at first, getting sharper by itself.

**Why the picture starts softer.** An away-from-home session starts at a safe rate and climbs. It takes about one step
every 3 minutes and reaches full quality in about 12–15 minutes; it takes longer after a link stall
([`REMOTE_TRUST.md`](REMOTE_TRUST.md) §14). Every new game start does this, including a return from Home. Each step
keeps the same stream, so there is no short gap at each step. This all comes from the hub's adopted settings. There is nothing
to switch on for a trip, and no per-run flags.

## Playing with people

1. **Pair the controllers to the onn as at home** (each controller's own pairing, or plug it in). Expect: each one
   moves in the game.
2. **Play.** Nothing on the link changes with more players; each controller is a few bytes a second.

## If it breaks

1. **The stream drops** (the picture freezes, or a "Reconnecting" screen). Expect: **the game pauses and comes back by
   itself within seconds.** Wait, and do not press anything. A short drop with no loss resumes where you were, without
   loading a saved state.
2. **You pressed Home, or switched apps and came back.** Expect: **the picture back in about 2 seconds,** with the
   game where you left it.
3. **The picture never comes back** (more than about 30 seconds). Back out of the game (BACK on the remote) and start
   it again from PrivyHub. Expect: the game on the TV again, as after a relaunch at home.
4. **PrivyHub cannot reach the hub** (the game list does not load).
   - Check that the overlay app on the onn says **"Connected"** (press Connect if not).
   - Check that SETTINGS → Hub host is **`<hub-overlay-name>`** away, or **`<home-value>`** at home. Then try again.
5. **Change nothing on the hub yourself.** The diagnostics keeper keeps the hub's notes either way, and the reads
   below tell you what happened.

## Going home

1. **On the onn, open the overlay app and press Disconnect.** Expect: "Disconnected".
2. **PrivyHub → SETTINGS → Hub host back to `<home-value>` → Save.** Expect: at home, the game list loads.
3. **At home, put the onn back on the home 5 GHz Wi-Fi** (Settings → Network). Expect: "Connected", and no 2.4 GHz box
   in a game.

## The one-line reads

The hub keeps its own notes all the time. The `privyhub-diag` keeper copies the hub's logs every 5 minutes into
`~/privyhub_diag/`. Every address and name is replaced before anything is written, and the copies are kept for 30
days. You do nothing for it. On the hub, from the repo (or ask Code to run them):

**`python3 tools/diag_check.py`** prints six short lines:
- **`adopted:`** the adopted line count and `host check ok`.
- **`apk:`** whether the onn's app is on the pin. Away from home it reads "not read (adb off-LAN)", which is normal.
- **`overlay:`** whether the overlay is connected, and the path.
  - `path direct`: the onn reaches the hub straight across the internet. This is the good case.
  - `path relayed`: the connection goes through an overlay relay, because the local router does not allow a direct
    one. There is nothing to fix on their side; play anyway.
- **`routing:`** how the onn's newest session came in. `overlay` is right away from home.
- **`band:`** 5 GHz or 2.4 GHz at home. `adb off-LAN` is normal away from home.
- **`diag-keeper:`** its status, and whether the `privyhub-diag` unit is active.

If a line says **NOT ok** or **unknown**, read it to Code exactly as printed. Do not change anything yourself.

**`python3 tools/diag_read.py "<range>"`** reads the notes for a time range:
- `today`;
- `"last night"` (17:00 yesterday to 08:00 today, local time);
- `"YYYY-MM-DD HH:MM..HH:MM"` (UTC).

It writes one read under `docs/memory/evidence/reads/` and prints its path. The read gives a table per session and per
10 minutes, and every restart, rewind and pause with its cause.
