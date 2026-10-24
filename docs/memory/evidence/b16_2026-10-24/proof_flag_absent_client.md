# B16 (client) — the host's key absent = today (only added lines, all in the stated forms)

| file | removed / changed | added | outside the forms | the one gate | `fastReadyTick` only in `?.let` |
| --- | ---: | ---: | ---: | --- | --- |
| `NativeStreamActivity.kt` | **0** | 50 | **0** | yes | yes |

Result: **PROVEN**. `FastReady.kt` (new) is reached only through `fastReady`.

- no-op without a FastReady (`?.` on null): `fastReady?.let { uiHandler.removeCallbacks(fastReadyTick) }`, `fastReady?.let { f ->`, `root.put("fast_ready_releases", f.releases)`, `root.put("fast_ready_frame_to_post_ms", f.lastFrameToPostMs)`, `f.onRecoveryEntered(decoder?.renderedFrameCount() ?: 0L)`, `uiHandler.removeCallbacks(fastReadyTick)`, `uiHandler.postDelayed(fastReadyTick, 50L)`
- null to null: `fastReady = null`
- the one gate (false without the host's key) and its body: `if (json.optJSONObject(FastReadyHint.KEY)?.optBoolean(FastReadyHint.FIELD, false) == true) {`, `fastReady = FastReady()`
- declarations reached only through a FastReady: `@Volatile`, `private var fastReady: FastReady? = null`, `private val fastReadyTick: Runnable by lazy {`, `object : Runnable {`, `override fun run() {`, `val f = fastReady ?: return`, `if (!sessionStarted || stopping || !recoveryActive || gameplayReleased) return`, `if (f.tick(fastReadyInputs())) {`, `requestGameplayRelease()`, `return`, `uiHandler.postDelayed(this, 50L)`, `private fun fastReadyInputs(): FastReadyInputs =`, `FastReadyInputs(`, `recoveryActive = recoveryActive,`, `released = gameplayReleased,`, `requestInFlight = releaseRequestInFlight,`, `hostMetadataComplete = hostMetadataComplete,`, `waitingForIdr = receiver?.snapshot()?.waitingForIdr ?: true,`, `renderedFrames = decoder?.renderedFrameCount() ?: 0L,`, `outputAgeMs = decoder?.lastOutputAgeMs() ?: -1L,`

```
        // B16: a new session waits for its own host's fast ready (null = today)
        fastReady?.let { uiHandler.removeCallbacks(fastReadyTick) }
        fastReady = null

                // B16: the host's fast ready, only with PRIVYHUB_STALL_RESUME=1 (absent key = today's gate)
                if (json.optJSONObject(FastReadyHint.KEY)?.optBoolean(FastReadyHint.FIELD, false) == true) {
                    fastReady = FastReady()
                }
        // B16: the fast ready's releases (null = today: no key)
        fastReady?.let { f ->
            root.put("fast_ready_releases", f.releases)
            root.put("fast_ready_frame_to_post_ms", f.lastFrameToPostMs)
        }


    // B16: the recovery gate's ready at the first decodable frame, only with the host's fast ready (null = today).
    @Volatile
    private var fastReady: FastReady? = null

    private val fastReadyTick: Runnable by lazy {
        object : Runnable {
            override fun run() {
                val f = fastReady ?: return
                if (!sessionStarted || stopping || !recoveryActive || gameplayReleased) return
                if (f.tick(fastReadyInputs())) {
                    requestGameplayRelease()
                    return
                }
                uiHandler.postDelayed(this, 50L)
            }
        }
    }

    private fun fastReadyInputs(): FastReadyInputs =
        FastReadyInputs(
            recoveryActive = recoveryActive,
            released = gameplayReleased,
            requestInFlight = releaseRequestInFlight,
            hostMetadataComplete = hostMetadataComplete,
            waitingForIdr = receiver?.snapshot()?.waitingForIdr ?: true,
            renderedFrames = decoder?.renderedFrameCount() ?: 0L,
            outputAgeMs = decoder?.lastOutputAgeMs() ?: -1L,
        )

        // B16: the recovery's 50-ms fast-ready tick (null = today)
        fastReady?.let { f ->
            f.onRecoveryEntered(decoder?.renderedFrameCount() ?: 0L)
            uiHandler.removeCallbacks(fastReadyTick)
            uiHandler.postDelayed(fastReadyTick, 50L)
        }
```
