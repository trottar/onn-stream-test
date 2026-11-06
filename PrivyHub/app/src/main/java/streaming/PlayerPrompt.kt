package com.safeiot.privyhub.streaming

import org.json.JSONArray
import org.json.JSONObject

/**
 * B41: the player prompt, behind the system property `debug.privyhub.player_prompt=1` (CL-B7P's convention).
 * Absent / empty / any other value = today: no object, no view, no query or report key.
 *
 * On top of B34 / B38's stable slots (the prompt implies them): at a game's start and when a new eligible pad
 * appears, "Player N — press any button" bottom-centre; the first unclaimed eligible pad to press a face button or
 * Start claims the lowest open slot below the title's player count (the host's `players`, 2 when absent) and shows
 * "PN" for 2 s; the press also reaches the game (never blocking input). A pad already in the map keeps its slot and
 * shows its badge on its first press. Select + Start held 2 s releases a slot ("PN released"). A 1-player title:
 * no prompt, B34's assignment. Design: `docs/memory/evidence/b41_2026-11-06/design_written_before_code.md`
 * (hashed before this code).
 */
object PlayerPromptFlag {
    const val PROPERTY = "debug.privyhub.player_prompt"

    fun parse(value: String?): Boolean = value?.trim() == "1"

    /** The property, read through reflection; a failed read is absent (today). */
    fun fromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            false
        }
}

class PlayerPrompt(private val slots: PadSlots) {
    data class View(val prompt: String?, val badge: String?)

    @Volatile
    var players: Int = DEFAULT_PLAYERS
        private set

    private val lock = Any()
    private val claimedBy = HashMap<Int, String>()      // slot -> prompt | stable
    private val badgeShown = HashSet<String>()           // pad keys badged this session
    private val holdBits = HashMap<String, Int>()        // pad key -> Select (1) / Start (2) held
    private val holdSince = HashMap<String, Long>()      // pad key -> both held since
    private var badgeText: String? = null
    private var badgeUntilMs = 0L

    val active: Boolean get() = players >= 2

    /** The sender's start, in place of [PadSlots.beginStart]: no pre-assignment; the map's pads keep their slots. */
    fun beginStart(connected: List<PadDevice>) {
        synchronized(lock) {
            badgeShown.clear()
            holdBits.clear()
            holdSince.clear()
            badgeText = null
            if (!active) slots.beginStart(connected)
            markStable()
        }
    }

    /** After the start response: the title's player count; 1 = B34's assignment, no prompt. */
    fun setPlayers(n: Int, connected: List<PadDevice>) {
        synchronized(lock) {
            players = n.coerceIn(1, 4)
            if (!active) {
                slots.beginStart(connected)
                markStable()
            }
        }
    }

    /** A key event's slot: null = no player (an unclaimed pad's non-claim key, or not a gamepad). */
    fun slotForKey(d: PadDevice, keyCode: Int, down: Boolean, nowMs: Long, connected: () -> List<PadDevice>): Int? {
        if (!active) return slots.slotFor(d, connected)
        if (!PadSlots.eligible(d)) return null
        val k = PadSlots.key(d)
        synchronized(lock) {
            slots.slotOfKey(k)?.let { s ->
                trackHold(k, keyCode, down, nowMs)
                if (down && badgeShown.add(k)) badge("P${s + 1}", nowMs)
                return s
            }
            if (!down || keyCode !in CLAIM_KEYS) return null
            val s = openSlot(connected())?.also { slots.claim(d, it) }
                ?: slots.slotFor(d, connected)
                ?: return null
            claimedBy[s] = PROMPT
            holdBits.remove(k)
            badgeShown.add(k)
            badge("P${s + 1}", nowMs)
            return s
        }
    }

    /** A motion event's slot: a stick never claims. */
    fun slotForMotion(d: PadDevice, connected: () -> List<PadDevice>): Int? =
        if (!active) slots.slotFor(d, connected) else slots.slotOf(d)

    /** The UI tick: a Select + Start hold of [RELEASE_MS] frees the pad's slot. */
    fun tick(nowMs: Long) {
        synchronized(lock) {
            val due = holdSince.filter { nowMs - it.value >= RELEASE_MS }.keys.toList()
            for (k in due) {
                holdSince.remove(k)
                holdBits.remove(k)
                val s = slots.slotOfKey(k) ?: continue
                slots.release(s)
                claimedBy.remove(s)
                badgeShown.remove(k)
                badge("P${s + 1} released", nowMs)
            }
        }
    }

    fun view(nowMs: Long, connected: List<PadDevice>): View = synchronized(lock) {
        val prompt = if (!active) null else {
            val unclaimed = connected.any { PadSlots.eligible(it) && slots.slotOf(it) == null }
            openSlot(connected)?.takeIf { unclaimed }?.let { "Player ${it + 1} — press any button" }
        }
        View(prompt, badgeText?.takeIf { nowMs < badgeUntilMs })
    }

    /** `slot:p|s` for each claimed or kept slot (the start's and the heartbeat's `pad_claims`). */
    fun claimsString(): String = synchronized(lock) {
        claimedBy.entries.sortedBy { it.key }.joinToString(",") { "${it.key}:${if (it.value == PROMPT) "p" else "s"}" }
    }

    fun claimsJson(): JSONArray = synchronized(lock) {
        JSONArray().apply {
            claimedBy.entries.sortedBy { it.key }.forEach { put(JSONObject().put("slot", it.key).put("claimed_by", it.value)) }
        }
    }

    fun claimedBy(slot: Int): String? = synchronized(lock) { claimedBy[slot] }

    /** The lowest slot below [players] with no holder, or whose holder is not connected. */
    private fun openSlot(connected: List<PadDevice>): Int? {
        val present = connected.filter { PadSlots.eligible(it) }.map { PadSlots.key(it) }.toSet()
        return (0 until players).firstOrNull { s -> slots.holderOf(s)?.let { it !in present } ?: true }
    }

    private fun markStable() {
        claimedBy.clear()
        slots.map().forEach { claimedBy[it.slot] = STABLE }
    }

    private fun trackHold(k: String, keyCode: Int, down: Boolean, nowMs: Long) {
        val bit = when (keyCode) {
            KEYCODE_BUTTON_SELECT -> 1
            KEYCODE_BUTTON_START -> 2
            else -> return
        }
        val bits = (holdBits[k] ?: 0).let { if (down) it or bit else it and bit.inv() }
        holdBits[k] = bits
        if (bits == 3) holdSince.putIfAbsent(k, nowMs) else holdSince.remove(k)
    }

    private fun badge(text: String, nowMs: Long) {
        badgeText = text
        badgeUntilMs = nowMs + BADGE_MS
    }

    companion object {
        const val DEFAULT_PLAYERS = 2
        const val BADGE_MS = 2_000L
        const val RELEASE_MS = 2_000L
        const val PROMPT = "prompt"
        const val STABLE = "stable"

        // android.view.KeyEvent's codes, inlined so the JVM tests need no Android stub
        const val KEYCODE_BUTTON_A = 96
        const val KEYCODE_BUTTON_B = 97
        const val KEYCODE_BUTTON_X = 99
        const val KEYCODE_BUTTON_Y = 100
        const val KEYCODE_BUTTON_START = 108
        const val KEYCODE_BUTTON_SELECT = 109

        /** A face button or Start claims a slot. */
        val CLAIM_KEYS = setOf(KEYCODE_BUTTON_A, KEYCODE_BUTTON_B, KEYCODE_BUTTON_X, KEYCODE_BUTTON_Y, KEYCODE_BUTTON_START)
    }
}
