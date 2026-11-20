package com.safeiot.privyhub.streaming

/**
 * G6-HM2: the touch pad's player rules, pure Kotlin (JVM-tested). Design:
 * `docs/memory/evidence/g6_hm1_2026-11-19/design_written_before_code.md` §5 (hashed before this code) and the user's
 * answers `…/g6_hm1_2026-11-19/user_answers_2026-11-19.md` (D2; Q2 (d); Q3 (b), (i); Q4 (b)). Used only by the
 * handheld activity; nothing on the onn calls them.
 */

/**
 * D2 with Q3 (b), (i): after every start that clears the slots (a game's start, every unpause; not a self-restart),
 * the count starts at the first gameplay release, and at [WAIT_MS] the touch pad joins as P1 unless a real pad holds
 * P1 by then. Q4 (b): [secondsLeft] is the pad region's countdown. G6-JOIN1: a touch hold during the wait joins at
 * once ([TouchHoldJoin]); a shorter touch does not.
 */
class TouchP1Rule {
    enum class Action { NONE, JOIN_P1, GIVE_UP }

    private var waitingForRelease = false
    private var armedAtMs: Long? = null

    /** The prompt's start response: a cleared map arms the rule at the next release; a self-restart keeps the map. */
    fun onStart(selfRestart: Boolean) {
        armedAtMs = null
        waitingForRelease = !selfRestart
    }

    /** The gameplay release (hook H6). Only the first release after a start arms it (a link recovery's does not). */
    fun onGameplayReleased(nowMs: Long) {
        if (waitingForRelease && armedAtMs == null) armedAtMs = nowMs
    }

    /** The pause, the end, the activity's destruction. */
    fun cancel() {
        waitingForRelease = false
        armedAtMs = null
    }

    fun armed(): Boolean = armedAtMs != null

    /** The countdown's whole seconds left (5 … 1), or null when nothing is counting. */
    fun secondsLeft(nowMs: Long): Int? {
        val t = armedAtMs ?: return null
        val left = WAIT_MS - (nowMs - t)
        return if (left <= 0) null else ((left + 999) / 1000).toInt()
    }

    /**
     * The UI tick. [p1HeldByRealPad]: a real pad holds slot 0 now. A real P1 before the deadline ends the rule
     * ([Action.GIVE_UP]; the lower region shows the status panel, Q1 (c)); at the deadline with P1 free, once,
     * [Action.JOIN_P1].
     */
    fun tick(nowMs: Long, p1HeldByRealPad: Boolean): Action {
        val t = armedAtMs ?: return Action.NONE
        if (p1HeldByRealPad) { cancel(); return Action.GIVE_UP }
        if (nowMs - t < WAIT_MS) return Action.NONE
        cancel()
        return Action.JOIN_P1
    }

    companion object {
        const val WAIT_MS = 5_000L
    }
}

/**
 * Q2 (d), handheld only and only against the touch pad: a real pad's hold that began while the pad held no slot (the
 * hold that joins it at 0.5 s, or that could not join) and lasts [TAKEOVER_MS] on the same key moves that pad to P1
 * when the touch pad holds P1. A joined player holding a button in play never triggers it (its hold began joined).
 */
class TouchTakeover {
    private class Hold(val pad: PadDevice, val keyCode: Int, val sinceMs: Long)

    private val holds = LinkedHashMap<String, Hold>()

    /** Every key of a real pad; [joinedAtDown]: the pad held a slot when this key went down. */
    fun onKey(pad: PadDevice, keyCode: Int, down: Boolean, repeat: Int, nowMs: Long, joinedAtDown: Boolean) {
        if (!PadSlots.eligible(pad)) return
        val k = PadSlots.key(pad)
        if (down) {
            if (repeat == 0 && !joinedAtDown && keyCode in PlayerPrompt.CLAIM_KEYS && k !in holds) {
                holds[k] = Hold(pad, keyCode, nowMs)
            }
        } else if (holds[k]?.keyCode == keyCode) {
            holds.remove(k)
        }
    }

    /** The pad due for P1 (the longest hold first), or null; [p1IsTouchPad]: slot 0's holder is the touch pad. */
    fun due(nowMs: Long, p1IsTouchPad: Boolean): PadDevice? {
        if (!p1IsTouchPad) return null
        val e = holds.entries.filter { nowMs - it.value.sinceMs >= TAKEOVER_MS }.minByOrNull { it.value.sinceMs }
            ?: return null
        holds.remove(e.key)
        return e.value.pad
    }

    fun clear() = holds.clear()

    companion object {
        const val TAKEOVER_MS = 2_000L
    }
}

/**
 * G6-JOIN1 (the user, 2026-11-20: "if I hold a virtual button that registers P1"): while the countdown runs and P1 is
 * free, any touch control (a button, the D-pad, a shoulder, a stick, Select, Start; End is its own view, never here)
 * held for a real pad's join hold ([PlayerPrompt.HOLD_MS], 500 ms) makes the touch pad P1 at once and stops the
 * countdown. Shorter: nothing; the countdown goes on. P1 taken or no countdown: nothing (today). No hold: the countdown
 * joins at its deadline as before.
 */
class TouchHoldJoin(private val holdMs: Long = PlayerPrompt.HOLD_MS) {
    enum class Via(val report: String) { HOLD("hold"), TIMER("timer") }

    private val since = HashMap<TouchPadState.Control, Long>()

    /** The controls held now (each touch event and each tick): a control's hold starts when first seen held. */
    fun observe(held: Set<TouchPadState.Control>, nowMs: Long) {
        since.keys.retainAll(held)
        for (c in held) if (c !in since) since[c] = nowMs
    }

    fun reset() = since.clear()

    /**
     * The UI tick: [p1Free] no device holds slot 0; [p1HeldByRealPad] a real pad does. A due hold (the countdown
     * running, P1 free) -> [Via.HOLD] and the countdown stopped; otherwise the countdown's own tick ([Via.TIMER] at its
     * deadline). Null: no join now.
     */
    fun step(nowMs: Long, rule: TouchP1Rule, p1Free: Boolean, p1HeldByRealPad: Boolean): Via? {
        if (rule.armed() && p1Free && !p1HeldByRealPad && since.values.any { nowMs - it >= holdMs }) {
            rule.cancel()
            since.clear()
            return Via.HOLD
        }
        return if (rule.tick(nowMs, p1HeldByRealPad) == TouchP1Rule.Action.JOIN_P1) Via.TIMER else null
    }
}
