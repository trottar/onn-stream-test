package com.safeiot.privyhub.streaming

/**
 * B67 (B65's evidence): a game *start* whose stabilization window (15 s) ends while the decoder keeps rendering new
 * frames gets a new window instead of latching "Game stream isn't ready" -- up to [MAX_REARMS] (60 s in all). A
 * start with no new frames fails at 15 s, as before. `debug.privyhub.start_gate_rearm=0` = before (always fail).
 * A recovery does not use this (it re-arms on its own, D-BASE-R3).
 */
class StartGateRearm(private val enabled: Boolean) {
    var rearms: Int = 0
        private set
    private var renderedAtArm = 0L

    /** A new start's first window. */
    fun arm(rendered: Long) {
        rearms = 0
        renderedAtArm = rendered
    }

    /** At a window's end: true = re-armed (a new window), false = fail as before. */
    fun onTimeout(rendered: Long): Boolean {
        if (!enabled || rearms >= MAX_REARMS || rendered <= renderedAtArm) return false
        rearms += 1
        renderedAtArm = rendered
        return true
    }

    companion object {
        const val PROPERTY = "debug.privyhub.start_gate_rearm"
        const val MAX_REARMS = 3

        fun parse(value: String?): Boolean = value?.trim().let { it != "0" && it != "off" }

        fun fromSystem(): Boolean =
            try {
                val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
                parse(get.invoke(null, PROPERTY) as? String)
            } catch (_: Throwable) {
                parse(null)
            }
    }
}
