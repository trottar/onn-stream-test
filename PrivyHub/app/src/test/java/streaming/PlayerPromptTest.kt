package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/**
 * B46: the player chooser over the stable slots (debug.privyhub.player_prompt, on by default). Fake devices as B38 /
 * B41's tests: the onn's virtual remote (C4), real pads with controller numbers 2-5. B41's cases moved to B46's
 * meaning (disclosed, as B42): the prompt no longer skips a start whose pads hold slots, nor a 1-player title.
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
        const val LEFT = PlayerPrompt.KEYCODE_DPAD_LEFT
        const val RIGHT = PlayerPrompt.KEYCODE_DPAD_RIGHT
        const val CENTER = PlayerPrompt.KEYCODE_DPAD_CENTER
        const val L1 = 102
        val TWO = PortsSet(2, multitap = false, multitapAvailable = true, source = "launch")
        val FOUR = PortsSet(4, multitap = true, multitapAvailable = true, source = "launch")
        const val GAME = "ps1-two-player-title"
    }

    private val virtualRemote = Dev("virtual-remote-desc", 1, 0x18d1, 0x0001, KEYBOARD or DPAD or GAMEPAD,
        hasGamepadButton = true, isVirtual = false, hasFaceButton = true, hasStickOrHat = false)
    private fun pad(n: Int) = Dev("pad-$n-desc", n + 1, 0x054c, 0x09cc, GAMEPAD or JOYSTICK or KEYBOARD,
        hasGamepadButton = true, isVirtual = false, hasFaceButton = true, hasStickOrHat = true)
    private val padA = pad(1)
    private val padB = pad(2)
    private val onn = listOf(virtualRemote, padA, padB)
    private val conn = { onn }

    @Before
    fun clearProcess() {
        PlayerPromptProcess.lastChoice = null
    }

    private fun open(p: PlayerPrompt, devs: List<PadDevice> = onn, ports: PortsSet = TWO, hostPlayers: Int = 2,
                     self: Boolean = false) {
        p.beginStart(devs)
        p.onStartResponse(self, hostPlayers, ports, PlayerPrompt.gameKey(GAME), devs)
    }

    private fun fresh(ports: PortsSet = TWO, devs: List<PadDevice> = onn, hostPlayers: Int = 2,
                      store: PlayerChoiceStore = MemoryPlayerChoiceStore()): Pair<PadSlots, PlayerPrompt> {
        val s = PadSlots()
        val p = PlayerPrompt(s, store)
        open(p, devs, ports, hostPlayers)
        return s to p
    }

    private fun press(p: PlayerPrompt, d: PadDevice, key: Int, now: Long, devs: List<PadDevice> = onn): Int? {
        val slot = p.slotForKey(d, key, true, now, { devs })
        p.slotForKey(d, key, false, now + 50, { devs })
        return slot
    }

    /** A pick from a pad: the chooser consumes the down; the up reaches the sender as on the onn. */
    private fun pick(p: PlayerPrompt, d: PadDevice, now: Long) {
        assertTrue(p.onChooserKey(A, true, 0, d, now))
        assertFalse(p.onChooserKey(A, false, 0, d, now + 40))
        p.slotForKey(d, A, false, now + 40, conn)
    }

    @Test
    fun atTheStartTheChooserThenTwoThenBIsPlayerOneAndAIsPlayerTwo() {
        val (s, p) = fresh()
        assertEquals(PlayerPrompt.Phase.CHOOSING, p.phase)
        assertEquals("Players:  1  /  [2]  /  multitap (3-4)", p.view(0, onn).prompt)
        assertTrue(s.map().isEmpty())
        assertNull(p.slotForKey(padA, A, true, 10, conn))           // no pad holds a slot while choosing
        pick(p, padB, 100)
        assertEquals(2, p.chosen); assertEquals(2, p.count)
        assertEquals("Player 1 — press any button", p.view(120, onn).prompt)
        assertTrue(s.map().isEmpty())                                 // the pick's own up claimed nothing
        assertEquals(0, press(p, padB, A, 150))                       // B's fresh press takes P1
        assertEquals("P1", p.view(250, onn).badge)
        assertEquals("Player 2 — press any button", p.view(250, onn).prompt)
        assertEquals(1, press(p, padA, START, 300))
        assertEquals("P2", p.view(400, onn).badge)
        assertEquals(PlayerPrompt.Phase.DONE, p.phase)
        assertNull(p.view(400, onn).prompt)                          // no further prompt
        assertNull(p.view(2_400, onn).badge)
        assertEquals("0:p,1:p", p.claimsString())
        assertEquals(0, p.slotForKey(padB, L1, true, 500, conn))     // claimed: every key goes to its slot
    }

    @Test
    fun thePickItselfNeverClaims() {
        val (s, p) = fresh()
        assertTrue(p.onChooserKey(A, true, 0, padB, 0))
        // a repeat of the held pick key, then a down without an up: no claim
        assertNull(p.slotForKey(padB, A, true, 30, conn, repeat = 1))
        assertNull(p.slotForKey(padB, A, true, 60, conn))
        assertTrue(s.map().isEmpty())
        p.slotForKey(padB, A, false, 90, conn)
        assertEquals(0, press(p, padB, A, 120))
    }

    @Test
    fun anUnpauseOpensTheChooserAgainWithTheLastChoice() {
        val store = MemoryPlayerChoiceStore()
        val (s, p) = fresh(store = store)
        assertTrue(p.onChooserKey(LEFT, true, 0, virtualRemote, 0))   // the remote moves to 1
        assertTrue(p.onChooserKey(CENTER, true, 0, virtualRemote, 10))
        assertEquals(1, p.chosen)
        assertEquals(0, press(p, padA, A, 100))
        // Back, then Resume: a new start of the running game (not a self-restart)
        open(p)
        assertEquals(PlayerPrompt.Phase.CHOOSING, p.phase)
        assertTrue(s.map().isEmpty())                                 // the map cleared for the prompt
        assertEquals("Players:  [1]  /  2  /  multitap (3-4)", p.view(1_000, onn).prompt)
        assertNull(p.chosen)
        // a fresh PlayerPrompt (a new activity) reads the same store
        val p2 = PlayerPrompt(s, store); open(p2)
        assertEquals("Players:  [1]  /  2  /  multitap (3-4)", p2.view(0, onn).prompt)
    }

    @Test
    fun multitapOnAFourPortSessionTakesFourClaims() {
        val four = listOf(virtualRemote, pad(1), pad(2), pad(3), pad(4))
        val (s, p) = fresh(ports = FOUR, devs = four)
        assertTrue(p.onChooserKey(RIGHT, true, 0, pad(1), 0))
        assertTrue(p.onChooserKey(RIGHT, true, 0, pad(1), 10))        // stops at the last option
        assertEquals("Players:  1  /  2  /  [multitap (3-4)]", p.view(20, four).prompt)
        assertTrue(p.onChooserKey(X, true, 0, pad(1), 30)); p.slotForKey(pad(1), X, false, 60, { four })
        assertEquals(4, p.chosen); assertEquals(4, p.count)
        assertEquals(0, press(p, pad(3), A, 100, four))
        assertEquals(1, press(p, pad(1), A, 200, four))
        assertEquals("Player 3 — press any button", p.view(250, four).prompt)
        assertEquals(2, press(p, pad(4), A, 300, four))
        assertEquals(3, press(p, pad(2), A, 400, four))
        assertEquals("0:p,1:p,2:p,3:p", p.claimsString())
        assertEquals(PlayerPrompt.Phase.DONE, p.phase)
        assertEquals(4, s.map().size)
    }

    @Test
    fun multitapOnATwoPortSessionStopsAtTwoAndSaysSo() {
        val three = onn + pad(3)
        val (s, p) = fresh(ports = TWO, devs = three)
        p.onChooserKey(RIGHT, true, 0, padA, 0)
        p.onChooserKey(A, true, 0, padA, 10); p.slotForKey(padA, A, false, 20, { three })
        assertEquals(4, p.chosen); assertEquals(2, p.count)
        assertEquals("Player 1 — press any button\nMultitap from the next start", p.view(30, three).prompt)
        press(p, padA, A, 100, three); press(p, padB, A, 200, three)
        assertNull(press(p, pad(3), A, 300, three))                   // beyond the ports: no slot
        assertEquals(2, s.map().size)
        // a system with no multitap
        val (_, q) = fresh(ports = PortsSet(2, false, false, "metadata"))
        q.onChooserKey(RIGHT, true, 0, padA, 0); q.onChooserKey(A, true, 0, padA, 10)
        assertEquals("Player 1 — press any button\nNo multitap on this system — 2 players", q.view(20, onn).prompt)
    }

    @Test
    fun oneTakesOneClaimAndTheOtherPadGetsNoSlot() {
        val (s, p) = fresh()
        p.onChooserKey(LEFT, true, 0, padA, 0)
        p.onChooserKey(A, true, 0, padA, 10); p.slotForKey(padA, A, false, 20, conn)
        assertEquals(1, p.chosen); assertEquals(1, p.count)
        assertEquals(0, press(p, padB, A, 100))
        assertEquals(PlayerPrompt.Phase.DONE, p.phase)
        assertNull(press(p, padA, A, 200))                            // the other pad: no slot, no input
        assertNull(p.view(300, onn).prompt)
        assertEquals("0:p", p.claimsString())
        assertEquals(1, s.map().size)
    }

    @Test
    fun theHeldStartReleaseReclaimsOnlyAfterAFreshPress() {
        val (s, p) = fresh()
        pick(p, padA, 0)
        press(p, padA, A, 100); press(p, padB, A, 200)
        // HOME-3 C6 try 1: Select first, Start last and still held when the release fires
        p.slotForKey(padA, SELECT, true, 1_000, conn)
        p.slotForKey(padA, START, true, 1_050, conn)
        p.tick(3_060)
        assertNull(s.slotOf(padA))
        assertEquals("P1 released", p.view(3_100, onn).badge)
        assertEquals("Player 1 — press any button", p.view(3_100, onn).prompt)
        // Android repeats the held Start: no claim; Select lifted, Start still held: no claim
        assertNull(p.slotForKey(padA, START, true, 3_100, conn, repeat = 20))
        p.slotForKey(padA, SELECT, false, 3_150, conn)
        assertNull(p.slotForKey(padA, START, true, 3_200, conn, repeat = 21))
        assertNull(s.slotOf(padA))
        // Start lifted, then a fresh press: claimed
        p.slotForKey(padA, START, false, 3_300, conn)
        assertEquals(0, press(p, padA, START, 3_400))
        assertEquals("0:p,1:p", p.claimsString())
    }

    @Test
    fun aShortHoldReleasesNothing() {
        val (s, p) = fresh()
        pick(p, padA, 0); press(p, padA, A, 100)
        p.slotForKey(padA, SELECT, true, 1_000, conn); p.slotForKey(padA, START, true, 1_000, conn)
        p.tick(2_400)
        assertEquals(0, s.slotOf(padA))
        p.slotForKey(padA, START, false, 2_500, conn)
        p.tick(4_000)
        assertEquals(0, s.slotOf(padA))
    }

    @Test
    fun aSelfRestartKeepsTheMapAndTheChoiceWithNoChooser() {
        val (s, p) = fresh()
        pick(p, padB, 0); press(p, padB, A, 100); press(p, padA, A, 200)
        val p2 = PlayerPrompt(s)                                      // the guard's new activity, same process
        open(p2, self = true)
        assertEquals(PlayerPrompt.Phase.DONE, p2.phase)
        assertEquals(2, p2.chosen)
        assertEquals("0:s,1:s", p2.claimsString())
        assertNull(p2.view(0, onn).prompt)
        assertEquals(0, s.slotOf(padB)); assertEquals(1, s.slotOf(padA))
    }

    @Test
    fun theDefaultIsTheLastChoiceElseTwoElseOneForASinglePlayerTitle() {
        val (_, p) = fresh(hostPlayers = 1)
        assertEquals("Players:  [1]  /  2  /  multitap (3-4)", p.view(0, onn).prompt)
        val store = MemoryPlayerChoiceStore()
        store.put(PlayerPrompt.gameKey(GAME)!!, 4)
        val (_, q) = fresh(hostPlayers = 1, store = store)
        assertEquals("Players:  1  /  2  /  [multitap (3-4)]", q.view(0, onn).prompt)
        assertEquals(12, PlayerPrompt.gameKey(GAME)!!.length)
        assertNull(PlayerPrompt.gameKey(" "))
    }

    @Test
    fun theRemoteAndTheHatMoveTheChooserAndTheRemoteNeverClaims() {
        val (s, p) = fresh()
        assertTrue(p.onChooserHat(padA, -1f))
        assertTrue(p.onChooserHat(padA, -1f))                         // held: one move
        assertEquals("Players:  [1]  /  2  /  multitap (3-4)", p.view(0, onn).prompt)
        assertTrue(p.onChooserHat(padA, 0f)); assertTrue(p.onChooserHat(padA, 1f))
        assertEquals("Players:  1  /  [2]  /  multitap (3-4)", p.view(0, onn).prompt)
        assertFalse(p.onChooserHat(virtualRemote, 1f))                // not a pad
        assertFalse(p.onChooserKey(L1, true, 0, padA, 0))             // not a chooser key: passed on
        p.onChooserKey(CENTER, true, 0, virtualRemote, 10)
        assertNull(press(p, virtualRemote, A, 100))
        assertTrue(s.map().isEmpty())
        assertFalse(p.onChooserKey(RIGHT, true, 0, virtualRemote, 200))  // closed: the remote's keys pass on
    }

    @Test
    fun aStickNeverClaims() {
        val (s, p) = fresh()
        assertNull(p.slotForMotion(padA, conn))
        pick(p, padA, 0)
        assertNull(p.slotForMotion(padA, conn))
        assertNull(p.slotForKey(padA, L1, true, 10, conn))
        assertTrue(s.map().isEmpty())
        press(p, padA, A, 100)
        assertEquals(0, p.slotForMotion(padA, conn))
    }

    @Test
    fun thePortsEchoParses() {
        assertEquals(PortsSet.UNKNOWN, PortsSet.parse(null))          // an old host: no key, 2 ports
        assertEquals(2, PortsSet.UNKNOWN.players)
        assertEquals(FOUR, PortsSet.of(4, true, true, "launch"))
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
        // `0`: the activity builds no PlayerPrompt; the sender's path is PadSlots alone (8ba4d996…'s absent)
        val s = PadSlots()
        s.beginStart(onn)
        assertEquals(0, s.slotFor(padA) { onn }); assertEquals(1, s.slotFor(padB) { onn })
        assertNull(s.slotFor(virtualRemote) { onn })
    }
}
