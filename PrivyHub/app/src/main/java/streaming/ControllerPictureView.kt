package com.safeiot.privyhub.streaming

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.view.View

/**
 * B86: a small controller picture drawn by the app itself — a plain, original outline (a body with two grips, a cross
 * for the D-pad, four round face buttons, two round sticks, shoulders and triggers, Select / Start); no brand marks.
 * Each control is labelled with what it sends to the game now ([MappingPicture.pictureLabels]); changed ones in an
 * accent colour. Only drawing: the mapping is read, never written.
 */
class ControllerPictureView(context: Context) : View(context) {
    private var labels: Map<String, String> = emptyMap()
    private var changed: Set<String> = emptySet()
    private val line = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE; strokeWidth = 3f; color = Color.LTGRAY }
    private val text = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE; textAlign = Paint.Align.CENTER }
    private val accent = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFC107.toInt(); textAlign = Paint.Align.CENTER }

    fun show(mapping: Map<String, String>, default: Map<String, String>) {
        labels = MappingPicture.pictureLabels(mapping)
        changed = MappingPicture.changed(mapping, default)
        invalidate()
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val w = MeasureSpec.getSize(widthMeasureSpec)
        setMeasuredDimension(w, (w * 0.5f).toInt())
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val w = width.toFloat()
        val h = height.toFloat()
        if (w <= 0f || h <= 0f) return
        fun px(x: Float) = x * w
        fun py(y: Float) = y * h
        // the outline: a rounded body and two grips; shoulders and triggers as small rounded tabs
        canvas.drawRoundRect(RectF(px(0.08f), py(0.24f), px(0.92f), py(0.80f)), h * 0.18f, h * 0.18f, line)
        canvas.drawRoundRect(RectF(px(0.08f), py(0.50f), px(0.30f), py(0.98f)), h * 0.14f, h * 0.14f, line)
        canvas.drawRoundRect(RectF(px(0.70f), py(0.50f), px(0.92f), py(0.98f)), h * 0.14f, h * 0.14f, line)
        for (x in listOf(0.18f, 0.82f)) {
            canvas.drawRoundRect(RectF(px(x - 0.08f), py(0.00f), px(x + 0.08f), py(0.10f)), 8f, 8f, line)
            canvas.drawRoundRect(RectF(px(x - 0.09f), py(0.11f), px(x + 0.09f), py(0.20f)), 8f, 8f, line)
        }
        // the D-pad as a cross, the face buttons and the sticks as circles
        val arm = w * 0.035f
        canvas.drawRect(px(0.22f) - arm, py(0.28f), px(0.22f) + arm, py(0.58f), line)
        canvas.drawRect(px(0.10f), py(0.43f) - arm, px(0.34f), py(0.43f) + arm, line)
        for (key in listOf("x", "y", "a", "b")) {
            val (x, y) = MappingPicture.LAYOUT.getValue(key)
            canvas.drawCircle(px(x), py(y), h * 0.075f, line)
        }
        for (key in listOf("l3", "r3")) {
            val (x, y) = MappingPicture.LAYOUT.getValue(key)
            canvas.drawCircle(px(x), py(y), h * 0.13f, line)
        }
        // the labels: what each control sends now
        val size = (h * 0.065f).coerceAtLeast(12f)
        text.textSize = size
        accent.textSize = size
        for ((key, pos) in MappingPicture.LAYOUT) {
            val label = labels[key] ?: continue
            if (key.contains("stick") && key !in changed) continue      // stick directions: only when changed
            canvas.drawText(label, px(pos.first), py(pos.second) + size / 3f, if (key in changed) accent else text)
        }
    }
}
