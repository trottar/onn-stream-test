---
memory_schema: 1
as_of: 2026-11-19
status: TASK — session G6, docs only. G6-HM1: the portrait handheld mode's design, written and hashed before any code. Stops for the user's approval. Nothing adopted; nothing committed.
---

# G6-HM1 — portrait handheld mode: the design, before code

Plan: `docs/memory/architecture/G6_HANDHELD_PLAN_2026-11-19.md`. Brief:
`docs/memory/handoffs/G6_PORTRAIT_INVESTIGATION_HANDOFF_2026-11-19.md`. Its `L:` path is not used; the hub's repo is
authoritative. Context: `docs/memory/evidence/G6_S1_TABLET_FIRST_INSTALL_2026-11-19.md`.

**Docs only. You read code; you never change it.** Nothing under `PrivyHub/`, `companion/` or `tools/` is edited. No
build, no APK, no adb, no stream, no service restart, nothing fetched. The design is written and its sha256 recorded
before any later stage writes code. That is the project's "design written before code, hashed" rule.

## The user's decisions (2026-11-19), fixed inputs

- **D2:** the touch pad becomes **P1** by default when no real pad has joined as P1 (today's long-press join) within
  **5 s** of the game starting. A real pad that joins later takes the next player and does not displace the touch pad.
- **D3:** the **PS1 layout first**: D-pad, four face buttons, L1/R1/L2/R2, Select/Start. Sticks and L3/R3 come in G6-HM5.
- **D4:** tablet **landscape keeps today's full-screen fill**. No letterbox.
- **D1 (partly open):** stage 1 picks the mode at launch with a Settings choice ("TV / landscape", the default, or
  "Handheld"). Following the rotation live is G6-HM6.
- **The onn's experience is unchanged.** Today's stream activity's manifest entry stays byte for byte. The onn never
  launches the new activity.

## What the design must settle, each against the code as it is (cite file:line)

1. **The activity split.** A handheld subclass of `NativeStreamActivity` with its own `<activity>` entry
   (`screenOrientation="portrait"`; `configChanges` only if stage 1 needs it). List the minimum `open`/protected hooks
   the base needs: build the layout, place the overlays, allow touch. Show that each hook's default is today's code path.
   Name what stays private.
2. **Portrait layout.** The video `SurfaceView` at 1200×675 (width × 9/16, computed from the real view width, never
   hard-coded) at the top. The pad view fills the rest. The overlays go inside the video box: status, link notice,
   player prompt, paused bar, N64 card. Immersive and keep-screen-on as today.
3. **The touch path into the existing sender.** One new `NativeControllerSender` method that writes one player's
   state under the existing lock. Its exact signature. How it coexists with `neutralize()`, `resetState` and the send
   loop. The stick sign: check what `handleMotionEvent` passes for `AXIS_Y` and match it.
4. **`TouchPadState` (pure Kotlin, no Android types).**
   - Pointer ownership by pointer id. A finger belongs to the control under it at its down event and keeps it until its
     up event or a cancel.
   - D-pad: 8-way by angle, with a roll between directions.
   - Face buttons: one finger, one button.
   - Hit areas larger than the drawing.
   - L2/R2 digital (255).
   - Release on a finger's up, on cancel, and on a reset call.
   - Its output is the sender's state fields.
   - The JVM test list for G6-HM2: several fingers at once, cancel, a finger sliding off, the D-pad's angle edges, reset,
     the stick sign (stubbed for HM5).
5. **Slots and D2's 5 s rule.** Read `PadSlots.kt` and `PlayerPrompt.kt` and settle how a `TouchPadDevice : PadDevice`
   fits:
   - its key and sources;
   - whether `isVirtual` or the B38 eligibility test would exclude it;
   - how it claims P1 at 5 s without a hold;
   - what the prompt shows meanwhile;
   - the effect on the stored "highest joined count";
   - how a real pad joining afterwards becomes P2.

   If a choice is not fixed by D2, list it as a question for the user, with options. Do not pick.
6. **The pointer guard.** A touchscreen-only exemption, used by the subclass only. Mouse, touchpad and the DualShock
   touchpad stay consumed. Show from `isPointerSource` and `dispatchTouchEvent` that the onn's path is unchanged.
7. **Release safety.**
   - What clears the touch pad: a finger's up, cancel, focus loss, the view being hidden or detached, and `onPause`
     (the existing `neutralize`).
   - The sender never goes silent, so the hub's input hold is never tripped.
   - Gesture-exclusion zones over the edge controls.
   - What Back does in handheld mode.
8. **`MainActivity`.** Where the Settings choice lives and how a game launch picks the activity. Hidden when the device has
   no touchscreen.
9. **Proof the onn is unchanged, for G6-HM2/HM3.**
   - Which diff checks show the base's default paths are untouched.
   - The project's APK confirmation rule (CL-B7 §6) before any new APK replaces `ca53df0d…`.
   - The tablet-side cells for HM3, read from the decoder report the tablet already uploads.
10. **Open questions for the user**, each with options. Include at least: what the lower region shows when a real pad
    is P1; whether a later pad should take over P1; whether Back in handheld mode keeps today's "end to the paused frame".

## Files

- `docs/memory/handoffs/G6-HM1_PORTRAIT_DESIGN_TASK.md`: this task, copied in from
  `Claude outputs/G6_tablet/G6-HM1_PORTRAIT_DESIGN_TASK.md`.
- `docs/memory/evidence/g6_hm1_2026-11-19/design_written_before_code.md`: the design.
- `docs/memory/evidence/g6_hm1_2026-11-19/design.sha256`: its sha256.
- `docs/memory/architecture/G6_HANDHELD_PLAN_2026-11-19.md`: one dated line under the stages saying "G6-HM1 design
  written, awaiting the user's approval".
- `logs/g6_hm1_git_status.txt`: `git status --short`, this task's files only.

**Gates:** `tools/check_memory_health.py` passes; `git diff --check` is clean; the redaction check is clean; and
`git status --short` shows nothing of this task's outside `docs/` and `logs/`, and nothing at all under `PrivyHub/`.
Touch no other session's files. No address, serial, token or pairing code; device ids as 4 hex digits and "…"; no game
title.

Your last reply begins "YOU, now: commit", then:
- the design's sha256;
- one line per numbered point above, with what you settled;
- the open questions, each with its options.
