---
memory_schema: 1
as_of: 2026-09-25
baseline_commit: 05aac43
durable_memory_updated: true
---

# C4-M1: the xor8_2 FEC comparison arm (companion + client; default off)

## Purpose

This is the measured arm that `decisions/C4_ADAPTIVE_FEC_2026-09-24.md`
asked for. Task: `handoffs/C4-M1_FEC_MEASURED_ARM_TASK.md` (authorized by
the user 2026-09-25). Record: `evidence/C4_M1_FEC_ARM_2026-09-25.md`.
**Outcome: NOT SHOWN; nothing adopted.**

## Change

- **`companion/native_fec_rs.py` (new)**: the GF(256) Reed-Solomon Q parity
  (encoder), with a reference decoder for the tests.
- **`companion/native_fec_relay.py`**: the scheme comes from
  `PRIVYHUB_FEC_SCHEME`. Unset is the adopted scheme, byte for byte
  (golden). Under `xor8_2` a v2 Q datagram follows each unchanged v1
  parity. Status shows `version`, `scheme_source` and `q_parity_*`.
- **`companion/native_stream.py`**: `encoder_overrides()` reports
  `fec_scheme_override`, and `any_override` includes it.
- **`PrivyHub/.../streaming/FecRs82.kt` (new)**: the client's decoder.
- **`PrivyHub/.../streaming/RtpH264Receiver.kt`**: accepts v2, merges P and
  Q into one group, and recovers one packet from Q when P was lost, or two
  packets with P + Q. The v1 path is unchanged.
- **Tests (new)**: `tools/test_fec_xor8_2.py` (9) and
  `PrivyHub/app/src/test/java/streaming/FecRs82Test.kt` (6).

**APKs:**

- arm: `d2d855d82c30f986472a9ee839ef6b75f5102cb19900ef6c745a937a8eb87a79`,
  installed for the night only;
- adopted: `f31b1c180c5d0849230860d2f5b7ab1b4a8637f7be56a7dcf1f71aba77668ae7`,
  reinstalled and confirmed at 05:56Z.

**The installed APK predates this source change.**

## Files (SHA-256 after)

```
421f2c9a2bf9c4a92fc14df0f559b9007f72fedc9f338fd0d9912da1d9b064a3  companion/native_fec_rs.py
699617215d00cc8c9ca28a390086ccf3a8a6b3ace0626ea56b05347b73c2874a  companion/native_fec_relay.py
27852bde12040a20d1f2ada0b56b9de91ad256cd77b9a65ed865d97063702614  companion/native_stream.py
8c90972906a772b38c70ca70366e2a49b08528de4f77db500b2e80339cbe7f9c  PrivyHub/app/src/main/java/streaming/FecRs82.kt
0d75d34ab3e7fe2088b45bd16b7b943fc326ac577fb081c198cc1828557dc56f  PrivyHub/app/src/main/java/streaming/RtpH264Receiver.kt
a0dc535a911e3cc0060b720d774fbcad3496e2f2de9bdcac5dc39a322401e8aa  PrivyHub/app/src/test/java/streaming/FecRs82Test.kt
2fff354447367a3566d1a4832ddcbe7d802d30841292be015502edb86c522ec5  tools/test_fec_xor8_2.py
```

Before: `evidence/c4_m1_2026-09-25/pre_patch_sha256.txt`. The diff against
HEAD is `c4_m1_patch.diff`.

## Rollback

1. Delete `native_fec_rs.py`, `FecRs82.kt` and the two tests.
2. Revert the three hunks (`c4_m1_patch.diff`).
3. Restart the companion through its unit.

With the variable unset, the relay's output is already unchanged.
