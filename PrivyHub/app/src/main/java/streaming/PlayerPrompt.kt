package com.safeiot.privyhub.streaming

import org.json.JSONArray
import org.json.JSONObject
import java.security.MessageDigest

/**
 * B41: the player prompt, behind the system property `debug.privyhub.player_prompt` (CL-B7P's convention).
 * B46 (the user, 2026-11-07: "Player one press any button by default also"; "I want every game to have that 1 player,
 * 2 player, and multitap"; "It should pop up every time a game is active or unpaused"): **on by default** --
 * absent / empty / junk / `1` = the chooser; `0` / `off` = no prompt at all (no object, no view, no query or report
 * key: `8ba4d996…`'s absent).
 *
 * At every session start that is not a self-restart (a game's start, and every unpause: the Resume tile's new start),
 * the slot map is cleared and a bottom-centre chooser reads "Players:  1  /  2  /  multitap (3-4)"; left / right (a
 * pad's d-pad or hat, or the remote) moves, a face button (or the remote's centre) picks; the default is the title's
 * last choice, else 2 (1 when the host's `players` is 1). Then "Player N — press any button" up to the chosen count
 * (capped by the session's ports, `ports_set`); the first fresh face-button / Start press of an unclaimed pad takes the
 * lowest open slot with a 2-s "PN" badge; the press reaches the game. Key repeats never claim, and a key held through
 * a pick or a release must be lifted first (HOME-3 C6's held-Start re-claim). A pad beyond the count gets no slot.
 * Select + Start held 2 s releases a slot. The game is never paused.
 * Design: `docs/memory/evidence/b46_2026-11-07/design_written_before_code.md` (hashed before this code).
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

/** B46: the title's last choice, keyed by [PlayerPrompt.gameKey] (a private preference on the onn; fakes on the JVM). */
interface PlayerChoiceStore {
    fun get(key: String): Int?
    fun put(key: String, players: Int)
}

class MemoryPlayerChoiceStore : PlayerChoiceStore {
    private val m = HashMap<String, Int>()
    override fun get(key: String): Int? = m[key]
    override fun put(key: String, players: Int) { m[key] = players }
}

/** B46: the session's ports as the host set them at the launch (`ports_set`); an old host's absent key = 2 ports. */
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

/** B46: the session's choice across a self-restart (a new activity in the same process). */
object PlayerPromptProcess {
    @Volatile
    var lastChoice: Int? = null
}

class PlayerPrompt(private val slots: PadSlots, private val store: PlayerChoiceStore = MemoryPlayerChoiceStore()) {
    data class View(val prompt: String?, val badge: String?)

    enum class Phase { NONE, CHOOSING, CLAIMING, DONE }

    /** The host's B41 `players` (the default's input and the report's `players`). */
    @Volatile
    var players: Int = DEFAULT_PLAYERS
        private set

    @Volatile
    var phase: Phase = Phase.NONE
        private set

    /** 1 / 2 / 4 once picked (the queries' and the report's `players_chosen`). */
    @Volatile
    var chosen: Int? = null
        private set

    @Volatile
    var ports: PortsSet = PortsSet.UNKNOWN
        private set

    private val lock = Any()
    private val claimedBy = HashMap<Int, String>()      // slot -> prompt | stable
    private val badgeShown = HashSet<String>()           // pad keys badged this session
    private val holdBits = HashMap<String, Int>()        // pad key -> Select (1) / Start (2) held
    private val holdSince = HashMap<String, Long>()      // pad key -> both held since
    private val needsUp = HashSet<Pair<String, Int>>()   // (pad key, key code) held through a pick / release
    private val hatX = HashMap<String, Int>()            // pad key -> the hat's last side (-1 / 0 / 1)
    private var highlight = 1                            // index into OPTIONS
    private var gameKey: String? = null
    private var badgeText: String? = null
    private var badgeUntilMs = 0L
    private var noteText: String? = null
    private var noteUntilMs = 0L

    /** The claims' target: the choice capped by the session's ports. */
    val count: Int get() = chosen?.let { capped(it) } ?: 0

    /** The sender's start: no pre-assignment; the opening waits for the start response. */
    fun beginStart(connected: List<PadDevice>) {
        synchronized(lock) {
            badgeShown.clear()
            holdBits.clear()
            holdSince.clear()
            needsUp.clear()
            hatX.clear()
            badgeText = null
        }
    }

    /**
     * After the start response: [selfRestart] keeps the map and the session's choice (no chooser); any other start
     * (a game's start, an unpause) clears the map and opens the chooser.
     */
    fun onStartResponse(selfRestart: Boolean, hostPlayers: Int, portsSet: PortsSet, key: String?, connected: List<PadDevice>) {
        synchronized(lock) {
            players = hostPlayers.coerceIn(1, 4)
            ports = portsSet
            gameKey = key
            if (selfRestart) {
                chosen = PlayerPromptProcess.lastChoice ?: key?.let { store.get(it) } ?: defaultChoice()
                markStable()
                phase = Phase.DONE
                return
            }
            slots.clearAll()
            claimedBy.clear()
            chosen = null
            noteText = null
            highlight = OPTIONS.indexOf((key?.let { store.get(it) }) ?: defaultChoice()).coerceAtLeast(0)
            phase = Phase.CHOOSING
        }
    }

    /** A key from any device while the chooser is open: true = consumed (left / right / pick). */
    fun onChooserKey(keyCode: Int, down: Boolean, repeat: Int, pad: PadDevice?, nowMs: Long): Boolean {
        synchronized(lock) {
            if (phase != Phase.CHOOSING) return false
            val k = pad?.takeIf { PadSlots.eligible(it) }?.let { PadSlots.key(it) }
            when (keyCode) {
                KEYCODE_DPAD_LEFT, KEYCODE_DPAD_RIGHT -> {
                    if (down && repeat == 0) move(if (keyCode == KEYCODE_DPAD_LEFT) -1 else 1)
                    return true
                }
                in PICK_KEYS -> {
                    if (down && repeat == 0) {
                        k?.let { needsUp.add(it to keyCode) }
                        pick(OPTIONS[highlight], nowMs)
                    }
                    return true
                }
                else -> return false
            }
        }
    }

    /** A pad's hat while the chooser is open: a crossing of ±0.5 moves once; true = consumed. */
    fun onChooserHat(pad: PadDevice, x: Float): Boolean {
        synchronized(lock) {
            if (phase != Phase.CHOOSING || !PadSlots.eligible(pad)) return false
            val k = PadSlots.key(pad)
            val side = if (x <= -0.5f) -1 else if (x >= 0.5f) 1 else 0
            if (side != 0 && hatX[k] != side) move(side)
            hatX[k] = side
            return true
        }
    }

    /** A key event's slot: null = no player (the chooser is open, an unclaimed pad's non-claim key, not a gamepad). */
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
            if (phase == Phase.CHOOSING) return null
            slots.slotOfKey(k)?.let { s ->
                trackHold(k, keyCode, down, nowMs)
                if (down && badgeShown.add(k)) badge("P${s + 1}", nowMs)
                return s
            }
            // a fresh press only: no repeat, and not a key held through a pick or a release
            if (!down || repeat > 0 || keyCode !in CLAIM_KEYS || (k to keyCode) in needsUp) return null
            val s = openSlot(connected()) ?: return null
            slots.claim(d, s)
            claimedBy[s] = PROMPT
            holdBits.remove(k)
            badgeShown.add(k)
            badge("P${s + 1}", nowMs)
            if ((0 until count).all { slots.holderOf(it) != null }) phase = Phase.DONE
            return s
        }
    }

    /** A motion event's slot: a stick never claims. */
    fun slotForMotion(d: PadDevice, connected: () -> List<PadDevice>): Int? =
        if (phase == Phase.CHOOSING) null else slots.slotOf(d)

    /** The UI tick: a Select + Start hold of [RELEASE_MS] frees the pad's slot; both keys must be lifted first. */
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
                needsUp.add(k to KEYCODE_BUTTON_SELECT)
                needsUp.add(k to KEYCODE_BUTTON_START)
                badge("P${s + 1} released", nowMs)
                if (phase == Phase.DONE) phase = Phase.CLAIMING
            }
        }
    }

    fun view(nowMs: Long, connected: List<PadDevice>): View = synchronized(lock) {
        val badgeNow = badgeText?.takeIf { nowMs < badgeUntilMs }
        if (phase == Phase.CHOOSING) return@synchronized View(chooserLine(), badgeNow)
        val note = noteText?.takeIf { phase == Phase.CLAIMING || nowMs < noteUntilMs }
        val ask = if (phase == Phase.CLAIMING || phase == Phase.DONE) {
            val unclaimed = connected.any { PadSlots.eligible(it) && slots.slotOf(it) == null }
            openSlot(connected)?.takeIf { unclaimed }?.let { "Player ${it + 1} — press any button" }
        } else null
        View(listOfNotNull(ask, note).joinToString("\n").ifEmpty { null }, badgeNow)
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

    /** The chooser's line, the highlighted option in brackets. */
    fun chooserLine(): String = synchronized(lock) {
        "Players:  " + OPTIONS.indices.joinToString("  /  ") { i ->
            val label = LABELS[i]
            if (i == highlight) "[$label]" else label
        }
    }

    private fun defaultChoice(): Int = if (players == 1) 1 else 2

    private fun move(step: Int) {
        highlight = (highlight + step).coerceIn(0, OPTIONS.size - 1)
    }

    private fun pick(n: Int, nowMs: Long) {
        chosen = n
        PlayerPromptProcess.lastChoice = n
        gameKey?.let { store.put(it, n) }
        noteText = noteFor(n)
        noteUntilMs = nowMs + NOTE_MS
        phase = Phase.CLAIMING
    }

    /** The choice capped by the session's ports (the host cannot change them mid-session, B46 S2). */
    private fun capped(n: Int): Int = when (n) {
        4 -> if (ports.multitap && ports.players >= 4) 4 else minOf(2, ports.players)
        else -> minOf(n, ports.players)
    }

    private fun noteFor(n: Int): String? = when {
        n == 4 && !ports.multitapAvailable && !ports.multitap -> "No multitap on this system — 2 players"
        n == 4 && !(ports.multitap && ports.players >= 4) -> "Multitap from the next start"
        n < 4 && ports.multitap -> "Multitap off from the next start"
        n == 2 && ports.players < 2 -> "2 players from the next start"
        else -> null
    }

    /** The lowest slot below [count] with no holder, or whose holder is not connected. */
    private fun openSlot(connected: List<PadDevice>): Int? {
        val present = connected.filter { PadSlots.eligible(it) }.map { PadSlots.key(it) }.toSet()
        return (0 until count).firstOrNull { s -> slots.holderOf(s)?.let { it !in present } ?: true }
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
        const val NOTE_MS = 5_000L
        const val PROMPT = "prompt"
        const val STABLE = "stable"

        /** The chooser's options: 1, 2, multitap (sent as 4). */
        val OPTIONS = listOf(1, 2, 4)
        val LABELS = listOf("1", "2", "multitap (3-4)")

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

        /** A face button or Start claims a slot. */
        val CLAIM_KEYS = setOf(KEYCODE_BUTTON_A, KEYCODE_BUTTON_B, KEYCODE_BUTTON_X, KEYCODE_BUTTON_Y, KEYCODE_BUTTON_START)

        /** A face button, or the remote's centre / Enter, picks in the chooser. */
        val PICK_KEYS = setOf(KEYCODE_BUTTON_A, KEYCODE_BUTTON_B, KEYCODE_BUTTON_X, KEYCODE_BUTTON_Y,
            KEYCODE_DPAD_CENTER, KEYCODE_ENTER)

        /** The title's preference key: sha256 of the host's game id, 12 hex (no id or title stored). */
        fun gameKey(id: String?): String? =
            id?.trim()?.takeIf { it.isNotEmpty() }?.let { s ->
                MessageDigest.getInstance("SHA-256").digest(("privyhub-players:" + s).toByteArray(Charsets.UTF_8))
                    .take(6).joinToString("") { "%02x".format(it) }
            }
    }
}
