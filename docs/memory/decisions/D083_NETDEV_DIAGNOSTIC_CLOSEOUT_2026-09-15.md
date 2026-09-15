# Decision: close D083 branch without further router debugging

Date: 2026-09-15
Status: **Active**

## Decision

Pause the D083 netdev-counter branch and end the current Opal/Siflower
diagnostic session.

Do not issue another router diagnostic merely to repair D083.

## Rationale

Two diagnostic iterations failed for tooling/process reasons and produced no
network evidence. The current product goal is not to reverse engineer one
vendor router indefinitely.

D082 remains useful evidence: standard packet-capture points on the Opal are
blind to confirmed WLAN-to-WLAN traffic while endpoint duplication persists.

Any future re-entry must begin with a product-level decision: identify one
bounded measurement that would change the roadmap, or defer the vendor-specific
path to a different representative network/router environment.

## Guardrails

- raw evidence overrides classifier output;
- capability-check old/minimal router commands before use;
- do not suppress failure detail at the stage under test;
- fail closed on missing/insufficient evidence;
- do not call a hypothesis established until the targeted probe proves it.
