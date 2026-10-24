package com.safeiot.privyhub.streaming

import java.io.File
import java.util.Properties
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicLong

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
 *
 * B15 (the same property): the pending is also kept beyond the activity object, in a private file, so a start in
 * another instance -- a recreation, or a new process after the old one died with the session open (CL-B10 cell 1's
 * Home press) -- flushes it too; `restart_cause.trigger` names the path (`surface` / `recreate` / `process`). A
 * recreation hands the session over instead of racing its own stop against the next start, and a pending another
 * instance already flushed is not posted twice.
 *
 * B17 (the same property): CL-B11's new instance started its audio on the host's old stream and starved for ~3.4 s
 * while B15's flush waited on the host's stop (~2.3 s of encoder teardown). Here the pending is taken before the audio
 * (`prepareStart`), the audio waits for the start response, and the old session's end rides in the start
 * (`native-stream-start?…&guard_end=1`, which runs the stop's bookkeeping first; its own `_stop_locked()` ends the
 * stream); the old report follows the start. No separate stop: one that is not waited on could reach the host's lock
 * after the start and end the new stream.
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
    // B15: who wrote it (this process's instance number, the process's mark) and the path it was taken on
    val instance: Long = 0L,
    val processMark: Long = 0L,
    val trigger: String = "surface",
)

/** B15: this process's mark (the monotonic time the guard first loaded here) and its activity instances' numbers. */
object RestartGuardProcess {
    val mark: Long = System.nanoTime() / 1_000_000L
    private val instances = AtomicLong(0L)

    fun nextInstance(): Long = instances.incrementAndGet()
}

/** B15: where the pending lives beyond the activity object. Failures are reported, never thrown. */
interface PendingStore {
    fun save(p: PendingRestart): Boolean
    fun load(): PendingRestart?
    fun clear()
}

/** B15: a private file (`java.util.Properties`); cleared by truncation. No address, no identifier in it. */
class FilePendingStore(private val file: File) : PendingStore {
    override fun save(p: PendingRestart): Boolean =
        try {
            val props = Properties()
            p.report?.let { props.setProperty("report", it) }
            props.setProperty("lost_at_ms", p.lostAtMs.toString())
            props.setProperty("last_frame_age_ms", p.lastFrameAgeMs.toString())
            props.setProperty("rtp_silence_ms", p.rtpSilenceMs.toString())
            props.setProperty("recovery_active", p.recoveryActive.toString())
            props.setProperty("paused_before_loss_ms", p.pausedBeforeLossMs.toString())
            props.setProperty("instance", p.instance.toString())
            props.setProperty("process_mark", p.processMark.toString())
            file.outputStream().use { props.store(it, null) }
            true
        } catch (_: Exception) {
            false
        }

    override fun load(): PendingRestart? =
        try {
            if (!file.isFile || file.length() == 0L) {
                null
            } else {
                val props = Properties()
                file.inputStream().use { props.load(it) }
                PendingRestart(
                    report = props.getProperty("report"),
                    lostAtMs = props.getProperty("lost_at_ms").toLong(),
                    lastFrameAgeMs = props.getProperty("last_frame_age_ms").toLong(),
                    rtpSilenceMs = props.getProperty("rtp_silence_ms").toLong(),
                    recoveryActive = props.getProperty("recovery_active").toBoolean(),
                    pausedBeforeLossMs = props.getProperty("paused_before_loss_ms").toLong(),
                    instance = props.getProperty("instance").toLong(),
                    processMark = props.getProperty("process_mark").toLong(),
                )
            }
        } catch (_: Exception) {
            null
        }

    override fun clear() {
        try {
            file.outputStream().use { }
        } catch (_: Exception) {
        }
    }
}

class RestartGuard(private val clockMs: () -> Long = { System.nanoTime() / 1_000_000L }) {
    companion object {
        /** B15: the store's file name in the app's no-backup directory. */
        const val STORE_FILE = "restart_guard_pending.properties"
    }

    @Volatile
    private var pending: PendingRestart? = null

    // B15: the store (null = B11's memory only), this instance's number and its process's mark
    @Volatile
    private var store: PendingStore? = null
    private var instance = 0L
    private var processMark = 0L

    /** B15: this instance's pending reached the store. */
    @Volatile
    private var persisted = false

    // B17: this instance's creation, the pending taken before the audio (once), the live cause the start updates
    @Volatile
    private var createdAtMs = -1L

    @Volatile
    private var prepared: PendingRestart? = null

    @Volatile
    private var preparedSet = false

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

    /** B15: `onCreate`: the store, this instance's number in its process, the process's mark. */
    fun attach(store: PendingStore, instance: Long, processMark: Long) {
        this.store = store
        this.instance = instance
        this.processMark = processMark
        createdAtMs = clockMs()
    }

    /** B17, `startSession` before the audio receiver: take the pending now; true = a restart (the audio waits). */
    fun prepareStart(): Boolean {
        prepared = takeNow()
        preparedSet = true
        return prepared != null
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
            instance = instance,
            processMark = processMark,
        )
        // B15: kept beyond this object (memory still serves this instance if the write fails)
        val p = pending
        persisted = p != null && (store?.save(p) ?: false)
    }

    private fun mine(s: PendingRestart?): Boolean =
        s != null && s.instance == instance && s.processMark == processMark

    /**
     * B15, `stopSession` before today's posts. True = skip them:
     * - this instance's pending was already flushed by another instance's start (its report and stop were sent; a
     *   second stop would end the new stream);
     * - the activity is being recreated: the open session is kept in the store for the next instance's start, which
     *   flushes it in order (report, stop, start) instead of this stop racing that start.
     */
    fun handOver(changingConfigurations: Boolean, sessionLive: Boolean, report: () -> String?): Boolean {
        val st = store ?: return false
        val p = pending
        if (p != null && persisted && !mine(st.load())) {
            pending = null
            persisted = false
            return true
        }
        if (!changingConfigurations || (p == null && !sessionLive)) {
            return false
        }
        if (p == null) {
            onSurfaceLost(report(), -1L, -1L, false)
        }
        return persisted
    }

    /** `stopSession`: the activity ends; today's stop path posts the cached report and the stop. */
    fun onSessionStopped() {
        pending = null
        // B15: this instance's own pending leaves the store too (never another instance's)
        store?.let { st -> if (persisted && mine(st.load())) st.clear() }
        persisted = false
    }

    /** The session thread, before `native-stream-start`: the pending restart (once), or null for a normal start. */
    fun takePending(): PendingRestart? {
        // B17: the one `prepareStart` took already
        if (preparedSet) {
            preparedSet = false
            val p = prepared
            prepared = null
            if (p == null) {
                lastCause = null
            }
            return p
        }
        return takeNow()
    }

    private fun takeNow(): PendingRestart? {
        var p = pending
        pending = null
        // B15: the store first: this instance's own (`surface`), another instance's (`recreate`), another process's
        // (`process`); this instance's persisted pending gone from the store was flushed by another instance already
        val st = store
        if (st != null) {
            val s = st.load()
            if (s != null) {
                st.clear()
                val trigger = when {
                    s.processMark != processMark -> "process"
                    s.instance != instance -> "recreate"
                    else -> "surface"
                }
                p = s.copy(trigger = trigger)
            } else if (persisted) {
                p = null
            }
            persisted = false
        }
        if (p == null) {
            lastCause = null
        }
        return p
    }

    /**
     * B17, the session thread before `native-stream-start?…&guard_end=1`: the cause, nothing posted yet (the start
     * carries the old session's end; the report follows it).
     */
    fun beginViaStart(p: PendingRestart): Map<String, Any> {
        restarts++
        val now = clockMs()
        val away = now - p.lostAtMs
        val cause = ConcurrentHashMap<String, Any>()
        cause["away_ms"] = if (away >= 0L || store == null) away.coerceAtLeast(0L) else -1L
        cause["last_frame_age_ms"] = p.lastFrameAgeMs
        cause["rtp_silence_ms"] = p.rtpSilenceMs
        cause["recovery_active"] = p.recoveryActive
        cause["paused_before_loss_ms"] = p.pausedBeforeLossMs
        cause["old_report_posted"] = false
        cause["stop_posted"] = false
        cause["restarts"] = restarts
        cause["trigger"] = p.trigger
        cause["flush"] = "via_start"
        cause["create_to_start_ms"] = if (createdAtMs >= 0L) (now - createdAtMs).coerceAtLeast(0L) else -1L
        cause["host_ended_session"] = false
        lastCause = cause
        return cause
    }

    /** B17: the start's response: the host ran the stop's bookkeeping (`"guard_end": true`). */
    fun noteStartResponse(hostEndedSession: Boolean) {
        (lastCause as? MutableMap<String, Any>)?.put("host_ended_session", hostEndedSession)
    }

    /** B17, its own thread after the start's response: the old report; a failed post is recorded, never thrown. */
    fun reportAfterStart(p: PendingRestart, postReport: (String) -> Unit): Boolean {
        val ok = !p.report.isNullOrBlank() && try { postReport(p.report); true } catch (_: Exception) { false }
        (lastCause as? MutableMap<String, Any>)?.put("old_report_posted", ok)
        return ok
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
        val away = clockMs() - p.lostAtMs
        val cause = linkedMapOf<String, Any>(
            // B15: -1 when the clock reads backwards across processes (a reboot)
            "away_ms" to (if (away >= 0L || store == null) away.coerceAtLeast(0L) else -1L),
            "last_frame_age_ms" to p.lastFrameAgeMs,
            "rtp_silence_ms" to p.rtpSilenceMs,
            "recovery_active" to p.recoveryActive,
            "paused_before_loss_ms" to p.pausedBeforeLossMs,
            "old_report_posted" to reportPosted,
            "stop_posted" to stopPosted,
            "restarts" to restarts,
            // B15: the path (`surface` / `recreate` / `process`)
            "trigger" to p.trigger,
        )
        lastCause = cause
        return cause
    }
}
