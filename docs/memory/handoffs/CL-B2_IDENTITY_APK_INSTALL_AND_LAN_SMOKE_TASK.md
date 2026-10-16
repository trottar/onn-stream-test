---
memory_schema: 1
as_of: 2026-10-16
status: TASK HANDOFF — CL-B2: install G3-S2's APK on the onn as the CONFIRMED client (the user's say-so, 2026-10-16), pair it on the LAN, and run G3 end to end on the LAN with the host flag on: signed setup, token, declared endpoints, a real PS1-STREAM session, then the flag off and the legacy path shown unchanged. Runs only after the watch is stopped (E4-S4C) and only if G3-S2's record exists. The host flag is not adopted; the APK is
---

# CL-B2 — the identity APK on the onn; G3 end to end on the LAN

Read first: `CL_B1_APK_ADOPTION_2026-09-30.md` (how the CONFIRMED APK
is installed, hashed and checked by the state tools), `G3_S2_…` (the APK
built, its sha256, the client setting `identity_v2`), `G3_S1_…` §1 (the
pairing command on the host), E3-A3B's validity reading.

1. **Precondition:** the watch inactive; `--check` five lines; the
   CONFIRMED APK's hash as recorded by CL-B1. **The release APK if G3-S2
   built it; else the debug APK, stated** (CL-B1 says which flavour the
   CONFIRMED one was; if it was release and only debug exists, stop and
   say so).
2. **Install** (`adb install -r`), the new hash written into the state
   tools' CONFIRMED value (`patches/CL-B2_…md`), `--check` passes. With
   `identity_v2` **off** (the default) and the host flag absent: one
   PS1-STREAM ×10 min — today byte for byte (the host handlers' replay
   comparison, the suite's host-side gates).
3. **Pair:** host flag on (`e3_flag.conf` = `PRIVYHUB_SESSION_IDENTITY=v2`,
   restart); the pairing window opened by the host's command; the code
   entered on the onn (the user, by hand, on the TV — the task waits for
   the user: say so and wait, up to 10 min); `paired_devices.json` holds
   one device; the audit log shows `pairing_ok`.
4. **End to end:** `identity_v2` on; one PS1-STREAM ×20 min through the
   normal client flow: the audit shows nonce → signed setup → token →
   calls with the header, endpoints **declared** (the host's chosen
   targets = the declared ones, the source recorded as routing evidence
   only); the stream's host-side gates as E4-S1's PS1-STREAM (RetroArch ≥
   59.9, capture 60 ± 0.1, dup+drop ≤ 0.2/min, host CPU within E1's band);
   the link reported. Then: a forged token from the host side (`curl`
   with a bad header) → 401 and audited; the pairing removed → setup
   refused `device-unknown`, the client shows the reason; re-paired.
5. **Flag off, setting off:** restart; one PS1-STREAM ×10 min; today's
   behaviour; `flags_absent` true. The APK stays (adopted as CL-B2).
6. The record `evidence/CL_B2_IDENTITY_APK_AND_LAN_SMOKE_2026-10-16.md`
   + `cl_b2_2026-10-16/` (the runs, the audit log excerpts with no
   address or token, the hashes, `manifest.sha256`, `--check`,
   `validity.json`, `redact_check.txt`); `logs/cl_b2_git_status.txt`.
   **Adoption lines for the user, written, not applied:** the host flag
   (`session-identity.conf`, `Environment=PRIVYHUB_SESSION_IDENTITY=v2`)
   and the client setting. Then the queue's close.
