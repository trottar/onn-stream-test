package com.safeiot.privyhub.streaming

/**
 * B11: the client's self-restart, behind the system property
 * `debug.privyhub.restart_guard=1` (CL-B7P's convention). Absent = today.
 *
 * A session starts only from `surfaceCreated`; when the surface is lost
 * (`surfaceDestroyed`) the pipeline stops and the report is cached but never
 * posted, and the next `startSession` discards it and posts a new
 * `native-stream-start` with no stop (UX-R4 event 2). The host's start restarts
 * its audio at sequence 0 while the new receiver had locked onto the old
 * stream, so every new frame read as late (the underrun storm). Here:
 * - the surface's loss keeps the report and the cause;
 * - the next start first posts the old report, then `native-stream-stop`;
 * - the audio receiver is rebuilt after the host's start response;
 * - the cause goes in the new session's report (`restart_cause`).
 */
object RestartGuardFlag {
    const val PROPERTY = "debug.privyhub.restart_guard"

    fun parse(value: String?): Boolean = value?.trim() == "1"

    fun fromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            false
        }
}

/** What the guard flushes at a self-restart. */
data class PendingRestart(
    val report: String?,
    val lostAtMs: Long,
    val lastFrameAgeMs: Long,
    val rtpSilenceMs: Long,
    val recoveryActive: Boolean,
    val pausedBeforeLossMs: Long,
)

class RestartGuard(private val clockMs: () -> Long = { System.nanoTime() / 1_000_000L }) {
    @Volatile
    private var pending: PendingRestart? = null

    @Volatile
    private var lastPauseAtMs = -1L

    /** The last self-restart's cause (the new session's report), null for a normal start. */
    @Volatile
    var lastCause: Map<String, Any>? = null
        private set

    var restarts = 0L
        private set

    fun notePause() {
        lastPauseAtMs = clockMs()
    }

    /** `surfaceDestroyed`, before the pipeline stops (a session was started). */
    fun onSurfaceLost(report: String?, lastFrameAgeMs: Long, rtpSilenceMs: Long, recoveryActive: Boolean) {
        val now = clockMs()
        pending = PendingRestart(
            report = report,
            lostAtMs = now,
            lastFrameAgeMs = lastFrameAgeMs,
            rtpSilenceMs = rtpSilenceMs,
            recoveryActive = recoveryActive,
            pausedBeforeLossMs = if (lastPauseAtMs >= 0L) now - lastPauseAtMs else -1L,
        )
    }

    /** `stopSession`: the activity ends; today's stop path posts the cached report and the stop. */
    fun onSessionStopped() {
        pending = null
    }

    /** The session thread, before `native-stream-start`: the pending restart (once), or null for a normal start. */
    fun takePending(): PendingRestart? {
        val p = pending
        pending = null
        if (p == null) {
            lastCause = null
        }
        return p
    }

    /**
     * Ends the old session in order — its report, then the stop — and records the cause. The transport is the
     * activity's (the tests' fake); a failed post is recorded, never thrown.
     */
    fun flush(p: PendingRestart, postReport: (String) -> Unit, postStop: () -> Unit): Map<String, Any> {
        var reportPosted = false
        var stopPosted = false
        if (!p.report.isNullOrBlank()) {
            reportPosted = try { postReport(p.report); true } catch (_: Exception) { false }
        }
        stopPosted = try { postStop(); true } catch (_: Exception) { false }
        restarts++
        val cause = linkedMapOf<String, Any>(
            "away_ms" to (clockMs() - p.lostAtMs).coerceAtLeast(0L),
            "last_frame_age_ms" to p.lastFrameAgeMs,
            "rtp_silence_ms" to p.rtpSilenceMs,
            "recovery_active" to p.recoveryActive,
            "paused_before_loss_ms" to p.pausedBeforeLossMs,
            "old_report_posted" to reportPosted,
            "stop_posted" to stopPosted,
            "restarts" to restarts,
        )
        lastCause = cause
        return cause
    }
}
