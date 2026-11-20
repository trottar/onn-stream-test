package com.safeiot.privyhub.streaming

import com.safeiot.privyhub.streaming.TouchPadState.Control
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.sin

/**
 * G6-STICK1: the touch sticks as a DualShock 2 end to end (after PCSX2's AxisScale 1.33): dead zone 0.1, full at 0.75
 * of the throw (the user's choice; first 0.9), the circle mapped to the square, the 1.33 compensated on the tablet; the report's figures.
 */
class G6Stick1Test {

    private val r = Ps2TouchLayout.STICK_R
    private fun e2e(v: Short) = Ds2Stick.endToEnd(v).toDouble()
    private fun push(frac: Float, deg: Double): Pair<Short, Short> {
        val a = Math.toRadians(deg)
        return Ds2Stick.send((frac * r * cos(a)).toFloat(), (frac * r * sin(a)).toFloat(), r)
    }

    @Test
    fun theDeadZoneIsATenthOfTheThrow() {
        assertEquals(0.toShort() to 0.toShort(), push(0.099f, 0.0))
        assertEquals(0.toShort() to 0.toShort(), push(0.099f, 45.0))
        assertTrue(push(0.11f, 0.0).first > 0)
        assertEquals(0.0, e2e(push(0.1f, 0.0).first), 1.0 / 128)                     // the ramp starts at 0
    }

    @Test
    fun fullAt75PercentOfTheThrowAndNeverBeyond() {
        assertEquals(0.75f, Ds2Stick.FULL_AT, 0f)
        for (f in listOf(0.75f, 0.8f, 0.9f, 1f, 1.5f, 3f)) {
            val (x, y) = push(f, 0.0)
            assertEquals("$f", 32767.toShort(), x); assertEquals(0.toShort(), y)
            assertEquals(1.0, e2e(x), 0.0)
        }
        assertTrue(e2e(push(0.74f, 0.0).first) < 1.0)                                // not saturated early
        assertEquals(-32767, push(1f, 180.0).first.toInt())                          // no output beyond full
    }

    @Test
    fun aFull45DegreePushIsFullOnBothAxesEndToEnd() {
        for (deg in listOf(45.0, 135.0, 225.0, 315.0)) {
            val (x, y) = push(1f, deg)
            assertEquals("$deg", 1.0, e2e(x), 0.0); assertEquals("$deg", 1.0, e2e(y), 0.0)
        }
        // at 0.75 of the throw too; and a 45-degree push half way up the ramp (0.425) is half on both axes
        val (x9, y9) = push(0.75f, 45.0)
        assertEquals(1.0, e2e(x9), 0.0); assertEquals(1.0, e2e(y9), 0.0)
        assertTrue(e2e(push(0.74f, 45.0).first) < 1.0)
        val (xh, yh) = push(0.425f, 45.0)
        assertEquals(0.5, e2e(xh), 1.0 / 128); assertEquals(0.5, e2e(yh), 1.0 / 128)
    }

    @Test
    fun cardinalValuesKeepTheirDirectionAndAreMonotonic() {
        var last = -1.0
        for (i in 10..100) {
            val f = i / 100f
            val (x, y) = push(f, 90.0)
            assertEquals(0.toShort(), x)
            assertTrue(y >= 0)
            val v = e2e(y)
            assertTrue("$f", v >= last)
            last = v
            assertEquals("$f", ((f - 0.1) / 0.65).coerceIn(0.0, 1.0), v, 1.0 / 128 + 1e-6)  // the target, end to end
        }
        // the sign rules: up / right positive, down / left negative
        assertTrue(push(0.5f, 270.0).second < 0 && push(0.5f, 180.0).first < 0)
    }

    // the 1.33 compensated: what is sent is the target / 1.33, so PCSX2's x 1.33 gives the target (residual <= 1/128)
    @Test
    fun pcsx2sScaleIsCompensated() {
        assertEquals(1.33f, Ds2Stick.PCSX2_AXIS_SCALE, 0f)
        var worst = 0.0
        for (i in 0..999) {
            val t = i / 1000f
            val sent = Ds2Stick.sendAxis(t)
            assertEquals((t / 1.33f * 32767f).toDouble(), sent.toDouble(), 1.0)
            worst = maxOf(worst, abs(e2e(sent) - t))
            val neg = Ds2Stick.sendAxis(-t)
            worst = maxOf(worst, abs(e2e(neg) - t))
        }
        assertTrue("residual $worst", worst <= 1.0 / 127 + 1e-6)
        // without the compensation, 0.8 of full would already be full in PCSX2
        assertEquals(1.0, Ds2Stick.endToEnd((0.8f * 32767).toInt().toShort()).toDouble(), 0.0)
        assertEquals("ds2-square-0.75-c1.33", Ds2Stick.MAPPING)
    }

    // the touch pad sends the mapping; the knob and the report's deflection keep the circle
    @Test
    fun theTouchPadSendsTheMapping() {
        val s = TouchPadState(TouchPadState.Kind.PS2).apply { layout(1200, 1100) }
        val (lx, ly) = s.centreOf(Control.LSTICK)!!
        s.down(1, lx, ly)
        val d = 0.95f * r / Math.sqrt(2.0).toFloat()
        val out = s.move(1, lx + d, ly - d)                                          // up-right, 95 % of the throw
        assertEquals(32767.toShort(), out.lx); assertEquals(32767.toShort(), out.ly)
        assertEquals(0.95f, s.stickMagnitude(Control.LSTICK)!!, 1e-3f)
        assertEquals(0.672f, s.stickDeflection(Control.LSTICK).first, 1e-3f)       // the circle, unchanged
        s.up(1)
        assertEquals(null, s.stickMagnitude(Control.LSTICK))
    }

    // the report's figures
    @Test
    fun theStickStats() {
        val st = StickStats()
        st.onSent(32767, 0); st.onSent(-12000, -20000); st.onSent(25000, 26000)
        assertEquals(listOf(26000, 20000, 12000, 32767), st.outMax.toList())        // up, down, left, right
        assertEquals(25000, st.diagMax)
        st.sample(null, 100)                                                         // unowned: not counted
        st.sample(0.95f, 200); st.sample(0.76f, 100); st.sample(0.74f, 100); st.sample(1.4f, 100)
        assertEquals(0.8, st.edgeFrac(), 1e-9)                                       // at >= 0.75 of the throw
        val h = st.histFracs()
        assertEquals(10, h.size)
        assertEquals(0.4, h[7], 1e-9); assertEquals(0.6, h[9], 1e-9)
        assertEquals(1.0, h.sum(), 1e-9)
        assertEquals(1.0, Ds2Stick.endToEnd(32767).toDouble(), 0.0)
    }
}
