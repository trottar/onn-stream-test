package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B38: the onn's "virtual-remote" takes no slot (HOME-1 C4: KEYBOARD | DPAD | GAMEPAD, controller number 1, slot 0).
 * Inside debug.privyhub.pad_slots=stable; fake devices with the B38 fields set explicitly.
 */
class VirtualRemoteNoSlotTest {

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
        const val MOUSE = 0x00002002
    }

    // as C4 read it: GAMEPAD declared, controller number 1, every key answered present, no stick or hat axis
    private val virtualRemote = Dev("virtual-remote-desc", 1, 0x18d1, 0x0001, KEYBOARD or DPAD or GAMEPAD,
        hasGamepadButton = true, isVirtual = false, hasFaceButton = true, hasStickOrHat = false)
    private val remoteKeyboard = Dev("remote-keyboard-desc", 0, 0x0957, 0x0002, KEYBOARD or DPAD,
        hasGamepadButton = false, isVirtual = false, hasFaceButton = false, hasStickOrHat = false)
    private val padA = Dev("pad-a-desc", 2, 0x054c, 0x09cc, GAMEPAD or JOYSTICK or KEYBOARD,
        hasGamepadButton = true, isVirtual = false, hasFaceButton = true, hasStickOrHat = true)
    private val padB = Dev("pad-b-desc", 3, 0x054c, 0x09cc, GAMEPAD or JOYSTICK or KEYBOARD,
        hasGamepadButton = true, isVirtual = false, hasFaceButton = true, hasStickOrHat = true)
    private val touchpad = Dev("pad-a-touchpad", 0, 0x054c, 0x09cc, MOUSE,
        hasGamepadButton = false, isVirtual = false, hasFaceButton = false, hasStickOrHat = false)

    private val onn = listOf(virtualRemote, remoteKeyboard, padA, touchpad, padB)

    @Test
    fun theVirtualRemoteAsC4DescribedItTakesNoSlot() {
        assertFalse(PadSlots.eligible(virtualRemote))
        val s = PadSlots()
        s.beginStart(onn)
        assertNull(s.slotFor(virtualRemote) { onn })
        assertEquals(listOf(0, 1), s.map().map { it.slot })
        assertEquals(setOf(PadSlots.key(padA), PadSlots.key(padB)), s.map().map { it.pad }.toSet())
    }

    @Test
    fun twoPadsInEitherOrderAreSlotsZeroAndOneAndARestartKeepsThem() {
        val first = PadSlots().apply { beginStart(onn) }
        val bFirst = listOf(first.slotFor(padB) { onn }, first.slotFor(padA) { onn })
        val second = PadSlots().apply { beginStart(onn.reversed()) }
        val aFirst = listOf(second.slotFor(padA) { onn }, second.slotFor(padB) { onn })
        assertEquals(listOf(1, 0), bFirst)        // pad A (number 2) is slot 0, pad B (3) slot 1, whoever presses first
        assertEquals(listOf(0, 1), aFirst)
        first.beginStart(onn)                     // a restart in the same process
        assertEquals(0, first.slotFor(padA) { onn })
        assertEquals(1, first.slotFor(padB) { onn })
        assertEquals(2, first.map().size)
    }

    @Test
    fun aVirtualDeviceAPadWithoutFaceButtonsAndAKeyOnlyGamepadAreExcluded() {
        assertFalse(PadSlots.eligible(padA.copy(isVirtual = true)))
        assertFalse(PadSlots.eligible(padA.copy(hasFaceButton = false)))
        assertFalse(PadSlots.eligible(padA.copy(hasStickOrHat = false)))
        assertFalse(PadSlots.eligible(remoteKeyboard))
        assertFalse(PadSlots.eligible(touchpad))
        assertTrue(PadSlots.eligible(padA))
    }

    @Test
    fun aHatOnlyPadStillTakesASlot() {
        // a D-pad-only pad reports its hat as joystick axes
        val hatPad = padA.copy(descriptor = "hat-pad", sources = GAMEPAD or JOYSTICK, hasStickOrHat = true)
        assertTrue(PadSlots.eligible(hatPad))
    }

    @Test
    fun absentIsToday() {
        // absent / empty / other: no PadSlots object, so the sender's first-input order (B34's absent) applies
        assertFalse(PadSlotsFlag.parse(null))
        assertFalse(PadSlotsFlag.parse(""))
        assertFalse(PadSlotsFlag.parse("1"))
        assertTrue(PadSlotsFlag.parse("stable"))
    }
}
