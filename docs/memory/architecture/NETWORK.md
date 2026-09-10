---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Network Architecture

The prototype is not a flat same-LAN design. The onn client is on an isolated secondary network and the Windows companion remains on the trusted/home network. Explicitly routed service ports connect the two sides.

Production endpoint flow is request-derived rather than permanently hard-coded: Android stores the companion host, contacts the companion control API, and the companion learns the live client endpoint from that request for native streaming. Development ADB transport is separate from production routing.

Do not redesign this topology casually and do not ask the user to paste network addresses.

Current logical service separation:

- control API: TCP 8765;
- media serving: TCP 8000;
- native game video: UDP 48100;
- native game audio: UDP 48101;
- native controller input: UDP 48102.

The severe bidirectional burst/gap/duplication behavior observed in the Prototype 1 physical/network path is documented and deferred. Do not tune product buffering around that environment unless representative infrastructure reproduces it.
