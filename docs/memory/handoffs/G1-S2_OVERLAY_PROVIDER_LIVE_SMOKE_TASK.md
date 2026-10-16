---
memory_schema: 1
as_of: 2026-10-16
status: TASK HANDOFF — G1-S2: the overlay provider's live smoke on the running companion. Tailscale is installed and logged in on the hub (the user, by hand, 2026-10-16; never touched by Code). The companion reads it through G1-S1's provider behind `PRIVYHUB_OVERLAY_PROVIDER=tailscale`; then the flag comes off and `/status` is checked byte for byte. No stream. Nothing adopted; nothing committed
---

# G1-S2 — the overlay provider, live

Read first: `evidence/G1_S1_…` §3 and `companion/overlay/`;
`e3_flag.conf`'s use in E3/E4 (the flag drop-in, written for a run,
removed at teardown); `tools/e3_state.py`.

1. **Before:** `tools/e3_state.py --check` (five lines, no flag);
   `curl -s localhost:8765/status` saved as `status_before.json`;
   `python3 -m companion.overlay --state --provider tailscale` with the
   binary now present: expect `available: true`, `connected: true`,
   `path` direct or relayed, `endpoint: present` + hash, a DERP region
   name in diagnostics; **nothing else from the binary's output is
   written** (no names, IPs, keys, tailnet).
2. **With the flag:** `e3_flag.conf` = `Environment=PRIVYHUB_OVERLAY_PROVIDER=tailscale`,
   `daemon-reload`, restart the companion, wait for `/status`; read the
   `overlay` object: the contract's fields and nothing more; one log
   line for the state change; the companion's CPU and PSS 60 s later
   (the provider must cost nothing measurable: ≤ 0.5 point of a core,
   ≤ 2 MB). `status_with_flag.json`. Then `tailscale netcheck` through
   the provider's diagnostics: direct/relayed and the region, recorded.
3. **Flag off:** remove `e3_flag.conf`, `daemon-reload`, restart;
   `status_after.json` **byte for byte equal to `status_before.json`**
   except fields that are time or counters (name them); `--check`
   passes; `flags_absent` true.
4. The record `evidence/G1_S2_OVERLAY_PROVIDER_LIVE_SMOKE_2026-10-16.md`
   + `g1_s2_2026-10-16/` (the three status files, the `--state` output,
   the CPU/PSS reading, `redact_check.txt`, `manifest.sha256`);
   `logs/g1_s2_git_status.txt`. **The adoption line, written, not
   applied:** `overlay.conf` with `Environment=PRIVYHUB_OVERLAY_PROVIDER=tailscale`
   — the user's call; the provider is read-only, so adopting it changes
   only what `/status` reports.
