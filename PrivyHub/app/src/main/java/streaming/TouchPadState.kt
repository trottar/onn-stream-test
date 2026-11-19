package com.safeiot.privyhub.streaming

import kotlin.math.atan2
import kotlin.math.floor
import kotlin.math.hypot
import kotlin.math.roundToInt

/**
 * G6-HM2: the touch pad's state, pure Kotlin (no Android types; JVM-tested). Design:
 * `docs/memory/evidence/g6_hm1_2026-11-19/design_written_before_code.md` (hashed before this code), §4.
 *
 * - A finger belongs to the control under it at its down event (hit areas larger than the drawing; overlapping hit
 *   areas: the nearest centre) and keeps it until its up event, a cancel or a reset. Sliding off keeps the control;
 *   sliding onto another presses nothing new.
 * - The D-pad is 8-way by angle: eight 45° sectors, half-open `[k·45° − 22.5°, k·45° + 22.5°)`, re-read on every
 *   move (a roll), nothing inside 0.25 r.
 * - One finger, one button. L2 / R2 are digital (255). The output is the sender's state fields.
 * - The PS1 layout (D3) in fractions of the pad region; G6-HM6 adds customization.
 */
class TouchPadState {

    enum class Control { DPAD, CROSS, CIRCLE, SQUARE, TRIANGLE, L1, R1, L2, R2, SELECT, START }

    /** The sender's fields (NativeControllerSender.writePlayerState). */
    data class Output(
        val buttons: Int = 0,
        val lx: Short = 0,
        val ly: Short = 0,
        val rx: Short = 0,
        val ry: Short = 0,
        val lt: Int = 0,
        val rt: Int = 0,
    )

    private sealed class Shape(val cx: Float, val cy: Float) {
        abstract fun hit(x: Float, y: Float): Boolean
        class Circle(cx: Float, cy: Float, val r: Float, val hitScale: Float) : Shape(cx, cy) {
            override fun hit(x: Float, y: Float) = hypot(x - cx, y - cy) <= r * hitScale
        }
        class Rect(cx: Float, cy: Float, val halfW: Float, val halfH: Float, val hitScale: Float) : Shape(cx, cy) {
            override fun hit(x: Float, y: Float) =
                kotlin.math.abs(x - cx) <= halfW * hitScale && kotlin.math.abs(y - cy) <= halfH * hitScale
        }
    }

    private class Finger(val control: Control, var x: Float, var y: Float)

    private val shapes = LinkedHashMap<Control, Shape>()
    private val fingers = HashMap<Int, Finger>()
    private var dpadR = 0f

    /** The geometry from the pad region's real size (design §4 fractions). */
    fun layout(w: Int, h: Int) {
        shapes.clear()
        fingers.clear()
        if (w <= 0 || h <= 0) return
        val W = w.toFloat()
        val H = h.toFloat()
        fun band(x0: Float, x1: Float) =
            Shape.Rect((x0 + x1) / 2 * W, 0.08f * H, (x1 - x0) / 2 * W, 0.05f * H, SHOULDER_HIT)
        shapes[Control.L2] = band(0.03f, 0.22f)
        shapes[Control.L1] = band(0.24f, 0.44f)
        shapes[Control.R1] = band(0.56f, 0.76f)
        shapes[Control.R2] = band(0.78f, 0.97f)
        dpadR = 0.17f * W
        shapes[Control.DPAD] = Shape.Circle(0.25f * W, 0.50f * H, dpadR, DPAD_HIT)
        val fx = 0.75f * W
        val fy = 0.50f * H
        val d = 0.12f * W
        val br = 0.07f * W
        shapes[Control.TRIANGLE] = Shape.Circle(fx, fy - d, br, BUTTON_HIT)
        shapes[Control.CIRCLE] = Shape.Circle(fx + d, fy, br, BUTTON_HIT)
        shapes[Control.CROSS] = Shape.Circle(fx, fy + d, br, BUTTON_HIT)
        shapes[Control.SQUARE] = Shape.Circle(fx - d, fy, br, BUTTON_HIT)
        shapes[Control.SELECT] = Shape.Rect(0.40f * W, 0.82f * H, 0.07f * W, 0.03f * H, BUTTON_HIT)
        shapes[Control.START] = Shape.Rect(0.60f * W, 0.82f * H, 0.07f * W, 0.03f * H, BUTTON_HIT)
    }

    /** The control whose hit area holds the point (the nearest centre among several), or null. */
    fun controlAt(x: Float, y: Float): Control? =
        shapes.entries.filter { it.value.hit(x, y) }.minByOrNull { hypot(x - it.value.cx, y - it.value.cy) }?.key

    /** G6-HM3: what the view draws: a circle (halfH = 0) of radius halfW, or a rectangle of half-sizes halfW x halfH. */
    data class Drawn(val control: Control, val cx: Float, val cy: Float, val halfW: Float, val halfH: Float)

    fun drawn(): List<Drawn> = shapes.map { (c, s) ->
        when (s) {
            is Shape.Circle -> Drawn(c, s.cx, s.cy, s.r, 0f)
            is Shape.Rect -> Drawn(c, s.cx, s.cy, s.halfW, s.halfH)
        }
    }

    /** The control's drawn centre (for the view and the tests), or null before [layout]. */
    fun centreOf(c: Control): Pair<Float, Float>? = shapes[c]?.let { it.cx to it.cy }

    fun down(id: Int, x: Float, y: Float): Output {
        if (id !in fingers) controlAt(x, y)?.let { fingers[id] = Finger(it, x, y) }
        return output()
    }

    fun move(id: Int, x: Float, y: Float): Output {
        fingers[id]?.let { it.x = x; it.y = y }
        return output()
    }

    fun up(id: Int): Output {
        fingers.remove(id)
        return output()
    }

    fun cancel(): Output {
        fingers.clear()
        return output()
    }

    fun reset(): Output = cancel()

    fun heldFingers(): Int = fingers.size

    fun output(): Output {
        var buttons = 0
        var lt = 0
        var rt = 0
        for (f in fingers.values) {
            when (f.control) {
                Control.DPAD -> buttons = buttons or dpadBits(f.x, f.y)
                Control.CROSS -> buttons = buttons or XUSB_A
                Control.CIRCLE -> buttons = buttons or XUSB_B
                Control.SQUARE -> buttons = buttons or XUSB_X
                Control.TRIANGLE -> buttons = buttons or XUSB_Y
                Control.L1 -> buttons = buttons or XUSB_LEFT_SHOULDER
                Control.R1 -> buttons = buttons or XUSB_RIGHT_SHOULDER
                Control.L2 -> lt = 255
                Control.R2 -> rt = 255
                Control.SELECT -> buttons = buttons or XUSB_BACK
                Control.START -> buttons = buttons or XUSB_START
            }
        }
        return Output(buttons = buttons, lt = lt, rt = rt)
    }

    private fun dpadBits(x: Float, y: Float): Int {
        val c = shapes[Control.DPAD] ?: return 0
        return dpadSector(x - c.cx, c.cy - y, dpadR)?.let { SECTOR_BITS[it] } ?: 0
    }

    companion object {
        // The XUSB bits of the PHI1 packet (NativeControllerSender's private values; the test pins them)
        const val XUSB_DPAD_UP = 0x0001
        const val XUSB_DPAD_DOWN = 0x0002
        const val XUSB_DPAD_LEFT = 0x0004
        const val XUSB_DPAD_RIGHT = 0x0008
        const val XUSB_START = 0x0010
        const val XUSB_BACK = 0x0020
        const val XUSB_LEFT_SHOULDER = 0x0100
        const val XUSB_RIGHT_SHOULDER = 0x0200
        const val XUSB_A = 0x1000
        const val XUSB_B = 0x2000
        const val XUSB_X = 0x4000
        const val XUSB_Y = 0x8000

        const val DPAD_HIT = 1.5f
        const val BUTTON_HIT = 1.3f
        const val SHOULDER_HIT = 1.15f
        const val DPAD_DEAD = 0.25f

        /** Sector k (0 = right, counter-clockwise in 45° steps) → its bits; a diagonal is two. */
        private val SECTOR_BITS = intArrayOf(
            XUSB_DPAD_RIGHT,
            XUSB_DPAD_RIGHT or XUSB_DPAD_UP,
            XUSB_DPAD_UP,
            XUSB_DPAD_UP or XUSB_DPAD_LEFT,
            XUSB_DPAD_LEFT,
            XUSB_DPAD_LEFT or XUSB_DPAD_DOWN,
            XUSB_DPAD_DOWN,
            XUSB_DPAD_DOWN or XUSB_DPAD_RIGHT,
        )

        /**
         * The D-pad's sector for an offset from its centre, `dy` positive **up** (screen y flipped); null inside the
         * dead radius. Sector k covers `[k·45° − 22.5°, k·45° + 22.5°)`.
         */
        fun dpadSector(dx: Float, dyUp: Float, radius: Float): Int? {
            if (hypot(dx, dyUp) < DPAD_DEAD * radius) return null
            var a = Math.toDegrees(atan2(dyUp.toDouble(), dx.toDouble()))
            if (a < 0) a += 360.0
            return floor((a + 22.5) / 45.0).toInt() % 8
        }

        /**
         * G6-HM5's stick, stubbed here for its sign: the sender's `ly` is positive **up** (it stores `-AXIS_Y`,
         * NativeControllerSender `toStick(-ly)`), so a finger above the centre gives a positive value.
         */
        fun stickY(fingerY: Float, centreY: Float, radius: Float): Short {
            if (radius <= 0f) return 0
            val v = ((centreY - fingerY) / radius).coerceIn(-1f, 1f)
            return (v * 32767f).roundToInt().coerceIn(-32768, 32767).toShort()
        }
    }
}
