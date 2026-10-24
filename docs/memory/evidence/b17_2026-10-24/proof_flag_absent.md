# B17 — absent = today

- **Host** `companion/plugins/games.py`: the AST with B17's 3 items removed = HEAD's: **identical** (guard_end = self._first(query, 'guard_end') == '1'; if guard_end:; if guard_end:).
- **Client** `NativeStreamActivity.kt`: 9 added lines, 3 changed (the three stated: **yes**), 0 removed, 0 outside the forms; 3 comment-only lines added (set aside before the diff).

Result: **PROVEN**.

Changed lines:
```
- it.start()
+ if (!guardHoldsAudio) it.start()
- restart?.let { p -> restartGuard?.flush(p, { r -> postRestartReport(host, r) }, { postRestartStop(host) }) }
+ restart?.let { p -> restartGuard?.beginViaStart(p) }
- "?port=$VIDEO_PORT",
+ "?port=$VIDEO_PORT" + (if (restart != null) "&guard_end=1" else ""),
```

Added lines:
```
        val guardHoldsAudio = restartGuard?.prepareStart() == true


                restart?.let { p ->
                    restartGuard?.noteStartResponse(json.optBoolean("guard_end", false))
                    thread(start = true, isDaemon = true, name = "PrivyHub-Guard-Report") {
                        restartGuard?.reportAfterStart(p) { r -> postRestartReport(host, r) }
                    }
                }
```
