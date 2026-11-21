package com.safeiot.privyhub.streaming

import android.content.Context
import android.content.pm.ActivityInfo
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Matrix
import android.graphics.Paint
import android.graphics.Rect
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.Gravity
import android.view.KeyEvent
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.FrameLayout
import android.widget.TextView
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.atomic.AtomicLong

/**
 * G6-HM3 / G6-HM4: the tablet's portrait handheld mode (design `docs/memory/evidence/g6_hm1_2026-11-19/`, the amendment
 * `…/g6_hm1a_2026-11-19/` and addendum B2, all hashed before code, with the user's answers). The game's picture in a
 * W x W·3/4 box at the top (G6-SCREEN1; G6-HM3's was W·9/16; every overlay inside it, unchanged); the PS2 touch pad
 * below. A system proven 4:3 is cropped to fill the box; any other keeps its 16:9 picture at the box's top.
 * Launched only when the user picks "Handheld" in Settings on a device with a touchscreen; the onn's NativeStreamActivity entry and paths are
 * unchanged.
 *
 * - D5: the PS2 layout on every system: D-pad, four face buttons, L1 / L2 / R1 / R2 (side by side, B2), two absolute
 *   sticks with L3 / R3, Select, Start, End.
 * - D2 with Q3 (b)/(i) and Q4 (b): the touch pad becomes P1 5 s after the gameplay release unless a real pad holds P1;
 *   a countdown in the pad region. Q2 (d): a real pad's unjoined hold kept 2 s takes P1 from the touch pad.
 * - Q5 (c): Back does nothing in a game; **End** ends to the paused picture. Q1 (c): a real P1 -> the status panel.
 */
class HandheldStreamActivity : NativeStreamActivity() {

    companion object {
        /** G6-HM4: live (G6-HM3 had it false: the pad drawn and inert). */
        const val TOUCH_LIVE = true
        private const val TICK_MS = 100L
        private const val TEXT_PREVIEW = "Touch buttons: coming in the next update"
        private val DIRECTIONS = arrayOf("up", "down", "left", "right")
        /** G6-SCREEN1: a cropped paused picture: 4:3 at the stored preview's height (today's preview: 480 x 270). */
        private const val PAUSED_W_4X3 = 360f
        private const val PAUSED_H = 270f
    }

    private val ui = Handler(Looper.getMainLooper())
    private val pad = TouchPadState(TouchPadState.Kind.PS2)
    private val p1Rule = TouchP1Rule()
    /** G6-JOIN1: a touch hold joins P1 during the countdown; the joining controls are not sent until lifted. */
    private val holdJoin = TouchHoldJoin()
    private val joinSuppressed = LinkedHashSet<TouchPadState.Control>()
    @Volatile private var joinVia = "none"
    private val takeover = TouchTakeover()
    private var padView: TouchPadView? = null
    private var panel: TextView? = null
    private var hint: TextView? = null
    private var frame: HandheldLayout? = null

    private val touchEvents = AtomicLong(0)
    private val touchWrites = AtomicLong(0)
    private val exempted = AtomicLong(0)
    private val backSwallowed = AtomicLong(0)
    private val endPresses = AtomicLong(0)
    private val takeovers = AtomicLong(0)
    @Volatile private var navMode = -1
    @Volatile private var density = 0f
    @Volatile private var releaseAtMs: Long? = null
    @Volatile private var p1JoinAfterReleaseMs: Long = -1
    /** G6-SCREEN1: the catalog entry's system (H10), and whether the picture is cropped now. */
    @Volatile private var gameSystem: String? = null
    /** G6-SCREEN1b: the reply's `widescreen` (H12; null = no field) and the fill shown, with the box's share of the surface. */
    @Volatile private var gameWidescreen: Boolean? = null
    @Volatile private var fillShown = HandheldGeometry.Fill.NONE
    @Volatile private var shownShare = 1.0
    private val pressed = java.util.Collections.synchronizedSet(LinkedHashSet<String>())
    /** [left, right] stick x [up, down, left, right]: the largest deflection seen, 0..1. */
    private val stickMax = Array(2) { FloatArray(4) }
    /** G6-STICK1: [left, right]: the sent values and owned time by magnitude. */
    private val stickStats = arrayOf(StickStats(), StickStats())
    @Volatile private var lastTickMs = -1L

    override val streamOrientation: Int get() = ActivityInfo.SCREEN_ORIENTATION_PORTRAIT

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        density = resources.displayMetrics.density
        navMode = try { Settings.Secure.getInt(contentResolver, "navigation_mode", -1) } catch (_: Exception) { -1 }
        ui.post(tick)
    }

    override fun wrapStreamLayer(streamLayer: FrameLayout): View {
        val end = Button(this).apply {
            text = "End"
            isAllCaps = false
            minWidth = 0
            minimumWidth = 0
            minHeight = 0
            minimumHeight = 0
            setPadding(0, 0, 0, 0)
            // Q5 (c): the only way out of a game here (Back does nothing)
            setOnClickListener { endPresses.incrementAndGet(); pressed.add("END"); endToPausedFrame() }
        }
        val area = PadArea(this, pad, end).apply { setBackgroundColor(Color.BLACK) }
        val pv = TouchPadView(this, pad, { touchEvents.incrementAndGet() }) { out -> onPadOutput(out) }
        padView = pv
        area.addView(pv, FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT))
        panel = TextView(this).apply {
            setTextColor(Color.WHITE)
            textSize = 18f
            gravity = Gravity.CENTER
            visibility = View.GONE
        }.also {
            area.addView(it, FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT))
        }
        hint = TextView(this).apply {
            setTextColor(0xFFAAAAAA.toInt())
            textSize = 14f
            text = if (TOUCH_LIVE) "" else TEXT_PREVIEW
        }.also {
            area.addView(it, FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT)
                .apply { gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL; bottomMargin = 24 })
        }
        // End last: on top of the pad and the panel, so it stays reachable with the status panel shown (Q1 (c))
        area.addView(end, FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT))
        return HandheldLayout(this, streamLayer, area, streamSurface, { gameSystem }, { gameWidescreen }) { fill, share ->
            fillShown = fill
            shownShare = share
        }.also { frame = it }
    }

    // B70: the touchscreen only, in this activity only; mice, touchpads and a pad's touchpad stay consumed
    override fun exemptFromPointerGuard(event: MotionEvent): Boolean =
        HandheldInput.isTouchscreen(event.source).also { if (it) exempted.incrementAndGet() }

    // design §5 / hook H4: the touch pad is "present" (only once it can hold a slot)
    override fun connectedPadDevices(): List<PadDevice> =
        if (TOUCH_LIVE) super.connectedPadDevices() + TouchPadDevice else super.connectedPadDevices()

    // G6-SCREEN1 (H10): the system decides the crop; the box re-lays its surface (before the first frame, normally)
    override fun onGameSystem(system: String?) {
        gameSystem = system
        // on the surface itself: its parents re-measure with it, so the box's placeSurface runs before the layer's measure
        ui.post { streamSurface.requestLayout() }
    }

    // G6-SCREEN1b (H12): the hub ran this PS2 launch without its widescreen patch -> PS2 is cropped too
    override fun onGameWidescreen(widescreen: Boolean?) {
        gameWidescreen = widescreen
        ui.post { streamSurface.requestLayout() }
    }

    // G6-SCREEN1 (H11): a cropped (or, G6-SCREEN1b, stretched) picture's paused copy is what the box shows (the
    // surface's centre, the box's share of its width), 360 x 270
    override fun pausedFramePreview(source: Bitmap): Bitmap {
        if (fillShown == HandheldGeometry.Fill.NONE) return super.pausedFramePreview(source)
        val ch = source.height
        val cw = minOf(source.width, Math.round(source.width * shownShare).toInt())
        if (cw <= 0 || ch <= 0) return super.pausedFramePreview(source)
        val m = Matrix().apply { setScale(PAUSED_W_4X3 / cw, PAUSED_H / ch) }
        return Bitmap.createBitmap(source, (source.width - cw) / 2, 0, cw, ch, m, true)
    }

    override fun onPlayersOpened(selfRestart: Boolean) {
        ui.post { p1Rule.onStart(selfRestart); takeover.clear(); releaseAtMs = null; holdJoin.reset() }
    }

    override fun onGameplayReleased() {
        val now = nowMs()
        val wasArmed = p1Rule.armed()
        p1Rule.onGameplayReleased(now)
        if (!wasArmed && p1Rule.armed()) releaseAtMs = now
    }

    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        if (TOUCH_LIVE) {
            event.device?.let { d ->
                val pd = AndroidPadDevice(d)
                takeover.onKey(pd, event.keyCode, event.action == KeyEvent.ACTION_DOWN, event.repeatCount, nowMs(),
                    joinedAtDown = streamSlots?.slotOf(pd) != null)
            }
        }
        // Q5 (c): Back does nothing in a game here (End ends)
        if (event.keyCode == KeyEvent.KEYCODE_BACK) {
            if (event.action == KeyEvent.ACTION_UP) backSwallowed.incrementAndGet()
            return true
        }
        return super.dispatchKeyEvent(event)
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (!hasFocus) resetPad()
    }

    override fun onPause() {
        super.onPause()
        resetPad()
        p1Rule.cancel()
    }

    override fun onDestroy() {
        ui.removeCallbacks(tick)
        super.onDestroy()
    }

    override fun putHandheldReport(report: JSONObject) {
        val w = frame?.width ?: 0
        val h = frame?.height ?: 0
        val sticks = JSONObject()
        // G6-STICK1: the sent values (int16) per direction, the diagonal, owned time at the edge and by magnitude
        val outMax = JSONObject()
        val diagMax = JSONObject()
        val edgeFrac = JSONObject()
        val magHist = JSONObject()
        for ((i, name) in arrayOf("left", "right").withIndex()) {
            val st = stickStats[i]
            val o = JSONObject()
            synchronized(st) {
                for ((j, dir) in DIRECTIONS.withIndex()) o.put(dir, st.outMax[j])
                diagMax.put(name, JSONObject().put("sent", st.diagMax)
                    .put("end_to_end", Math.round(Ds2Stick.endToEnd(st.diagMax.toShort()) * 1000.0) / 1000.0))
            }
            outMax.put(name, o)
            edgeFrac.put(name, st.edgeFrac())
            magHist.put(name, JSONArray(st.histFracs()))
        }
        synchronized(stickMax) {
            for ((i, name) in arrayOf("left", "right").withIndex()) {
                val o = JSONObject()
                for ((j, dir) in DIRECTIONS.withIndex()) o.put(dir, Math.round(stickMax[i][j] * 1000.0) / 1000.0)
                sticks.put(name, o)
            }
        }
        report.put("handheld", JSONObject()
            .put("mode", "portrait")
            .put("layout", "ps2")
            .put("layout_version", Ps2TouchLayout.LAYOUT_VERSION)
            .put("touch_live", TOUCH_LIVE)
            .put("video_box", "${w}x${HandheldGeometry.videoBoxHeight(w, h)}")
            .put("pad_region", "${w}x${HandheldGeometry.padRegionHeight(w, h)}")
            .put("video_crop", HandheldGeometry.videoCrop(fillShown))
            .put("video_source_rect", HandheldGeometry.videoSourceRect(fillShown))
            .put("density", density.toDouble())
            .put("nav_mode", navMode)
            .put("sdk", Build.VERSION.SDK_INT)
            .put("touch_events", touchEvents.get())
            .put("touch_writes", touchWrites.get())
            .put("touch_slot", streamSlots?.slotOf(TouchPadDevice) ?: -1)
            .put("p1_join_after_release_ms", p1JoinAfterReleaseMs)
            .put("p1_join_via", joinVia)
            .put("p1_join_hold_ms", PlayerPrompt.HOLD_MS)
            .put("takeovers", takeovers.get())
            .put("controls_pressed", JSONArray(synchronized(pressed) { pressed.toList() }))
            .put("stick_max_deflection", sticks)
            .put("stick_out_max", outMax)
            .put("stick_diag_max", diagMax)
            .put("stick_edge_frac", edgeFrac)
            .put("stick_mag_hist", magHist)
            .put("stick_mapping", Ds2Stick.MAPPING)
            .put("pointer_exempted_events", exempted.get())
            .put("back_swallowed", backSwallowed.get())
            .put("end_presses", endPresses.get()))
    }

    private fun nowMs() = System.nanoTime() / 1_000_000L

    private fun resetPad() {
        onPadOutput(pad.reset())
        padView?.invalidate()
    }

    /** What was touched (the report's keys), then the touch pad's fields into its own slot (none = nothing). */
    private fun onPadOutput(out: TouchPadState.Output) {
        val held = pad.heldControls()
        held.forEach { pressed.add(it.name) }
        holdJoin.observe(held, nowMs())
        stickStats[0].onSent(out.lx, out.ly)
        stickStats[1].onSent(out.rx, out.ry)
        synchronized(stickMax) {
            for ((i, c) in arrayOf(TouchPadState.Control.LSTICK, TouchPadState.Control.RSTICK).withIndex()) {
                val (x, y) = pad.stickDeflection(c)
                val m = stickMax[i]
                if (y > m[0]) m[0] = y
                if (-y > m[1]) m[1] = -y
                if (-x > m[2]) m[2] = -x
                if (x > m[3]) m[3] = x
            }
        }
        if (!TOUCH_LIVE) return
        val sender = streamSender ?: return
        val slot = streamSlots?.slotOf(TouchPadDevice) ?: return
        // G6-JOIN1: the joining controls stay out until lifted (as a real pad's joining key)
        if (joinSuppressed.isNotEmpty()) joinSuppressed.retainAll(held)
        val sent = if (joinSuppressed.isEmpty()) out else pad.output(joinSuppressed)
        val o = if (gameplayLive) sent else TouchPadState.Output()
        if (sender.writePlayerState(slot, o.buttons, o.lx, o.ly, o.rx, o.ry, o.lt, o.rt)) touchWrites.incrementAndGet()
    }

    private val tick = object : Runnable {
        override fun run() {
            val now = nowMs()
            // G6-STICK1: owned time by magnitude, sampled at each tick (100 ms)
            val dt = if (lastTickMs < 0) 0L else now - lastTickMs
            lastTickMs = now
            stickStats[0].sample(pad.stickMagnitude(TouchPadState.Control.LSTICK), dt)
            stickStats[1].sample(pad.stickMagnitude(TouchPadState.Control.RSTICK), dt)
            val slots = streamSlots
            val p1 = slots?.holderOf(0)
            val realP1 = p1 != null && p1 != TouchPadDevice.KEY
            if (TOUCH_LIVE) {
                val prompt = streamPrompt
                // G6-JOIN1: a touch hold during the countdown joins at once; else the countdown at 5 s as before
                val via = holdJoin.step(now, p1Rule, p1 == null, realP1)
                if (via != null) {
                    val held = pad.heldControls()
                    val s = prompt?.joinAsP1WithoutHold(TouchPadDevice, now, connectedPadDevices())
                    if (s == 0) {
                        releaseAtMs?.let { p1JoinAfterReleaseMs = now - it }
                        joinVia = via.report
                        if (via == TouchHoldJoin.Via.HOLD) joinSuppressed.addAll(held)
                    }
                }
                takeover.due(now, p1 == TouchPadDevice.KEY)?.let { real ->
                    streamSender?.writePlayerState(0, 0, 0, 0, 0, 0, 0, 0)
                    pad.reset()
                    if (prompt?.takeOverP1(real, TouchPadDevice.KEY, now) == 0) takeovers.incrementAndGet()
                }
                onPadOutput(pad.output())
            }
            // Q1 (c): a real pad as P1 -> the status panel instead of the pad (End stays on top)
            padView?.let { v ->
                val want = if (realP1) View.GONE else View.VISIBLE
                if (v.visibility != want) v.visibility = want
                v.invalidate()
            }
            panel?.let { t ->
                t.visibility = if (realP1) View.VISIBLE else View.GONE
                if (realP1) t.text = panelText(slots)
            }
            hint?.let { t ->
                t.visibility = if (realP1) View.GONE else View.VISIBLE
                t.text = when {
                    !TOUCH_LIVE -> TEXT_PREVIEW
                    p1 == TouchPadDevice.KEY -> "Touch buttons: Player 1"
                    else -> p1Rule.secondsLeft(now)?.let { "Hold any button to join · P1 in $it…" } ?: ""
                }
            }
            ui.postDelayed(this, TICK_MS)
        }
    }

    private fun panelText(slots: PadSlots?): String {
        val joined = slots?.map().orEmpty().joinToString("   ") { "P${it.slot + 1}" }
        return "Players joined: $joined\n\nA controller is Player 1,\nso the touch buttons are off."
    }

    /**
     * The video box on top (G6-SCREEN1: W x W·3/4, or G6-HM3's W·9/16 where the pad region would be too short), the pad
     * region below. The video surface inside the box (G6-SCREEN1): cropped, 16:9 of the box's height centred, its side
     * bars off the screen; not cropped, the 16:9 picture full width at the box's top.
     */
    private class HandheldLayout(
        ctx: Context,
        private val video: View,
        private val area: View,
        private val surface: View,
        private val system: () -> String?,
        private val widescreen: () -> Boolean?,
        private val onFill: (HandheldGeometry.Fill, Double) -> Unit,
    ) : ViewGroup(ctx) {
        init {
            addView(video)
            addView(area)
        }

        override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
            val w = MeasureSpec.getSize(widthMeasureSpec)
            val h = MeasureSpec.getSize(heightMeasureSpec)
            val box = HandheldGeometry.videoBoxHeight(w, h)
            placeSurface(w, box)
            video.measure(MeasureSpec.makeMeasureSpec(w, MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec(box, MeasureSpec.EXACTLY))
            area.measure(MeasureSpec.makeMeasureSpec(w, MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec(HandheldGeometry.padRegionHeight(w, h), MeasureSpec.EXACTLY))
            setMeasuredDimension(w, h)
        }

        /** The surface's size and gravity in the stream layer (a FrameLayout), set before the layer is measured. */
        private fun placeSurface(w: Int, box: Int) {
            val lp = surface.layoutParams as? FrameLayout.LayoutParams ?: return
            val fill = HandheldGeometry.fill(system(), widescreen(), w, box)
            val r = HandheldGeometry.surfaceRect(w, box, fill)
            lp.width = r[2]
            lp.height = r[3]
            lp.gravity = if (fill != HandheldGeometry.Fill.NONE) Gravity.TOP or Gravity.CENTER_HORIZONTAL else Gravity.TOP or Gravity.START
            onFill(fill, if (r[2] > 0) minOf(1.0, w.toDouble() / r[2]) else 1.0)
        }

        override fun onLayout(changed: Boolean, l: Int, t: Int, r: Int, b: Int) {
            val w = r - l
            val box = HandheldGeometry.videoBoxHeight(w, b - t)
            video.layout(0, 0, w, box)
            area.layout(0, box, w, b - t)
        }
    }

    /** The pad region: its children as a FrameLayout, then the End button put exactly on B2's End rectangle. */
    private class PadArea(ctx: Context, private val state: TouchPadState, private val end: View) : FrameLayout(ctx) {
        override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
            super.onMeasure(widthMeasureSpec, heightMeasureSpec)
            val r = state.endRect(measuredWidth, measuredHeight)
            end.measure(MeasureSpec.makeMeasureSpec((r[2] - r[0]).toInt(), MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec((r[3] - r[1]).toInt(), MeasureSpec.EXACTLY))
        }

        override fun onLayout(changed: Boolean, left: Int, top: Int, right: Int, bottom: Int) {
            super.onLayout(changed, left, top, right, bottom)
            val r = state.endRect(right - left, bottom - top)
            end.layout(r[0].toInt(), r[1].toInt(), r[0].toInt() + end.measuredWidth, r[1].toInt() + end.measuredHeight)
        }
    }

    /** Draws [TouchPadState]'s layout and feeds it the fingers; releases on cancel, hide and detach. */
    private class TouchPadView(
        ctx: Context,
        private val state: TouchPadState,
        private val onEvent: () -> Unit,
        private val onOutput: (TouchPadState.Output) -> Unit,
    ) : View(ctx) {
        private val fill = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.FILL }
        private val line = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE; strokeWidth = 4f }
        private val label = Paint(Paint.ANTI_ALIAS_FLAG).apply { textAlign = Paint.Align.CENTER; color = Color.WHITE }

        override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
            super.onSizeChanged(w, h, oldw, oldh)
            state.layout(w, h)
            onOutput(state.output())
            excludeEdgeGestures()
        }

        /**
         * Design §7: the side-edge back gesture kept off the shoulders, the controls nearest the edges (200 dp per edge
         * at most; the band is the shoulders' press height). A swipe there would otherwise cancel a held L2 / R2.
         */
        private fun excludeEdgeGestures() {
            if (Build.VERSION.SDK_INT < 29) return
            val maxPx = (200 * resources.displayMetrics.density).toInt()
            val rects = state.drawn().filter {
                it.control == TouchPadState.Control.L2 || it.control == TouchPadState.Control.L1 ||
                    it.control == TouchPadState.Control.R1 || it.control == TouchPadState.Control.R2
            }.map { d ->
                val half = minOf(d.hitHalfH.toInt(), maxPx / 2)
                Rect((d.cx - d.hitHalfW).toInt(), d.cy.toInt() - half, (d.cx + d.hitHalfW).toInt(), d.cy.toInt() + half)
            }
            systemGestureExclusionRects = rects
        }

        override fun onDraw(canvas: Canvas) {
            super.onDraw(canvas)
            val alpha = if (TOUCH_LIVE) 255 else 110
            val held = state.heldControls()
            for (d in state.drawn()) {
                val on = d.control in held
                fill.color = if (on) 0xFF5A5A5A.toInt() else 0xFF2A2A2A.toInt(); fill.alpha = alpha
                line.color = 0xFF888888.toInt(); line.alpha = alpha
                label.alpha = alpha
                if (d.halfH == 0f) {
                    canvas.drawCircle(d.cx, d.cy, d.halfW, fill)
                    canvas.drawCircle(d.cx, d.cy, d.halfW, line)
                    when (d.control) {
                        TouchPadState.Control.DPAD -> {
                            canvas.drawLine(d.cx - d.halfW, d.cy, d.cx + d.halfW, d.cy, line)
                            canvas.drawLine(d.cx, d.cy - d.halfW, d.cx, d.cy + d.halfW, line)
                        }
                        TouchPadState.Control.LSTICK, TouchPadState.Control.RSTICK -> {
                            // the knob at the deflection (absolute: the base never moves)
                            val (x, y) = state.stickDeflection(d.control)
                            fill.color = 0xFF777777.toInt(); fill.alpha = alpha
                            canvas.drawCircle(d.cx + x * d.halfW, d.cy - y * d.halfW, d.halfW * 0.45f, fill)
                        }
                        else -> {}
                    }
                    label.textSize = d.halfW * 0.8f
                } else {
                    canvas.drawRoundRect(d.cx - d.halfW, d.cy - d.halfH, d.cx + d.halfW, d.cy + d.halfH, 16f, 16f, fill)
                    canvas.drawRoundRect(d.cx - d.halfW, d.cy - d.halfH, d.cx + d.halfW, d.cy + d.halfH, 16f, 16f, line)
                    label.textSize = minOf(d.halfH, d.halfW) * 0.8f
                }
                val text = labelOf(d.control)
                if (text.isNotEmpty()) canvas.drawText(text, d.cx, d.cy + label.textSize / 3f, label)
            }
        }

        private fun labelOf(c: TouchPadState.Control): String = when (c) {
            TouchPadState.Control.DPAD, TouchPadState.Control.LSTICK, TouchPadState.Control.RSTICK -> ""
            TouchPadState.Control.TRIANGLE -> glyph("△", "T")
            TouchPadState.Control.CIRCLE -> glyph("○", "O")
            TouchPadState.Control.CROSS -> glyph("✕", "X")
            TouchPadState.Control.SQUARE -> glyph("□", "S")
            TouchPadState.Control.SELECT -> "SELECT"
            TouchPadState.Control.START -> "START"
            else -> c.name
        }

        private fun glyph(g: String, fallback: String): String = if (label.hasGlyph(g)) g else fallback

        override fun onTouchEvent(event: MotionEvent): Boolean {
            onEvent()
            val i = event.actionIndex
            val out = when (event.actionMasked) {
                MotionEvent.ACTION_DOWN, MotionEvent.ACTION_POINTER_DOWN ->
                    state.down(event.getPointerId(i), event.getX(i), event.getY(i))
                MotionEvent.ACTION_MOVE -> {
                    for (p in 0 until event.pointerCount) state.move(event.getPointerId(p), event.getX(p), event.getY(p))
                    state.output()
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_POINTER_UP -> state.up(event.getPointerId(i))
                MotionEvent.ACTION_CANCEL -> state.cancel()
                else -> state.output()
            }
            onOutput(out)
            invalidate()
            return true
        }

        override fun onVisibilityChanged(changedView: View, visibility: Int) {
            super.onVisibilityChanged(changedView, visibility)
            if (visibility != VISIBLE) onOutput(state.reset())
        }

        override fun onDetachedFromWindow() {
            onOutput(state.reset())
            super.onDetachedFromWindow()
        }
    }
}
