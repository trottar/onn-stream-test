---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 3107fb5 (G1-S1 / G3-S1 / G3-S2 uncommitted beside it, not touched)
---

# G1-S2 — the overlay provider, live

**Classification: PASSED; not adopted.** On the running companion,
G1-S1's Tailscale provider (behind `PRIVYHUB_OVERLAY_PROVIDER=tailscale`)
reads the hub's overlay as connected.

- `/status` gains the `overlay` object, with the contract's fields and
  nothing more, and one log line.
- It costs +0.28 point of a core and +0.55 MB.
- With the flag off, `/status` is byte for byte the same as before,
  except the process id.
- **Path `no-peer`:** no other device was online in the tailnet, so
  direct vs relayed could not be seen. That needs a second device online:
  G4's off-site test.

Task: `handoffs/G1-S2_OVERLAY_PROVIDER_LIVE_SMOKE_TASK.md`, session A
item 2 of `QUEUE_2026-10-16.md`. Files: `g1_s2_2026-10-16/`. Tailscale
was installed and logged in on the hub by the user, by hand, on
2026-10-16. Code ran only read commands (`tailscale status`, `netcheck`):
no `up` / `down` / `set`, no sudo.

**The tree loaded by the restarts** was HEAD `3107fb5` plus G1-S1 / G3-S1
(and session B's G3-S2 as it stood), uncommitted. With their flags
absent, that code behaves as today byte for byte: G1-S1 §4 and G3-S1's
replay comparison. This smoke's own before/after check (§3) agrees for
`/status`.

## 1. Before (02:09Z)

- `tools/e3_state.py --check` (`check_before.json`): ok. Five lines, no
  `e3_flag.conf`, no game.
- `status_before.json` (`GET /status`, 547 bytes): no `overlay` key.
- `python3 -m companion.overlay --state --provider tailscale
  --diagnostics` (`overlay_state_before.json`), the binary present:
  - `available: true`, `connected: true`, `reason: running`;
  - `path: no-peer`, `peer_ready: false`;
  - `mtu: 1280`;
  - `endpoint: present`, `endpoint_hash: 757c5de7`;
  - diagnostics: `backend_state Running`, `peers_online 0`,
    `peers_direct 0`, `netcheck_udp true`,
    `netcheck_mapping_varies false`.
- **The DERP region:** the provider's diagnostics carry no region
  field. `tailscale netcheck`'s text was read in memory and only these
  lines kept (`netcheck_region.txt`):
  - `UDP: true`;
  - `MappingVariesByDestIP: false`;
  - `PortMapping:` (none);
  - **`Nearest DERP: Ashburn`**.
- Nothing else from the binary's output was written: no names, addresses,
  keys or tailnet.

## 2. With the flag (02:10Z)

- `e3_flag.conf` (`e3_flag.conf.txt`):
  `[Service]` / `Environment=PRIVYHUB_OVERLAY_PROVIDER=tailscale`.
  Then `daemon-reload` and a restart. MainPID serves 8765, and the
  environ is the five lines plus the flag (`restart_with_flag.json`).
- **`/status`'s `overlay` object** (`status_with_flag.json`):
  `provider tailscale, available true, connected true, path no-peer,
  peer_ready false, mtu 1280, reason running, endpoint present,
  endpoint_hash 757c5de7`.
  - These are the contract's fields only: no endpoint value and no
    diagnostics.
  - It held the same through 12 polls (`cost_flag_on.json`).
- **One log line** for the state change (`overlay_log_lines.txt`):
  `overlay: provider=tailscale available=True connected=True path=no-peer peer_ready=False mtu=1280 reason=running endpoint=present`.
- **The cost** (`g1_s2_cost.py`, the same reading in both arms, 10 s
  after the restart: `/status` every 5 s for 60 s; the unit cgroup's CPU,
  including the provider's `tailscale` child processes; the MainPID's
  PSS):

  | arm | CPU, % of a core | PSS at end |
  | --- | --- | --- |
  | flag on | 0.333 | 27,549 kB |
  | flag off | 0.053 | 27,000 kB |
  | **the provider** | **+0.28** (≤ 0.5 ✓) | **+0.55 MB** (≤ 2 ✓) |

  The CPU is the provider's two CLI reads per cache expiry, under a
  5-s poll. With nobody polling `/status`, it reads nothing.

## 3. Flag off (02:12Z)

- `e3_flag.conf` removed (the per-run flag drop-in, as in E3 / E4), then
  `daemon-reload` and a restart (`restart_after.json`: the five lines).
- **`status_after.json` vs `status_before.json`:** byte for byte equal
  except **`server.pid`**, the process id, which is new after the
  restart. No `overlay` key.
- `tools/e3_state.py --check` (`check_after.json`): ok. Five lines, no
  `e3_flag.conf`.
- **flags_absent: true.** The manager has none, the environ is exactly
  `ADOPTED`, and no flag or constraint drop-in exists.

## 4. The adoption line (written, not applied; the user's call)

- `~/.config/systemd/user/privyhub-companion.service.d/overlay.conf`:

  ```
  [Service]
  Environment=PRIVYHUB_OVERLAY_PROVIDER=tailscale
  ```

  Then `systemctl --user daemon-reload`, restart the companion, and add
  the line to `tools/e1_suite.py`'s `ADOPTED` (six names).
- **Revert:** delete `overlay.conf`, `daemon-reload`, restart, and take
  the line out of `ADOPTED`.
- The provider is read-only. Adopting it changes only what `/status`
  reports: the `overlay` object and its log line.

## 5. Files

`g1_s2_2026-10-16/`:

- `baseline_head.txt`, `git_status_at_start.txt`;
- `check_before.json`, `check_after.json`;
- `status_before.json`, `status_with_flag.json`, `status_after.json`;
- `overlay_state_before.json`, `netcheck_region.txt`, `e3_flag.conf.txt`;
- `restart_with_flag_at.txt`, `restart_with_flag.json`,
  `restart_after.json`, `overlay_log_lines.txt`;
- `g1_s2_cost.py`, `cost_flag_on.json`, `cost_flag_off.json`;
- `redact_check.txt`, `manifest.sha256`.

Also `logs/g1_s2_git_status.txt`. Nothing adopted; nothing committed.
