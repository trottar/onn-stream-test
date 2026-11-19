package com.safeiot.privyhub.streaming

import android.content.Context
import android.content.pm.ActivityInfo
import android.graphics.Canvas
import android.graphics.Color
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
import org.json.JSONObject
import java.util.concurrent.atomic.AtomicLong

/**
 * G6-HM3: the tablet's portrait handheld mode (design `docs/memory/evidence/g6_hm1_2026-11-19/`, hashed before code,
 * with the user's answers). The game's picture in a W x W·9/16 box at the top (every overlay inside it, unchanged);
 * the touch pad below. Launched only when the user picks "Handheld" in Settings on a device with a touchscreen; the
 * onn's NativeStreamActivity entry and paths are unchanged.
 *
 * - Q5 (c): Back does nothing in a game (a key or an edge swipe); the **End** button ends to the paused picture.
 * - Q1 (c): when a real pad is P1, the lower region shows a status panel instead of the touch pad.
 * - [TOUCH_LIVE] false (G6-HM3): the pad is drawn and counts touches but takes no slot and writes nothing. G6-HM4 sets
 *   it true: D2's 5-s rule (Q3 (b)/(i)), the countdown (Q4 (b)), the 2-s takeover (Q2 (d)), the writes.
 */
class HandheldStreamActivity : NativeStreamActivity() {

    companion object {
        const val TOUCH_LIVE = false
        private const val TICK_MS = 100L
        private const val TEXT_PREVIEW = "Touch buttons: coming in the next update"
    }

    private val ui = Handler(Looper.getMainLooper())
    private val pad = TouchPadState()
    private val p1Rule = TouchP1Rule()
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
    @Volatile private var navMode = -1
    @Volatile private var density = 0f

    override val streamOrientation: Int get() = ActivityInfo.SCREEN_ORIENTATION_PORTRAIT

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        density = resources.displayMetrics.density
        navMode = try { Settings.Secure.getInt(contentResolver, "navigation_mode", -1) } catch (_: Exception) { -1 }
        ui.post(tick)
    }

    override fun wrapStreamLayer(streamLayer: FrameLayout): View {
        val area = FrameLayout(this).apply { setBackgroundColor(Color.BLACK) }
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
        // Q5 (c): the only way out of a game here (Back does nothing)
        Button(this).apply {
            text = "End"
            isAllCaps = false
            minWidth = 0
            minimumWidth = 0
            setOnClickListener { endPresses.incrementAndGet(); endToPausedFrame() }
        }.also {
            area.addView(it, FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT)
                .apply { gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL; topMargin = 8 })
        }
        return HandheldLayout(this, streamLayer, area).also { frame = it }
    }

    // B70: the touchscreen only, in this activity only; mice, touchpads and a pad's touchpad stay consumed
    override fun exemptFromPointerGuard(event: MotionEvent): Boolean =
        HandheldInput.isTouchscreen(event.source).also { if (it) exempted.incrementAndGet() }

    // design §5 / hook H4: the touch pad is "present" (only once it can hold a slot)
    override fun connectedPadDevices(): List<PadDevice> =
        if (TOUCH_LIVE) super.connectedPadDevices() + TouchPadDevice else super.connectedPadDevices()

    override fun onPlayersOpened(selfRestart: Boolean) {
        ui.post { p1Rule.onStart(selfRestart); takeover.clear() }
    }

    override fun onGameplayReleased() {
        p1Rule.onGameplayReleased(nowMs())
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
        report.put("handheld", JSONObject()
            .put("mode", "portrait")
            .put("touch_live", TOUCH_LIVE)
            .put("video_box", "${w}x${HandheldGeometry.videoBoxHeight(w)}")
            .put("pad_region", "${w}x${HandheldGeometry.padRegionHeight(w, h)}")
            .put("density", density.toDouble())
            .put("nav_mode", navMode)
            .put("sdk", Build.VERSION.SDK_INT)
            .put("touch_events", touchEvents.get())
            .put("touch_writes", touchWrites.get())
            .put("touch_slot", streamSlots?.slotOf(TouchPadDevice) ?: -1)
            .put("pointer_exempted_events", exempted.get())
            .put("back_swallowed", backSwallowed.get())
            .put("end_presses", endPresses.get()))
    }

    private fun nowMs() = System.nanoTime() / 1_000_000L

    private fun resetPad() {
        onPadOutput(pad.reset())
        padView?.invalidate()
    }

    /** The touch pad's fields into its own slot (none = nothing; before the release = neutral). */
    private fun onPadOutput(out: TouchPadState.Output) {
        if (!TOUCH_LIVE) return
        val sender = streamSender ?: return
        val slot = streamSlots?.slotOf(TouchPadDevice) ?: return
        val o = if (gameplayLive) out else TouchPadState.Output()
        if (sender.writePlayerState(slot, o.buttons, o.lx, o.ly, o.rx, o.ry, o.lt, o.rt)) touchWrites.incrementAndGet()
    }

    private val tick = object : Runnable {
        override fun run() {
            val now = nowMs()
            val slots = streamSlots
            val p1 = slots?.holderOf(0)
            val realP1 = p1 != null && p1 != TouchPadDevice.KEY
            if (TOUCH_LIVE) {
                val prompt = streamPrompt
                if (p1Rule.tick(now, realP1) == TouchP1Rule.Action.JOIN_P1) {
                    prompt?.joinAsP1WithoutHold(TouchPadDevice, now, connectedPadDevices())
                }
                takeover.due(now, p1 == TouchPadDevice.KEY)?.let { real ->
                    streamSender?.writePlayerState(0, 0, 0, 0, 0, 0, 0, 0)
                    pad.reset()
                    prompt?.takeOverP1(real, TouchPadDevice.KEY, now)
                }
                onPadOutput(pad.output())
            }
            // Q1 (c): a real pad as P1 -> the status panel instead of the pad
            padView?.let { v ->
                val want = if (realP1) View.GONE else View.VISIBLE
                if (v.visibility != want) v.visibility = want
            }
            panel?.let { t ->
                t.visibility = if (realP1) View.VISIBLE else View.GONE
                if (realP1) t.text = panelText(slots)
            }
            hint?.let { t ->
                t.visibility = if (realP1) View.GONE else View.VISIBLE
                t.text = if (!TOUCH_LIVE) TEXT_PREVIEW else p1Rule.secondsLeft(now)?.let { "Touch buttons: P1 in $it…" } ?: ""
            }
            ui.postDelayed(this, TICK_MS)
        }
    }

    private fun panelText(slots: PadSlots?): String {
        val joined = slots?.map().orEmpty().joinToString("   ") { "P${it.slot + 1}" }
        return "Players joined: $joined\n\nA controller is Player 1,\nso the touch buttons are off."
    }

    /** The video box on top (W x W·9/16, from the measured width), the pad region below. */
    private class HandheldLayout(ctx: Context, private val video: View, private val area: View) : ViewGroup(ctx) {
        init {
            addView(video)
            addView(area)
        }

        override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
            val w = MeasureSpec.getSize(widthMeasureSpec)
            val h = MeasureSpec.getSize(heightMeasureSpec)
            video.measure(MeasureSpec.makeMeasureSpec(w, MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec(HandheldGeometry.videoBoxHeight(w), MeasureSpec.EXACTLY))
            area.measure(MeasureSpec.makeMeasureSpec(w, MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec(HandheldGeometry.padRegionHeight(w, h), MeasureSpec.EXACTLY))
            setMeasuredDimension(w, h)
        }

        override fun onLayout(changed: Boolean, l: Int, t: Int, r: Int, b: Int) {
            val w = r - l
            val box = HandheldGeometry.videoBoxHeight(w)
            video.layout(0, 0, w, box)
            area.layout(0, box, w, b - t)
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

        /** Design §7: the D-pad's and the face buttons' bands kept from the side-edge gestures (200 dp per edge). */
        private fun excludeEdgeGestures() {
            if (Build.VERSION.SDK_INT < 29) return
            val maxPx = (200 * resources.displayMetrics.density).toInt()
            val rects = state.drawn().filter { it.control == TouchPadState.Control.DPAD || it.control == TouchPadState.Control.CIRCLE }
                .map { d ->
                    val half = minOf((d.halfW * TouchPadState.DPAD_HIT).toInt(), maxPx / 2)
                    if (d.control == TouchPadState.Control.DPAD) Rect(0, d.cy.toInt() - half, (d.cx + d.halfW).toInt(), d.cy.toInt() + half)
                    else Rect((d.cx - d.halfW).toInt(), d.cy.toInt() - half, width, d.cy.toInt() + half)
                }
            systemGestureExclusionRects = rects
        }

        override fun onDraw(canvas: Canvas) {
            super.onDraw(canvas)
            val alpha = if (TOUCH_LIVE) 255 else 110
            for (d in state.drawn()) {
                fill.color = 0xFF2A2A2A.toInt(); fill.alpha = alpha
                line.color = 0xFF888888.toInt(); line.alpha = alpha
                label.alpha = alpha
                if (d.halfH == 0f) {
                    canvas.drawCircle(d.cx, d.cy, d.halfW, fill)
                    canvas.drawCircle(d.cx, d.cy, d.halfW, line)
                    if (d.control == TouchPadState.Control.DPAD) {
                        canvas.drawLine(d.cx - d.halfW, d.cy, d.cx + d.halfW, d.cy, line)
                        canvas.drawLine(d.cx, d.cy - d.halfW, d.cx, d.cy + d.halfW, line)
                    }
                    label.textSize = d.halfW * 0.8f
                } else {
                    canvas.drawRoundRect(d.cx - d.halfW, d.cy - d.halfH, d.cx + d.halfW, d.cy + d.halfH, 16f, 16f, fill)
                    canvas.drawRoundRect(d.cx - d.halfW, d.cy - d.halfH, d.cx + d.halfW, d.cy + d.halfH, 16f, 16f, line)
                    label.textSize = d.halfH * 0.9f
                }
                val text = labelOf(d.control)
                if (text.isNotEmpty()) canvas.drawText(text, d.cx, d.cy + label.textSize / 3f, label)
            }
        }

        private fun labelOf(c: TouchPadState.Control): String = when (c) {
            TouchPadState.Control.DPAD -> ""
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
