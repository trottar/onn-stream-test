---
memory_schema: 1
as_of: 2026-09-16
status: runtime-evidence
---

# D4 Linux runtime reconciliation evidence — 2026-09-16

## Scope

This evidence records the newest validated boundaries from the Linux migration
debug session and the subsequent ExpressVPN/Windows-bridge follow-up. It is
intentionally address-free.

## Persistent Linux prerequisites

Validated after reboot:

- `uinput` module auto-load configured in
  `/etc/modules-load.d/99-privyhub-uinput.conf`;
- `/dev/uinput` ownership rule applies;
- realtime priority allowance persists (`ulimit -r` observed as `1`).

Result: persistent uinput/module-load and RT-priority setup are closed for the
current development host.

## Routed network path

Temporary topology:

`GL-iNet -> Wi-Fi -> Windows -> Ethernet -> Linux`

Packet tracing showed ingress traffic on Windows Wi-Fi with no matching Ethernet
egress. Windows Firewall disable did not repair it. `expressvpn-pkf` was present
on both physical adapters. Disabling those bindings restored Linux reachability,
companion connection, game launch, and native streaming.

## ExpressVPN active-tunnel discriminator

With both physical `expressvpn-pkf` bindings disabled:

| State | Windows Internet | Linux -> Windows gateway | Linux Internet |
| --- | --- | --- | --- |
| ExpressVPN disconnected | working | working | working |
| ExpressVPN connected | working | working | failing |

Windows forwarding remained enabled. `Get-NetNat` and the ICS sharing query
returned no active configuration. Route inspection showed the selected Internet
route move from physical Wi-Fi to the ExpressVPN interface when connected.

Conclusion: the remaining Linux-Internet failure is above the local
Linux-to-Windows link and belongs to the temporary VPN/routing topology.

## Controller boundary

Validated:

- controller transport packets arrive with zero observed send errors in the
  captured session;
- Linux virtual pad is created;
- RetroArch detects P1;
- expected absolute axes are exposed;
- live `ABS_X` / `ABS_Y` events change with stick movement.

Conclusion: current PS1 movement failure is above transport/uinput generation,
inside RetroArch/core/session controller-mode behavior.

## LPS discriminator

Ordinary LPS was disabled successfully during one stream run, yet the run still
showed large sender/receiver socket errors and audio send errors. LPS is a real
driver fault but is not sufficient to explain the failed stream.

## Non-conclusions

- Android signing mismatch is not a runtime streaming diagnosis.
- The blocked fixed-bitrate audio probe does not disprove the validated Linux
  PulseAudio design.
- One Linux hard freeze does not establish memory leak/GPU/driver root cause.

## Re-entry rules

Do not reopen uinput, realtime priority, ICS, Windows Firewall, or temporary
ExpressVPN-bridge debugging without contradictory evidence. Investigate
RetroArch PS1 analog mode next.
