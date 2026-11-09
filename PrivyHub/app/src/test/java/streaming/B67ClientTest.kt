package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/**
 * B67: the N64 layout card's rule and text; "This game supports 2 players" (B63's `capable`); the onn's stored
 * joined count capped at an incapable title's ports; no joined count between a start and its response (B64's
 * order); the start gate's re-arm (B65). Fake pads as PlayerPromptTest's; a fake clock (ms passed in).
 */
class B67ClientTest {

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

    private fun pad(n: Int) = Dev("pad-$n-desc", n + 1, 0x054c, 0x09cc, 0x00000401 or 0x01000010 or 0x00000101,
        hasGamepadButton = true, isVirtual = false, hasFaceButton = true, hasStickOrHat = true)
    private val padA = pad(1)
    private val padB = pad(2)
    private val padC = pad(3)
    private val onn = listOf(padA, padB, padC)
    private val a = PlayerPrompt.KEYCODE_BUTTON_A
    private val game = PlayerPrompt.gameKey("ps1-two-player-title")

    private val incapable = PortsSet.of(2, false, false, "join", capable = false)
    private val oldHost = PortsSet.of(2, false, false, "metadata")
    private val capableTwo = PortsSet.of(2, false, true, "join", capable = true)

    @Before
    fun clear() {
        PlayerPromptProcess.lastJoined = null
    }

    private fun start(p: PlayerPrompt, ports: PortsSet) {
        p.beginStart(onn)
        p.onStartResponse(false, 2, ports, game, onn)
    }

    private fun hold(p: PlayerPrompt, d: PadDevice, from: Long): Long {
        p.onJoinKey(a, true, 0, d, from)
        var t = from
        while (t < from + PlayerPrompt.HOLD_MS + 100) { t += 50; p.tick(t, onn) }
        p.onJoinKey(a, false, 0, d, t)
        return t + 50
    }

    // --- 1. the N64 layout card -----------------------------------------------------------------------------------

    @Test
    fun theCardOnlyOnceForN64WithThePromptOn() {
        assertTrue(N64LayoutCard.shouldShow("n64", promptOn = true, alreadyShown = false))
        assertTrue(N64LayoutCard.shouldShow(" N64 ", promptOn = true, alreadyShown = false))
        assertFalse(N64LayoutCard.shouldShow("n64", promptOn = true, alreadyShown = true))
        assertFalse(N64LayoutCard.shouldShow("n64", promptOn = false, alreadyShown = false))
        assertFalse(N64LayoutCard.shouldShow("ps1", promptOn = true, alreadyShown = false))
        assertFalse(N64LayoutCard.shouldShow(null, promptOn = true, alreadyShown = false))
    }

    @Test
    fun theCardsGlyphsOnlyWhenAllDraw() {
        assertEquals("A = ✕, B = □, C-buttons = right stick (also △ = C-up, ○ = C-right), Z = L2",
            N64LayoutCard.text { true })
        assertEquals(N64LayoutCard.TEXT_LETTERS, N64LayoutCard.text { it != "△" })
        assertEquals("A = Cross, B = Square, C-buttons = right stick (also Triangle = C-up, Circle = C-right), Z = L2",
            N64LayoutCard.text { false })
    }

    // --- 2. the note ------------------------------------------------------------------------------------------------

    @Test
    fun anIncapableTitleSaysThisGameSupportsTwo() {
        val p = PlayerPrompt(PadSlots(), MemoryPlayerChoiceStore())
        start(p, incapable)
        var t = hold(p, padA, 1_000)
        t = hold(p, padB, t)
        t = hold(p, padC, t)
        assertEquals(2, p.joined)
        assertNull(p.takeRelaunchRequest())
        assertTrue(p.view(t, onn).prompt!!.contains("This game supports 2 players"))
    }

    @Test
    fun anOldHostKeepsTodaysWords() {
        val p = PlayerPrompt(PadSlots(), MemoryPlayerChoiceStore())
        start(p, oldHost)
        var t = hold(p, padA, 1_000)
        t = hold(p, padB, t)
        t = hold(p, padC, t)
        assertTrue(p.view(t, onn).prompt!!.contains("No multitap on this system — 2 players"))
    }

    @Test
    fun aCapableTitleStillAsksTheRelaunch() {
        val p = PlayerPrompt(PadSlots(), MemoryPlayerChoiceStore())
        start(p, capableTwo)
        var t = hold(p, padA, 1_000)
        t = hold(p, padB, t)
        hold(p, padC, t)
        assertEquals(4, p.takeRelaunchRequest())
    }

    // --- 3. the stored count ----------------------------------------------------------------------------------------

    @Test
    fun aStoredThreeIsCappedAtTheFirstStart() {
        val store = MemoryPlayerChoiceStore()
        store.put(game!!, 3)
        start(PlayerPrompt(PadSlots(), store), incapable)
        assertEquals(2, store.get(game))
    }

    @Test
    fun joinsNeverStoreAboveTheIncapablePorts() {
        val store = MemoryPlayerChoiceStore()
        val p = PlayerPrompt(PadSlots(), store)
        start(p, incapable)
        var t = hold(p, padA, 1_000)
        t = hold(p, padB, t)
        hold(p, padC, t)
        assertEquals(2, store.get(game!!))
    }

    @Test
    fun aCapableTitleKeepsItsThree() {
        val store = MemoryPlayerChoiceStore()
        store.put(game!!, 3)
        start(PlayerPrompt(PadSlots(), store), PortsSet.of(4, true, true, "join", capable = true))
        assertEquals(3, store.get(game))
        start(PlayerPrompt(PadSlots(), store), oldHost)
        assertEquals(3, store.get(game))
    }

    // --- 4. the order at a new start --------------------------------------------------------------------------------

    @Test
    fun noJoinedCountBetweenAStartAndItsResponse() {
        val p = PlayerPrompt(PadSlots(), MemoryPlayerChoiceStore())
        start(p, incapable)
        var t = hold(p, padA, 1_000)
        hold(p, padB, t)
        assertEquals(2, p.joinedForHeartbeat())
        p.beginStart(onn)                                        // the next game: the map still the last game's
        assertEquals(2, p.joined)
        assertNull(p.joinedForHeartbeat())
        p.onStartResponse(false, 2, incapable, game, onn)
        assertEquals(0, p.joinedForHeartbeat())
        t = hold(p, padA, 10_000)
        assertEquals(1, p.joinedForHeartbeat())
    }

    // --- 5. the start gate's re-arm ---------------------------------------------------------------------------------

    @Test
    fun theGateReArmsWhileFramesFlowAtMostThree() {
        val g = StartGateRearm(enabled = true)
        g.arm(0)
        assertTrue(g.onTimeout(900))
        assertTrue(g.onTimeout(1800))
        assertTrue(g.onTimeout(2700))
        assertFalse(g.onTimeout(3600))                           // 60 s in all, then today's failure
        assertEquals(3, g.rearms)
        g.arm(0)
        assertEquals(0, g.rearms)
    }

    @Test
    fun noNewFramesOrOffFailsAsToday() {
        val g = StartGateRearm(enabled = true)
        g.arm(0)
        assertFalse(g.onTimeout(0))
        val h = StartGateRearm(enabled = true)
        h.arm(0)
        assertTrue(h.onTimeout(500))
        assertFalse(h.onTimeout(500))                            // frames stopped since the last window
        val off = StartGateRearm(enabled = false)
        off.arm(0)
        assertFalse(off.onTimeout(900))
        assertTrue(StartGateRearm.parse(null))
        assertFalse(StartGateRearm.parse("0"))
        assertFalse(StartGateRearm.parse("off"))
    }

    @Test
    fun portsSetCarriesCapable() {
        assertNull(PortsSet.of(2, false, true, "x").capable)
        assertEquals(false, PortsSet.of(2, false, false, "x", capable = false).capable)
    }
}
