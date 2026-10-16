---
memory_schema: 1
as_of: 2026-10-16
status: TASK HANDOFF — G8-P1 (session B, unattended): a user-space network-impairment shim so ROADMAP §G8's adverse-network characterization (reduced bandwidth, added latency, jitter, random loss, burst loss, reordering) can run from the suite without `nft` or `sudo` — the two things Code cannot use and the user has had to do by hand (D-BASE R3B). The shim sits on the loopback hop between the encoder's RTP output and the FEC sender, behind `PRIVYHUB_IMPAIRMENT=<profile>` (absent = today, byte for byte: the shim is not in the path). Proved in process. No stream
---

# G8-P1 — the impairment shim

**Why it can be user-space.** The companion's media path already has a
loopback hop: the encoder sends RTP to the loopback FEC sender (port
48110, E4-S5B's wire check), which forwards to the client. A process in
between on the loopback can delay, drop, reorder and rate-limit packets
with no privileges, and the FEC sender, the client and every Phase C
mechanism downstream see a real impaired stream. It impairs only the
host → client media direction (video, and audio if it shares the hop —
say which); the controller return path and the client → host direction
are untouched (stated as the shim's limit; the nft harness remains the
whole-link tool).

Read first: `companion/native_stream.py` (the encoder command's RTP sink,
the FEC sender's listen/forward), `D_BASE_P3_…` / `P6_…` (sender pacing,
frame-tail control — the shim must not defeat them in ways the record
cannot explain), `C4_M1_…` (FEC 8+1), `D_BASE_R3B_…` (the nft harness's
profiles: what loss/latency shapes were used, so the shim's profiles
match them), `G5_S1_…` (the classifier the shim's output will be read
with).

## 1. The design (in the record §1 before the code, hashed)

- `companion/impairment.py`: a UDP relay on the loopback. With the flag,
  the encoder's sink becomes the shim's port and the shim forwards to
  the FEC sender's port; without the flag, no process, no port, the
  encoder command byte for byte as today.
- **Profiles** (named, in a table in the module and the record; the
  ROADMAP §G8 list): `loss-1`, `loss-5` (random % loss), `burst-50x20`
  (bursts of N packets every M s), `delay-50`, `delay-150` (ms), `jitter-30`
  (ms, uniform), `reorder-5` (% delayed one slot), `cap-6000`, `cap-4500`
  (kbit/s token bucket with a bounded queue — the queue depth reported,
  never unbounded, per §G5 "do not hide a bad WAN path with
  ever-growing buffers"), and combinations by `+`. Deterministic with a
  seed; the seed and the profile in the run's record.
- **Telemetry:** the shim counts in/out/dropped/delayed/reordered
  packets per second to `impairment.jsonl`; the suite picks it up when
  the flag is set.
- **Cost:** ≤ 1 point of a core at 7 Mbit/s (measured in process).

## 2. The proof (in process, no stream)

- A synthetic RTP source → shim → a capture socket, per profile, 60 s:
  the measured loss / delay / jitter / order / rate match the profile
  within stated tolerances (a table).
- The shim in front of the **real FEC sender** code (in process, its
  module imported, loopback only): the sender's recovered / unrecoverable
  counters respond as expected to `loss-1` (recovered) vs `burst-50x20`
  (unrecoverable groups), and the G5-S1 classifier reads the synthetic
  heartbeat as `lossy` / `capacity-limited` accordingly.
- Flag absent: the encoder command builder's output byte for byte
  (E4-S5B's masked-hash method); no port bound.
- Unit tests; the redactor.

## 3. The record

`evidence/G8_P1_IMPAIRMENT_SHIM_2026-10-16.md` + `g8_p1_…/` (design +
hash, the diff, the profile table, the proof tables, test output,
`redact_check.txt`, `manifest.sha256`); ROADMAP §G8 status ("harness
built; envelope not measured"); `patches/G8-P1_…md`;
`logs/g8_p1_git_status.txt`. **Proposed next (not run):** G8-S1 — the
E1 PS1-STREAM row under each profile on the LAN, 10 min each, with
G5-S1 on and G5-S2 off/on — ~3 h unattended, no hands, the first
adverse-network envelope. Then `SESSION_B_DONE_2026-10-16C2.md`.
