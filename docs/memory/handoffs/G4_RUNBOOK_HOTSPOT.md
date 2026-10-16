---
memory_schema: 1
as_of: 2026-10-16
status: RUNBOOK (G4-P1, drafted overnight by session B) — the user's steps for G4-S1, the first off-site test over a phone hotspot. One action per step, with what the screen or the terminal must show. Placeholders only: <hub-tailnet-name>, <your-tailnet-account>, <hotspot-name>, <run-dir>. Use it only after CL-B2 is closed and G4-S1's pre-registration is finalized and hashed
---

# G4 runbook — the first off-site test (phone hotspot)

**Before you start, all of these must be true:**

- CL-B2 is closed: the onn is paired with the hub, and its "Use paired
  identity (identity v2)" box is ticked.
- The companion runs with `PRIVYHUB_SESSION_IDENTITY=v2` and
  `PRIVYHUB_OVERLAY_PROVIDER=tailscale` (session A sets the drop-in and
  restarts).
- `handoffs/G4-S1_OFFSITE_FIRST_SESSION_TASK.md` is finalized and its
  pre-registration hashed.

**This test substitutes** a phone hotspot and the Tailscale app on the onn
for the ROADMAP's travel router (§G2, later).

## A. The onn joins the tailnet (at home, once)

1. On the onn, open the Play Store, search **Tailscale**, and install it.
   **Expect:** the Tailscale app on the home screen. If the Play Store has
   no Tailscale for this device, **stop**: that is a blocker for G4-S1.
2. Open Tailscale on the onn and sign in with **<your-tailnet-account>**,
   the account the hub uses. **Expect:** Tailscale shows "Connected", and
   asks once to allow a VPN connection; allow it.
3. On the hub, run `tailscale status`. **Expect:** two devices listed, the
   hub and the onn, both online. **Do not paste the output anywhere**; just
   check that there are two lines.
4. On the hub, run
   `python3 -m companion.overlay --state --provider tailscale` from the
   repo. **Expect:** `"connected": true`, and `"path"` now `"direct"` or
   `"relayed"` rather than `"no-peer"`.

## B. The onn points at the hub's tailnet name (at home)

5. On the onn, open PrivyHub and press **SETTINGS** (main screen). **Expect:**
   the "PrivyHub Settings" dialog with one text field (the companion host).
6. Write down the field's current value somewhere private (your home
   setting), then replace it with **<hub-tailnet-name>**, the hub's MagicDNS
   name as `tailscale status` shows it, and press **Save**. **Expect:** the
   catalog reloads.
   - The field takes an IP or a hostname; nothing else changes.
   - If the catalog fails to load, Tailscale DNS (MagicDNS) is off on the
     onn: in the Tailscale app turn on **Use Tailscale DNS**, then retry.
7. Still at home, press **SETTINGS** again and confirm the identity line
   reads `Identity v2: on; paired as "…"`. **Expect:** no "Last refusal".

## C. Off the home network (the phone hotspot)

8. On your phone, turn on the hotspot **<hotspot-name>**. **Expect:** the
   phone shows the hotspot on.
9. On the onn, Settings → Network → choose **<hotspot-name>** and connect.
   **Expect:** the onn connected to the hotspot. Tailscale on the onn
   still shows "Connected" (it may take ~10 s).
10. On the hub, start the suite's remote row (from the repo):
    `python3 tools/e1_suite.py run --remote --out <run-dir> --prereg docs/memory/handoffs/G4-S1_OFFSITE_FIRST_SESSION_TASK.prereg.txt --runs 3 --window 600 --gap 300`.
    **Expect:** within a few seconds, either a refusal (it names what is
    missing; fix it and rerun) or "idle gap 300s".
11. When the hub's terminal prints **"waiting up to 900s -- start a PS1
    game on the onn"**, open PrivyHub on the onn → Games → the PS1 title
    → start it. **Expect:** the game on the TV. The terminal then prints
    "PLAYING; client control peer class [...] overlay hash …" and
    "window … + 600s".
    - If it prints "not reached over the overlay", the onn is still on the
      home network: check step 9.
12. Play normally for the 10 minutes. During the window, once each:
    - press **Pause**, then **Resume**;
    - **save** a state, then **load** it.

    **Expect:** each works as at home.
13. **Run 2 only, at about 5 minutes in:** turn the phone's hotspot **off**,
    count 10 seconds, and turn it **on** again. **Expect:** the stream
    pauses (the recovery screen), then resumes on its own.
14. When the window ends, press **BACK** on the onn. **Expect:** the game
    ends; the terminal prints the run's status. Wait for the next
    "waiting… start a PS1 game", then repeat steps 11-14 for runs 2 and 3.

## D. Back home (the overlay absent)

15. On the onn, open Tailscale and **disconnect** it. **Expect:** Tailscale
    shows "Disconnected".
16. On the onn, connect back to the home Wi-Fi.
17. PrivyHub → **SETTINGS** → put back the home value from step 6 → **Save**.
    **Expect:** the catalog loads as before.
18. Start the same PS1 title and play for at least 2 minutes, then BACK.
    **Expect:** it plays exactly as before the test. This is the "local
    behaviour unchanged when the overlay is absent" check.
19. Turn the phone's hotspot off.
20. Tell the next session the run directory **<run-dir>**. It writes the
    G4-S1 record from the suite's files and the session audit log. Paste
    nothing: the files are read from the repo.
