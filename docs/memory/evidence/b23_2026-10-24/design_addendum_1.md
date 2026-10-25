# B23 — design addendum 1, written after the first replay and before the code that follows it

The design (`design_written_before_code.md`, `f4a8b493…`, 18:15:45Z) decides a session's set once, at its stream's
start. The first run of `replay_holds.py` (whole logs, the real detector) showed what that misses:

- **G4-S1 run 2** started on the direct path and went `no-peer` after the hotspot toggle, inside the same session.
- At H 450 its control-gap log gives **18 false holds** (silences of 467-1,894 ms); at 950 it gives 1.
- A session that starts `remote-direct` and then leaves the direct path would keep H 450 / the stall 200 through the
  flapping.
- **The LAN windows** at 450 would hold falsely on CL-B11 cell 1 (540, 564 ms) and 59 times on the 2.4-GHz reference.
  That is already covered: the LAN keeps its wired values.

**The change (only inside `PRIVYHUB_LINK_RECOVERY_WAN=1`):**
1. **The path is re-read during a remote session, every 10 s** (the provider's own cache is 10 s), on the same daemon
   thread, while the session is current.
   - A change of the path's set applies the new set and logs one `link_recovery_config` row (unchanged → no row).
   - A path leaving `direct` is seen within ~10-20 s.
2. **A guard for the seconds before that:**
   - on `remote-direct`, the first hold whose silence ends in < 3 s (a non-drop silence ≥ 450 ms; none in WAN-R1's
     113 direct min) reverts the session to the wired values;
   - set `remote-unknown`, why "a non-drop silence ≥ 450 ms on the direct path: not WAN-R1's direct; as wired for the
     rest of the session";
   - **the re-read does not re-apply `remote-direct` in that session.**
   - Read from B2's detector's own `("release", ms)` event: its emit is wrapped, the original called first and
     unchanged, only under the flag.
3. **The replay gains a third column:** H 450 with the guard (the session starts direct and reverts at its first
   non-drop hold), for every log.

Tests added for: the re-read (direct → no-peer → as wired; → direct again → 450 / 200 unless the guard fired); the
guard (a 600-ms silence on direct → one hold, then the wired values, logged); a real drop (≥ 3 s) does not trip it; and
the guard's replay of G4-S1 run 2.
