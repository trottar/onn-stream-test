package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/**
 * G6-HM2: the touch pad in the slots and the prompt (design `g6_hm1_2026-11-19` §5; the user's answers D2, Q2 (d),
 * Q3 (b)/(i), Q4 (b)). The prompt's own paths (B54) are driven exactly as PlayerPromptTest drives them.
 */
class G6TouchSlotsTest {

    private data class Dev(
        override val descriptor: String,
        override val controllerNumber: Int,
        override val vendorId: Int = 0x054c,
        override val productId: Int = 0x09cc,
        override val sources: Int = 0x00000401 or 0x01000010,
        override val hasGamepadButton: Boolean = true,
        override val isVirtual: Boolean = false,
        override val hasFaceButton: Boolean = true,
        override val hasStickOrHat: Boolean = true,
    ) : PadDevice

    private val padA = Dev("pad-a", 2)
    private val padB = Dev("pad-b", 3)
    private val touch = TouchPadDevice
    private val tablet = listOf<PadDevice>(padA, padB, touch)      // hook H4: the touch pad is "present"
    private val A = PlayerPrompt.KEYCODE_BUTTON_A
    private val X = PlayerPrompt.KEYCODE_BUTTON_X
    private val TWO = PortsSet(2, multitap = false, multitapAvailable = false, source = "join")

    @Before
    fun clearProcess() { PlayerPromptProcess.lastJoined = null }

    private fun fresh(hostPlayers: Int = 2, store: PlayerChoiceStore = MemoryPlayerChoiceStore(),
                      connected: List<PadDevice> = tablet): Pair<PadSlots, PlayerPrompt> {
        val s = PadSlots()
        val p = PlayerPrompt(s, store)
        p.beginStart(connected)
        p.onStartResponse(false, hostPlayers, TWO, PlayerPrompt.gameKey("g6-title"), connected)
        return s to p
    }

    private fun key(p: PlayerPrompt, d: PadDevice, code: Int, down: Boolean, now: Long, connected: List<PadDevice>): Int? =
        if (p.onJoinKey(code, down, 0, d, now)) null else p.slotForKey(d, code, down, now, { connected }, 0)

    /** A hold with the 50-ms tick running, without the release (the key stays down). */
    private fun press(p: PlayerPrompt, d: PadDevice, code: Int, from: Long, ms: Long, connected: List<PadDevice>) {
        key(p, d, code, true, from, connected)
        var t = from
        while (t < from + ms) { t += 50; p.tick(t, connected) }
    }

    @Test
    fun theTouchPadIsEligibleWithAFixedKey() {
        assertTrue(PadSlots.eligible(touch))
        assertEquals(TouchPadDevice.KEY, PadSlots.key(touch))
        assertEquals("01097c", PadSlots.key(touch))
        assertEquals("gamepad", PadSlots.vendorClass(touch.vendorId))
    }

    @Test
    fun theTouchPadJoinsAsP1WithoutAHold() {
        val store = MemoryPlayerChoiceStore()
        val (s, p) = fresh(store = store)
        assertEquals(0, p.joinAsP1WithoutHold(touch, 6_000, tablet))
        assertEquals(TouchPadDevice.KEY, s.holderOf(0))
        assertEquals("P1", p.view(6_000, tablet).badge)
        assertEquals(1, p.joined)
        assertEquals(1, store.get(PlayerPrompt.gameKey("g6-title")!!))
        assertNull(p.joinAsP1WithoutHold(touch, 6_100, tablet))          // already holds a slot
    }

    @Test
    fun theTouchPadDoesNotJoinWhenARealPadIsP1() {
        val (s, p) = fresh()
        press(p, padA, A, 1_000, 600, tablet)
        assertEquals(0, s.slotOf(padA))
        assertNull(p.joinAsP1WithoutHold(touch, 6_000, tablet))
        assertNull(s.slotOf(touch))
    }

    @Test
    fun aLaterRealPadIsP2AndTheStoredCountIsTwo() {
        val store = MemoryPlayerChoiceStore()
        val (s, p) = fresh(store = store)
        p.joinAsP1WithoutHold(touch, 6_000, tablet)
        press(p, padA, A, 7_000, 600, tablet)
        assertEquals(1, s.slotOf(padA))
        assertEquals(TouchPadDevice.KEY, s.holderOf(0))
        assertEquals(2, store.get(PlayerPrompt.gameKey("g6-title")!!))
    }

    /** Why hook H4 is needed: without the touch pad in the connected list its P1 counts as open (PP openSlot). */
    @Test
    fun withoutTheTouchPadPresentARealPadWouldTakeP1() {
        val onnLike = listOf<PadDevice>(padA, padB)
        val (s, p) = fresh(connected = onnLike)
        p.joinAsP1WithoutHold(touch, 6_000, onnLike)
        press(p, padA, A, 7_000, 600, onnLike)
        assertEquals(0, s.slotOf(padA))
    }

    @Test
    fun theJoinIsRefusedWhenThePromptIsNotJoining() {
        val s = PadSlots()
        val p = PlayerPrompt(s)
        assertNull(p.joinAsP1WithoutHold(touch, 0, tablet))              // no start response yet: phase NONE
        assertNull(p.takeOverP1(padA, TouchPadDevice.KEY, 0))
    }

    // Q2 (d): the hold that joined a pad at 0.5 s, kept to 2 s, takes P1 from the touch pad
    @Test
    fun aJoiningHoldKeptToTwoSecondsTakesP1FromTheTouchPad() {
        val (s, p) = fresh()
        val t = TouchTakeover()
        p.joinAsP1WithoutHold(touch, 6_000, tablet)
        t.onKey(padA, A, true, 0, 7_000, joinedAtDown = s.slotOf(padA) != null)
        press(p, padA, A, 7_000, 600, tablet)
        assertEquals(1, s.slotOf(padA))                                   // P2 at 0.5 s, as today
        assertNull(t.due(8_900, p1IsTouchPad = s.holderOf(0) == TouchPadDevice.KEY))   // 1.9 s: not yet
        val due = t.due(9_000, p1IsTouchPad = s.holderOf(0) == TouchPadDevice.KEY)
        assertEquals(padA, due)
        assertEquals(0, p.takeOverP1(due!!, TouchPadDevice.KEY, 9_000))
        assertEquals(0, s.slotOf(padA))
        assertNull(s.slotOf(touch))                                       // the touch pad has no slot: inert
        assertNull(s.holderOf(1))                                         // P2 freed
        assertEquals("P1", p.view(9_000, tablet).badge)
        assertEquals(1, p.joined)
        // the joining key is still not play until lifted (B54's rule)
        assertNull(key(p, padA, A, true, 9_050, tablet))
    }

    @Test
    fun aHoldLiftedBeforeTwoSecondsStaysP2() {
        val (s, p) = fresh()
        val t = TouchTakeover()
        p.joinAsP1WithoutHold(touch, 6_000, tablet)
        t.onKey(padA, A, true, 0, 7_000, joinedAtDown = false)
        press(p, padA, A, 7_000, 600, tablet)
        t.onKey(padA, A, false, 0, 8_900, joinedAtDown = true)
        key(p, padA, A, false, 8_900, tablet)
        assertNull(t.due(9_500, p1IsTouchPad = true))
        assertEquals(1, s.slotOf(padA))
        assertEquals(TouchPadDevice.KEY, s.holderOf(0))
    }

    @Test
    fun aJoinedPlayerHoldingAButtonInPlayNeverTakesP1() {
        val (s, p) = fresh()
        val t = TouchTakeover()
        p.joinAsP1WithoutHold(touch, 6_000, tablet)
        press(p, padA, A, 7_000, 600, tablet); key(p, padA, A, false, 7_700, tablet)
        assertEquals(1, s.slotOf(padA))
        t.onKey(padA, X, true, 0, 10_000, joinedAtDown = true)             // X held 3 s in the game
        assertNull(t.due(13_000, p1IsTouchPad = true))
        assertEquals(TouchPadDevice.KEY, s.holderOf(0))
    }

    @Test
    fun aRealPadNeverTakesARealPadsP1() {
        val (s, p) = fresh()
        press(p, padA, A, 1_000, 600, tablet); key(p, padA, A, false, 1_700, tablet)
        val t = TouchTakeover()
        t.onKey(padB, A, true, 0, 2_000, joinedAtDown = false)
        press(p, padB, A, 2_000, 600, tablet)
        assertNull(t.due(4_100, p1IsTouchPad = s.holderOf(0) == TouchPadDevice.KEY))
        assertNull(p.takeOverP1(padB, TouchPadDevice.KEY, 4_100))         // P1 is not the touch pad's
        assertEquals(0, s.slotOf(padA)); assertEquals(1, s.slotOf(padB))
    }

    /** A 1-player title: the pad cannot join at 0.5 s (closed after P1); its 2-s hold still takes P1. */
    @Test
    fun onAOnePlayerTitleTheTwoSecondHoldTakesP1() {
        val (s, p) = fresh(hostPlayers = 1)
        val t = TouchTakeover()
        p.joinAsP1WithoutHold(touch, 6_000, tablet)
        t.onKey(padA, A, true, 0, 7_000, joinedAtDown = false)
        press(p, padA, A, 7_000, 600, tablet)
        assertNull(s.slotOf(padA))                                         // the join is closed after P1
        assertEquals(padA, t.due(9_000, p1IsTouchPad = true))
        assertEquals(0, p.takeOverP1(padA, TouchPadDevice.KEY, 9_000))
        assertEquals(0, s.slotOf(padA)); assertNull(s.slotOf(touch))
    }

    // D2 with Q3 (b), (i) and Q4 (b): the 5-s rule
    @Test
    fun theFiveSecondsCountFromTheGameplayRelease() {
        val r = TouchP1Rule()
        r.onStart(selfRestart = false)
        assertEquals(TouchP1Rule.Action.NONE, r.tick(10_000, p1HeldByRealPad = false))   // not released yet
        assertNull(r.secondsLeft(10_000))
        r.onGameplayReleased(12_000)
        assertEquals(5, r.secondsLeft(12_000)); assertEquals(5, r.secondsLeft(12_001)); assertEquals(1, r.secondsLeft(16_999))
        assertEquals(TouchP1Rule.Action.NONE, r.tick(16_999, false))
        assertEquals(TouchP1Rule.Action.JOIN_P1, r.tick(17_000, false))
        assertEquals(TouchP1Rule.Action.NONE, r.tick(17_050, false))                     // once
        assertNull(r.secondsLeft(17_050))
    }

    @Test
    fun aRealP1WithinTheWaitEndsTheRule() {
        val r = TouchP1Rule()
        r.onStart(false); r.onGameplayReleased(0)
        assertEquals(TouchP1Rule.Action.GIVE_UP, r.tick(3_000, p1HeldByRealPad = true))
        assertEquals(TouchP1Rule.Action.NONE, r.tick(6_000, false))
    }

    @Test
    fun everyUnpauseRunsTheRuleAgainButASelfRestartDoesNot() {
        val r = TouchP1Rule()
        r.onStart(false); r.onGameplayReleased(0)
        assertEquals(TouchP1Rule.Action.JOIN_P1, r.tick(5_000, false))
        r.onStart(false); r.onGameplayReleased(60_000)                    // an unpause
        assertEquals(TouchP1Rule.Action.JOIN_P1, r.tick(65_000, false))
        r.onStart(true); r.onGameplayReleased(90_000)                     // a self-restart keeps the map
        assertEquals(TouchP1Rule.Action.NONE, r.tick(96_000, false))
    }

    @Test
    fun aLinkRecoveryReleaseDoesNotRestartTheCount() {
        val r = TouchP1Rule()
        r.onStart(false); r.onGameplayReleased(0)
        r.onGameplayReleased(3_000)                                        // a second release (link recovery)
        assertEquals(TouchP1Rule.Action.JOIN_P1, r.tick(5_000, false))
    }

    @Test
    fun cancelStopsTheCount() {
        val r = TouchP1Rule()
        r.onStart(false); r.onGameplayReleased(0); r.cancel()
        assertEquals(TouchP1Rule.Action.NONE, r.tick(9_000, false))
        assertNull(r.secondsLeft(1_000))
    }
}
