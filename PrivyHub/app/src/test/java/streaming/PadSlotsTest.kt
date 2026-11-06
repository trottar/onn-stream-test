package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B34: stable player slots, gamepads only (debug.privyhub.pad_slots=stable). Fake devices; one PadSlots object plays
 * the process-wide holder (PadSlotsProcess.slots) across starts and self-restarts.
 */
class PadSlotsTest {

    private data class Fake(
        override val descriptor: String,
        override val controllerNumber: Int,
        override val vendorId: Int = 0x054c,
        override val productId: Int = 0x0268,
        override val sources: Int = GAMEPAD or JOYSTICK,
        override val hasGamepadButton: Boolean = true,
        override val isVirtual: Boolean = false,
    ) : PadDevice

    companion object {
        const val GAMEPAD = 0x00000401
        const val JOYSTICK = 0x01000010
        const val KEYBOARD = 0x00000101
        const val DPAD = 0x00000201
        const val MOUSE = 0x00002002
    }

    private val padA = Fake("descriptor-of-pad-a-0123456789", controllerNumber = 1)
    private val padB = Fake("descriptor-of-pad-b-9876543210", controllerNumber = 2)
    private val padC = Fake("descriptor-of-pad-c", controllerNumber = 3, vendorId = 0x045e)
    // the onn's remote: keyboard + dpad, no gamepad source, no gamepad button
    private val remote = Fake("remote", 0, vendorId = 0x0957, sources = KEYBOARD or DPAD, hasGamepadButton = false)
    // an air mouse / a pad's motion device: joystick axes, no gamepad button
    private val airMouse = Fake("air-mouse", 0, vendorId = 0x1d5a, sources = JOYSTICK or MOUSE, hasGamepadButton = false)

    private fun slotsAfter(connected: List<PadDevice>, pressOrder: List<PadDevice>): List<Int?> {
        val s = PadSlots()
        s.beginStart(connected)
        return pressOrder.map { s.slotFor(it) { connected } }
    }

    @Test
    fun twoPadsGetTheSameSlotsWhicheverIsListedOrPressedFirst() {
        val want = listOf(0, 1)   // A (controller 1) -> P1, B (controller 2) -> P2
        for (listed in listOf(listOf(padA, padB), listOf(padB, padA))) {
            assertEquals(want, slotsAfter(listed, listOf(padA, padB)))
            assertEquals(want.reversed(), slotsAfter(listed, listOf(padB, padA)))
        }
    }

    @Test
    fun aRestartKeepsTheSlots() {
        val s = PadSlots()
        val both = listOf<PadDevice>(padA, padB)
        s.beginStart(both)
        assertEquals(1, s.slotFor(padB) { both })
        val before = s.mapString()
        // the self-restart: the same process object, a new start, B presses first this time
        s.beginStart(listOf(padB, padA))
        assertEquals(1, s.slotFor(padB) { both })
        assertEquals(0, s.slotFor(padA) { both })
        assertEquals(before, s.mapString())
    }

    @Test
    fun aStickAxisRemoteAndAnAirMouseAreExcluded() {
        val all = listOf(remote, airMouse, padB)
        val s = PadSlots()
        s.beginStart(all)
        assertNull(s.slotFor(remote) { all })
        assertNull(s.slotFor(airMouse) { all })
        assertEquals(0, s.slotFor(padB) { all })   // the real pad is P1, not pushed to P2 / P3
        assertEquals(1, s.map().size)
        assertFalse(PadSlots.eligible(remote))
        assertFalse(PadSlots.eligible(airMouse))
        assertFalse(PadSlots.eligible(padA.copy(isVirtual = true)))
        assertTrue(PadSlots.eligible(padA))
    }

    @Test
    fun aLaterPadTakesTheLowestFreeSlotAndALeavingPadKeepsItsSlot() {
        val s = PadSlots()
        s.beginStart(listOf(padA, padB))
        // A leaves; C joins: C takes slot 2 (the lowest free), A keeps 0
        val now = listOf<PadDevice>(padB, padC)
        assertEquals(2, s.slotFor(padC) { now })
        s.beginStart(now)
        assertEquals(listOf(0, 1, 2), s.map().map { it.slot })
        // A comes back: still P1
        assertEquals(0, s.slotFor(padA) { listOf(padA, padB, padC) })
    }

    @Test
    fun aFifthPadGetsAGonePadsSlotOrNone() {
        val pads = (1..5).map { Fake("pad-$it", it) }
        val s = PadSlots()
        s.beginStart(pads.take(4))
        assertNull(s.slotFor(pads[4]) { pads })                         // all four connected: none, as today
        val withoutSecond = pads.filter { it != pads[1] }
        assertEquals(1, s.slotFor(pads[4]) { withoutSecond })            // the gone pad's slot
        assertNull(s.map().firstOrNull { it.pad == PadSlots.key(pads[1]) })
    }

    @Test
    fun theMapCarriesNoDescriptorOrName() {
        val s = PadSlots()
        s.beginStart(listOf(padA, padC))
        val m = s.mapString()
        assertTrue(m, Regex("^[0-3]:[0-9a-f]{6}:[a-z0-9]{2,12}(,[0-3]:[0-9a-f]{6}:[a-z0-9]{2,12}){0,3}$").matches(m))
        assertFalse(m.contains("descriptor"))
        assertEquals(listOf("sony", "microsoft"), s.map().map { it.cls })
        assertEquals(6, PadSlots.key(padA).length)
        assertEquals("", PadSlots().mapString())
    }

    @Test
    fun theFlagIsStableOnly() {
        assertTrue(PadSlotsFlag.parse("stable"))
        assertTrue(PadSlotsFlag.parse(" stable "))
        // B42 (disclosed): absent / empty / junk moved to stable; `0` (and `off`) off as before
        for (v in listOf(null, "", "1", "Stable", "junk")) assertTrue(v.toString(), PadSlotsFlag.parse(v))
        assertFalse(PadSlotsFlag.parse("0"))
        // off the device the property cannot be read: absent, so stable (B42)
        assertTrue(PadSlotsFlag.fromSystem())
    }
}
