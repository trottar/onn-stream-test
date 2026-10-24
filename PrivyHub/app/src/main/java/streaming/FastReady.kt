package com.safeiot.privyhub.streaming

/**
 * B16: the recovery gate's ready as soon as a decodable frame is in hand, armed only by the host's
 * `native-stream-start` response (`"stall_resume": {"fast_ready": true}`, sent with `PRIVYHUB_STALL_RESUME=1`).
 * Absent = today: no object, the gate's baseline tick + 3 clean 500-ms ticks.
 *
 * CL-B10 cell 3: after a 4-s `@down` drop the frames were flowing again ~2.6 s before the gate's ready (blackout 1),
 * the picture held behind the "Reconnecting" overlay, and v2's 5-s hold expired first in all 5. Here a 50-ms tick
 * during a recovery releases at the first tick that sees a frame rendered since the recovery began, the receiver not
 * waiting for an IDR, the last output <= [freshMs] old and the host's metadata complete. The startup gate is unchanged.
 */
object FastReadyHint {
    const val KEY = "stall_resume"
    const val FIELD = "fast_ready"
}

/** What the tick reads: the gate's state, the receiver's IDR wait, the decoder's frame count and output age. */
data class FastReadyInputs(
    val recoveryActive: Boolean,
    val released: Boolean,
    val requestInFlight: Boolean,
    val hostMetadataComplete: Boolean,
    val waitingForIdr: Boolean,
    val renderedFrames: Long,
    val outputAgeMs: Long,
)

class FastReady(val freshMs: Long = 100L, private val clockMs: () -> Long = { System.nanoTime() / 1_000_000L }) {
    private var baseline = -1L
    private var firstFrameAtMs = -1L

    var releases = 0L
        private set

    /** The first frame since the recovery began → the release's POST, the last release (-1 before one). */
    var lastFrameToPostMs = -1L
        private set

    /** The recovery's entry: the frame count to beat. */
    fun onRecoveryEntered(renderedFrames: Long) {
        baseline = renderedFrames
        firstFrameAtMs = -1L
    }

    /** One 50-ms tick: true = release now (once per recovery). */
    fun tick(inp: FastReadyInputs): Boolean {
        if (!inp.recoveryActive || inp.released || inp.requestInFlight || baseline < 0L) {
            return false
        }
        if (inp.renderedFrames <= baseline) {
            return false
        }
        val now = clockMs()
        if (firstFrameAtMs < 0L) {
            firstFrameAtMs = now
        }
        if (!inp.hostMetadataComplete || inp.waitingForIdr || inp.outputAgeMs < 0L || inp.outputAgeMs > freshMs) {
            return false
        }
        releases++
        lastFrameToPostMs = now - firstFrameAtMs
        baseline = -1L
        return true
    }
}
