# B11 (client) — property absent = the CONFIRMED client (only added lines, all in the allowed forms)

| file | removed / changed | added | outside the forms |
| --- | ---: | ---: | ---: |
| `NativeStreamActivity.kt` | **0** | 44 | **0** |

Result: **PROVEN**. New file `RestartGuard.kt` is reached only through `restartGuard`, null without the property.

```
        // B11: the guard keeps the cached report and the cause for the next start (null = today)
        if (sessionStarted) {
            restartGuard?.onSurfaceLost(
                cachedSessionReport,
                decoder?.lastOutputAgeMs() ?: -1L,
                if (lastRtpAdvanceAtNs > 0L) (System.nanoTime() - lastRtpAdvanceAtNs) / 1_000_000L else -1L,
                recoveryActive
            )
        }

        // B11: when the activity last paused, for a self-restart's cause (null = today)
        restartGuard?.notePause()
                // B11: a self-restart first ends the old session: its report, then native-stream-stop (null = today)
                val restart = restartGuard?.takePending()
                restart?.let { p -> restartGuard?.flush(p, { r -> postRestartReport(host, r) }, { postRestartStop(host) }) }

                // B11: the host restarted its audio at sequence 0: a fresh receiver, its start-up hold re-armed
                if (restart != null) {
                    audioReceiver?.stop()
                    audioReceiver = NativeAudioReceiver(port = AUDIO_PORT)
                }


                // B11: the rebuilt receiver starts with the host's cushion and redundancy already in force
                if (restart != null) audioReceiver?.start()

        // B11: the activity ends; today's stop path posts the cached report and the stop (null = today)
        restartGuard?.onSessionStopped()
        // B11: the self-restart's cause (null = today: no key)
        restartGuard?.lastCause?.let { c -> root.put("restart_cause", JSONObject(c)) }


    // B11: the self-restart guard, only with debug.privyhub.restart_guard=1 (null = today).
    private val restartGuard: RestartGuard? by lazy { if (RestartGuardFlag.fromSystem()) RestartGuard() else null }

    // B11: the old session's report and stop, posted at a self-restart (the guard's transport)
    private fun postRestartReport(host: String, report: String) {
        httpPostBody("http://$host:$CONTROL_PORT" + DecoderReportUpload.PATH, DecoderReportUpload.encode(report),
            DecoderReportUpload.CONTENT_TYPE)
    }

    private fun postRestartStop(host: String) {
        httpPost("http://$host:$CONTROL_PORT" + "/plugins/games/native-stream-stop")
    }
```
