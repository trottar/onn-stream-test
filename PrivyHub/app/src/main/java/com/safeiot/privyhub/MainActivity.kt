package com.safeiot.privyhub

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.text.InputType
import android.util.Log
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.GridLayout
import android.widget.TextView

import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.OnBackPressedCallback
import androidx.core.content.ContextCompat

import androidx.media3.common.AudioAttributes
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.DefaultLoadControl
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView

import org.json.JSONArray
import org.json.JSONObject

import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors


@UnstableApi
class MainActivity : AppCompatActivity() {

    private var player: ExoPlayer? = null

    private lateinit var playerView: PlayerView

    private lateinit var topControlBar: View
    private lateinit var sourceScroll: View
    private lateinit var sourceGrid: GridLayout
    private lateinit var breadcrumbText: TextView
    private lateinit var statusText: TextView

    private lateinit var backButton: Button
    private lateinit var refreshButton: Button
    private lateinit var settingsButton: Button
    private lateinit var stopButton: Button

    private lateinit var nowPlayingBar: View
    private lateinit var nowPlayingTitle: TextView
    private lateinit var nowPlayingProgress: TextView
    private lateinit var fullScreenButton: Button
    private lateinit var restartButton: Button

    private var isFullscreen =
        false

    private val networkExecutor: ExecutorService =
        Executors.newSingleThreadExecutor()

    private val navigationStack =
        mutableListOf<SourceNode>()

    private var rootNodes:
        List<SourceNode> =
        emptyList()

    private var activeSourceId:
        String? =
        null

    private var currentSourceId:
        String? =
        null

    private var currentSourceName:
        String? =
        null

    private var currentPlayback:
        PlaybackInfo? =
        null

    private val playbackUiHandler =
        Handler(
            Looper.getMainLooper()
        )

    private var playbackUiTicks =
        0


    companion object {

        private const val TAG =
            "PrivyHub"

        private const val PREFS_NAME =
            "privyhub_settings"

        private const val PREF_COMPANION_HOST =
            "companion_host"

        private const val CONTROL_PORT =
            8765

        private const val DEFAULT_MEDIA_PORT =
            8000

        private const val CONTROL_CONNECT_TIMEOUT_MS =
            5_000

        /*
         * The companion owns live-source startup retries,
         * so a source-start request can legitimately take
         * roughly 45 seconds.
         */
        private const val CONTROL_READ_TIMEOUT_MS =
            60_000

        private const val CATALOG_READ_TIMEOUT_MS =
            10_000

        /*
         * A resume prompt is unnecessary for trivial
         * playback positions.
         */
        private const val MIN_RESUME_POSITION_MS =
            30_000L

        private const val CONTINUE_WATCHING_ID =
            "__continue_watching"

        /*
         * Update the Now Playing display every second.
         */
        private const val PLAYBACK_UI_INTERVAL_MS =
            1_000L

        /*
         * Persist VOD progress every ten UI ticks
         * (approximately every ten seconds).
         */
        private const val PROGRESS_SAVE_EVERY_TICKS =
            10
    }


    data class PlaybackInfo(
        val type: String,
        val port: Int,
        val path: String
    )


    data class SourceNode(
        val id: String,
        val name: String,
        val nodeType: String,
        val children: List<SourceNode> = emptyList(),
        val playback: PlaybackInfo? = null
    )


    data class PlaybackProgress(
        val positionMs: Long,
        val durationMs: Long,
        val updatedAtMs: Long,
        val completed: Boolean
    )


    private val playbackUiRunnable =
        object : Runnable {

            override fun run() {

                updateNowPlayingUi()

                playbackUiTicks++


                if (
                    playbackUiTicks >=
                    PROGRESS_SAVE_EVERY_TICKS
                ) {

                    playbackUiTicks =
                        0

                    saveCurrentProgress()
                }


                if (player != null) {

                    playbackUiHandler.postDelayed(
                        this,
                        PLAYBACK_UI_INTERVAL_MS
                    )
                }
            }
        }


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContentView(
            R.layout.activity_main
        )


        playerView =
            findViewById(
                R.id.player_view
            )

        topControlBar =
            findViewById(
                R.id.top_control_bar
            )

        sourceScroll =
            findViewById(
                R.id.source_scroll
            )

        sourceGrid =
            findViewById(
                R.id.source_grid
            )

        breadcrumbText =
            findViewById(
                R.id.breadcrumb_text
            )

        statusText =
            findViewById(
                R.id.status_text
            )

        backButton =
            findViewById(
                R.id.button_back
            )

        refreshButton =
            findViewById(
                R.id.button_refresh
            )

        settingsButton =
            findViewById(
                R.id.button_settings
            )

        stopButton =
            findViewById(
                R.id.button_stop
            )

        nowPlayingBar =
            findViewById(
                R.id.now_playing_bar
            )

        nowPlayingTitle =
            findViewById(
                R.id.now_playing_title
            )

        nowPlayingProgress =
            findViewById(
                R.id.now_playing_progress
            )

        fullScreenButton =
            findViewById(
                R.id.button_fullscreen
            )

        restartButton =
            findViewById(
                R.id.button_restart
            )


        backButton.setOnClickListener {

            navigateBack()
        }


        refreshButton.setOnClickListener {

            loadCatalog()
        }


        settingsButton.setOnClickListener {

            showCompanionSettings()
        }


        stopButton.setOnClickListener {

            stopPlaybackAndRemoteSource()
        }


        fullScreenButton.setOnClickListener {

            setFullscreenMode(
                true
            )
        }


        restartButton.setOnClickListener {

            restartCurrentVod()
        }


        onBackPressedDispatcher.addCallback(
            this,
            object : OnBackPressedCallback(true) {

                override fun handleOnBackPressed() {

                    if (isFullscreen) {

                        setFullscreenMode(
                            false
                        )

                        return
                    }


                    if (
                        navigationStack.isNotEmpty()
                    ) {

                        navigateBack()

                        return
                    }


                    isEnabled =
                        false

                    onBackPressedDispatcher.onBackPressed()
                }
            }
        )


        hideNowPlaying()


        val companionHost =
            getCompanionHost()


        if (companionHost.isBlank()) {

            statusText.text =
                "Set companion host"

            renderEmptyCatalog()

            showCompanionSettings()

        } else {

            loadCatalog()
        }
    }


    /*
     * ----------------------------------------------------------------
     * COMPANION SETTINGS
     * ----------------------------------------------------------------
     */


    private fun getCompanionHost(): String {

        return getSharedPreferences(
            PREFS_NAME,
            MODE_PRIVATE
        ).getString(
            PREF_COMPANION_HOST,
            ""
        ) ?: ""
    }


    private fun saveCompanionHost(
        host: String
    ) {

        getSharedPreferences(
            PREFS_NAME,
            MODE_PRIVATE
        )
            .edit()
            .putString(
                PREF_COMPANION_HOST,
                host
            )
            .apply()
    }


    private fun showCompanionSettings() {

        val input =
            EditText(this)

        input.inputType =
            InputType.TYPE_CLASS_TEXT or
                InputType.TYPE_TEXT_VARIATION_URI

        input.setSingleLine(
            true
        )

        input.setText(
            getCompanionHost()
        )

        input.hint =
            "192.168.x.x"


        val padding =
            dp(24)

        val container =
            androidx.appcompat.widget.LinearLayoutCompat(
                this
            )

        container.orientation =
            androidx.appcompat.widget.LinearLayoutCompat.VERTICAL

        container.setPadding(
            padding,
            padding,
            padding,
            padding
        )

        container.addView(
            input,
            ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        )


        val dialog =
            AlertDialog.Builder(this)
                .setTitle(
                    "Companion Host"
                )
                .setMessage(
                    "Enter the IP address or hostname of the PrivyHub companion."
                )
                .setView(
                    container
                )
                .setPositiveButton(
                    "Save",
                    null
                )
                .setNegativeButton(
                    "Cancel",
                    null
                )
                .create()


        dialog.setOnShowListener {

            dialog.getButton(
                AlertDialog.BUTTON_POSITIVE
            ).setOnClickListener {

                val host =
                    normalizeHost(
                        input.text
                            .toString()
                    )


                if (host.isBlank()) {

                    input.error =
                        "Companion host is required"

                    return@setOnClickListener
                }


                if (
                    host.contains("/") ||
                    host.contains(" ")
                ) {

                    input.error =
                        "Enter only an IP address or hostname"

                    return@setOnClickListener
                }


                saveCompanionHost(
                    host
                )

                dialog.dismiss()


                releasePlayer()

                activeSourceId =
                    null

                navigationStack.clear()

                loadCatalog()
            }
        }


        dialog.show()

        input.requestFocus()
    }


    private fun normalizeHost(
        raw: String
    ): String {

        var host =
            raw.trim()


        if (
            host.startsWith(
                "http://",
                ignoreCase = true
            )
        ) {

            host =
                host.substring(7)
        }


        if (
            host.startsWith(
                "https://",
                ignoreCase = true
            )
        ) {

            host =
                host.substring(8)
        }


        return host
            .trim()
            .trimEnd('/')
    }


    /*
     * ----------------------------------------------------------------
     * SOURCE CATALOG
     * ----------------------------------------------------------------
     */


    private fun loadCatalog() {

        val host =
            getCompanionHost()


        if (host.isBlank()) {

            statusText.text =
                "Set companion host"

            renderEmptyCatalog()

            return
        }


        statusText.text =
            "Loading sources..."


        networkExecutor.execute {

            try {

                val catalogJson =
                    httpGet(
                        "http://$host:$CONTROL_PORT/sources"
                    )


                val nodes =
                    parseCatalog(
                        catalogJson
                    )


                runOnUiThread {

                    rootNodes =
                        nodes

                    navigationStack.clear()

                    statusText.text =
                        "Connected: $host"

                    renderCurrentPage()
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to load source catalog",
                    error
                )


                runOnUiThread {

                    rootNodes =
                        emptyList()

                    navigationStack.clear()

                    statusText.text =
                        "Companion unavailable"

                    renderEmptyCatalog()
                }
            }
        }
    }


    private fun parseCatalog(
        jsonText: String
    ): List<SourceNode> {

        val root =
            JSONObject(
                jsonText
            )


        val rootArray =
            root.getJSONArray(
                "root"
            )


        return parseNodeArray(
            rootArray
        )
    }


    private fun parseNodeArray(
        array: JSONArray
    ): List<SourceNode> {

        val result =
            mutableListOf<SourceNode>()


        for (
            index in 0 until array.length()
        ) {

            result.add(
                parseNode(
                    array.getJSONObject(
                        index
                    )
                )
            )
        }


        return result
    }


    private fun parseNode(
        json: JSONObject
    ): SourceNode {

        val id =
            json.getString(
                "id"
            )

        val name =
            json.optString(
                "name",
                id
            )

        val nodeType =
            json.getString(
                "node_type"
            )


        return when (
            nodeType
        ) {

            "category" -> {

                val children =
                    parseNodeArray(
                        json.getJSONArray(
                            "children"
                        )
                    )


                SourceNode(
                    id = id,
                    name = name,
                    nodeType = nodeType,
                    children = children
                )
            }


            "source" -> {

                val playbackJson =
                    json.getJSONObject(
                        "playback"
                    )


                val playback =
                    PlaybackInfo(
                        type =
                            playbackJson.getString(
                                "type"
                            ),
                        port =
                            playbackJson.optInt(
                                "port",
                                DEFAULT_MEDIA_PORT
                            ),
                        path =
                            playbackJson.getString(
                                "path"
                            )
                    )


                SourceNode(
                    id = id,
                    name = name,
                    nodeType = nodeType,
                    playback = playback
                )
            }


            else -> {

                throw IllegalArgumentException(
                    "Unsupported node type: $nodeType"
                )
            }
        }
    }


    /*
     * ----------------------------------------------------------------
     * NESTED NAVIGATION
     * ----------------------------------------------------------------
     */


    private fun renderCurrentPage() {

        sourceGrid.removeAllViews()


        val nodes =
            sortNodesForDisplay(
                if (
                    navigationStack.isEmpty()
                ) {

                    buildRootNodesForDisplay()

                } else {

                    navigationStack
                        .last()
                        .children
                }
            )


        breadcrumbText.text =
            buildBreadcrumb()


        backButton.isEnabled =
            navigationStack.isNotEmpty()


        if (nodes.isEmpty()) {

            renderEmptyCatalog()

            return
        }


        var firstButton:
            Button? =
            null


        for (node in nodes) {

            val button =
                createSourceButton(
                    node
                )


            if (firstButton == null) {

                firstButton =
                    button
            }


            sourceGrid.addView(
                button
            )
        }


        sourceGrid.post {

            firstButton?.requestFocus()
        }
    }


    private fun sortNodesForDisplay(
        nodes: List<SourceNode>
    ): List<SourceNode> {

        return nodes.sortedWith(
            compareBy<SourceNode> { node ->

                /*
                 * Continue Watching is a synthetic root category and
                 * remains pinned ahead of normal catalog entries.
                 */
                when {

                    node.id ==
                        CONTINUE_WATCHING_ID ->
                        0

                    node.nodeType ==
                        "category" ->
                        1

                    else ->
                        2
                }
            }.thenBy { node ->

                node.name.lowercase()
            }
        )
    }


    private fun buildRootNodesForDisplay():
        List<SourceNode> {

        val continueWatching =
            collectContinueWatching(
                rootNodes
            )


        if (
            continueWatching.isEmpty()
        ) {

            return rootNodes
        }


        val continueCategory =
            SourceNode(
                id =
                    CONTINUE_WATCHING_ID,
                name =
                    "Continue Watching",
                nodeType =
                    "category",
                children =
                    continueWatching
            )


        return listOf(
            continueCategory
        ) + rootNodes
    }


    private fun collectContinueWatching(
        nodes: List<SourceNode>
    ): List<SourceNode> {

        val candidates =
            mutableListOf<
                Pair<
                    SourceNode,
                    PlaybackProgress
                >
            >()


        fun walk(
            currentNodes: List<SourceNode>
        ) {

            for (
                node in currentNodes
            ) {

                if (
                    node.nodeType ==
                    "category"
                ) {

                    walk(
                        node.children
                    )

                    continue
                }


                val playback =
                    node.playback
                        ?: continue


                if (
                    playback.type !=
                    "vod"
                ) {

                    continue
                }


                val progress =
                    loadProgress(
                        node.id
                    )
                        ?: continue


                if (
                    progress.completed ||
                    progress.positionMs <
                    MIN_RESUME_POSITION_MS
                ) {

                    continue
                }


                candidates.add(
                    node to progress
                )
            }
        }


        walk(
            nodes
        )


        return candidates
            .sortedByDescending {
                it.second.updatedAtMs
            }
            .map {
                it.first
            }
    }


    private fun renderEmptyCatalog() {

        sourceGrid.removeAllViews()

        breadcrumbText.text =
            "PrivyHub"

        backButton.isEnabled =
            false
    }


    private fun buildBreadcrumb(): String {

        if (
            navigationStack.isEmpty()
        ) {

            return "PrivyHub"
        }


        val names =
            mutableListOf(
                "PrivyHub"
            )


        names.addAll(
            navigationStack.map {
                it.name
            }
        )


        return names.joinToString(
            "  >  "
        )
    }


    private fun navigateBack() {

        if (
            navigationStack.isEmpty()
        ) {

            return
        }


        navigationStack.removeAt(
            navigationStack.lastIndex
        )


        renderCurrentPage()
    }


    private fun createSourceButton(
        node: SourceNode
    ): Button {

        val button =
            Button(this)


        val isContinueWatchingSource =
            node.nodeType ==
                "source" &&
                navigationStack
                    .lastOrNull()
                    ?.id ==
                    CONTINUE_WATCHING_ID


        button.text =
            when {

                node.nodeType ==
                    "category" -> {

                    "${node.name}  >"
                }


                isContinueWatchingSource -> {

                    val progress =
                        loadProgress(
                            node.id
                        )


                    if (progress != null) {

                        "${node.name}\nResume ${formatTime(progress.positionMs)}"

                    } else {

                        node.name
                    }
                }


                else -> {

                    node.name
                }
            }


        button.textSize =
            if (isContinueWatchingSource) {

                16f

            } else {

                18f
            }


        /*
         * Category labels remain visually distinct, while media titles keep
         * their natural capitalization.
         */
        button.isAllCaps =
            node.nodeType ==
                "category"


        button.maxLines =
            if (isContinueWatchingSource) {

                2

            } else {

                3
            }

        button.isFocusable =
            true


        button.setTextColor(
            ContextCompat.getColorStateList(
                this,
                R.color.mode_button_text
            )
        )


        button.setBackgroundResource(
            R.drawable.mode_button_background
        )


        button.isSelected =
            node.nodeType == "source" &&
                node.id == activeSourceId


        val layoutParams =
            GridLayout.LayoutParams()


        layoutParams.width =
            dp(240)

        layoutParams.height =
            dp(
                if (isContinueWatchingSource) {

                    86

                } else {

                    72
                }
            )


        val margin =
            dp(10)


        layoutParams.setMargins(
            margin,
            margin,
            margin,
            margin
        )


        button.layoutParams =
            layoutParams


        button.setOnClickListener {

            when (
                node.nodeType
            ) {

                "category" -> {

                    navigationStack.add(
                        node
                    )

                    renderCurrentPage()
                }


                "source" -> {

                    startSource(
                        node
                    )
                }
            }
        }


        return button
    }


    /*
     * ----------------------------------------------------------------
     * SOURCE CONTROL
     * ----------------------------------------------------------------
     */


    private fun startSource(
        node: SourceNode
    ) {

        val host =
            getCompanionHost()


        if (host.isBlank()) {

            showCompanionSettings()

            return
        }


        releasePlayer()


        statusText.text =
            "Starting ${node.name}..."


        networkExecutor.execute {

            try {

                val response =
                    httpPost(
                        "http://$host:$CONTROL_PORT" +
                            "/sources/${node.id}/start"
                    )


                val playback =
                    parseStartedSourcePlayback(
                        response
                    )


                val mediaUrl =
                    "http://$host:" +
                        "${playback.port}" +
                        playback.path


                runOnUiThread {

                    handleReadySource(
                        node = node,
                        playback = playback,
                        mediaUrl = mediaUrl
                    )
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to start source ${node.id}",
                    error
                )


                runOnUiThread {

                    statusText.text =
                        "Failed: ${node.name}"
                }
            }
        }
    }


    private fun handleReadySource(
        node: SourceNode,
        playback: PlaybackInfo,
        mediaUrl: String
    ) {

        if (
            playback.type !=
            "vod"
        ) {

            beginPlayback(
                node = node,
                playback = playback,
                mediaUrl = mediaUrl,
                startPositionMs = 0L,
                clearSavedProgress = false
            )

            return
        }


        val progress =
            loadProgress(
                node.id
            )


        if (
            progress != null &&
            !progress.completed &&
            progress.positionMs >=
                MIN_RESUME_POSITION_MS
        ) {

            val resumeLabel =
                formatTime(
                    progress.positionMs
                )


            val dialog =
                AlertDialog.Builder(this)
                    .setTitle(
                        node.name
                    )
                    .setMessage(
                        "Resume from $resumeLabel?"
                    )
                    .setPositiveButton(
                        "Resume"
                    ) { _, _ ->

                        beginPlayback(
                            node = node,
                            playback = playback,
                            mediaUrl = mediaUrl,
                            startPositionMs =
                                progress.positionMs,
                            clearSavedProgress =
                                false
                        )
                    }
                    .setNegativeButton(
                        "Start Over"
                    ) { _, _ ->

                        beginPlayback(
                            node = node,
                            playback = playback,
                            mediaUrl = mediaUrl,
                            startPositionMs = 0L,
                            clearSavedProgress =
                                true
                        )
                    }
                    .create()


            dialog.setOnCancelListener {

                statusText.text =
                    "Ready: ${node.name}"
            }


            dialog.show()

            return
        }


        /*
         * Completed media, or a trivial saved position,
         * begins at the start.
         */
        beginPlayback(
            node = node,
            playback = playback,
            mediaUrl = mediaUrl,
            startPositionMs = 0L,
            clearSavedProgress =
                progress?.completed == true
        )
    }


    private fun beginPlayback(
        node: SourceNode,
        playback: PlaybackInfo,
        mediaUrl: String,
        startPositionMs: Long,
        clearSavedProgress: Boolean
    ) {

        if (clearSavedProgress) {

            clearProgress(
                node.id
            )
        }


        activeSourceId =
            node.id


        statusText.text =
            if (
                startPositionMs >
                0L
            ) {

                "Resuming: ${node.name}"

            } else {

                "Playing: ${node.name}"
            }


        renderCurrentPage()


        playMedia(
            sourceId = node.id,
            sourceName = node.name,
            url = mediaUrl,
            playback = playback,
            startPositionMs =
                startPositionMs
        )
    }


    private fun parseStartedSourcePlayback(
        jsonText: String
    ): PlaybackInfo {

        val root =
            JSONObject(
                jsonText
            )


        if (
            !root.optBoolean(
                "ok",
                false
            )
        ) {

            throw IllegalStateException(
                root.optString(
                    "error",
                    "Companion rejected source"
                )
            )
        }


        val source =
            root.getJSONObject(
                "source"
            )


        val playback =
            source.getJSONObject(
                "playback"
            )


        return PlaybackInfo(
            type =
                playback.getString(
                    "type"
                ),
            port =
                playback.optInt(
                    "port",
                    DEFAULT_MEDIA_PORT
                ),
            path =
                playback.getString(
                    "path"
                )
        )
    }


    private fun stopPlaybackAndRemoteSource() {

        releasePlayer()

        activeSourceId =
            null

        renderCurrentPage()

        statusText.text =
            "Stopping..."


        val host =
            getCompanionHost()


        if (host.isBlank()) {

            statusText.text =
                "Stopped"

            return
        }


        networkExecutor.execute {

            try {

                httpPost(
                    "http://$host:$CONTROL_PORT/stop"
                )


                runOnUiThread {

                    statusText.text =
                        "Stopped"
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to stop companion source",
                    error
                )


                runOnUiThread {

                    statusText.text =
                        "Stopped locally; control error"
                }
            }
        }
    }


    /*
     * ----------------------------------------------------------------
     * PLAYBACK PROGRESS
     * ----------------------------------------------------------------
     */


    private fun progressKey(
        sourceId: String,
        field: String
    ): String {

        return "progress.$sourceId.$field"
    }


    private fun loadProgress(
        sourceId: String
    ): PlaybackProgress? {

        val prefs =
            getSharedPreferences(
                PREFS_NAME,
                MODE_PRIVATE
            )


        val positionKey =
            progressKey(
                sourceId,
                "position_ms"
            )


        if (
            !prefs.contains(
                positionKey
            )
        ) {

            return null
        }


        return PlaybackProgress(
            positionMs =
                prefs.getLong(
                    positionKey,
                    0L
                ),
            durationMs =
                prefs.getLong(
                    progressKey(
                        sourceId,
                        "duration_ms"
                    ),
                    0L
                ),
            updatedAtMs =
                prefs.getLong(
                    progressKey(
                        sourceId,
                        "updated_at_ms"
                    ),
                    0L
                ),
            completed =
                prefs.getBoolean(
                    progressKey(
                        sourceId,
                        "completed"
                    ),
                    false
                )
        )
    }


    private fun saveProgress(
        sourceId: String,
        positionMs: Long,
        durationMs: Long,
        completed: Boolean
    ) {

        getSharedPreferences(
            PREFS_NAME,
            MODE_PRIVATE
        )
            .edit()
            .putLong(
                progressKey(
                    sourceId,
                    "position_ms"
                ),
                positionMs
            )
            .putLong(
                progressKey(
                    sourceId,
                    "duration_ms"
                ),
                durationMs
            )
            .putLong(
                progressKey(
                    sourceId,
                    "updated_at_ms"
                ),
                System.currentTimeMillis()
            )
            .putBoolean(
                progressKey(
                    sourceId,
                    "completed"
                ),
                completed
            )
            .apply()
    }


    private fun clearProgress(
        sourceId: String
    ) {

        getSharedPreferences(
            PREFS_NAME,
            MODE_PRIVATE
        )
            .edit()
            .remove(
                progressKey(
                    sourceId,
                    "position_ms"
                )
            )
            .remove(
                progressKey(
                    sourceId,
                    "duration_ms"
                )
            )
            .remove(
                progressKey(
                    sourceId,
                    "updated_at_ms"
                )
            )
            .remove(
                progressKey(
                    sourceId,
                    "completed"
                )
            )
            .apply()
    }


    private fun saveCurrentProgress(
        forceCompleted: Boolean =
            false
    ) {

        val sourceId =
            currentSourceId
                ?: return

        val playback =
            currentPlayback
                ?: return

        if (
            playback.type !=
            "vod"
        ) {

            return
        }


        val exoPlayer =
            player
                ?: return


        val positionMs =
            exoPlayer.currentPosition
                .coerceAtLeast(
                    0L
                )


        val rawDurationMs =
            exoPlayer.duration


        val durationMs =
            if (
                rawDurationMs ==
                C.TIME_UNSET ||
                rawDurationMs <
                0L
            ) {

                0L

            } else {

                rawDurationMs
            }


        val completed =
            forceCompleted ||
                isEffectivelyCompleted(
                    positionMs =
                        positionMs,
                    durationMs =
                        durationMs
                )


        saveProgress(
            sourceId = sourceId,
            positionMs = positionMs,
            durationMs = durationMs,
            completed = completed
        )
    }


    private fun isEffectivelyCompleted(
        positionMs: Long,
        durationMs: Long
    ): Boolean {

        if (
            durationMs <=
            0L
        ) {

            return false
        }


        val remainingMs =
            (
                durationMs -
                positionMs
            ).coerceAtLeast(
                0L
            )


        val twoPercent =
            (
                durationMs *
                0.02
            ).toLong()


        val completionWindowMs =
            minOf(
                120_000L,
                twoPercent.coerceAtLeast(
                    10_000L
                )
            )


        return remainingMs <=
            completionWindowMs
    }


    private fun restartCurrentVod() {

        val exoPlayer =
            player
                ?: return

        val sourceId =
            currentSourceId
                ?: return

        val sourceName =
            currentSourceName
                ?: "VOD"

        val playback =
            currentPlayback
                ?: return


        if (
            playback.type !=
            "vod"
        ) {

            return
        }


        clearProgress(
            sourceId
        )


        exoPlayer.seekTo(
            0L
        )

        exoPlayer.playWhenReady =
            true


        statusText.text =
            "Restarted: $sourceName"


        updateNowPlayingUi()
    }


    /*
     * ----------------------------------------------------------------
     * FULL SCREEN
     * ----------------------------------------------------------------
     */


    private fun setFullscreenMode(
        fullscreen: Boolean
    ) {

        if (
            fullscreen &&
            player == null
        ) {

            return
        }


        isFullscreen =
            fullscreen


        if (fullscreen) {

            topControlBar.visibility =
                View.GONE

            statusText.visibility =
                View.GONE

            sourceScroll.visibility =
                View.GONE

            nowPlayingBar.visibility =
                View.GONE


            playerView.requestFocus()

            playerView.showController()

        } else {

            topControlBar.visibility =
                View.VISIBLE

            statusText.visibility =
                View.VISIBLE

            sourceScroll.visibility =
                View.VISIBLE


            updateNowPlayingUi()


            fullScreenButton.post {

                fullScreenButton.requestFocus()
            }
        }
    }


    /*
     * ----------------------------------------------------------------
     * NOW PLAYING
     * ----------------------------------------------------------------
     */


    private fun showNowPlaying() {

        nowPlayingBar.visibility =
            if (isFullscreen) {

                View.GONE

            } else {

                View.VISIBLE
            }
    }


    private fun hideNowPlaying() {

        nowPlayingBar.visibility =
            View.GONE

        nowPlayingTitle.text =
            "Nothing playing"

        nowPlayingProgress.text =
            ""

        restartButton.isEnabled =
            false
    }


    private fun startPlaybackUiTicker() {

        playbackUiHandler.removeCallbacks(
            playbackUiRunnable
        )

        playbackUiTicks =
            0

        updateNowPlayingUi()

        playbackUiHandler.postDelayed(
            playbackUiRunnable,
            PLAYBACK_UI_INTERVAL_MS
        )
    }


    private fun stopPlaybackUiTicker() {

        playbackUiHandler.removeCallbacks(
            playbackUiRunnable
        )

        playbackUiTicks =
            0
    }


    private fun updateNowPlayingUi() {

        val exoPlayer =
            player

        val sourceName =
            currentSourceName

        val playback =
            currentPlayback


        if (
            exoPlayer == null ||
            sourceName == null ||
            playback == null
        ) {

            hideNowPlaying()

            return
        }


        showNowPlaying()


        nowPlayingTitle.text =
            sourceName


        if (
            playback.type ==
            "live"
        ) {

            nowPlayingProgress.text =
                "LIVE"

            restartButton.isEnabled =
                false

            return
        }


        restartButton.isEnabled =
            true


        val positionMs =
            exoPlayer.currentPosition
                .coerceAtLeast(
                    0L
                )


        val rawDurationMs =
            exoPlayer.duration


        val durationMs =
            if (
                rawDurationMs ==
                C.TIME_UNSET ||
                rawDurationMs <
                0L
            ) {

                0L

            } else {

                rawDurationMs
            }


        nowPlayingProgress.text =
            if (
                durationMs >
                0L
            ) {

                "${formatTime(positionMs)} / " +
                    formatTime(durationMs)

            } else {

                formatTime(
                    positionMs
                )
            }
    }


    private fun formatTime(
        milliseconds: Long
    ): String {

        val totalSeconds =
            (
                milliseconds /
                1_000L
            ).coerceAtLeast(
                0L
            )


        val hours =
            totalSeconds /
                3_600L

        val minutes =
            (
                totalSeconds %
                3_600L
            ) /
                60L

        val seconds =
            totalSeconds %
                60L


        return if (
            hours >
            0L
        ) {

            String.format(
                "%d:%02d:%02d",
                hours,
                minutes,
                seconds
            )

        } else {

            String.format(
                "%d:%02d",
                minutes,
                seconds
            )
        }
    }


    /*
     * ----------------------------------------------------------------
     * HTTP
     * ----------------------------------------------------------------
     */


    private fun httpGet(
        urlString: String
    ): String {

        val connection =
            URL(
                urlString
            ).openConnection()
                as HttpURLConnection


        return try {

            connection.requestMethod =
                "GET"

            connection.connectTimeout =
                CONTROL_CONNECT_TIMEOUT_MS

            connection.readTimeout =
                CATALOG_READ_TIMEOUT_MS

            connection.useCaches =
                false

            connection.setRequestProperty(
                "Cache-Control",
                "no-cache"
            )


            val responseCode =
                connection.responseCode


            val body =
                readResponseBody(
                    connection,
                    responseCode
                )


            if (
                responseCode <
                HttpURLConnection.HTTP_OK ||
                responseCode >=
                HttpURLConnection.HTTP_MULT_CHOICE
            ) {

                throw IllegalStateException(
                    "HTTP $responseCode: $body"
                )
            }


            body

        } finally {

            connection.disconnect()
        }
    }


    private fun httpPost(
        urlString: String
    ): String {

        val connection =
            URL(
                urlString
            ).openConnection()
                as HttpURLConnection


        return try {

            connection.requestMethod =
                "POST"

            connection.connectTimeout =
                CONTROL_CONNECT_TIMEOUT_MS

            connection.readTimeout =
                CONTROL_READ_TIMEOUT_MS

            connection.useCaches =
                false

            connection.doOutput =
                false

            connection.setRequestProperty(
                "Content-Length",
                "0"
            )

            connection.setRequestProperty(
                "Cache-Control",
                "no-cache"
            )


            val responseCode =
                connection.responseCode


            val body =
                readResponseBody(
                    connection,
                    responseCode
                )


            if (
                responseCode <
                HttpURLConnection.HTTP_OK ||
                responseCode >=
                HttpURLConnection.HTTP_MULT_CHOICE
            ) {

                throw IllegalStateException(
                    "HTTP $responseCode: $body"
                )
            }


            body

        } finally {

            connection.disconnect()
        }
    }


    private fun readResponseBody(
        connection: HttpURLConnection,
        responseCode: Int
    ): String {

        val stream =
            if (
                responseCode >=
                400
            ) {

                connection.errorStream

            } else {

                connection.inputStream
            }


        if (stream == null) {

            return ""
        }


        return stream
            .bufferedReader()
            .use {

                it.readText()
            }
    }


    /*
     * ----------------------------------------------------------------
     * PLAYER
     * ----------------------------------------------------------------
     */


    private fun playMedia(
        sourceId: String,
        sourceName: String,
        url: String,
        playback: PlaybackInfo,
        startPositionMs: Long
    ) {

        releasePlayer()


        val isLive =
            playback.type ==
                "live"


        val loadControl =
            if (isLive) {

                DefaultLoadControl.Builder()
                    .setBufferDurationsMs(
                        10_000,
                        25_000,
                        8_000,
                        10_000
                    )
                    .setPrioritizeTimeOverSizeThresholds(
                        true
                    )
                    .build()

            } else {

                DefaultLoadControl.Builder()
                    .setBufferDurationsMs(
                        15_000,
                        30_000,
                        10_000,
                        15_000
                    )
                    .setPrioritizeTimeOverSizeThresholds(
                        true
                    )
                    .build()
            }


        val audioAttributes =
            AudioAttributes.Builder()
                .setUsage(
                    C.USAGE_MEDIA
                )
                .setContentType(
                    C.AUDIO_CONTENT_TYPE_MOVIE
                )
                .build()


        currentSourceId =
            sourceId

        currentSourceName =
            sourceName

        currentPlayback =
            playback


        player =
            ExoPlayer.Builder(this)
                .setLoadControl(
                    loadControl
                )
                .build()
                .also { exoPlayer ->


                    playerView.player =
                        exoPlayer


                    exoPlayer.setAudioAttributes(
                        audioAttributes,
                        true
                    )


                    exoPlayer.volume =
                        1.0f


                    exoPlayer.addListener(

                        object :
                            Player.Listener {


                            override fun onPlayerError(
                                error:
                                    PlaybackException
                            ) {

                                Log.e(
                                    TAG,
                                    "Playback failed",
                                    error
                                )


                                saveCurrentProgress()


                                statusText.text =
                                    "Playback error"
                            }


                            override fun onPlaybackStateChanged(
                                playbackState:
                                    Int
                            ) {

                                val stateName =
                                    when (
                                        playbackState
                                    ) {

                                        Player.STATE_IDLE ->
                                            "IDLE"

                                        Player.STATE_BUFFERING ->
                                            "BUFFERING"

                                        Player.STATE_READY ->
                                            "READY"

                                        Player.STATE_ENDED ->
                                            "ENDED"

                                        else ->
                                            "UNKNOWN"
                                    }


                                Log.d(
                                    TAG,
                                    "Playback state = $stateName"
                                )


                                Log.d(
                                    TAG,
                                    "Buffered position = " +
                                        "${exoPlayer.bufferedPosition} ms"
                                )


                                if (isLive) {

                                    Log.d(
                                        TAG,
                                        "Current live offset = " +
                                            "${exoPlayer.currentLiveOffset} ms"
                                    )
                                }


                                if (
                                    playbackState ==
                                    Player.STATE_ENDED &&
                                    !isLive
                                ) {

                                    saveCurrentProgress(
                                        forceCompleted =
                                            true
                                    )

                                    statusText.text =
                                        "Finished: $sourceName"
                                }


                                updateNowPlayingUi()
                            }
                        }
                    )


                    val mediaItem =
                        if (isLive) {

                            val liveConfiguration =
                                MediaItem
                                    .LiveConfiguration
                                    .Builder()
                                    .setTargetOffsetMs(
                                        15_000
                                    )
                                    .setMinOffsetMs(
                                        10_000
                                    )
                                    .setMaxOffsetMs(
                                        25_000
                                    )
                                    .build()


                            MediaItem.Builder()
                                .setUri(
                                    url
                                )
                                .setLiveConfiguration(
                                    liveConfiguration
                                )
                                .build()

                        } else {

                            MediaItem.Builder()
                                .setUri(
                                    url
                                )
                                .build()
                        }


                    Log.d(
                        TAG,
                        "Opening media: $url"
                    )


                    exoPlayer.setMediaItem(
                        mediaItem
                    )


                    if (
                        !isLive &&
                        startPositionMs >
                        0L
                    ) {

                        exoPlayer.seekTo(
                            startPositionMs
                        )
                    }


                    exoPlayer.prepare()


                    exoPlayer.playWhenReady =
                        true
                }


        showNowPlaying()

        startPlaybackUiTicker()
    }


    private fun releasePlayer() {

        saveCurrentProgress()

        stopPlaybackUiTicker()


        if (isFullscreen) {

            setFullscreenMode(
                false
            )
        }


        player?.release()

        player =
            null

        playerView.player =
            null


        currentSourceId =
            null

        currentSourceName =
            null

        currentPlayback =
            null


        hideNowPlaying()
    }


    /*
     * ----------------------------------------------------------------
     * UTILITIES / LIFECYCLE
     * ----------------------------------------------------------------
     */


    private fun dp(
        value: Int
    ): Int {

        return (
            value *
                resources.displayMetrics.density
            ).toInt()
    }


    override fun onStop() {

        /*
         * Save VOD progress before local playback is released.
         * The companion source is intentionally left alone.
         */
        releasePlayer()

        super.onStop()
    }


    override fun onDestroy() {

        stopPlaybackUiTicker()

        networkExecutor.shutdownNow()

        super.onDestroy()
    }
}
