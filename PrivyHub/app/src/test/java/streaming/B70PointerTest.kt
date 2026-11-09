package com.safeiot.privyhub.streaming

import android.view.InputDevice
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B70: the pads' touchpad and any mouse consumed in a game, the pointer hidden and captured; the remote's D-pad / OK
 * and the pads' buttons and sticks passed. Fake events (a source and a kind) and a fake host.
 */
class B70PointerTest {

    private class FakeHost : PointerGuard.Host {
        var hidden = 0
        var captures = 0
        var releases = 0
        override fun hideIcon() { hidden += 1 }
        override fun requestCapture() { captures += 1 }
        override fun releaseCapture() { releases += 1 }
    }

    private enum class Kind { MOTION, TOUCH, KEY }
    private data class FakeEvent(val source: Int, val kind: Kind)

    private fun consumed(g: PointerGuard, e: FakeEvent): Boolean = when (e.kind) {
        Kind.MOTION -> g.consumeMotion(e.source)
        Kind.TOUCH -> g.consumeTouch(e.source)
        Kind.KEY -> g.consumeKey(e.source)
    }

    // the sources as Android stamps them on these events
    private val touchpadMotion = FakeEvent(InputDevice.SOURCE_TOUCHPAD, Kind.MOTION)
    private val touchpadAsPointer = FakeEvent(InputDevice.SOURCE_MOUSE, Kind.MOTION)          // the pointer's presentation
    private val touchpadClick = FakeEvent(InputDevice.SOURCE_MOUSE, Kind.TOUCH)
    private val mouseBackKey = FakeEvent(InputDevice.SOURCE_MOUSE, Kind.KEY)                  // a secondary click's Back
    private val capturedMouse = FakeEvent(InputDevice.SOURCE_MOUSE_RELATIVE, Kind.MOTION)
    private val touchscreen = FakeEvent(InputDevice.SOURCE_TOUCHSCREEN, Kind.TOUCH)
    private val remoteDpad = FakeEvent(InputDevice.SOURCE_DPAD or InputDevice.SOURCE_KEYBOARD, Kind.KEY)
    private val padButton = FakeEvent(InputDevice.SOURCE_GAMEPAD or InputDevice.SOURCE_KEYBOARD, Kind.KEY)
    private val padButtonDpad =
        FakeEvent(InputDevice.SOURCE_GAMEPAD or InputDevice.SOURCE_KEYBOARD or InputDevice.SOURCE_DPAD, Kind.KEY)
    private val padStick = FakeEvent(InputDevice.SOURCE_JOYSTICK, Kind.MOTION)
    private val padStickAndGamepad = FakeEvent(InputDevice.SOURCE_JOYSTICK or InputDevice.SOURCE_GAMEPAD, Kind.MOTION)

    @Test
    fun touchpadMotionConsumedNoPointer() {
        val g = PointerGuard(true)
        val host = FakeHost()
        g.onAttach(host)
        g.onFocus(host, true)
        assertTrue(consumed(g, touchpadMotion))
        assertEquals(1, host.hidden)          // the null icon
        assertEquals(1, host.captures)        // the capture: no arrow, no touch spots
        assertEquals(1, g.consumed)
    }

    @Test
    fun everyPointerEventConsumed() {
        val g = PointerGuard(true)
        for (e in listOf(touchpadMotion, touchpadAsPointer, touchpadClick, mouseBackKey, capturedMouse, touchscreen)) {
            assertTrue(e.toString(), consumed(g, e))
        }
        assertTrue(g.consumeTrackball())
        assertEquals(7, g.consumed)
    }

    @Test
    fun dpadPassed() {
        val g = PointerGuard(true)
        assertFalse(consumed(g, remoteDpad))
        assertEquals(0, g.consumed)
    }

    @Test
    fun padButtonPassed() {
        val g = PointerGuard(true)
        assertFalse(consumed(g, padButton))
        assertFalse(consumed(g, padButtonDpad))
        assertEquals(0, g.consumed)
    }

    @Test
    fun padSticksPassed() {
        val g = PointerGuard(true)
        assertFalse(consumed(g, padStick))
        assertFalse(consumed(g, padStickAndGamepad))
    }

    @Test
    fun offIsToday() {
        val g = PointerGuard(false)
        val host = FakeHost()
        g.onAttach(host)
        g.onFocus(host, true)
        g.onFocus(host, false)
        for (e in listOf(touchpadMotion, touchpadClick, mouseBackKey, remoteDpad, padButton, padStick)) {
            assertFalse(e.toString(), consumed(g, e))
        }
        assertFalse(g.consumeTrackball())
        assertEquals(0, host.hidden)
        assertEquals(0, host.captures)
        assertEquals(0, host.releases)
        assertEquals(0, g.consumed)
    }

    @Test
    fun captureOnlyWithFocus() {
        val g = PointerGuard(true)
        val host = FakeHost()
        g.onFocus(host, false)
        assertEquals(0, host.captures)
        assertEquals(1, host.releases)
        g.onFocus(host, true)
        assertEquals(1, host.captures)
        assertEquals(1, g.captureRequests)
    }

    @Test
    fun constantsAreTheSdks() {
        assertEquals(InputDevice.SOURCE_CLASS_POINTER, PointerGuard.SOURCE_CLASS_POINTER)
        assertEquals(InputDevice.SOURCE_MOUSE, PointerGuard.SOURCE_MOUSE)
        assertEquals(InputDevice.SOURCE_TOUCHPAD, PointerGuard.SOURCE_TOUCHPAD)
        assertEquals(InputDevice.SOURCE_MOUSE_RELATIVE, PointerGuard.SOURCE_MOUSE_RELATIVE)
        assertEquals(InputDevice.SOURCE_TOUCH_NAVIGATION, PointerGuard.SOURCE_TOUCH_NAVIGATION)
    }

    @Test
    fun propertyParse() {
        assertTrue(PointerGuard.parse(null))
        assertTrue(PointerGuard.parse(""))
        assertTrue(PointerGuard.parse("1"))
        assertFalse(PointerGuard.parse("0"))
        assertFalse(PointerGuard.parse(" off "))
        assertEquals("debug.privyhub.pointer_hide", PointerGuard.PROPERTY)
    }
}
