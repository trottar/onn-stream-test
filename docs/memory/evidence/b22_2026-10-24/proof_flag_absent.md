# B22 — absent = today

## Host

- `companion/plugins/games.py`: 4 B22 items removed — `_restart_fast = None`; `(os.environ.get('PRIVYHUB_RESTART_FAST') or '').strip() == '1'`; `_restart_fast is not None`; `_restart_fast is not None and guard_end and _restart_fast.RestartFast.eligible(self._native_stream) -> its else` → AST **identical** to the predecessor's.
- `companion/native_stream.py`: `git diff HEAD` empty.
- `companion/restart_fast.py`: new, imported only under the flag (`tests/restart_fast` `test_nothing_imported`).

## Client (`NativeStreamActivity.kt`)

- removed lines: 1 — `if (restart != null) audioReceiver?.start()`
- added code lines (not blank / comment): 72, in 12 hunks

| hunk (new line) | code lines | first line | without the host key |
| --- | --- | --- | --- |
| 622 | 2 | `restartFast?.let { uiHandler.removeCallbacks(restartFastTick) }` | startSession: removes a tick that is not posted and sets null a field that is null |
| 797 | 1 | `val ssrcAtStart = restart?.let { receiver?.snapshot()?.ssrcChanges } ?: 0L` | a read of the receiver's counter at a guarded start; consumed only inside the key's block |
| 814 | 8 | `if (restart != null) {` | the key's block: `restartFast` set only when the response carries `restart_fast.armed` true |
| 829 | 1 | `restartFast?.reportDone = true` | null-safe: nothing without the key |
| 914 | 1 | `if (restart != null && restartFast == null) audioReceiver?.start()` | CHANGED line: = today's when `restartFast` is null |
| 1068 | 4 | `restartFast?.let {` | a `restartFast?.let` block: skipped without the key |
| 2381 | 9 | `restartFast?.let { r ->` | a `restartFast?.let` block: skipped without the key |
| 2478 | 28 | `}` | declarations: the field (null), the tick and its inputs (run only from the key's paths) (difflib aligned its first `}` with the preceding block's) |
| 3182 | 1 | `restartFast?.noteRelease()` | null-safe: nothing without the key |
| 3217 | 1 | `if (restartFast?.takeAudio() == true) audioReceiver?.start()` | null-safe: nothing without the key |
| 3240 | 1 | `if (restartFast?.takeAudio() == true) audioReceiver?.start()` | null-safe: nothing without the key |
| 3593 | 15 | `restartFast?.let { r ->` | a `restartFast?.let` block: skipped without the key |

- the one removed line is today's rebuilt-audio start, now `if (restart != null && restartFast == null)`: yes.
- `restartFast` is assigned a non-null value in one place only: inside `if (restart != null)` when the response carries `restart_fast.armed` true (a host with `PRIVYHUB_RESTART_FAST=1`); `restart_guard 0` → no guard → `restart` null.

Result: **PROVEN** (host: AST; client: every added line is null-safe on `restartFast`, a read, or reached only with the key; the changed line equals today's without it).
