package com.safeiot.privyhub.streaming

/**
 * B22: a guarded restart's release at the new stream's first fresh frame, armed only by the host's `native-stream-start`
 * response (`"restart_fast": {"armed": true, "old_stream_active": true}`, sent with `PRIVYHUB_RESTART_FAST=1` on an
 * eligible `guard_end=1` start). Lives inside the existing `restart_guard` (B11 … B19): no guarded start, or no key,
 * = today (no object).
 *
 * CL-B12 cell 1: the new stream's frames were decoded 0.3-0.5 s before the host's start response, and the start-up gate
 * then needed a baseline tick + 6 clean 500-ms ticks (≥ ~3.5-4 s; press 1 8.8 s with a reset). With the host's fast
 * restart the response comes before its teardown, so the old encoder's frames can still arrive after it: the release
 * waits for the switch (the receiver's `ssrcChanges` above its value at the start's POST), a frame rendered after it,
 * no IDR wait, the output <= [freshMs] old, and the old report's post finished (or [reportWaitCapMs] since the
 * response), so the host logs ended → report → started. Today's gate keeps running beside it; if this never fires the
 * gate's release still comes. The rebuilt audio receiver waits for the release ([takeAudio]): the host's new audio is
 * up once the ready returns (its `status()` waits for the host's restart), and the old one is gone.
 */
object RestartFastHint {
    const val KEY = "restart_fast"
    const val ARMED = "armed"
    const val OLD_STREAM = "old_stream_active"
}

/** What the 50-ms tick reads. */
data class RestartFastInputs(
    val released: Boolean,
    val requestInFlight: Boolean,
    val hostMetadataComplete: Boolean,
    val ssrcChanges: Long,
    val waitingForIdr: Boolean,
    val renderedFrames: Long,
    val outputAgeMs: Long,
    val reportDone: Boolean,
)

class RestartFast(
    val ssrcAtStart: Long,
    val needSwitch: Boolean,
    val freshMs: Long = 100L,
    val reportWaitCapMs: Long = 1_000L,
    private val clockMs: () -> Long = { System.nanoTime() / 1_000_000L },
) {
    @Volatile
    private var armedAtMs = -1L

    @Volatile
    private var switchAtMs = -1L

    @Volatile
    private var renderedAtSwitch = -1L

    @Volatile
    private var freshAtMs = -1L

    @Volatile
    private var audioPending = true

    /** The old report's post finished (posted or failed): the guard's report thread. */
    @Volatile
    var reportDone = false

    /** `fast` (this tick), `gate` (today's 6-tick release first), `none`. */
    @Volatile
    var releasedBy = "none"
        private set

    @Volatile
    var responseToSwitchMs = -1L
        private set

    @Volatile
    var switchToReleaseMs = -1L
        private set

    @Volatile
    var responseToReleaseMs = -1L
        private set

    /** How long a release that was otherwise ready waited on the old report. */
    @Volatile
    var reportWaitMs = -1L
        private set

    /** Today's gate's resets while armed, and the last failed condition (CL-B12 press 1's unlogged reason). */
    @Volatile
    var gateResets = 0L
        private set

    @Volatile
    var gateLastReset = ""
        private set

    /** The start's response: the arm. */
    fun onResponse() {
        armedAtMs = clockMs()
    }

    /** One 50-ms tick: true = release now (once). */
    fun tick(inp: RestartFastInputs): Boolean {
        if (armedAtMs < 0L || releasedBy != "none" || inp.released || inp.requestInFlight || !inp.hostMetadataComplete) {
            return false
        }
        if (needSwitch && inp.ssrcChanges <= ssrcAtStart) {
            return false
        }
        val now = clockMs()
        if (renderedAtSwitch < 0L) {
            renderedAtSwitch = inp.renderedFrames
            switchAtMs = now
            responseToSwitchMs = now - armedAtMs
        }
        if (inp.renderedFrames <= renderedAtSwitch || inp.waitingForIdr || inp.outputAgeMs < 0L ||
            inp.outputAgeMs > freshMs
        ) {
            return false
        }
        if (freshAtMs < 0L) {
            freshAtMs = now
        }
        if (!inp.reportDone && now - armedAtMs < reportWaitCapMs) {
            return false
        }
        reportWaitMs = now - freshAtMs
        releasedBy = "fast"
        switchToReleaseMs = now - switchAtMs
        responseToReleaseMs = now - armedAtMs
        return true
    }

    /** `requestGameplayRelease`: a release this tick did not make is today's gate's. */
    fun noteRelease() {
        if (releasedBy == "none") {
            releasedBy = "gate"
            if (armedAtMs >= 0L) {
                responseToReleaseMs = clockMs() - armedAtMs
            }
        }
    }

    fun noteGateReset(reason: String) {
        gateResets++
        gateLastReset = reason
    }

    /** The ready's return (released or not): true once = start the rebuilt audio receiver now. */
    fun takeAudio(): Boolean {
        if (!audioPending) {
            return false
        }
        audioPending = false
        return true
    }
}
