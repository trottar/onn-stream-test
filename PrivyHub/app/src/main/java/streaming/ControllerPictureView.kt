package com.safeiot.privyhub.streaming

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.view.View

/**
 * B86 / B89: a small controller picture drawn by the app itself from [MappingPicture]'s one geometry — a plain,
 * original gamepad outline (one path: a body with two grips), shoulders and triggers above, a D-pad left, four face
 * buttons right, two sticks, Select / Start; one stroke width; no brand marks. Each control's label is fitted inside its
 * box ([MappingPicture.BOXES]); the changed ones in an accent colour. At most a fifth of the screen's height
 * ([MappingPicture.pictureSize]). Only drawing: the mapping is read, never written.
 */
class ControllerPictureView(context: Context) : View(context) {
    private var labels: Map<String, String> = emptyMap()
    private var changed: Set<String> = emptySet()
    private val line = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE; color = Color.LTGRAY; strokeJoin = Paint.Join.ROUND
    }
    private val text = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE; textAlign = Paint.Align.CENTER }
    private val accent = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFC107.toInt(); textAlign = Paint.Align.CENTER }

    private var mapping: Map<String, String> = emptyMap()
    private var default: Map<String, String> = emptyMap()
    /** B91: beside the rows, labels at this text size in px (null = B89's picture above the rows). */
    private var besideTextPx: Float? = null
    private val leader = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE; color = Color.LTGRAY }

    fun show(mapping: Map<String, String>, default: Map<String, String>) {
        labels = MappingPicture.shortLabels(mapping)
        changed = MappingPicture.changed(mapping, default)
        this.mapping = mapping
        this.default = default
        invalidate()
    }

    /** B91: draw beside the rows ([MappingEditorLayout]): the controller scaled to fill the pane, every label at
     *  `labelTextPx` (the rows' text size), placed without overlap ([MappingPicture.placeLabels]). */
    fun beside(labelTextPx: Float) {
        besideTextPx = labelTextPx
        requestLayout()
        invalidate()
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        if (besideTextPx != null) {
            var w = MeasureSpec.getSize(widthMeasureSpec)
            val hSpec = MeasureSpec.getMode(heightMeasureSpec)
            val hMax = MeasureSpec.getSize(heightMeasureSpec)
            if (hSpec != MeasureSpec.UNSPECIFIED && MappingPicture.besideHeight(w) > hMax)
                w = (hMax / MappingPicture.BESIDE_ASPECT).toInt()
            setMeasuredDimension(w, MappingPicture.besideHeight(w))
            return
        }
        val (w, h) = MappingPicture.pictureSize(MeasureSpec.getSize(widthMeasureSpec), resources.displayMetrics.heightPixels)
        setMeasuredDimension(w, h)
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        besideTextPx?.let { drawBeside(canvas, it); return }
        val k = width.toFloat()
        if (k <= 0f) return
        line.strokeWidth = MappingPicture.STROKE * k
        for (s in MappingPicture.SHAPES) when (s) {
            is MappingPicture.Shape.Outline -> canvas.drawPath(polygon(s.points, k), line)
            is MappingPicture.Shape.RoundRect ->
                canvas.drawRoundRect(RectF(s.x * k, s.y * k, (s.x + s.w) * k, (s.y + s.h) * k), s.r * k, s.r * k, line)
            is MappingPicture.Shape.Circle -> canvas.drawCircle(s.cx * k, s.cy * k, s.r * k, line)
            is MappingPicture.Shape.Cross -> canvas.drawPath(polygon(MappingPicture.crossPath(s), k), line)
        }
        for (box in MappingPicture.BOXES) {
            val label = labels[box.id] ?: continue
            if (box.id.contains("stick") && box.id !in changed) continue      // stick directions: only when changed
            val paint = if (box.id in changed) accent else text
            paint.textSize = box.h * k * 0.85f
            while (paint.textSize > 6f && paint.measureText(label) > box.w * k) paint.textSize *= 0.9f
            val fm = paint.fontMetrics
            canvas.drawText(label, box.cx * k, box.cy * k - (fm.ascent + fm.descent) / 2f, paint)
        }
    }

    private fun drawBeside(canvas: Canvas, textPx: Float) {
        val w = width.toFloat()
        if (w <= 0f) return
        val k = MappingPicture.besideScale(w)
        canvas.save()
        canvas.translate(MappingPicture.besideLeft(w), MappingPicture.besideTop(w))
        line.strokeWidth = MappingPicture.STROKE * k
        for (s in MappingPicture.SHAPES) when (s) {
            is MappingPicture.Shape.Outline -> canvas.drawPath(polygon(s.points, k), line)
            is MappingPicture.Shape.RoundRect ->
                canvas.drawRoundRect(RectF(s.x * k, s.y * k, (s.x + s.w) * k, (s.y + s.h) * k), s.r * k, s.r * k, line)
            is MappingPicture.Shape.Circle -> canvas.drawCircle(s.cx * k, s.cy * k, s.r * k, line)
            is MappingPicture.Shape.Cross -> canvas.drawPath(polygon(MappingPicture.crossPath(s), k), line)
        }
        canvas.restore()
        text.textSize = textPx; accent.textSize = textPx
        leader.strokeWidth = MappingPicture.STROKE * k * 0.6f
        for (p in MappingPicture.placeLabels(w, height.toFloat(), textPx, mapping, default) { text.measureText(it) }) {
            val paint = if (p.changed) accent else text
            if (p.leader) {
                val (ex, ey) = MappingPicture.nearest(p.box, p.ax, p.ay)
                leader.color = paint.color
                canvas.drawLine(p.ax, p.ay, ex, ey, leader)
            }
            val fm = paint.fontMetrics
            canvas.drawText(p.text, p.box.cx, p.box.cy - (fm.ascent + fm.descent) / 2f, paint)
        }
    }

    private fun polygon(points: List<Pair<Float, Float>>, k: Float): Path = Path().apply {
        points.forEachIndexed { i, (x, y) -> if (i == 0) moveTo(x * k, y * k) else lineTo(x * k, y * k) }
        close()
    }
}
