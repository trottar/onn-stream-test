package com.safeiot.privyhub.streaming

import org.json.JSONArray
import org.json.JSONObject
import java.security.MessageDigest

/**
 * B41: the player prompt, behind the system property `debug.privyhub.player_prompt` (CL-B7P's convention).
 * B46: on by default -- absent / empty / junk / `1` = on; `0` / `off` = no prompt at all (no object, no view, no query
 * or report key).
 * B54 (the user, 2026-11-08: "a quick press and hold might be a more clear and intuitive check"; a multitap change "At
 * once"): **hold-to-join replaces B46's chooser.** At every session start that is not a self-restart (a game's start,
 * every unpause) the slot map is cleared and a bottom-centre line reads "Hold any button to join"; an unclaimed real
 * pad holding a face button or Start for [HOLD_MS] becomes the next player with a 2-s "PN" badge, and the line reads
 * "P1 joined — hold to add Player 2". A 1-player title closes the join after P1; the line closes when the session's
 * ports are taken and 10 s after the last join, and comes back while an unclaimed pad holds. A hold that needs a port
 * beyond the session's (P3 on two ports) asks the host to relaunch the title with the multitap at once ("Setting up 4
 * players…"); the pad joins when the host answers. An unclaimed pad's keys go nowhere (it has no port) and the joining
 * hold is not sent to the game; a joined pad's keys are play. Key repeats never start a hold. Select + Start held 2 s
 * releases a slot; a fresh hold re-joins.
 * Design: `docs/memory/evidence/b54_2026-11-08/design_written_before_code.md` (hashed before this code).
 */
object PlayerPromptFlag {
    const val PROPERTY = "debug.privyhub.player_prompt"

    // B46: on unless `0` / `off` (the user's "by default also", 2026-11-07); `off` as B42's pad_slots
    fun parse(value: String?): Boolean = value?.trim().let { it != "0" && it != "off" }

    /** The property, read through reflection; a failed read is absent, so on (B46). */
    fun fromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            parse(null)
        }
}

/** B46 / B54: the title's highest joined count, keyed by [PlayerPrompt.gameKey] (a private preference on the onn). */
interface PlayerChoiceStore {
    fun get(key: String): Int?
    fun put(key: String, players: Int)
}

class MemoryPlayerChoiceStore : PlayerChoiceStore {
    private val m = HashMap<String, Int>()
    override fun get(key: String): Int? = m[key]
    override fun put(key: String, players: Int) { m[key] = players }
}

/** B46: the session's ports as the host set them (`ports_set`); an old host's absent key = 2 ports. */
data class PortsSet(val players: Int, val multitap: Boolean, val multitapAvailable: Boolean, val source: String) {
    fun toJson(): JSONObject = JSONObject().put("players", players).put("multitap", multitap)
        .put("multitap_available", multitapAvailable).put("source", source)

    companion object {
        val UNKNOWN = PortsSet(2, multitap = false, multitapAvailable = false, source = "absent")

        fun parse(o: JSONObject?): PortsSet =
            if (o == null) UNKNOWN else of(
                o.optInt("players", 2),
                o.optBoolean("multitap", false),
                o.optBoolean("multitap_available", false),
                o.optString("source", "host"),
            )

        /** The echo's fields (the JVM tests' path: org.json is a stub there). */
        fun of(players: Int, multitap: Boolean, multitapAvailable: Boolean, source: String): PortsSet =
            PortsSet(players.coerceIn(1, 4), multitap, multitapAvailable, source)
    }
}

/** B46 / B54: the session's joined count across a self-restart (a new activity in the same process). */
object PlayerPromptProcess {
    @Volatile
    var lastJoined: Int? = null
}

class PlayerPrompt(private val slots: PadSlots, private val store: PlayerChoiceStore = MemoryPlayerChoiceStore()) {
    data class View(val prompt: String?, val badge: String?)

    /** B54: a relaunch's answer, for the report. */
    data class Relaunch(val ok: Boolean, val state: String?, val totalMs: Long?)

    enum class Phase { NONE, JOINING, RELAUNCHING }

    /** The host's B41 `players` (1 = a 1-player title: the join closes after P1). */
    @Volatile
    var players: Int = DEFAULT_PLAYERS
        private set

    @Volatile
    var phase: Phase = Phase.NONE
        private set

    @Volatile
    var ports: PortsSet = PortsSet.UNKNOWN
        private set

    /** B54: relaunches asked this session, and the last answer. */
    @Volatile
    var relaunches: Int = 0
        private set

    @Volatile
    var lastRelaunch: Relaunch? = null
        private set

    private class Hold(val pad: PadDevice, val keyCode: Int, val sinceMs: Long)

    private val lock = Any()
    private val claimedBy = HashMap<Int, String>()      // slot -> prompt | stable
    private val holds = HashMap<String, Hold>()          // B54: unclaimed pad key -> its hold in progress
    private val holdBits = HashMap<String, Int>()        // pad key -> Select (1) / Start (2) held
    private val holdSince = HashMap<String, Long>()      // pad key -> both held since
    private val needsUp = HashSet<Pair<String, Int>>()   // (pad key, key code) held through a join / release
    private var gameKey: String? = null
    private var badgeText: String? = null
    private var badgeUntilMs = 0L
    private var noteText: String? = null
    private var noteUntilMs = 0L
    private var lastJoinAtMs: Long? = null
    private var relaunchAsk: Int? = null                 // the ports to ask the host for (taken by the activity)
    private var relaunchPad: PadDevice? = null           // the pad waiting for the relaunch
    private var relaunchTarget = MAX_PLAYERS             // the ports asked for (the line's count)

    /** The joined count (the queries' and the report's `players_joined`). */
    val joined: Int get() = synchronized(lock) { slots.map().size }

    /** The sender's start: no pre-assignment; the opening waits for the start response. */
    fun beginStart(connected: List<PadDevice>) {
        synchronized(lock) {
            holds.clear()
            holdBits.clear()
            holdSince.clear()
            needsUp.clear()
            badgeText = null
        }
    }

    /**
     * After the start response: [selfRestart] keeps the map (no line); any other start (a game's start, an unpause)
     * clears the map and opens "Hold any button to join".
     */
    fun onStartResponse(selfRestart: Boolean, hostPlayers: Int, portsSet: PortsSet, key: String?, connected: List<PadDevice>) {
        synchronized(lock) {
            players = hostPlayers.coerceIn(1, 4)
            ports = portsSet
            gameKey = key
            relaunchAsk = null
            relaunchPad = null
            phase = Phase.JOINING
            if (selfRestart) {
                markStable()
                lastJoinAtMs = Long.MIN_VALUE / 2   // the line stays closed until an unclaimed pad holds
                return
            }
            slots.clearAll()
            claimedBy.clear()
            noteText = null
            lastJoinAtMs = null
        }
    }

    /**
     * B54: every key of a real pad, before the gameplay gate. An unclaimed pad's key is consumed (true; its hold is
     * tracked); a joined pad's key goes on to the sender (false). Not a pad, or the prompt not open: false.
     */
    fun onJoinKey(keyCode: Int, down: Boolean, repeat: Int, pad: PadDevice?, nowMs: Long): Boolean {
        if (pad == null || !PadSlots.eligible(pad)) return false
        val k = PadSlots.key(pad)
        synchronized(lock) {
            if (phase == Phase.NONE) return false
            if (slots.slotOfKey(k) != null) {
                // the joining key (and its repeats) is not play until lifted
                if ((k to keyCode) !in needsUp) return false
                if (!down) needsUp.remove(k to keyCode)
                return true
            }
            if (!down) {
                needsUp.remove(k to keyCode)
                if (holds[k]?.keyCode == keyCode) holds.remove(k)   // a tap: no join
                return true
            }
            if (phase == Phase.RELAUNCHING) return true             // holds wait out the relaunch
            if (repeat == 0 && keyCode in CLAIM_KEYS && (k to keyCode) !in needsUp && k !in holds) {
                holds[k] = Hold(pad, keyCode, nowMs)
            }
            return true
        }
    }

    /** True while an unclaimed pad is holding (the activity ticks every 50 ms then). */
    fun holdPending(): Boolean = synchronized(lock) { holds.isNotEmpty() }

    /** A key event's slot: null = no player (an unclaimed pad, not a gamepad). A joined pad's key is play. */
    fun slotForKey(
        d: PadDevice,
        keyCode: Int,
        down: Boolean,
        nowMs: Long,
        connected: () -> List<PadDevice>,
        repeat: Int = 0,
    ): Int? {
        if (!PadSlots.eligible(d)) return null
        val k = PadSlots.key(d)
        synchronized(lock) {
            if (!down) needsUp.remove(k to keyCode)
            val s = slots.slotOfKey(k) ?: return null
            trackHold(k, keyCode, down, nowMs)
            return s
        }
    }

    /** A motion event's slot: a stick never joins. */
    fun slotForMotion(d: PadDevice, connected: () -> List<PadDevice>): Int? = slots.slotOf(d)

    /**
     * The UI tick: a hold of [HOLD_MS] joins (or asks for the relaunch); a Select + Start hold of [RELEASE_MS] frees
     * the pad's slot (both keys must then be lifted).
     */
    fun tick(nowMs: Long, connected: List<PadDevice> = emptyList()) {
        synchronized(lock) {
            val due = holdSince.filter { nowMs - it.value >= RELEASE_MS }.keys.toList()
            for (k in due) {
                holdSince.remove(k)
                holdBits.remove(k)
                val s = slots.slotOfKey(k) ?: continue
                slots.release(s)
                claimedBy.remove(s)
                needsUp.add(k to KEYCODE_BUTTON_SELECT)
                needsUp.add(k to KEYCODE_BUTTON_START)
                badge("P${s + 1} released", nowMs)
            }
            if (phase != Phase.JOINING) return
            val ready = holds.entries.filter { nowMs - it.value.sinceMs >= HOLD_MS }.sortedBy { it.value.sinceMs }
            for ((k, h) in ready) {
                holds.remove(k)
                needsUp.add(k to h.keyCode)   // the joining key is not play until lifted
                join(h.pad, k, nowMs, connected)
                if (phase != Phase.JOINING) break
            }
        }
    }

    /** B54: the ports to ask the host for, once (the activity posts the relaunch). */
    fun takeRelaunchRequest(): Int? = synchronized(lock) { relaunchAsk.also { relaunchAsk = null } }

    /** B54: the host's answer to the relaunch: success → the new ports and the waiting pad joins; failure → a note. */
    fun onRelaunchResult(ok: Boolean, portsSet: PortsSet?, state: String?, totalMs: Long?, nowMs: Long,
                         connected: List<PadDevice>) {
        synchronized(lock) {
            if (phase != Phase.RELAUNCHING) return
            lastRelaunch = Relaunch(ok, state, totalMs)
            phase = Phase.JOINING
            val pad = relaunchPad
            relaunchPad = null
            if (ok && portsSet != null) ports = portsSet
            if (!ok || portsSet == null) {
                note("Couldn't set up $relaunchTarget players", nowMs)
                return
            }
            if (pad != null && connected.any { PadSlots.eligible(it) && PadSlots.key(it) == PadSlots.key(pad) }) {
                join(pad, PadSlots.key(pad), nowMs, connected)
            }
        }
    }

    fun view(nowMs: Long, connected: List<PadDevice>): View = synchronized(lock) {
        val badgeNow = badgeText?.takeIf { nowMs < badgeUntilMs }
        val note = noteText?.takeIf { nowMs < noteUntilMs }
        val line = when (phase) {
            Phase.NONE -> null
            Phase.RELAUNCHING -> "Setting up $relaunchTarget players…"
            Phase.JOINING -> joinLine(nowMs)
        }
        View(listOfNotNull(line, note).joinToString("\n").ifEmpty { null }, badgeNow)
    }

    /** `slot:p|s` for each joined or kept slot (the start's and the heartbeat's `pad_claims`). */
    fun claimsString(): String = synchronized(lock) {
        claimedBy.entries.sortedBy { it.key }.joinToString(",") { "${it.key}:${if (it.value == PROMPT) "p" else "s"}" }
    }

    fun claimsJson(): JSONArray = synchronized(lock) {
        JSONArray().apply {
            claimedBy.entries.sortedBy { it.key }.forEach { put(JSONObject().put("slot", it.key).put("claimed_by", it.value)) }
        }
    }

    fun claimedBy(slot: Int): String? = synchronized(lock) { claimedBy[slot] }

    /** B54: the report's `relaunches`. */
    fun relaunchesJson(): JSONObject = synchronized(lock) {
        JSONObject().put("count", relaunches).apply {
            lastRelaunch?.let { r ->
                put("last", JSONObject().put("ok", r.ok).put("state", r.state ?: JSONObject.NULL)
                    .put("total_ms", r.totalMs ?: JSONObject.NULL))
            }
        }
    }

    /** The most players this title's ports can take now (1 for a 1-player title). */
    private fun cap(): Int = if (players == 1) 1 else ports.players

    private fun full(): Boolean = joinedLocked() >= cap()

    private fun joinedLocked(): Int = slots.map().size

    private fun joinLine(nowMs: Long): String? {
        val n = joinedLocked()
        if (n == 0) return "Hold any button to join"
        if (players == 1) return null                                   // a 1-player title: closed after P1
        val next = openSlot(emptyList(), ignorePresence = true) ?: return null   // four joined
        val holding = holds.isNotEmpty()
        if (!holding) {
            if (full()) return null
            val last = lastJoinAtMs
            if (last != null && nowMs - last >= LINE_MS) return null
        }
        val labels = slots.map().joinToString(", ") { "P${it.slot + 1}" }
        return "$labels joined — hold to add Player ${next + 1}"
    }

    private fun join(pad: PadDevice, k: String, nowMs: Long, connected: List<PadDevice>) {
        if (players == 1 && joinedLocked() >= 1) return   // a 1-player title: closed after P1
        val s = openSlot(connected) ?: return
        if (s >= ports.players) {
            if (s < MAX_PLAYERS && ports.multitapAvailable) {
                relaunchAsk = if (s < 2) 2 else MAX_PLAYERS
                relaunchTarget = relaunchAsk ?: MAX_PLAYERS
                relaunchPad = pad
                relaunches += 1
                holds.clear()
                phase = Phase.RELAUNCHING
            } else {
                note("No multitap on this system — ${ports.players} players", nowMs)
            }
            return
        }
        slots.claim(pad, s)
        claimedBy[s] = PROMPT
        holdBits.remove(k)
        lastJoinAtMs = nowMs
        badge("P${s + 1}", nowMs)
        val n = joinedLocked()
        PlayerPromptProcess.lastJoined = n
        gameKey?.let { g -> if ((store.get(g) ?: 0) < n) store.put(g, n) }
    }

    /** The lowest slot below 4 with no holder, or whose holder is not connected. */
    private fun openSlot(connected: List<PadDevice>, ignorePresence: Boolean = false): Int? {
        val present = connected.filter { PadSlots.eligible(it) }.map { PadSlots.key(it) }.toSet()
        return (0 until MAX_PLAYERS).firstOrNull { s ->
            slots.holderOf(s)?.let { !ignorePresence && it !in present } ?: true
        }
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

    private fun note(text: String, nowMs: Long) {
        noteText = text
        noteUntilMs = nowMs + NOTE_MS
    }

    companion object {
        const val DEFAULT_PLAYERS = 2
        const val MAX_PLAYERS = 4
        const val HOLD_MS = 500L
        const val LINE_MS = 10_000L
        const val BADGE_MS = 2_000L
        const val RELEASE_MS = 2_000L
        const val NOTE_MS = 5_000L
        const val TICK_MS = 200L
        const val TICK_HOLD_MS = 50L
        const val PROMPT = "prompt"
        const val STABLE = "stable"

        // android.view.KeyEvent's codes, inlined so the JVM tests need no Android stub
        const val KEYCODE_DPAD_LEFT = 21
        const val KEYCODE_DPAD_RIGHT = 22
        const val KEYCODE_DPAD_CENTER = 23
        const val KEYCODE_ENTER = 66
        const val KEYCODE_BUTTON_A = 96
        const val KEYCODE_BUTTON_B = 97
        const val KEYCODE_BUTTON_X = 99
        const val KEYCODE_BUTTON_Y = 100
        const val KEYCODE_BUTTON_START = 108
        const val KEYCODE_BUTTON_SELECT = 109

        /** A face button or Start, held, joins. */
        val CLAIM_KEYS = setOf(KEYCODE_BUTTON_A, KEYCODE_BUTTON_B, KEYCODE_BUTTON_X, KEYCODE_BUTTON_Y, KEYCODE_BUTTON_START)

        /** The title's preference key: sha256 of the host's game id, 12 hex (no id or title stored). */
        fun gameKey(id: String?): String? =
            id?.trim()?.takeIf { it.isNotEmpty() }?.let { s ->
                MessageDigest.getInstance("SHA-256").digest(("privyhub-players:" + s).toByteArray(Charsets.UTF_8))
                    .take(6).joinToString("") { "%02x".format(it) }
            }
    }
}
