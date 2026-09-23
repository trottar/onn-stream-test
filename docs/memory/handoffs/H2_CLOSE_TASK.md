---
memory_schema: 1
as_of: 2026-09-22
status: TASK HANDOFF — H2 close-out: classify check 5 from the user-run `h2_check5.sh --session` output and finish the H2 record; documentation only, no host change
---

# H2 close-out — classify check 5, finish the record

**Gate.** The user has rebooted the host with only the dummy plug attached and run
`evidence/h2_2026-09-22/h2_check5.sh --session` from a fresh SSH shell. If
`evidence/h2_2026-09-22/check5_postboot.txt` does not exist, stop and say so.

Read first: `evidence/H2_HEADLESS_CUTOVER_2026-09-22.md` (the record this
closes; its "Check 5 — pending" section states the PASS rule),
`evidence/h2_2026-09-22/check5_postboot.txt`, `evidence/h2_2026-09-22/h2_analysis.txt`
(now carries `S2`), `evidence/h2_2026-09-22/S2/`, `handoffs/D-BASE-H2_TASK.md`
(the classification rule), `TOOLS.md` §headless.

**Nothing on the host changes.** No reboot, no `/etc`, no `xrandr --output`, no
config file. Do not restart the companion unless 8765 is not answering. If the
onn is not on adb, do not go looking for an endpoint — record `S2` as NOT RUN.

## Read check 5, item by item, against check 2

From `check5_postboot.txt`:

1. Session: `Type=x11`, `Service=lightdm-autologin`, `Desktop=xfce`,
   `State=active` on the seat session — **the desktop, not the greeter**. A
   `lightdm-gtk-greeter` process, or no `xfce4-session`, is a FAIL.
2. Display: `DisplayPort-1` connected `1920x1080 60.00*+`, `card0-DP-2`
   connected, the other two disconnected; `DPMS is Disabled`, `timeout: 0`.
3. adb: the device listed in state `device` after `adb connect` on the pinned
   port (the script redacts the address; leave it redacted).
4. Companion: one pid on 8765, `DISPLAY=:0` in its environ,
   `capture_backend x11grab_window`, `max_frame_size_bytes 90000 source
   profile any_override False`. Note whether the script started it
   (`pre-existing: no`) — expected, since nothing starts it at boot.
5. tmux: record what it says; it is informational, not a gate.

From `h2_analysis.txt`, `S2` against the same bounds `S1` was read against:
`capture_description` and source `879x720` identical; rendered fps and
spikes ≥ 20 ms/min within B2 (59.63-59.71, 46.4-54.4); `max_output_gap_ms`
not worse than B2 (≤ 231); stale drops/min ≤ 8.0; both thermal readings
present; `any_override: false` in the mid-session status.

## Classify

- All five items and `S2` in bounds → **H2 RUNTIME VALIDATED**: the host
  comes back streaming after an unattended power cycle with nothing but the
  plug, given the companion is started by hand.
- Greeter instead of desktop → **FAIL on check 5**; the smallest fix is
  autologin (`10-autologin.conf`), name it, apply nothing.
- Mode not 1080p60 → FAIL; smallest fix is the `xorg.conf.d` Monitor section
  with `Identifier "DisplayPort-1"`, then `video=DP-2:1920x1080@60e`; apply
  nothing.
- `S2` not run (onn unreachable) → check 5 items 1-2 and 4 can still PASS;
  classify **CHARACTERIZED — session after second boot not run** and say
  exactly why.

## Record and memory

- Append a "Check 5 — result" section to
  `evidence/H2_HEADLESS_CUTOVER_2026-09-22.md` with the raw readings first,
  the `S2` row in the check-3 table, and the classification; change the
  front-matter `status` line and the "Classification" section to match.
  Keep the pending section's text as history, marked superseded.
- Regenerate `h2_2026-09-22/h2_sha256.txt` (it must now cover
  `check5_postboot.txt`, `S2/*`, the rewritten `h2_analysis.txt`, and
  `h2_check5.sh`); `sha256sum -c` clean.
- Run `h2_prep_redact.py --check` over `check5_postboot.txt` and every
  `S2/` text file: 0 residual matches, stated in the record.
- `evidence/RUNTIME_VALIDATION.md`: the H2 line with the final
  classification.
- `CURRENT.md` (fixed headings; Current Work Item and Next Action updated:
  next is tonight's `OVERNIGHT_2026-09-23_QUEUE.md`, then E30/N05/N15b by
  hand), `python3 tools/check_memory_health.py` healthy; `MEMORY.md` (the
  headless host as a durable fact, with the plug's connector
  `DisplayPort-1` = `card0-DP-2`); `handoffs/CURRENT_HANDOFF.md`;
  `TOOLS.md` only if something in the headless section is now wrong; the
  dated memory file; `KNOWN_ISSUES.md` only on a FAIL.
- Teardown per `TOOLS.md`. Never retry a failing action more than twice.
  No addresses, MACs, SSIDs, ADB endpoints, serials or device identifiers in
  any memory or evidence file. Nothing committed to git.
