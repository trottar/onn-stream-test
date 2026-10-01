---
memory_schema: 1
as_of: 2026-10-01
baseline_commit: 4e45a4f
status: DECISION 2026-09-30 (the user's) — live adaptive bitrate ON BY DEFAULT, made 2026-10-01 13:07Z through the systemd user-unit drop-in named in the C3.L4 close; the unit file unchanged, no set-environment. Kill switches - delete the drop-in + daemon-reload + restart (off); POST /plugins/games/adaptive-bitrate/disable (shadow for one session). Shown - the status reads live / configured live / acts true from the drop-in; an injected FALLBACK acted 7000 → 5000 and reset at BACK (the session NOT PASS AS PRE-REGISTERED on two clauses traced to the pre-registration and the harness's read timing, not to the controller); a 30-min hold on the default SILENT. Open - the mild step's ~120 s bound
---

# C3-L4-D1 — live adaptive bitrate on by default

**Status:** in force since 2026-10-01 13:07Z. The decision is the
user's; this record writes it down with what it rests on and what was
seen after it.

## The authorization

The user, 2026-09-30, verbatim: **"do the loss row look first and then
the live default"**.

- The loss row look is `LINK-L1`: MIXED, 3 of 6 holds
  (`../evidence/LINK_L1_LOSS_ROW_2026-10-01.md`). It ran first, with
  adaptive off.
- The default was made after it, as the C3.L4 close described it
  (`C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`, "The change that would make
  it the default").

## The change, verbatim

`~/.config/systemd/user/privyhub-companion.service.d/adaptive.conf`:

```ini
[Service]
Environment=PRIVYHUB_ADAPTIVE_BITRATE_MODE=live
```

then `systemctl --user daemon-reload && systemctl --user restart
privyhub-companion`.

- The unit file is unchanged (H3's "no PRIVYHUB_* diagnostic variable is
  ever set here" stands for the unit itself).
- No `set-environment`, so the default survives a reboot.
- A copy is at `../evidence/c3_l4_d1_2026-10-01/adaptive.conf`, and in
  `../TOOLS.md`.

## What the status shows

- `native-stream-status` → `adaptive_bitrate`: `mode live`,
  `configured_mode live`, `acts true`, level 7000.
- `encoder_overrides.any_override` **false**: the adaptive mode is not an
  encoder override.
- The companion's environ carries exactly one `PRIVYHUB_*`, this one. The
  user manager carries none.
- The profile is adopted at 7000. `PRIVYHUB_FEC_SCHEME` and the profile
  selector are absent, and the shadow is byte-identical.

## The kill switches

- **Off, persistently:** delete the drop-in, `systemctl --user
  daemon-reload`, then restart the unit. The mode reads `off` (unset).
- **Shadow, for one session:** `POST
  /plugins/games/adaptive-bitrate/disable` (loopback, idempotent). The
  next session is live again. There is no enable route.

## What the proof sessions showed (`../evidence/C3_L4_D1_LIVE_DEFAULT_2026-10-01.md`)

**The injection session**, live from the default with a session-only
inject flag:

- **The controller did what the close says.** One injected FALLBACK
  acted 7000 → 5000 in 1,237 ms. The client saw exactly one SSRC change,
  and the 3-report blackout followed. The level reset to 7000 at BACK.
  Afterwards the inject flag was gone and the route answered 403.
- **By its pre-registration the session is NOT PASS.** Two clauses
  failed as worded:
  - an "`ssrc_change` row" that the live controller never emits for its
    own transition (only for recovery restarts);
  - "stream 7000" after BACK, read 0.3 s before the client's stop
    reached the companion. The stop path resets to 7000, but no read was
    taken after it.
- Both trace to the pre-registration and the inherited harness timing,
  not to the controller. **The rows stand as recorded.**

**The 30-minute hold** on the default, with no flags:

- **SILENT**: 0 transitions, refusals or HOLDs over 901 reports, and the
  client rows met.
- Loss 7.59/min met the row; the max gap of 447 ms missed its row.

**The harnesses.**

- `tools/c3_l4_nft_night.py` and `tools/d7_regression.py` now accept the
  one name and nothing else. They refuse manager residue, and the
  teardown restores the baseline (live) instead of ending at off
  (`../patches/C3-L4-D1_LIVE_DEFAULT_PREFLIGHTS.md`).
- The fake-sudo FULL and ABORT runs PASS with that end state.

## Carried over, open

- **The mild step's ~120 s bound.** After an increase, `capacity_mild`'s
  step down waits for the 60-report ROUTINE reversal hold-down (night 3:
  121 s), not the ~90 s once expected. Shortening it is a rule change for
  the user to ask for, or not. Unchanged here.
- **Adaptive-off measurements now need the drop-in out for the session**,
  or the disable route each session. `LINK-L1`'s holds were the last made
  under off-by-default. `TOOLS.md` says how.
