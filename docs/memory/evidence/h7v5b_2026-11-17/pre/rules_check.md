# Steps 2-6 — the setups read as the onn reads them; the rules folder checked read only (nothing relearnt, copied or renamed; ids replaced)

- **T88's cheat setup** (`cheat-profiles`, the one with slot 1): source 0, indexes [9]; its slot 1 `be4aa243…`
  - the spec: `(2, 0.082, {'end_P1': 0.1044, 'end_P2': 0.0983, 'start': 0.0958}, 0.0921, 12244, 104)` — as B132 lists: **True**
  - the setup's begin in the rules folder `be4aa243…` (expected `be4aa243…`): **True**; the sidecar's `cheat` names this setup (source, indexes, `profile_id`): **True**; `players` 2
- **T89's cheat setup** (`cheat-profiles`, the one with slot 1): source 0, indexes [0, 6]; its slot 1 `78c53af3…`
  - the spec: `(3, {'end': 0.1011, 'start': 0.0932}, {'1': 0.2212, '2': 0.2218, '3': 0.1744, '4': 0.1915}, 0.0796)` — as B132 lists (the place thresholds read in port order 1-4: [0.2212, 0.2218, 0.1744, 0.1915]): **True**
  - the setup's begin in the rules folder `78c53af3…` (expected `78c53af3…`): **True**; the sidecar's `cheat` names this setup (source, indexes, `profile_id`): **True**; `players` 4

**All as H7-V5 left them: True.** (A first reading compared the place thresholds as a list against the spec's ports-keyed object — the comparison's shape, not the spec; re-read in port order.)
