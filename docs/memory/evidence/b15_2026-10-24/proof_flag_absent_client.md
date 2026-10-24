# B15 (client) — property absent = today (only added lines, all in the allowed forms)

| file | removed / changed | added | outside the forms |
| --- | ---: | ---: | ---: |
| `NativeStreamActivity.kt` | **0** | 14 | **0** |

Result: **PROVEN**. `thermalSampler?.stop()`, `sessionStarted = false`, `stopLocalPipeline()` and `return` are the body of the one `if (restartGuard?.handOver(...) == true)`, which is false without the property. `RestartGuard.kt` (B11's file, +B15) is reached only through `restartGuard`, null without the property.

```

        // B15: the guard's pending kept beyond this object (a private file), and this instance's place in its process
        // (null = today)
        restartGuard?.attach(FilePendingStore(File(noBackupFilesDir, RestartGuard.STORE_FILE)),
            RestartGuardProcess.nextInstance(), RestartGuardProcess.mark)

        // B15: a recreation hands the open session to the next instance's start (report, stop, start in order); a
        // pending another instance already flushed is not posted twice (null = today)
        if (restartGuard?.handOver(isChangingConfigurations, sessionStarted) { cacheSessionReport() } == true) {
            thermalSampler?.stop()
            sessionStarted = false
            stopLocalPipeline()
            return
        }
```
