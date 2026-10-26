package com.safeiot.privyhub.streaming

/**
 * B14: the "any house" link notice, behind the system property
 * `debug.privyhub.link_notice` (CL-B7P's convention). B25: on unless `0`
 * (as B13's link_report, B19's stall_signal / restart_guard); `0` = B14's
 * absent: no object, no view, no key.
 *
 * LINK-R1: on 5 GHz 0 uplink silences and 0 hitch seconds per 10 min; on
 * 2.4 GHz 16-22 and 20 in every room. The onn sat on 2.4 GHz for a month and
 * nothing told anyone. From the client's own link reading (B3's LinkSample;
 * no network call), a small plain notice: what it sees and the one thing to
 * do. Shown on 2.4 GHz at once, or RSSI <= -72 dBm / tx <= 54 Mbps held 10 s;
 * cleared after 30 s good; at most once a session unless the band changes.
 * Nothing about the stream changes.
 */
object LinkNoticeFlag {
    const val PROPERTY = "debug.privyhub.link_notice"

    // B25: on unless `0` (the user's "Yes", 2026-10-26: the onn fell back to 2.4 GHz on its own and nothing told anyone)
    fun parse(value: String?): Boolean = value?.trim() != "0"

    /** The property, read through reflection; a failed read is absent, so on (B25). */
    fun fromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            parse(null)
        }
}

/** What the notice says; the wording is the user's to edit (the record lists it). */
object LinkNoticeText {
    const val ACTION_BAND = "Use your router's 5 GHz Wi-Fi for this box."
    const val ACTION_WEAK = "Move this box or the router closer, or use a wired connection."
    const val ACTION_SLOW = "Use the 5 GHz network or move closer to the router."

    fun of(reasons: Int, s: LinkSample?): String {
        val seen = mutableListOf<String>()
        if (reasons and LinkNotice.BAND_24 != 0) seen.add("2.4 GHz")
        if (reasons and LinkNotice.WEAK != 0) seen.add("weak signal (${s?.rssiDbm ?: "?"} dBm)")
        if (reasons and LinkNotice.SLOW != 0) seen.add("slow link (${s?.txMbps ?: "?"} Mbps)")
        val action = when {
            reasons and LinkNotice.BAND_24 != 0 -> ACTION_BAND
            reasons and LinkNotice.WEAK != 0 -> ACTION_WEAK
            else -> ACTION_SLOW
        }
        return "Wi-Fi: ${seen.joinToString(", ")}\n$action"
    }
}

/** The last notice, for the diagnostics page (this process only). */
object LinkNoticeStatus {
    @Volatile
    var lastText: String? = null

    @Volatile
    var lastShownAtMs: Long = 0L

    @Volatile
    var showing: Boolean = false
}

class LinkNotice(
    private val rssiThresholdDbm: Int = -72,
    private val txThresholdMbps: Int = 54,
    private val sustainMs: Long = 10_000L,
    private val clearMs: Long = 30_000L,
) {
    companion object {
        const val BAND_24 = 1
        const val WEAK = 2
        const val SLOW = 4

        /** 24 / 5 / 6 GHz from the frequency, null when unknown. */
        fun band(frequencyMhz: Int?): Int? =
            when (frequencyMhz) {
                null -> null
                in 2_400..2_500 -> 24
                in 4_900..5_900 -> 5
                in 5_925..7_125 -> 6
                else -> null
            }
    }

    sealed class Event {
        data class Shown(val reasons: Int, val text: String) : Event()
        object Cleared : Event()
    }

    var shown = false
        private set
    var reasons = 0
        private set
    var shownCount = 0L
        private set
    var lastReasons = 0
        private set

    private var shownThisSession = false
    private var lastBand: Int? = null
    private var weakSinceMs: Long? = null
    private var slowSinceMs: Long? = null
    private var goodSinceMs: Long? = null

    /** A new session re-arms it (the notice itself is cleared). */
    fun onSessionStart() {
        shown = false
        reasons = 0
        shownThisSession = false
        lastBand = null
        weakSinceMs = null
        slowSinceMs = null
        goodSinceMs = null
    }

    /** One reading (null = nothing new); returns the transition, if any. */
    fun update(s: LinkSample?, nowMs: Long): Event? {
        if (s == null) return null
        val band = band(s.frequencyMhz)
        if (band != null && lastBand != null && band != lastBand) {
            shownThisSession = false                    // the band changed: the notice may be shown again
        }
        if (band != null) lastBand = band
        val is24 = band == 24
        val weakNow = s.rssiDbm != null && s.rssiDbm <= rssiThresholdDbm
        val slowNow = s.txMbps != null && s.txMbps <= txThresholdMbps
        weakSinceMs = if (weakNow) (weakSinceMs ?: nowMs) else null
        slowSinceMs = if (slowNow) (slowSinceMs ?: nowMs) else null
        var bits = 0
        if (is24) bits = bits or BAND_24
        if (weakSinceMs != null && nowMs - weakSinceMs!! >= sustainMs) bits = bits or WEAK
        if (slowSinceMs != null && nowMs - slowSinceMs!! >= sustainMs) bits = bits or SLOW
        val goodNow = !is24 && !weakNow && !slowNow
        if (!shown) {
            if (bits != 0 && !shownThisSession) {
                shown = true
                shownThisSession = true
                reasons = bits
                lastReasons = bits
                shownCount++
                goodSinceMs = null
                return Event.Shown(bits, LinkNoticeText.of(bits, s))
            }
            return null
        }
        if (!goodNow) {
            goodSinceMs = null
            return null
        }
        val since = goodSinceMs ?: nowMs.also { goodSinceMs = it }
        if (nowMs - since >= clearMs) {
            shown = false
            reasons = 0
            goodSinceMs = null
            return Event.Cleared
        }
        return null
    }

    /** The heartbeat's fragment: the reasons while shown, else 0. */
    fun query(): String = "&link_notice=${if (shown) reasons else 0}"
}
