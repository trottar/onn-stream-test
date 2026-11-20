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
class TouchPadState(private val kind: Kind = Kind.PS1) {

    /**
     * G6-HM4: [Kind.PS2] is the layout in use (the amendment G6-HM1a, the shoulders as addendum B2). [Kind.PS1] is
     * G6-HM2's first layout, kept as the default only so G6-HM2's tests run unchanged; the app does not use it.
     */
    enum class Kind { PS1, PS2 }

    enum class Control { DPAD, CROSS, CIRCLE, SQUARE, TRIANGLE, L1, R1, L2, R2, SELECT, START, LSTICK, RSTICK, L3, R3 }

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
        if (kind == Kind.PS2) { layoutPs2(w, h); return }
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

    /**
     * G6-HM4: addendum B2's numbers exactly (`docs/memory/evidence/g6_hm1a_2026-11-19/layout_check_b.py`, B2), in px of
     * the reference region, scaled to the measured size (x and radii by the width, y by the height).
     * G6-SCREEN1: the region is 1200 x 1100 under the 4:3 box. Every control but SELECT / START keeps its on-screen
     * place: its y is B2's minus 225 (the box grew by 225 px). SELECT and START stay at y 70 of the region, so they
     * move down 225 px on the screen, toward the controls (`layout_check_screen1.py`).
     */
    private fun layoutPs2(w: Int, h: Int) {
        val sx = w / Ps2TouchLayout.REF_W
        val sy = h / Ps2TouchLayout.REF_H
        fun circle(c: Control, x: Float, y: Float, r: Float, hit: Float) {
            shapes[c] = Shape.Circle(x * sx, y * sy, r * sx, hit)
        }
        fun rect(c: Control, x: Float, y: Float, hw: Float, hh: Float, hit: Float) {
            shapes[c] = Shape.Rect(x * sx, y * sy, hw * sx, hh * sy, hit)
        }
        circle(Control.LSTICK, 300f, 805f, Ps2TouchLayout.STICK_R, Ps2TouchLayout.STICK_HIT)
        circle(Control.DPAD, 300f, 295f, Ps2TouchLayout.DPAD_R, Ps2TouchLayout.DPAD_HIT)
        dpadR = Ps2TouchLayout.DPAD_R * sx
        circle(Control.L3, 540f, 815f, Ps2TouchLayout.THUMB_R, Ps2TouchLayout.BUTTON_HIT)
        circle(Control.TRIANGLE, 900f, 715f, Ps2TouchLayout.FACE_R, Ps2TouchLayout.BUTTON_HIT)
        circle(Control.CIRCLE, 990f, 805f, Ps2TouchLayout.FACE_R, Ps2TouchLayout.BUTTON_HIT)
        circle(Control.CROSS, 900f, 895f, Ps2TouchLayout.FACE_R, Ps2TouchLayout.BUTTON_HIT)
        circle(Control.SQUARE, 810f, 805f, Ps2TouchLayout.FACE_R, Ps2TouchLayout.BUTTON_HIT)
        circle(Control.RSTICK, 900f, 295f, Ps2TouchLayout.STICK_R, Ps2TouchLayout.STICK_HIT)
        circle(Control.R3, 690f, 565f, Ps2TouchLayout.THUMB_R, Ps2TouchLayout.BUTTON_HIT)
        rect(Control.SELECT, 400f, 70f, Ps2TouchLayout.SMALL_HW, Ps2TouchLayout.SMALL_HH, Ps2TouchLayout.BUTTON_HIT)
        rect(Control.START, 600f, 70f, Ps2TouchLayout.SMALL_HW, Ps2TouchLayout.SMALL_HH, Ps2TouchLayout.BUTTON_HIT)
        rect(Control.L2, 56f, Ps2TouchLayout.SHOULDER_Y, Ps2TouchLayout.SHOULDER_HW, Ps2TouchLayout.SHOULDER_HH, Ps2TouchLayout.SHOULDER_HIT)
        rect(Control.L1, 170f, Ps2TouchLayout.SHOULDER_Y, Ps2TouchLayout.SHOULDER_HW, Ps2TouchLayout.SHOULDER_HH, Ps2TouchLayout.SHOULDER_HIT)
        rect(Control.R1, 1030f, Ps2TouchLayout.SHOULDER_Y, Ps2TouchLayout.SHOULDER_HW, Ps2TouchLayout.SHOULDER_HH, Ps2TouchLayout.SHOULDER_HIT)
        rect(Control.R2, 1144f, Ps2TouchLayout.SHOULDER_Y, Ps2TouchLayout.SHOULDER_HW, Ps2TouchLayout.SHOULDER_HH, Ps2TouchLayout.SHOULDER_HIT)
    }

    /**
     * G6-HM4: the End button's place in the PS2 layout (a separate view; reserved here so nothing overlaps it).
     * G6-SCREEN1: at x [Ps2TouchLayout.END_X] (was 960), y 70: the smallest x keeping >= 0.5 cm from the right stick's
     * press area now that the stick is 225 px nearer the top of the region.
     */
    fun endRect(w: Int, h: Int): FloatArray {
        val sx = w / Ps2TouchLayout.REF_W
        val sy = h / Ps2TouchLayout.REF_H
        val x = Ps2TouchLayout.END_X
        return floatArrayOf((x - Ps2TouchLayout.SMALL_HW) * sx, (70f - Ps2TouchLayout.SMALL_HH) * sy, (x + Ps2TouchLayout.SMALL_HW) * sx, (70f + Ps2TouchLayout.SMALL_HH) * sy)
    }

    /** The controls held now (a stick or the D-pad counts as held while a finger owns it). */
    fun heldControls(): Set<Control> = fingers.values.map { it.control }.toSet()

    /**
     * G6-HM4: a stick's deflection now, (x right-positive, y up-positive), each in -1..1, clamped to the unit circle,
     * 0 inside the 0.1 r dead zone; (0, 0) when no finger owns it. The stick is absolute: its base never moves.
     */
    fun stickDeflection(c: Control): Pair<Float, Float> {
        val s = shapes[c] as? Shape.Circle ?: return 0f to 0f
        val f = fingers.values.lastOrNull { it.control == c } ?: return 0f to 0f
        return stickVector(f.x - s.cx, s.cy - f.y, s.r)
    }

    /**
     * G6-STICK1: a stick's magnitude now as a fraction of its throw (not clamped; > 1 past the ring), or null when no
     * finger owns it.
     */
    fun stickMagnitude(c: Control): Float? {
        val s = shapes[c] as? Shape.Circle ?: return null
        val f = fingers.values.lastOrNull { it.control == c } ?: return null
        return if (s.r <= 0f) null else hypot(f.x - s.cx, s.cy - f.y) / s.r
    }

    /** G6-STICK1: the stick's sent (x right, y up) values: [Ds2Stick.send] of the finger's offset; (0, 0) unowned. */
    fun stickSent(c: Control): Pair<Short, Short> {
        val s = shapes[c] as? Shape.Circle ?: return 0.toShort() to 0.toShort()
        val f = fingers.values.lastOrNull { it.control == c } ?: return 0.toShort() to 0.toShort()
        return Ds2Stick.send(f.x - s.cx, s.cy - f.y, s.r)
    }

    /** The control whose hit area holds the point (the nearest centre among several), or null. */
    fun controlAt(x: Float, y: Float): Control? =
        shapes.entries.filter { it.value.hit(x, y) }.minByOrNull { hypot(x - it.value.cx, y - it.value.cy) }?.key

    /** G6-HM3: what the view draws: a circle (halfH = 0) of radius halfW, or a rectangle of half-sizes halfW x halfH. */
    data class Drawn(val control: Control, val cx: Float, val cy: Float, val halfW: Float, val halfH: Float,
                     val hitHalfW: Float = halfW, val hitHalfH: Float = halfH)

    fun drawn(): List<Drawn> = shapes.map { (c, s) ->
        when (s) {
            is Shape.Circle -> Drawn(c, s.cx, s.cy, s.r, 0f, s.r * s.hitScale, 0f)
            is Shape.Rect -> Drawn(c, s.cx, s.cy, s.halfW, s.halfH, s.halfW * s.hitScale, s.halfH * s.hitScale)
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

    fun output(): Output = output(emptySet())

    /**
     * G6-JOIN1: the output with the fingers on [skip] left out (a touch hold's joining control is not sent until it is
     * lifted, as a real pad's joining key). An empty set is [output].
     */
    fun output(skip: Set<Control>): Output {
        var buttons = 0
        var lt = 0
        var rt = 0
        for (f in fingers.values) {
            if (f.control in skip) continue
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
                Control.L3 -> buttons = buttons or XUSB_LEFT_THUMB
                Control.R3 -> buttons = buttons or XUSB_RIGHT_THUMB
                Control.LSTICK, Control.RSTICK -> {}
            }
        }
        // G6-STICK1: the sticks' sent values through the DualShock 2 mapping ([Ds2Stick]); the knob and the report's
        // deflection keep [stickDeflection]
        val (lx, ly) = if (Control.LSTICK in skip) 0.toShort() to 0.toShort() else stickSent(Control.LSTICK)
        val (rx, ry) = if (Control.RSTICK in skip) 0.toShort() to 0.toShort() else stickSent(Control.RSTICK)
        return Output(buttons = buttons, lx = lx, ly = ly, rx = rx, ry = ry,
            lt = lt, rt = rt)
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
        const val XUSB_LEFT_THUMB = 0x0040     // L3 (G6-HM4)
        const val XUSB_RIGHT_THUMB = 0x0080    // R3 (G6-HM4)
        const val STICK_DEAD = 0.1f
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
        /** G6-HM4: a stick's offset (dx right, dyUp up) over its radius: clamped to the unit circle; 0 inside 0.1 r. */
        fun stickVector(dx: Float, dyUp: Float, radius: Float): Pair<Float, Float> {
            if (radius <= 0f) return 0f to 0f
            var x = dx / radius
            var y = dyUp / radius
            val m = hypot(x, y)
            if (m < STICK_DEAD) return 0f to 0f
            if (m > 1f) { x /= m; y /= m }
            return x to y
        }


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

/**
 * G6-HM4: addendum B2's reference numbers (px of the region; `layout_check_b.py`, B2), exactly.
 * G6-SCREEN1: the region 1200 x 1100 (was 1325) under the 4:3 box; the cluster's y 225 less, so it stays put on the
 * screen; End at x 1080.
 */
object Ps2TouchLayout {
    const val REF_W = 1200f
    const val REF_H = 1100f
    /** G6-HM4's region height (B2's numbers were in px of 1200 x 1325). */
    const val REF_H_HM4 = 1325f
    /** G6-SCREEN1: how far the box grew, so how far every cluster y moved up in the region: 1325 - 1100. */
    const val BOX_GROWTH = REF_H_HM4 - REF_H
    /** G6-SCREEN1: End's x (G6-HM4: 960). */
    const val END_X = 1080f
    /** G6-HM4's stick radius (drawn ring = full throw). */
    const val STICK_R_HM4 = 132f
    /** G6-HM4b: the throw shortened to 0.875 x (the user: "10-15% smaller"); the drawn ring matches it. */
    const val STICK_THROW = 0.875f
    const val STICK_R = STICK_R_HM4 * STICK_THROW          // 115.5 px: full deflection here
    /** G6-HM4b: the press (catch) area unchanged from G6-HM4: 132 x 1.2 = 158.4 px. */
    const val STICK_PRESS_R = STICK_R_HM4 * 1.2f
    const val STICK_HIT = STICK_PRESS_R / STICK_R
    const val DPAD_R = 125f
    const val DPAD_HIT = 1.25f
    const val THUMB_R = 48f
    const val FACE_R = 52f
    const val BUTTON_HIT = 1.2f
    const val SMALL_HW = 75.5f
    const val SMALL_HH = 47.5f
    const val SHOULDER_Y = 549f                          // G6-SCREEN1: B2's 774 - 225
    const val SHOULDER_HW = 50f
    const val SHOULDER_HH = 100f
    const val SHOULDER_HIT = 1.1f
}

/**
 * G6-STICK1: the touch sticks made to feel like a real DualShock 2 **end to end** (what the PS2 game receives, after
 * PCSX2's own stick scale). The chain (`docs/memory/evidence/G6_STICK1_DUALSHOCK2_FEEL_2026-11-20.md` §1): the sent
 * int16 -> the hub's uinput axis unchanged (y sign-flipped) -> SDL -> PCSX2's DualShock 2 pad, `AxisScale = 1.33`,
 * `Deadzone = 0` (`data/games/ps2/config/PCSX2/inis/PCSX2.ini` [Pad1], the hub's as launched): per direction
 * `clamp(v x 1.33 x 255, 0, 255)` truncated, merged around 127 (as PCSX2 2.x is understood; not read from its source).
 *
 * 1. dead zone 0.1 of the throw; 2. linear past it, full at 0.75 of the throw (the user's choice, 2026-11-20: where
 * PCSX2's 1.33 made a straight push full before; the outer quarter full); 3. the circle
 * mapped to the square (x 1 / max(|cos|, |sin|)): a full 45-degree push is full on both axes, a cardinal one unchanged;
 * 4. the target divided by PCSX2's 1.33 on the tablet, so the end-to-end value is the target and does not saturate
 * early; a full target is sent as full (PCSX2 clamps it). Touch sticks only: real pads and the onn never come here.
 */
object Ds2Stick {
    const val DEAD = 0.1f
    const val FULL_AT = 0.75f
    /** PCSX2's DualShock 2 `AxisScale` as the hub launches it (PCSX2.ini [Pad1]; PCSX2's default). */
    const val PCSX2_AXIS_SCALE = 1.33f
    const val MAPPING = "ds2-square-0.75-c1.33"

    /** The end-to-end target per axis (-1..1) for an offset (dx right, dyUp up) over the throw radius. */
    fun target(dx: Float, dyUp: Float, radius: Float): Pair<Float, Float> {
        if (radius <= 0f) return 0f to 0f
        val len = hypot(dx, dyUp)
        val m = len / radius
        if (m < DEAD || len <= 0f) return 0f to 0f
        val eff = ((m - DEAD) / (FULL_AT - DEAD)).coerceIn(0f, 1f)
        val c = dx / len
        val sn = dyUp / len
        val k = 1f / maxOf(kotlin.math.abs(c), kotlin.math.abs(sn))
        return (eff * c * k).coerceIn(-1f, 1f) to (eff * sn * k).coerceIn(-1f, 1f)
    }

    /** Within this of full is full (float rounding at 45 degrees gives 0.99999994; PCSX2's step is 1/128). */
    const val FULL_EPS = 1e-4f

    /** One axis's sent value for an end-to-end target: full as full; otherwise the target / 1.33. */
    fun sendAxis(t: Float): Short {
        val a = kotlin.math.abs(t)
        val v = if (a >= 1f - FULL_EPS) 32767 else (a / PCSX2_AXIS_SCALE * 32767f).roundToInt().coerceIn(0, 32767)
        return (if (t < 0f) -v else v).toShort()
    }

    fun send(dx: Float, dyUp: Float, radius: Float): Pair<Short, Short> =
        target(dx, dyUp, radius).let { (x, y) -> sendAxis(x) to sendAxis(y) }

    /**
     * PCSX2's value for a sent axis, as a fraction of full (0..1 of one direction), by the model above: the
     * direction's 0..255 (`v x 1.33 x 255`, clamped, truncated), merged as `127 + (raw + 1) / 2` (positive) or
     * `127 - raw / 2` (negative).
     */
    fun endToEnd(sent: Short, scale: Float = PCSX2_AXIS_SCALE): Float {
        val s = sent.toInt()
        if (s == 0) return 0f
        val v = kotlin.math.abs(s) / (if (s < 0) 32768f else 32767f)
        val raw = minOf(255, kotlin.math.floor(v * scale * 255f).toInt())
        return if (s > 0) ((raw + 1) / 2) / 128f else (raw / 2) / 127f
    }
}

/**
 * G6-STICK1: one stick's report figures. The largest sent value per direction, the largest min(|x|, |y|) sent (the
 * diagonal), and owned time by magnitude (10 bins of 0..1 of the throw; past the ring in the last) and at >= 0.75
 * ([Ds2Stick.FULL_AT], where the output is full).
 */
class StickStats {
    /** up, down, left, right: the largest sent magnitude. */
    val outMax = IntArray(4)
    var diagMax = 0
        private set
    val hist = LongArray(10)
    var ownedMs = 0L
        private set
    var edgeMs = 0L
        private set

    @Synchronized
    fun onSent(x: Short, yUp: Short) {
        val xi = x.toInt()
        val yi = yUp.toInt()
        if (yi > outMax[0]) outMax[0] = yi
        if (-yi > outMax[1]) outMax[1] = -yi
        if (-xi > outMax[2]) outMax[2] = -xi
        if (xi > outMax[3]) outMax[3] = xi
        val d = minOf(kotlin.math.abs(xi), kotlin.math.abs(yi))
        if (d > diagMax) diagMax = d
    }

    /** A sample of [dtMs] of a stick: its magnitude (fraction of the throw) when owned, or null. */
    @Synchronized
    fun sample(magnitude: Float?, dtMs: Long) {
        if (magnitude == null || dtMs <= 0) return
        ownedMs += dtMs
        if (magnitude >= Ds2Stick.FULL_AT) edgeMs += dtMs
        hist[minOf(9, maxOf(0, (magnitude * 10f).toInt()))] += dtMs
    }

    @Synchronized
    fun edgeFrac(): Double = if (ownedMs <= 0) 0.0 else Math.round(edgeMs * 1000.0 / ownedMs) / 1000.0

    @Synchronized
    fun histFracs(): List<Double> = hist.map { if (ownedMs <= 0) 0.0 else Math.round(it * 1000.0 / ownedMs) / 1000.0 }
}
