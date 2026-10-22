# B1 proof (in process, loopback only)

## A. The downlink

- `blackout-4s@down,every=20s,first=10s`, 60 s: sent 43200, received 34560, dropped 20.0 % (`dropped_blackout` 8640); dark spans start [9.984, 29.984, 49.984] s, last [4.008, 4.008, 4.008] s (the gap between the last packet before and the first after: 4 s + one frame). Tolerance: 3 spans at 10 / 30 / 50 s ± 2 frames, each 4 s + 1 frame ± 2 frames, 20 % ± 0.5: **MET**.
- `blackout-4s@both` (defaults: every 120 s, the first at 120 s), 60 s: dropped 0: **MET** (nothing before 120 s).
- The shim thread's CPU: 1.92 % / 2.11 % of a core (G8-P1: 2.1-7.0 %).

## B. The uplink (the real controller-bridge receive loop)

- 430 packets/s for 60 s: sent 25800, applied 20640, `uplink_dropped` 5160 (the schedule's count of sends in the dark: 5160).
- Applied-packet gaps > 60 ms: [(9.998, 4.003), (29.998, 4.002), (49.998, 4.002)] (start s, length s).
- Recovery's silence callback (threshold 1,000 ms): 3 calls at [(11.0, 1000), (31.0, 1000), (51.0, 1002)] (s, ms).
- Neutralize calls at [10.25, 30.25, 50.25, 60.26, 60.26] s (once per blackout, ~250 ms in).
- Tolerance: 3 gaps of 4.0 s ± 60 ms at 10 / 30 / 50 s, no other, 3 silence calls, the drop count ± the sender's 1 % timing: **MET**.

## C. Both directions on one clock

- Downlink dark spans start [9.985, 29.985, 49.985] s, uplink [9.999, 29.999, 49.999] s after the shared epoch: within [14, 14, 14] ms. Tolerance ≤ 20 ms + 2 frames: **MET**.

## D. The HTTP gates

- heartbeat / client_health at [5.0, 10.5, 13.9, 14.1, 31.0] s: [(False, False), (True, True), (True, True), (False, False), (True, True)]; counted {'controller': 0, 'heartbeat': 3, 'client_health': 3}: **MET**.

## E. Flag absent

| file | the function holding the hook | AST, every guarded B1-B3 statement removed, == HEAD's |
| --- | --- | --- |
| `companion/native_session_io.py` | `_receive_loop` | **identical** |
| `companion/plugins/games.py` | `handle_post_request` | **identical** |
| `companion/privyhub_service.py` | `do_POST` | **identical** |

- A fresh process with no flag, importing `native_session_io`: `impairment` imported / the gate = `False None` (want `False None`).
- **MET**.

## F. The cost

- The gate: 122 ns a call (outside a blackout); at 430 controller packets/s that is 0.0053 % of a core. The heartbeat / client-health gates run once per 2 s.
- The shim thread: §A's line (G8-P1's cost bar, reported there as not met, is not re-litigated).

**All: MET**
