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
 *
 * B43 (inside the same flag): each error carries a `reason` (`reset` / `refused` / `timeout` / `401` / `403`). A
 * refusal (401 / 403) is not a lost hub: the media token is refetched ([VodRetryController.Token]) before the attempt
 * (a companion restart ends the hub's sessions; the onn's cached token is then refused), and three refusals in a row,
 * each after a refetch, end the episode as `refused` -- never "connection lost". The Retry button refetches too.
 * Design: `docs/memory/evidence/b43_2026-11-06/design_written_before_code.md`.
 *
 * B47 (the user's "Reconnect by default yes", 2026-11-06; G-A13's client half): **on by default** -- absent / empty /
 * junk / `1` = the retry; `0` / `off` = today's absent (no controller). At READY the mark is always cleared and any
 * scheduled attempt dropped (HOME-3 C5'' (a): "reconnecting…" left on screen after a `reset` resume).
 * Design: `docs/memory/evidence/b47_2026-11-07/design_written_before_code.md`.
 */
object VodRetryFlag {
    const val PROPERTY = "debug.privyhub.vod_retry"

    // B47: on unless `0` / `off` (as B42's flags)
    fun parse(raw: String?): Boolean = raw?.trim().let { it != "0" && it != "off" }

    /** The property, read through reflection; a failed read is absent, so on (B47). */
    fun read(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            parse(null)
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

        // B43: the reasons, and three refusals in a row (each after a refetch) end an episode as `refused`
        const val REASON_RESET = "reset"
        const val REASON_REFUSED = "refused"
        const val REASON_TIMEOUT = "timeout"
        const val REASON_401 = "401"
        const val REASON_403 = "403"
        const val REFUSALS_MAX = 3

        /** B43: the reason from what the Android side read in the error's cause chain. */
        fun reasonOf(code: Int, httpStatus: Int?, connectRefused: Boolean, timedOut: Boolean): String =
            when {
                httpStatus == 401 -> REASON_401
                httpStatus == 403 -> REASON_403
                timedOut || code == 1003 || code == 2002 -> REASON_TIMEOUT
                connectRefused -> REASON_REFUSED
                else -> REASON_RESET
            }

        fun isRefusal(reason: String): Boolean = reason == REASON_401 || reason == REASON_403
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
    // B43: the media token's refetch (null = B35's behaviour: a refusal retried like a reset)
    private val token: Token? = null,
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

        /** B43: the give-up's kind (`lost` / `refused`) for the message; B35's Ui keeps its one method. */
        fun offerRetry(kind: String) = offerRetry()
    }

    /** B43: drop the cached media token and set up afresh (off the main thread); [done] on the main thread. */
    interface Token {
        fun refresh(done: (Boolean) -> Unit)
    }

    val media: String = opaqueId(sourceId)

    private var firstErrorAtMs = -1L
    private var positionMs = 0L
    private var attempts = 0
    private var lastCode = 0
    private var lastName = ""
    private var gaveUp = false
    private var cancelled = false
    private var lastReason = VodRetryPolicy.REASON_RESET
    private var refetched = false
    private var refusalsAfterRefetch = 0
    private var gaveUpKind = KIND_LOST

    val retrying: Boolean get() = firstErrorAtMs >= 0 && !gaveUp

    /** True = handled (an attempt is scheduled); false = today's error path runs now. */
    fun onError(code: Int, codeName: String, currentPositionMs: Long): Boolean =
        onError(code, codeName, currentPositionMs, VodRetryPolicy.REASON_RESET)

    /** B43: [reason] from [VodRetryPolicy.reasonOf]; a refusal refetches the token before its attempt. */
    fun onError(code: Int, codeName: String, currentPositionMs: Long, reason: String): Boolean {
        if (cancelled || !VodRetryPolicy.isRetryable(code)) {
            return false
        }
        val now = clock()
        lastCode = code
        lastName = codeName
        lastReason = reason
        if (firstErrorAtMs < 0 || gaveUp) {
            firstErrorAtMs = now
            positionMs = currentPositionMs.coerceAtLeast(0L)
            attempts = 0
            gaveUp = false
            refetched = false
            refusalsAfterRefetch = 0
            rows(row("vod_error") + mapOf("error_code" to code, "error_name" to codeName) + why(reason))
        }
        val refusal = token != null && VodRetryPolicy.isRefusal(reason)
        if (refusal && refetched) {
            refusalsAfterRefetch++
        } else if (!VodRetryPolicy.isRefusal(reason)) {
            refusalsAfterRefetch = 0
        }
        val next = attempts + 1
        val delay = policy.delayBefore(next)
        val elapsed = now - firstErrorAtMs
        if (refusal && refusalsAfterRefetch >= VodRetryPolicy.REFUSALS_MAX) {
            return giveUp(code, codeName, elapsed, reason, KIND_REFUSED)
        }
        if (elapsed + delay > policy.boundMs) {
            return giveUp(code, codeName, elapsed, reason,
                if (VodRetryPolicy.isRefusal(reason)) KIND_REFUSED else KIND_LOST)
        }
        attempts = next
        // B47: the mark only while the episode is open (it is: firstErrorAtMs set above)
        if (retrying) ui.showMark(next)
        scheduler.cancel()
        val base = row("vod_retry") + mapOf("attempt" to next, "delay_ms" to delay, "elapsed_ms" to elapsed,
            "error_code" to code, "error_name" to codeName) + why(reason)
        if (!refusal) {
            rows(base)
            scheduler.schedule(delay) {
                if (!cancelled && retrying) {
                    player.retryAt(positionMs)
                }
            }
            return true
        }
        // B43: a refusal -- the token refetched first, the row says whether it worked, then the attempt
        val episode = firstErrorAtMs
        token!!.refresh { ok ->
            if (cancelled || !retrying || firstErrorAtMs != episode) {
                return@refresh
            }
            refetched = true
            // a fresh token fixes the cause: the attempt at once; a failed refetch (the hub still down) keeps the backoff
            val wait = if (ok) 0L else delay
            rows(base + mapOf("delay_ms" to wait, "token_refetched" to ok))
            scheduler.cancel()
            scheduler.schedule(wait) {
                if (!cancelled && retrying) {
                    player.retryAt(positionMs)
                }
            }
        }
        return true
    }

    private fun giveUp(code: Int, codeName: String, elapsed: Long, reason: String, kind: String): Boolean {
        gaveUp = true
        gaveUpKind = kind
        scheduler.cancel()
        ui.hideMark()
        rows(row("vod_gave_up") + mapOf("attempts" to attempts, "elapsed_ms" to elapsed,
            "error_code" to code, "error_name" to codeName) + why(reason) +
            (if (token != null) mapOf("kind" to kind) else emptyMap()))
        return false
    }

    /** B43: the reason key, only with the token port (B35's rows as built without it). */
    private fun why(reason: String): Map<String, Any> =
        if (token != null) mapOf("reason" to reason) else emptyMap()

    /** After today's error branch ran: past the bound, offer Retry (new, flag only). */
    fun afterTodaysError() {
        if (gaveUp && !cancelled) {
            if (token != null) ui.offerRetry(gaveUpKind) else ui.offerRetry()
        }
    }

    /** The player is READY: an open episode closes. B47: the mark cleared and any scheduled attempt dropped, always. */
    fun onReady() {
        if (!cancelled) {
            scheduler.cancel()
            ui.hideMark()
        }
        if (firstErrorAtMs < 0 || gaveUp || cancelled) {
            return
        }
        rows(row("vod_resumed") + mapOf("attempts" to attempts, "elapsed_ms" to (clock() - firstErrorAtMs)))
        firstErrorAtMs = -1L
        attempts = 0
        refetched = false
        refusalsAfterRefetch = 0
    }

    /** The Retry button: a new episode at the saved position, the first attempt at once. */
    fun manualRetry() {
        if (cancelled) {
            return
        }
        firstErrorAtMs = clock()
        attempts = 1
        gaveUp = false
        refusalsAfterRefetch = 0
        val base = row("vod_retry") + mapOf("attempt" to 1, "delay_ms" to 0L, "elapsed_ms" to 0L,
            "error_code" to lastCode, "error_name" to lastName) + why(lastReason)
        ui.showMark(1)
        val t = token
        if (t == null) {
            rows(base)
            player.retryAt(positionMs)
            return
        }
        // B43: the Retry button refetches the token first (HOME-2: it reused the dead one)
        val episode = firstErrorAtMs
        t.refresh { ok ->
            if (cancelled || firstErrorAtMs != episode) {
                return@refresh
            }
            refetched = true
            rows(base + mapOf("token_refetched" to ok))
            player.retryAt(positionMs)
        }
    }

    fun cancel() {
        cancelled = true
        scheduler.cancel()
        ui.hideMark()
    }

    private fun row(event: String): Map<String, Any> =
        mapOf("event" to event, "media" to media, "position_ms" to positionMs, "bound_ms" to policy.boundMs)

    companion object {
        const val KIND_LOST = "lost"
        const val KIND_REFUSED = "refused"

        fun opaqueId(sourceId: String): String =
            MessageDigest.getInstance("SHA-256")
                .digest(("privyhub-vod-source:" + sourceId).toByteArray(Charsets.UTF_8))
                .take(6)
                .joinToString("") { "%02x".format(it) }

        /** As MainActivity builds it: only with the flag, only for VOD (never live). */
        fun wanted(flag: Boolean, isLive: Boolean): Boolean = flag && !isLive
    }
}
