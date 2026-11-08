package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/**
 * B54: hold-to-join over the stable slots (debug.privyhub.player_prompt, on by default). Fake devices as B38 / B41 /
 * B46's tests (the onn's virtual remote, real pads with controller numbers 2-5) and a fake clock (every time below is
 * a number of ms passed in). B46's chooser tests are replaced (disclosed): the chooser is gone.
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
        const val CENTER = PlayerPrompt.KEYCODE_DPAD_CENTER
        const val L1 = 102
        val TWO = PortsSet(2, multitap = false, multitapAvailable = true, source = "join")
        val FOUR = PortsSet(4, multitap = true, multitapAvailable = true, source = "relaunch")
        val NO_TAP = PortsSet(2, multitap = false, multitapAvailable = false, source = "metadata")
        const val GAME = "ps1-two-player-title"
    }

    private val virtualRemote = Dev("virtual-remote-desc", 1, 0x18d1, 0x0001, KEYBOARD or DPAD or GAMEPAD,
        hasGamepadButton = true, isVirtual = false, hasFaceButton = true, hasStickOrHat = false)
    private fun pad(n: Int) = Dev("pad-$n-desc", n + 1, 0x054c, 0x09cc, GAMEPAD or JOYSTICK or KEYBOARD,
        hasGamepadButton = true, isVirtual = false, hasFaceButton = true, hasStickOrHat = true)
    private val padA = pad(1)
    private val padB = pad(2)
    private val padC = pad(3)
    private val padD = pad(4)
    private val onn = listOf(virtualRemote, padA, padB, padC, padD)

    @Before
    fun clearProcess() {
        PlayerPromptProcess.lastJoined = null
    }

    private fun fresh(ports: PortsSet = TWO, hostPlayers: Int = 2,
                      store: PlayerChoiceStore = MemoryPlayerChoiceStore()): Pair<PadSlots, PlayerPrompt> {
        val s = PadSlots()
        val p = PlayerPrompt(s, store)
        p.beginStart(onn)
        p.onStartResponse(false, hostPlayers, ports, PlayerPrompt.gameKey(GAME), onn)
        return s to p
    }

    /** The activity's order: the join hook first; only a key it does not take goes to the sender. */
    private fun key(p: PlayerPrompt, d: PadDevice, code: Int, down: Boolean, now: Long, repeat: Int = 0): Int? =
        if (p.onJoinKey(code, down, repeat, d, now)) null
        else p.slotForKey(d, code, down, now, { onn }, repeat)

    /** A hold of [ms] with the 50-ms tick running, then the release of the key. */
    private fun hold(p: PlayerPrompt, d: PadDevice, code: Int, from: Long, ms: Long): Long {
        key(p, d, code, true, from)
        var t = from
        while (t < from + ms) { t += 50; p.tick(t, onn) }
        key(p, d, code, false, from + ms)
        return from + ms
    }

    @Test
    fun theOpeningLineAtAStart() {
        val (s, p) = fresh()
        assertEquals("Hold any button to join", p.view(0, onn).prompt)
        assertEquals(0, p.joined)
        assertTrue(s.map().isEmpty())
    }

    @Test
    fun aTapClaimsNothingAndAJoinedPadsTapReachesTheGame() {
        val (s, p) = fresh()
        assertNull(key(p, padA, A, true, 0)); assertNull(key(p, padA, A, false, 120))   // a tap
        p.tick(600, onn)
        assertEquals(0, p.joined); assertTrue(s.map().isEmpty())
        assertEquals("Hold any button to join", p.view(600, onn).prompt)
        hold(p, padA, A, 1_000, 600)
        assertEquals(0, s.slotOf(padA))
        assertEquals(0, key(p, padA, X, true, 2_000))     // a joined pad's tap: its slot, so the game gets it
        assertEquals(0, key(p, padA, X, false, 2_080))
    }

    @Test
    fun aHoldOf500MsJoinsAndNotBefore() {
        val (s, p) = fresh()
        key(p, padA, START, true, 1_000)
        p.tick(1_499, onn)
        assertNull(s.slotOf(padA))                       // 499 ms: not yet
        assertTrue(p.holdPending())
        p.tick(1_500, onn)
        assertEquals(0, s.slotOf(padA))                  // 500 ms: P1
        assertFalse(p.holdPending())
        assertEquals("P1", p.view(1_500, onn).badge)
        assertNull(p.view(3_600, onn).badge)             // the badge's 2 s
        assertEquals("P1 joined — hold to add Player 2", p.view(1_500, onn).prompt)
        assertEquals("0:p", p.claimsString())
        // the joining key is not play: its repeats and its up never reach the sender
        assertNull(key(p, padA, START, true, 1_600, repeat = 3))
        assertNull(key(p, padA, START, false, 1_700))
        assertEquals(0, key(p, padA, START, true, 2_000))   // a fresh press of it is play
    }

    @Test
    fun repeatsNeverStartAHoldAndTheRemoteNeverJoins() {
        val (s, p) = fresh()
        key(p, padA, A, true, 0, repeat = 2)
        p.tick(1_000, onn)
        assertNull(s.slotOf(padA))
        assertFalse(p.onJoinKey(CENTER, true, 0, virtualRemote, 0))
        assertNull(key(p, virtualRemote, CENTER, true, 0))
        p.tick(2_000, onn)
        assertTrue(s.map().isEmpty())
        assertFalse(p.onJoinKey(L1, true, 0, padA, 0) && s.slotOf(padA) != null)   // L1 is no join key
        p.tick(3_000, onn)
        assertNull(s.slotOf(padA))
        assertNull(p.slotForMotion(padA) { onn })        // a stick never joins
    }

    @Test
    fun aSecondPadIsP2AndTheLineClosesOnTwoPorts() {
        val (s, p) = fresh()
        val t = hold(p, padB, X, 0, 600)                 // the first to hold is P1, whichever pad
        assertEquals(0, s.slotOf(padB))
        hold(p, padA, A, t + 100, 600)
        assertEquals(1, s.slotOf(padA))
        assertEquals("P2", p.view(t + 800, onn).badge)
        assertNull(p.view(t + 800, onn).prompt)          // two ports taken: the line closes
        assertEquals(2, p.joined)
        assertEquals(2, PlayerPromptProcess.lastJoined)
    }

    @Test
    fun aThirdPadAsksForTheMultitapAtOnceThenJoinsAsP3() {
        val store = MemoryPlayerChoiceStore()
        val (s, p) = fresh(store = store)
        var t = hold(p, padA, A, 0, 600)
        t = hold(p, padB, A, t + 100, 600)
        assertNull(p.takeRelaunchRequest())
        key(p, padC, START, true, t + 100)
        p.tick(t + 300, onn)
        assertEquals("P1, P2 joined — hold to add Player 3", p.view(t + 300, onn).prompt)   // back while it holds
        p.tick(t + 600, onn)
        assertEquals(PlayerPrompt.Phase.RELAUNCHING, p.phase)
        assertEquals(4, p.takeRelaunchRequest())
        assertNull(p.takeRelaunchRequest())              // asked once
        assertEquals("Setting up 4 players…", p.view(t + 700, onn).prompt)
        assertNull(s.slotOf(padC))
        key(p, padD, A, true, t + 800); p.tick(t + 1_400, onn)
        assertNull(s.slotOf(padD))                       // other holds wait out the relaunch
        p.onRelaunchResult(true, FOUR, "loaded", 7_400, t + 8_000, onn)
        assertEquals(2, s.slotOf(padC))                  // P3
        assertEquals(0, s.slotOf(padA)); assertEquals(1, s.slotOf(padB))   // P1 / P2 kept
        assertEquals("P3", p.view(t + 8_000, onn).badge)
        assertEquals("P1, P2, P3 joined — hold to add Player 4", p.view(t + 8_000, onn).prompt)
        assertEquals(1, p.relaunches)
        assertEquals(PlayerPrompt.Relaunch(true, "loaded", 7_400), p.lastRelaunch)
        assertEquals(3, store.get(PlayerPrompt.gameKey(GAME)!!))   // the next launch's ports
        // a fourth pad: four ports now, no relaunch
        hold(p, padD, X, t + 9_000, 600)
        assertEquals(3, s.slotOf(padD))
        assertNull(p.takeRelaunchRequest())
        assertNull(p.view(t + 9_700, onn).prompt)        // four joined: closed
    }

    @Test
    fun aFailedRelaunchJoinsNobodyAndSaysSo() {
        val (s, p) = fresh()
        var t = hold(p, padA, A, 0, 600)
        t = hold(p, padB, A, t + 100, 600)
        hold(p, padC, A, t + 100, 600)
        assertEquals(4, p.takeRelaunchRequest())
        p.onRelaunchResult(false, null, null, null, t + 5_000, onn)
        assertNull(s.slotOf(padC))
        assertEquals("Couldn't set up 4 players", p.view(t + 5_000, onn).prompt)
        assertEquals(PlayerPrompt.Phase.JOINING, p.phase)
        assertEquals(PortsSet(2, false, true, "join"), p.ports)
    }

    @Test
    fun noMultitapOnTheSystemSaysSoAndJoinsNobody() {
        val (s, p) = fresh(ports = NO_TAP)
        var t = hold(p, padA, A, 0, 600)
        t = hold(p, padB, A, t + 100, 600)
        hold(p, padC, A, t + 100, 600)
        assertNull(p.takeRelaunchRequest())
        assertNull(s.slotOf(padC))
        assertEquals("No multitap on this system — 2 players", p.view(t + 800, onn).prompt)
    }

    @Test
    fun aOnePlayerTitleClosesAfterP1() {
        val (s, p) = fresh(hostPlayers = 1)
        assertEquals("Hold any button to join", p.view(0, onn).prompt)
        val t = hold(p, padA, A, 0, 600)
        assertEquals(0, s.slotOf(padA))
        assertNull(p.view(t, onn).prompt)
        key(p, padB, A, true, t + 100)
        assertNull(p.view(t + 200, onn).prompt)          // no line comes back for a second pad
        p.tick(t + 1_000, onn)
        assertNull(s.slotOf(padB))
        assertNull(p.takeRelaunchRequest())
    }

    @Test
    fun theReleaseThenAFreshHoldRejoinsButAHeldStartDoesNot() {
        val (s, p) = fresh()
        val t = hold(p, padA, A, 0, 600)
        key(p, padA, SELECT, true, t + 100); key(p, padA, START, true, t + 100)
        p.tick(t + 1_000, onn)
        assertEquals(0, s.slotOf(padA))                  // a short hold releases nothing
        p.tick(t + 2_100, onn)
        assertNull(s.slotOf(padA))
        assertEquals("P1 released", p.view(t + 2_100, onn).badge)
        p.tick(t + 5_000, onn)                           // Start still held: no re-join
        assertNull(s.slotOf(padA))
        key(p, padA, START, false, t + 5_100); key(p, padA, SELECT, false, t + 5_100)
        hold(p, padA, START, t + 6_000, 600)             // a fresh hold
        assertEquals(0, s.slotOf(padA))
    }

    @Test
    fun theLineGoesTenSecondsAfterTheLastJoinAndReturnsWhileAPadHolds() {
        val (_, p) = fresh(ports = FOUR)
        val t = hold(p, padA, A, 0, 600)
        assertEquals("P1 joined — hold to add Player 2", p.view(t + 9_000, onn).prompt)
        assertNull(p.view(t + 10_100, onn).prompt)
        key(p, padB, A, true, t + 11_000)
        assertEquals("P1 joined — hold to add Player 2", p.view(t + 11_100, onn).prompt)
        key(p, padB, A, false, t + 11_200)               // a tap: the line goes again
        assertNull(p.view(t + 11_300, onn).prompt)
    }

    @Test
    fun anUnpauseClearsTheMapAndASelfRestartKeepsIt() {
        val (s, p) = fresh()
        hold(p, padA, A, 0, 600)
        // a self-restart: the map stands, no line
        p.beginStart(onn)
        p.onStartResponse(true, 2, TWO, PlayerPrompt.gameKey(GAME), onn)
        assertEquals(0, s.slotOf(padA))
        assertEquals("0:s", p.claimsString())
        assertNull(p.view(5_000, onn).prompt)
        // an unpause: cleared, the line again
        p.beginStart(onn)
        p.onStartResponse(false, 2, TWO, PlayerPrompt.gameKey(GAME), onn)
        assertTrue(s.map().isEmpty())
        assertEquals("Hold any button to join", p.view(6_000, onn).prompt)
    }

    @Test
    fun portsSetParsesTheEcho() {
        assertEquals(PortsSet(4, true, true, "relaunch"), PortsSet.of(4, true, true, "relaunch"))
        assertEquals(4, PortsSet.of(9, true, true, "launch").players)  // clamped
        assertEquals(1, PortsSet.of(0, false, false, "launch").players)
    }

    @Test
    fun theFlagIsOnUnlessZeroOrOff() {
        assertTrue(PlayerPromptFlag.parse(null))
        assertTrue(PlayerPromptFlag.parse(""))
        assertTrue(PlayerPromptFlag.parse("junk"))
        assertTrue(PlayerPromptFlag.parse("1"))
        assertFalse(PlayerPromptFlag.parse("0"))
        assertFalse(PlayerPromptFlag.parse(" 0 "))
        assertFalse(PlayerPromptFlag.parse("off"))
        assertTrue(PlayerPromptFlag.fromSystem())                     // no Android on the JVM: absent = on
    }

    @Test
    fun offThePadSlotsAloneAreB34AndB38sAsBuilt() {
        // `0`: the activity builds no PlayerPrompt; the sender's path is PadSlots alone (the CONFIRMED build's `0`)
        val s = PadSlots()
        s.beginStart(onn)
        assertEquals(0, s.slotFor(padA) { onn }); assertEquals(1, s.slotFor(padB) { onn })
        assertNull(s.slotFor(virtualRemote) { onn })
    }
}
