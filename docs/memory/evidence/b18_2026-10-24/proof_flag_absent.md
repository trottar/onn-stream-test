# B18 — absent = today

| file | B18 items removed | AST then = predecessor |
| --- | --- | --- |
| `companion/games/link_drop_recovery.py` | 2: `_session_end: Any = None`; `if self._session_end is not None and self._session_end.blocks_hold(self):` | **identical** |
| `companion/plugins/games.py` | 1: `if getattr(self._recovery, '_session_end', None) is not None:` | **identical** |

- `companion/rewind_cores.py` (B9's module, imported only with PRIVYHUB_INPUT_HOLD_REWIND): +86 −0, listed in `b18.diff`.
- `companion/stall_signal.py` (B7's module, imported only with PRIVYHUB_STALL_SIGNAL): +8 −1, listed in `b18.diff`.
- `PrivyHub/app/src/main/java/streaming/StallSignal.kt` (the StallMonitor exists only with debug.privyhub.stall_signal): +24 −0, listed in `b18.diff`.

- `PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`: 0 removed, 11 added, 0 outside the forms. Without the property `stallMonitor` is null: the block is `if (isFinishing) { null?.let {…} }`, which does nothing.

Result: **PROVEN**.

```
        }

        // B18: a finishing activity tells the host its session is ending, before the sender stops (null = today)
        if (isFinishing) {
            stallMonitor?.let { m ->
                m.requestBye()
                val until = System.nanoTime() + 60_000_000L
                while (m.byesSent == 0L && System.nanoTime() < until) {
                    Thread.sleep(5L)
                }
            }
```
