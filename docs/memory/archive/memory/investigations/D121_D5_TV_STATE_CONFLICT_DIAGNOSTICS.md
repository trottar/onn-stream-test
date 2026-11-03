# D-121 — D5.4 stale-write conflict diagnostics

**Status:** diagnostic-only / runtime interaction required

## Narrow question

When the onn attempts a durable write from a stale remembered Linux revision:

1. does Linux reject it without changing authoritative state;
2. does Android persist the D-120 conflict metadata;
3. can normal authoritative pull restore exact parity afterward?

## Method

D-121 is diagnostic-only.

Prepare:
- require exact Linux/onn parity;
- save the original Linux user state privately in ignored mode-0600 state;
- advance Linux by one revision using only a temporary `country_name` marker;
- leave the onn on the previous revision.

User action:
- remain inside the already-open TV UI;
- do not return to the top-level source list;
- do not press Refresh;
- long-press one visible channel;
- toggle its Favorite state exactly once.

That local durable mutation uses the real production push path with the stale
remembered revision.

Verify:
- require D-120 conflict timestamp to advance;
- require conflict base revision = original onn revision;
- require conflict server revision = prepared Linux revision;
- require Linux revision/hash to remain exactly the prepared state;
- restore original Linux user-state content by one new revision.

Final:
- press normal TV Refresh once;
- require exact original durable-state hash on Linux and onn;
- require onn remembered revision = restored Linux revision;
- require last successful action = `pulled`;
- require the conflict diagnostics remain visible.

The temporary Favorite mutation is intentionally discarded by the final
authoritative pull.

## Safety

The probe never changes `country_code`.

No IP address or device identifier is requested, stored, or printed.

If Linux changes independently while the diagnostic marker is active, D-121
refuses to overwrite it.
