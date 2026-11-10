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

    fun show(mapping: Map<String, String>, default: Map<String, String>) {
        labels = MappingPicture.shortLabels(mapping)
        changed = MappingPicture.changed(mapping, default)
        invalidate()
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val (w, h) = MappingPicture.pictureSize(MeasureSpec.getSize(widthMeasureSpec), resources.displayMetrics.heightPixels)
        setMeasuredDimension(w, h)
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
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

    private fun polygon(points: List<Pair<Float, Float>>, k: Float): Path = Path().apply {
        points.forEachIndexed { i, (x, y) -> if (i == 0) moveTo(x * k, y * k) else lineTo(x * k, y * k) }
        close()
    }
}
