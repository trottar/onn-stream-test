package com.safeiot.privyhub.vod

import android.app.Activity
import android.graphics.Color
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.view.Gravity
import android.widget.FrameLayout
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.media3.common.PlaybackException
import androidx.media3.datasource.HttpDataSource
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import com.safeiot.privyhub.identity.PrivyHubIdentity
import org.json.JSONObject
import java.net.ConnectException
import java.net.HttpURLConnection
import java.net.SocketTimeoutException
import java.net.URL
import kotlin.concurrent.thread

/**
 * B35: the Android side of [VodRetryController] -- the main-thread scheduler, the "reconnecting…" mark on the
 * player's overlay, the Retry dialog, and the rows posted to the hub (`POST /diagnostics/vod-client`, JSON, the
 * session header as every control call; every failure ignored). Built by MainActivity only when
 * `debug.privyhub.vod_retry=1` and the playback is not live.
 *
 * B43: the error's reason read from its cause chain; the media token refetched through the identity session (drop
 * the cached token, set up afresh -- the path a playback's first media request takes) off the main thread; the
 * give-up dialog's message by its kind (`lost` only when the hub gave no answer).
 */
class VodRetryAndroid(
    private val activity: Activity,
    private val playerView: PlayerView,
    sourceId: String,
    private val rowsUrl: () -> String,
    private val currentPlayer: () -> ExoPlayer?,
    // B43: the hub host the media token is for (MainActivity's getCompanionHost)
    private val hubHost: () -> String,
) {
    private val handler = Handler(Looper.getMainLooper())
    private var pending: Runnable? = null
    private var mark: TextView? = null

    private val controller = VodRetryController(
        policy = VodRetryPolicy(),
        player = object : VodRetryController.Player {
            override fun retryAt(positionMs: Long) {
                val p = currentPlayer() ?: return
                p.seekTo(positionMs)
                p.prepare()
                p.playWhenReady = true
            }
        },
        scheduler = object : VodRetryController.Scheduler {
            override fun schedule(delayMs: Long, task: () -> Unit) {
                val r = Runnable {
                    pending = null
                    task()
                }
                pending = r
                handler.postDelayed(r, delayMs)
            }

            override fun cancel() {
                pending?.let { handler.removeCallbacks(it) }
                pending = null
            }
        },
        clock = { SystemClock.elapsedRealtime() },
        rows = { post(it) },
        ui = object : VodRetryController.Ui {
            override fun showMark(attempt: Int) = show()
            override fun hideMark() = hide()
            override fun offerRetry() = dialog(VodRetryController.KIND_LOST)
            override fun offerRetry(kind: String) = dialog(kind)
        },
        sourceId = sourceId,
        token = object : VodRetryController.Token {
            override fun refresh(done: (Boolean) -> Unit) {
                thread(start = true, isDaemon = true, name = "PrivyHub-VodRetry-Token") {
                    val ok = try {
                        if (!PrivyHubIdentity.isEnabled(activity)) {
                            false
                        } else {
                            val session = PrivyHubIdentity.get(activity)
                            session.endSessionLocally()
                            session.mediaHeaderFor(hubHost().trim()) != null
                        }
                    } catch (_: Throwable) {
                        false
                    }
                    handler.post { done(ok) }
                }
            }
        },
    )

    fun onError(error: PlaybackException, positionMs: Long): Boolean =
        controller.onError(error.errorCode, error.errorCodeName, positionMs, reasonOf(error))

    /** B43: 401 / 403 from the HTTP status; `refused` / `timeout` from the cause chain; else `reset`. */
    private fun reasonOf(error: PlaybackException): String {
        var status: Int? = null
        var refused = false
        var timedOut = false
        var t: Throwable? = error
        var depth = 0
        while (t != null && depth < 12) {
            when (t) {
                is HttpDataSource.InvalidResponseCodeException -> status = status ?: t.responseCode
                is ConnectException -> refused = true
                is SocketTimeoutException -> timedOut = true
            }
            t = t.cause
            depth++
        }
        return VodRetryPolicy.reasonOf(error.errorCode, status, refused, timedOut)
    }

    fun afterTodaysError() = controller.afterTodaysError()

    fun onReady() = controller.onReady()

    fun cancel() = controller.cancel()

    private fun show() {
        if (mark != null) {
            return
        }
        val frame = playerView.overlayFrameLayout ?: return
        val view = TextView(activity).apply {
            text = "reconnecting…"
            textSize = 14f
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.argb(140, 0, 0, 0))
            setPadding(16, 8, 16, 8)
        }
        frame.addView(
            view,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT,
                Gravity.TOP or Gravity.END
            ).apply { setMargins(0, 24, 24, 0) }
        )
        mark = view
    }

    private fun hide() {
        val view = mark ?: return
        (view.parent as? FrameLayout)?.removeView(view)
        mark = null
    }

    private fun dialog(kind: String) {
        if (activity.isFinishing) {
            return
        }
        AlertDialog.Builder(activity)
            .setTitle("Playback error")
            .setMessage(
                if (kind == VodRetryController.KIND_REFUSED) {
                    "The hub refused this playback. Press Retry or start the movie again."
                } else {
                    "The connection to the hub was lost."
                }
            )
            .setPositiveButton("Retry") { _, _ -> controller.manualRetry() }
            .setNegativeButton("Close", null)
            .show()
    }

    private fun post(row: Map<String, Any>) {
        val url = try {
            rowsUrl()
        } catch (_: Exception) {
            return
        }
        val body = JSONObject(row).toString().toByteArray(Charsets.UTF_8)
        thread(start = true, isDaemon = true, name = "PrivyHub-VodRetry-Row") {
            try {
                val c = (URL(url).openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    connectTimeout = 1_500
                    readTimeout = 1_500
                    doOutput = true
                    setRequestProperty("Content-Type", "application/json")
                    setFixedLengthStreamingMode(body.size)
                }
                PrivyHubIdentity.decorate(activity, c, url)
                c.outputStream.use { it.write(body) }
                c.responseCode
                c.disconnect()
            } catch (_: Exception) {
                // a diagnostic row must never disturb playback
            }
        }
    }
}
