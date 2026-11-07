package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B41: the player prompt over the stable slots (debug.privyhub.player_prompt=1). Fake devices as B38's test: the onn's
 * virtual remote (C4), two real pads with controller numbers 2 and 3.
 */
class PlayerPromptTest {

    private data class Dev(
        override val descriptor: String,
        override val controllerNumber: Int,
        override val vendorId: Int,
        override val productId: Int,
        override val sources: Int,
        override val hasGamepadButton: Boolean,
        override val isVirtual: Boolean,
        override val hasFaceButton: Boolean,
        override val hasStickOrHat: Boolean,
    ) : PadDevice

    companion object {
        const val GAMEPAD = 0x00000401
        const val JOYSTICK = 0x01000010
        const val KEYBOARD = 0x00000101
        const val DPAD = 0x00000201
        const val A = PlayerPrompt.KEYCODE_BUTTON_A
        const val X = PlayerPrompt.KEYCODE_BUTTON_X
        const val START = PlayerPrompt.KEYCODE_BUTTON_START
        const val SELECT = PlayerPrompt.KEYCODE_BUTTON_SELECT
        const val L1 = 102
    }

    private val virtualRemote = Dev("virtual-remote-desc", 1, 0x18d1, 0x0001, KEYBOARD or DPAD or GAMEPAD,
        hasGamepadButton = true, isVirtual = false, hasFaceButton = true, hasStickOrHat = false)
    private val padA = Dev("pad-a-desc", 2, 0x054c, 0x09cc, GAMEPAD or JOYSTICK or KEYBOARD,
        hasGamepadButton = true, isVirtual = false, hasFaceButton = true, hasStickOrHat = true)
    private val padB = Dev("pad-b-desc", 3, 0x054c, 0x09cc, GAMEPAD or JOYSTICK or KEYBOARD,
        hasGamepadButton = true, isVirtual = false, hasFaceButton = true, hasStickOrHat = true)
    private val onn = listOf(virtualRemote, padA, padB)
    private val conn = { onn }

    private fun fresh(players: Int = 2): Pair<PadSlots, PlayerPrompt> {
        val s = PadSlots()
        val p = PlayerPrompt(s)
        p.beginStart(onn)
        p.setPlayers(players, onn)
        return s to p
    }

    private fun press(p: PlayerPrompt, d: PadDevice, key: Int, now: Long): Int? {
        val slot = p.slotForKey(d, key, true, now, conn)
        p.slotForKey(d, key, false, now + 50, conn)
        return slot
    }

    @Test
    fun padBPressesFirstAndIsPlayerOneThenPadAIsPlayerTwo() {
        val (s, p) = fresh()
        assertEquals("Player 1 — press any button", p.view(0, onn).prompt)
        assertTrue(s.map().isEmpty())                       // no pre-assignment by controller number
        assertEquals(0, press(p, padB, A, 100))
        assertEquals("P1", p.view(200, onn).badge)
        assertEquals("Player 2 — press any button", p.view(200, onn).prompt)
        assertEquals(1, press(p, padA, START, 300))
        assertEquals("P2", p.view(400, onn).badge)
        assertNull(p.view(400, onn).prompt)                 // up to the title's count, then gone
        assertNull(p.view(2_400, onn).badge)                // the badge for 2 s
        assertEquals(0, s.slotOf(padB)); assertEquals(1, s.slotOf(padA))
        assertEquals("0:p,1:p", p.claimsString())
        assertEquals(0, p.slotForKey(padB, L1, true, 500, conn))  // claimed: every key goes to its slot
    }

    @Test
    fun aOnePlayerTitleShowsNoPromptAndKeepsB34sAssignment() {
        val (s, p) = fresh(players = 1)
        assertFalse(p.active)
        assertNull(p.view(0, onn).prompt)
        assertEquals(0, s.slotOf(padA)); assertEquals(1, s.slotOf(padB))   // B34: controller-number order
        assertEquals(1, press(p, padB, A, 100))
        assertNull(p.view(200, onn).badge)
        assertEquals("0:s,1:s", p.claimsString())
    }

    @Test
    fun selectStartHeldTwoSecondsReleasesAndAnotherPadReclaims() {
        val (s, p) = fresh()
        press(p, padA, A, 0); press(p, padB, A, 100)
        assertEquals(0, s.slotOf(padA))
        p.slotForKey(padA, SELECT, true, 1_000, conn)
        p.slotForKey(padA, START, true, 1_050, conn)
        p.tick(2_000); assertEquals(0, s.slotOf(padA))       // under 2 s: nothing
        p.tick(3_060)
        assertNull(s.slotOf(padA))
        assertEquals("P1 released", p.view(3_100, onn).badge)
        assertEquals("Player 1 — press any button", p.view(3_100, onn).prompt)
        p.slotForKey(padA, SELECT, false, 3_200, conn)
        p.slotForKey(padA, START, false, 3_210, conn)
        // swap: B releases too, then A presses first and is P1
        p.slotForKey(padB, SELECT, true, 4_000, conn); p.slotForKey(padB, START, true, 4_000, conn)
        p.tick(6_100)
        assertNull(s.slotOf(padB))
        p.slotForKey(padB, SELECT, false, 6_200, conn); p.slotForKey(padB, START, false, 6_200, conn)
        assertEquals(0, press(p, padA, X, 7_000))
        assertEquals(1, press(p, padB, A, 7_100))
        assertEquals("0:p,1:p", p.claimsString())
    }

    @Test
    fun aShortHoldReleasesNothing() {
        val (s, p) = fresh()
        press(p, padA, A, 0)
        p.slotForKey(padA, SELECT, true, 1_000, conn); p.slotForKey(padA, START, true, 1_000, conn)
        p.tick(2_400)                                         // 1.4 s held: not yet
        assertEquals(0, s.slotOf(padA))
        p.slotForKey(padA, START, false, 2_500, conn)
        p.tick(4_000)
        assertEquals(0, s.slotOf(padA))
    }

    @Test
    fun aPadAlreadyInTheMapKeepsItsSlotAndShowsItsBadgeOnItsFirstPress() {
        val s = PadSlots()
        val p = PlayerPrompt(s)
        p.beginStart(onn); p.setPlayers(2, onn)
        press(p, padB, A, 0); press(p, padA, A, 10)
        // a second start in the same process (a relaunch or a self-restart)
        p.beginStart(onn); p.setPlayers(2, onn)
        assertEquals("0:s,1:s", p.claimsString())
        assertNull(p.view(100, onn).prompt)                  // both pads hold slots: nothing to ask
        assertNull(p.view(100, onn).badge)
        assertEquals(1, p.slotForKey(padA, L1, true, 200, conn))
        assertEquals("P2", p.view(300, onn).badge)          // its badge on its first press
    }

    @Test
    fun aStickNeverClaimsAndANonClaimKeyIsDropped() {
        val (s, p) = fresh()
        assertNull(p.slotForMotion(padA, conn))
        assertNull(p.slotForKey(padA, L1, true, 0, conn))
        assertTrue(s.map().isEmpty())
        press(p, padA, A, 100)
        assertEquals(0, p.slotForMotion(padA, conn))
    }

    @Test
    fun theVirtualRemoteNeverClaims() {
        val (s, p) = fresh()
        assertNull(press(p, virtualRemote, A, 0))
        assertNull(press(p, virtualRemote, START, 10))
        assertTrue(s.map().isEmpty())
        assertNull(p.view(100, listOf(virtualRemote)).prompt)  // no eligible pad: no prompt
    }

    @Test
    fun aThirdPadOnATwoPlayerTitleStillGetsAPlayerAsB34Would() {
        val padC = padA.copy(descriptor = "pad-c-desc", controllerNumber = 4)
        val all = onn + padC
        val s = PadSlots(); val p = PlayerPrompt(s)
        p.beginStart(all); p.setPlayers(2, all)
        assertEquals(0, p.slotForKey(padA, A, true, 0, { all }))
        assertEquals(1, p.slotForKey(padB, A, true, 10, { all }))
        assertNull(p.view(20, all).prompt)                   // the count reached: no prompt for the third
        assertEquals(2, p.slotForKey(padC, A, true, 30, { all }))
        assertEquals("P3", p.view(40, all).badge)
    }

    @Test
    fun theFlagIsOptIn() {
        assertFalse(PlayerPromptFlag.parse(null))
        assertFalse(PlayerPromptFlag.parse(""))
        assertFalse(PlayerPromptFlag.parse("0"))
        assertFalse(PlayerPromptFlag.parse("true"))
        assertFalse(PlayerPromptFlag.parse("yes"))
        assertTrue(PlayerPromptFlag.parse("1"))
        assertTrue(PlayerPromptFlag.parse(" 1 "))
        assertFalse(PlayerPromptFlag.fromSystem())           // no Android on the JVM: absent
    }

    @Test
    fun absentThePadSlotsAloneAreB34AndB38sAsBuilt() {
        // with no prompt the sender's path is PadSlots alone: the start pre-assigns by controller number
        val s = PadSlots()
        s.beginStart(onn)
        assertEquals(0, s.slotFor(padA) { onn }); assertEquals(1, s.slotFor(padB) { onn })
        assertNull(s.slotFor(virtualRemote) { onn })
    }
}
