---
memory_schema: 1
as_of: 2026-11-06
baseline_commit: 795d80d4
---

# B43 — the movie retry made real (the token refetched; a companion restart survived; B40's refusal window)

**Result: SETTLED + BUILT.**
- **Tests:** JVM 8 new (203 / 203); host 7 + 3 new (B40's 14 and B35's 9 unedited); every suite as the baseline.
- **Mutations:** 4 caught.
- **Proof:** absent = `0132b944…`'s behaviour, PROVEN. No live run. Nothing committed.
- **Record:** `evidence/B43_VOD_RETRY_TOKEN_2026-11-06.md`. Diff: `evidence/b43_2026-11-06/b43.diff`.

- **Settled:**
  - a companion restart ends the hub's sessions, and the onn's cached media token (a per-request header) is then
    refused 401. Nothing on the media path dropped it, so B35 retried with it and named the refusal "connection lost";
  - Media3 1.11.0's own reconnect covers any outage its 15-30-s buffer covers (retry ≤ 5 s; it surfaces only when the
    buffer is spent with errorCount > 3). A drop must outlast ~35 s to reach B35, so the demonstration is `drop 45`.
- **Client, inside `debug.privyhub.vod_retry=1`:**
  - each error's `reason` (`reset` / `refused` / `timeout` / `401` / `403`);
  - a refusal refetches the token (the identity session's fresh setup) and then retries at once;
  - three refusals after refetches end as `refused`, never "lost". "Lost" is only past the 150-s bound with no answer;
  - the Retry button refetches; rows gain `reason` / `token_refetched` / `kind`.
- **Host:**
  - B35's client log whitelists the three fields;
  - B40's control file line `drop <seconds>` (0-600) resets the stream, then answers every new `/vod/` request with an
    RST for that long (rows `refuse_s`, `vod_refuse_ended` `vod_refused`). A plain line or `drop 0` = B40 as built;
    only appended bytes are read.
- **Apply:** `git apply evidence/b43_2026-11-06/b43.diff` from the repo root.
  - **Client:** it acts only in an APK built with it and with `debug.privyhub.vod_retry=1`.
  - **Host:** the window only with `PRIVYHUB_VOD_DROP_TEST=1` (bench, never adopted); the fields only with
    `PRIVYHUB_VOD_LOG=1`.
- **Rollback:** the property empty and no host lines (today's); or `git apply -R` the diff.
