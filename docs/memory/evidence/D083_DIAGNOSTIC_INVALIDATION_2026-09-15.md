# D083 diagnostic invalidation — 2026-09-15

Status: **INVALID / superseded diagnostic branch**

This evidence note exists to prevent future chats from treating D083 or D083R1
as transport measurements.

## Last valid predecessor

D082:
`logs/transport_probe/opal_bridge_20260915_141216`

- host successful sends: 3661;
- Android unique arrivals: 3661;
- Android duplicates: 2371;
- Android missing: 0;
- `br-lan` PCAP: 24 bytes, zero records.

## Invalid D083 run

The router counter CSV contained fewer than two rows. Analysis aborted. The
runner's zero exit was itself a diagnostic bug.

## Invalid D083R1 run

The revised sampler launch used `nohup`. The router has no `nohup` command and
no BusyBox `nohup` applet. Setup therefore failed before evidence collection.

## Smoke-control correction

Direct `sh` execution wrote four CSV lines, demonstrating that the simple
counter reads can execute.

Raw `/proc/mounts`:
`tmpfs /tmp tmpfs rw,nosuid,nodev,noatime 0 0`

The helper's `tmp_noexec=YES` output contradicted that raw evidence and must be
ignored.

## Conclusion

D083's underlying networking question remains unanswered.
Resume from D082 if this investigation is ever reopened.
