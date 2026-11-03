package com.safeiot.privyhub.vod

import java.security.MessageDigest

/**
 * B35: the movie player retries by itself. Behind `debug.privyhub.vod_retry=1` (CL-B7P's convention; a reboot
 * clears it). Absent / empty / `0` / junk = today: no controller, so MainActivity's `vodRetry?.` calls are no-ops and
 * a load / IO error shows today's "Playback error" at once.
 *
 * With the flag, on a retryable load / IO error during VOD (not live) playback: reconnect, seek to the position of
 * the episode's first error, resume -- backoff [BACKOFF_MS] then 15 s each, for up to [BOUND_MS] from the first
 * error; a small "reconnecting…" mark meanwhile; past the bound today's error plus a Retry button. Each step is a row
 * to the host (`vod_error` / `vod_retry` / `vod_resumed` / `vod_gave_up`); no title, path or URL in any row.
 *
 * Pure Kotlin (no Android type) so the JVM tests drive it with a fake clock, scheduler and player.
 */
object VodRetryFlag {
    const val PROPERTY = "debug.privyhub.vod_retry"

    fun parse(raw: String?): Boolean = raw?.trim() == "1"

    fun read(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            false
        }
}

class VodRetryPolicy(
    val backoffMs: LongArray = BACKOFF_MS,
    val boundMs: Long = BOUND_MS,
) {
    /** The delay before attempt [attempt] (1-based): 1, 2, 4, 8, 15 s, then 15 s each. */
    fun delayBefore(attempt: Int): Long = backoffMs[(attempt - 1).coerceIn(0, backoffMs.size - 1)]

    companion object {
        val BACKOFF_MS = longArrayOf(1_000L, 2_000L, 4_000L, 8_000L, 15_000L)
        const val BOUND_MS = 150_000L

        /** Media3 codes: TIMEOUT 1003; IO 2000 unspecified, 2001 connection failed, 2002 timeout, 2004 bad status. */
        val RETRYABLE = setOf(1003, 2000, 2001, 2002, 2004)

        fun isRetryable(code: Int): Boolean = code in RETRYABLE
    }
}

class VodRetryController(
    private val policy: VodRetryPolicy,
    private val player: Player,
    private val scheduler: Scheduler,
    private val clock: () -> Long,
    private val rows: (Map<String, Any>) -> Unit,
    private val ui: Ui,
    sourceId: String,
) {
    interface Player {
        /** Reconnect and resume at [positionMs] (Media3: seekTo, prepare, playWhenReady). */
        fun retryAt(positionMs: Long)
    }

    interface Scheduler {
        fun schedule(delayMs: Long, task: () -> Unit)
        fun cancel()
    }

    interface Ui {
        fun showMark(attempt: Int)
        fun hideMark()
        fun offerRetry()
    }

    val media: String = opaqueId(sourceId)

    private var firstErrorAtMs = -1L
    private var positionMs = 0L
    private var attempts = 0
    private var lastCode = 0
    private var lastName = ""
    private var gaveUp = false
    private var cancelled = false

    val retrying: Boolean get() = firstErrorAtMs >= 0 && !gaveUp

    /** True = handled (an attempt is scheduled); false = today's error path runs now. */
    fun onError(code: Int, codeName: String, currentPositionMs: Long): Boolean {
        if (cancelled || !VodRetryPolicy.isRetryable(code)) {
            return false
        }
        val now = clock()
        lastCode = code
        lastName = codeName
        if (firstErrorAtMs < 0 || gaveUp) {
            firstErrorAtMs = now
            positionMs = currentPositionMs.coerceAtLeast(0L)
            attempts = 0
            gaveUp = false
            rows(row("vod_error") + mapOf("error_code" to code, "error_name" to codeName))
        }
        val next = attempts + 1
        val delay = policy.delayBefore(next)
        val elapsed = now - firstErrorAtMs
        if (elapsed + delay > policy.boundMs) {
            gaveUp = true
            scheduler.cancel()
            ui.hideMark()
            rows(row("vod_gave_up") + mapOf("attempts" to attempts, "elapsed_ms" to elapsed,
                "error_code" to code, "error_name" to codeName))
            return false
        }
        attempts = next
        rows(row("vod_retry") + mapOf("attempt" to next, "delay_ms" to delay, "elapsed_ms" to elapsed,
            "error_code" to code, "error_name" to codeName))
        ui.showMark(next)
        scheduler.cancel()
        scheduler.schedule(delay) {
            if (!cancelled && retrying) {
                player.retryAt(positionMs)
            }
        }
        return true
    }

    /** After today's error branch ran: past the bound, offer Retry (new, flag only). */
    fun afterTodaysError() {
        if (gaveUp && !cancelled) {
            ui.offerRetry()
        }
    }

    /** The player is READY: an open episode closes. */
    fun onReady() {
        if (firstErrorAtMs < 0 || gaveUp || cancelled) {
            return
        }
        rows(row("vod_resumed") + mapOf("attempts" to attempts, "elapsed_ms" to (clock() - firstErrorAtMs)))
        ui.hideMark()
        firstErrorAtMs = -1L
        attempts = 0
    }

    /** The Retry button: a new episode at the saved position, the first attempt at once. */
    fun manualRetry() {
        if (cancelled) {
            return
        }
        firstErrorAtMs = clock()
        attempts = 1
        gaveUp = false
        rows(row("vod_retry") + mapOf("attempt" to 1, "delay_ms" to 0L, "elapsed_ms" to 0L,
            "error_code" to lastCode, "error_name" to lastName))
        ui.showMark(1)
        player.retryAt(positionMs)
    }

    fun cancel() {
        cancelled = true
        scheduler.cancel()
        ui.hideMark()
    }

    private fun row(event: String): Map<String, Any> =
        mapOf("event" to event, "media" to media, "position_ms" to positionMs, "bound_ms" to policy.boundMs)

    companion object {
        fun opaqueId(sourceId: String): String =
            MessageDigest.getInstance("SHA-256")
                .digest(("privyhub-vod-source:" + sourceId).toByteArray(Charsets.UTF_8))
                .take(6)
                .joinToString("") { "%02x".format(it) }

        /** As MainActivity builds it: only with the flag, only for VOD (never live). */
        fun wanted(flag: Boolean, isLive: Boolean): Boolean = flag && !isLive
    }
}
