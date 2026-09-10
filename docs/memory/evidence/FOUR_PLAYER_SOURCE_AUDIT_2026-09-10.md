---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
status: source-audit validated; runtime pending
---

# Four-Player Exact-Local Source Audit — 2026-09-10

The diagnostic-only probe ran against the authoritative local working tree and modified no production files. It collected no network addresses.

Classification: `EXPECTED_TWO_PLAYER_BASELINE_PROTOCOL_REUSABLE`.

## Raw architectural measurements

- Android `PLAYER_COUNT`: 2
- Windows `MAX_PLAYERS`: 2
- Android PHI1 packet allocation: 36 bytes
- Windows PHI1 struct: `<4sBBHIQIhhhhHH`
- PHI1 layout reusable for P3/P4 by current source evidence: true
- P1 textual profile/UI references: 17
- P2 textual profile/UI references: 19
- P3 textual profile/UI references: 0
- P4 textual profile/UI references: 0

## Exact audited production hashes

- `768bdd6e43550acf7d12ba0b6884629a8716b27fad3b4555ed0f8bb1fa47c55f` — `PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/NativeControllerSender.kt`
- `2e694d58dab56294e32097c92f88f66cabfbae4e0763f6bba6d10a04baf87d47` — `companion/native_session_io.py`
- `99597dbb1b110022b839ae88a092a9b5292b7f32911651fb6910f6def35b8c00` — `companion/plugins/games.py`
- `ecc171763255f4bce42af729691a2e001d7f269c31e701aa95dc73096c881e6c` — `companion/games/emulator_manager.py`
- `5a24b794cd1fb20953f729feb5a90d1627c81ebe3cf67eb02eaebf12ddc7dc6d` — `PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt`

## Interpretation

The two-player restriction is an explicit count/state limitation, not a demonstrated PHI1 packet limitation. Android already assigns descriptors to the first unused player index and sends one packet per configured player. Windows already creates ViGEm devices in a `MAX_PLAYERS` loop and validates the packet's player byte against that count.

Decision: preserve PHI1 v1/36-byte/global-sequence semantics for the base four-player extension. Generalize count-backed state to four and prove real ViGEm/XInput slots before changing A8 Player 3/4 profile/editor behavior.

The exact raw probe output is preserved at `evidence/raw/four_player_source_audit_2026-09-10.txt`.

This evidence does not itself prove four-player runtime behavior.
