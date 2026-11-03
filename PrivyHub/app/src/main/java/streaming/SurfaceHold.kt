package com.safeiot.privyhub.streaming

import java.net.URLEncoder

/**
 * B32: the stream survives a brief loss of the screen, behind the system property `debug.privyhub.surface_hold`
 * (CL-B7P's convention; a reboot clears it). **Absent / empty / `0` / junk = today: no object.**
 *
 * TRIP-R2 §1: six self-restarts in an evening, each `trigger: surface` -- Android took the stream activity out of the
 * foreground for 1-9 s, the surface went, the same instance came back and started a new stream (a new host session,
 * the rung back to the start). Here, on `surfaceDestroyed` the activity keeps the receiver, the audio and the
 * controller sender running (the decoder closed: it cannot outlive its surface) for up to [boundMs]; a surface back
 * within the bound continues the same session (no `native-stream-start`); past it, today's restart path. Every loss
 * becomes one `surface_lost` row (its cause as far as the activity can see it), sent at the next heartbeat. A system
 * key (guide / Home class) from a pad is consumed in the stream activity; the remote's passes as today.
 * Design: `docs/memory/evidence/b32_2026-10-31/design_written_before_code.md` (hashed before this code).
 */
object SurfaceHoldFlag {
    const val PROPERTY = "debug.privyhub.surface_hold"
    const val DEFAULT_BOUND_MS = 12_000L
    const val MIN_BOUND_MS = 10_000L
    const val MAX_BOUND_MS = 30_000L

    /** `1` = the default bound; an integer in range = that bound; anything else (absent included) = off (null). */
    fun parse(value: String?): Long? {
        val v = value?.trim() ?: return null
        if (v == "1") return DEFAULT_BOUND_MS
        val n = v.toLongOrNull() ?: return null
        return if (n in MIN_BOUND_MS..MAX_BOUND_MS) n else null
    }

    /** The property, read through reflection; a failed read is absent, so off. */
    fun fromSystem(): Long? =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            null
        }
}

class SurfaceHold(val boundMs: Long, private val clockMs: () -> Long = { System.nanoTime() / 1_000_000L }) {
    companion object {
        const val WINDOW_MS = 2_000L
        const val MAX_ROWS = 8
        const val MAX_KEYS = 8
        const val MAX_DEVICES = 4
        const val MAX_ROW_CHARS = 1_024

        // android.view.KeyEvent / InputDevice constants (inlined values, so the JVM tests need no framework)
        const val KEYCODE_HOME = 3
        const val KEYCODE_MENU = 82
        const val KEYCODE_SEARCH = 84
        const val KEYCODE_NOTIFICATION = 83
        const val KEYCODE_BUTTON_MODE = 110
        const val KEYCODE_GUIDE = 172
        const val KEYCODE_SETTINGS = 176
        const val KEYCODE_APP_SWITCH = 187
        const val KEYCODE_ASSIST = 219
        const val KEYCODE_VOICE_ASSIST = 231
        const val KEYCODE_ALL_APPS = 284
        const val SOURCE_GAMEPAD = 0x00000401
        const val SOURCE_JOYSTICK = 0x01000010
        const val SOURCE_KEYBOARD = 0x00000101
        const val SOURCE_DPAD = 0x00000201

        val SYSTEM_KEYS = setOf(
            KEYCODE_BUTTON_MODE, KEYCODE_GUIDE, KEYCODE_MENU, KEYCODE_SEARCH, KEYCODE_SETTINGS, KEYCODE_HOME,
            KEYCODE_ALL_APPS, KEYCODE_ASSIST, KEYCODE_VOICE_ASSIST, KEYCODE_NOTIFICATION, KEYCODE_APP_SWITCH,
        )

        fun sourceClass(sources: Int): String = when {
            (sources and SOURCE_GAMEPAD) == SOURCE_GAMEPAD || (sources and SOURCE_JOYSTICK) == SOURCE_JOYSTICK -> "pad"
            (sources and SOURCE_KEYBOARD) == SOURCE_KEYBOARD || (sources and SOURCE_DPAD) == SOURCE_DPAD -> "remote"
            else -> "other"
        }
    }

    private class KeySeen(val atMs: Long, val code: Int, val cls: String, val consumed: Boolean)
    private class DeviceSeen(val atMs: Long, val kind: String, val cls: String)

    private val lock = Any()
    private val keys = ArrayDeque<KeySeen>()
    private val devices = ArrayDeque<DeviceSeen>()
    private val rows = ArrayDeque<String>()

    private var focusLostAtMs = -1L
    private var topLostAtMs = -1L
    private var userLeaveAtMs = -1L
    private var pausedAtMs = -1L

    // the open loss
    @Volatile
    var holding = false
        private set
    private var lostAtMs = -1L
    private var ageAtLossMs = 0L
    private var lossFields: MutableMap<String, Any?>? = null

    // after a re-attach, until the new decoder's first frame
    @Volatile
    private var awaitingFirstFrame = false
    private var backAtMs = -1L
    private var pendingHeldRow: MutableMap<String, Any?>? = null

    var losses = 0L; private set
    var held = 0L; private set
    var restarted = 0L; private set
    var endedInHold = 0L; private set
    var decodersBuilt = 0L; private set
    var renderedBeforeReattach = 0L; private set
    var padSystemKeysConsumed = 0L; private set
    var systemKeysPassed = 0L; private set
    var rowsQueued = 0L; private set
    var rowsSent = 0L; private set
    var rowsDropped = 0L; private set
    private var seq = 0L

    // --- what the activity sees -------------------------------------------------------------------------------------

    /** `dispatchKeyEvent`, before anything else. True = consume it (a system-class key from a pad). */
    fun onKey(keyCode: Int, keyDown: Boolean, sources: Int): Boolean {
        val cls = sourceClass(sources)
        val system = keyCode in SYSTEM_KEYS
        val consume = system && cls == "pad"
        synchronized(lock) {
            if (keyDown) {
                keys.addLast(KeySeen(clockMs(), keyCode, cls, consume))
                while (keys.size > 32) keys.removeFirst()
                if (consume) padSystemKeysConsumed++ else if (system) systemKeysPassed++
            }
        }
        return consume
    }

    fun onDevice(kind: String, sources: Int) {
        synchronized(lock) {
            devices.addLast(DeviceSeen(clockMs(), kind, sourceClass(sources)))
            while (devices.size > 16) devices.removeFirst()
        }
    }

    fun onFocus(hasFocus: Boolean) {
        if (!hasFocus) focusLostAtMs = clockMs()
    }

    fun onTopResumed(isTop: Boolean) {
        if (!isTop) topLostAtMs = clockMs()
    }

    fun onUserLeave() {
        userLeaveAtMs = clockMs()
    }

    fun onPause() {
        pausedAtMs = clockMs()
    }

    // --- the loss -------------------------------------------------------------------------------------------------

    /** `surfaceDestroyed` (a session started, not finishing): the hold begins; the cause is read now. */
    fun onSurfaceLost(lastOutputAgeMs: Long, interactive: Boolean?) {
        val now = clockMs()
        synchronized(lock) {
            losses++
            holding = true
            awaitingFirstFrame = false
            lostAtMs = now
            ageAtLossMs = lastOutputAgeMs.coerceAtLeast(0L)
            fun before(at: Long): Long = if (at >= 0L && now - at <= 60_000L) now - at else -1L
            val recentKeys = keys.filter { now - it.atMs <= WINDOW_MS }.takeLast(MAX_KEYS)
            val recentDevices = devices.filter { now - it.atMs <= WINDOW_MS }.takeLast(MAX_DEVICES)
            val leave = before(userLeaveAtMs).let { it in 0..10_000L }
            val reason = when {
                recentKeys.any { it.code in SYSTEM_KEYS && it.cls == "pad" } -> "pad_system_key"
                recentKeys.any { it.code in SYSTEM_KEYS } -> "remote_system_key"
                leave -> "user_leave"
                interactive == false -> "screen_off"
                recentDevices.isNotEmpty() -> "input_device"
                before(topLostAtMs) >= 0L -> "top_lost"
                before(focusLostAtMs) >= 0L -> "focus_lost"
                else -> "unknown"
            }
            lossFields = linkedMapOf(
                "reason" to reason,
                "bound_ms" to boundMs,
                "paused_before_ms" to before(pausedAtMs),
                "focus_lost_before_ms" to before(focusLostAtMs),
                "top_lost_before_ms" to before(topLostAtMs),
                "user_leave" to leave,
                "interactive" to interactive,
                "keys" to recentKeys.map { "${it.code}:${it.cls}:${if (it.consumed) "c" else "p"}" },
                "devices" to recentDevices.map { "${it.kind}:${it.cls}:${now - it.atMs}" },
            )
        }
    }

    /** True while the bound has run out with no surface back (the activity then runs today's path). */
    fun expired(nowMs: Long = clockMs()): Boolean = holding && nowMs - lostAtMs >= boundMs

    /** `surfaceCreated`: true = within the bound, the same session continues (no start). False = today's start. */
    fun onSurfaceBack(): Boolean {
        val now = clockMs()
        synchronized(lock) {
            if (!holding) return false
            if (now - lostAtMs >= boundMs) return false
            holding = false
            held++
            awaitingFirstFrame = true
            backAtMs = now
            pendingHeldRow = (lossFields ?: linkedMapOf()).apply {
                put("outcome", "held")
                put("away_ms", now - lostAtMs)
            }
            lossFields = null
            return true
        }
    }

    /** The expiry with no surface back: the row is `restarted`; the activity runs today's surface-loss path. */
    fun onExpired() {
        val now = clockMs()
        synchronized(lock) {
            if (!holding) return
            holding = false
            restarted++
            queue((lossFields ?: linkedMapOf()).apply {
                put("outcome", "restarted")
                put("away_ms", now - lostAtMs)
                put("first_frame_ms", -1L)
            })
            lossFields = null
        }
    }

    /** The activity ends inside a hold (today's stop path runs); no row (no heartbeat follows). */
    fun onEndedInHold() {
        synchronized(lock) {
            if (!holding) return
            holding = false
            endedInHold++
            lossFields = null
        }
    }

    /** A decoder built (the first, or one on the re-attached surface); [closedRendered] = the old one's frames. */
    fun onDecoderClosed(closedRendered: Long) {
        synchronized(lock) { renderedBeforeReattach += closedRendered.coerceAtLeast(0L) }
    }

    fun onDecoderBuilt() {
        synchronized(lock) { decodersBuilt++ }
    }

    /**
     * The stall signal's output age while the player cannot see the game: the age at the loss plus the time since,
     * through the hold and until the re-attached decoder renders. Null = not holding (the real age is used).
     */
    fun stallAgeMs(nowMs: Long, renderedFrames: Long): Long? {
        if (holding) return ageAtLossMs + (nowMs - lostAtMs).coerceAtLeast(0L)
        if (!awaitingFirstFrame) return null
        if (renderedFrames > 0L) {
            synchronized(lock) {
                if (awaitingFirstFrame) {
                    awaitingFirstFrame = false
                    pendingHeldRow?.let { r -> r["first_frame_ms"] = nowMs - backAtMs; queue(r) }
                    pendingHeldRow = null
                }
            }
            return null
        }
        return ageAtLossMs + (nowMs - lostAtMs).coerceAtLeast(0L)
    }

    // --- the rows -------------------------------------------------------------------------------------------------

    private fun queue(r: MutableMap<String, Any?>) {
        seq++
        val row = linkedMapOf<String, Any?>("seq" to seq)
        row.putAll(r)
        if (!row.containsKey("first_frame_ms")) row["first_frame_ms"] = -1L
        rows.addLast(encode(row))
        rowsQueued++
        while (rows.size > MAX_ROWS) {
            rows.removeFirst()
            rowsDropped++
        }
    }

    /** The heartbeat's key: one queued row (oldest first), or "" (nothing queued). */
    fun query(): String {
        val r = synchronized(lock) { rows.removeFirstOrNull() } ?: return ""
        rowsSent++
        return "&surface_lost=" + URLEncoder.encode(r, "UTF-8")
    }

    fun pendingRows(): List<String> = synchronized(lock) { rows.toList() }

    /** The report's `surface_hold` object (numbers only). */
    fun reportFields(): Map<String, Any> = linkedMapOf(
        "bound_ms" to boundMs,
        "losses" to losses,
        "held" to held,
        "restarted" to restarted,
        "ended_in_hold" to endedInHold,
        "decoders_built" to decodersBuilt,
        "rendered_before_reattach" to renderedBeforeReattach,
        "pad_system_keys_consumed" to padSystemKeysConsumed,
        "system_keys_passed" to systemKeysPassed,
        "rows_queued" to rowsQueued,
        "rows_sent" to rowsSent,
        "rows_dropped" to rowsDropped,
    )

    /** Compact JSON of numbers, booleans, null, fixed words and lists of fixed words; capped at [MAX_ROW_CHARS]. */
    internal fun encode(row: Map<String, Any?>): String {
        fun v(x: Any?): String = when (x) {
            null -> "null"
            is Boolean, is Int, is Long -> x.toString()
            is List<*> -> x.joinToString(",", "[", "]") { v(it) }
            else -> "\"" + x.toString().filter { it.isLetterOrDigit() || it == '_' || it == ':' || it == '-' } + "\""
        }
        val s = row.entries.joinToString(",", "{", "}") { (k, x) -> "\"$k\":${v(x)}" }
        if (s.length <= MAX_ROW_CHARS) return s
        val short = LinkedHashMap(row)
        short["keys"] = emptyList<String>()
        short["devices"] = emptyList<String>()
        return short.entries.joinToString(",", "{", "}") { (k, x) -> "\"$k\":${v(x)}" }
    }
}
