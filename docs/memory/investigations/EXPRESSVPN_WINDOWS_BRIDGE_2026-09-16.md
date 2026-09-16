---
memory_schema: 1
as_of: 2026-09-16
status: deferred
---

# Temporary Windows router / ExpressVPN forwarding — 2026-09-16

## Status

**DEFERRED BY DESIGN**

## Question

Can the temporary Windows development PC simultaneously:

1. route the PrivyHub GL-iNet/onn path to the Ethernet-connected Linux server;
2. provide downstream Linux Internet; and
3. keep ExpressVPN connected for Windows traffic?

## Evidence

The physical ExpressVPN packet filter `expressvpn-pkf` was first shown to block
the routed Wi-Fi-to-Ethernet PrivyHub path. Disabling it on both physical
adapters restored local Linux/PrivyHub communication.

A later asymmetric-binding test was abandoned after the useful discriminator
was obtained. With both physical bindings disabled:

- VPN off -> Windows and Linux Internet both work;
- VPN on -> Windows Internet works, Linux reaches its Windows gateway, but Linux
  Internet fails.

Windows forwarding flags remain enabled. No active `NetNat` object or ICS share
is responsible. The selected Windows Internet route changes to the ExpressVPN
interface while the VPN is active.

## Classification

This is not:

- a Linux Ethernet/link failure;
- a Linux default-gateway failure;
- a PrivyHub service failure;
- an IP-forwarding-disabled failure;
- an active ICS/NetNat configuration failure.

It is a limitation of forwarding a downstream Linux host through the active
ExpressVPN route in this temporary Windows-as-router topology.

## Decision

Do not spend further Phase-D engineering time on this bridge.

Development workaround:

- keep the physical `expressvpn-pkf` bindings disabled for the known-good routed
  PrivyHub path;
- disconnect ExpressVPN when the Linux host needs upstream Internet.

## Re-entry condition

Reopen only if Windows-as-router becomes a lasting product requirement or if a
future network change produces contradictory evidence. The intended PrivyHub
architecture should give Linux an independent network path instead.
