package com.safeiot.privyhub

import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.drawable.BitmapDrawable

import com.safeiot.privyhub.streaming.NativeStreamActivity
import com.safeiot.privyhub.diagnostics.DiagnosticsActivity

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.text.InputType
import android.util.Log
import android.util.LruCache
import android.view.Gravity
import android.view.KeyEvent
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.GridLayout
import android.widget.ImageView
import android.widget.TextView

import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat

import androidx.media3.common.AudioAttributes
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.DefaultLoadControl
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory
import androidx.media3.ui.PlayerView

import org.json.JSONArray
import org.json.JSONObject

import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors


@UnstableApi
class MainActivity : AppCompatActivity() {

    private var player: ExoPlayer? = null

    private lateinit var playerView: PlayerView
    private lateinit var previewPlayerHost: ViewGroup
    private lateinit var fullscreenPlayerHost: ViewGroup

    private lateinit var topControlBar: View
    private lateinit var sourceScroll: View
    private lateinit var sourceGrid: GridLayout
    private lateinit var breadcrumbText: TextView
    private lateinit var statusText: TextView

    private lateinit var backButton: Button
    private lateinit var refreshButton: Button
    private lateinit var settingsButton: Button
    private lateinit var stopButton: Button

    private lateinit var nowPlayingBar: ViewGroup
    private lateinit var nowPlayingTitle: TextView
    private lateinit var nowPlayingProgress: TextView
    private lateinit var restartButton: Button
    private lateinit var gameSaveButton: Button
    private lateinit var gameLoadButton: Button
    private lateinit var gameEndButton: Button
    private lateinit var gameSessionPreview: ImageView
    private lateinit var gameSessionPreviewLabel: TextView
    private var gameSessionPreviewBitmap: Bitmap? = null

    // PrivyHub A2/A3 patch 01: persistent paused game-session banner.
    // PrivyHub A3 patch 11v2: frozen gameplay banner frame.
    private var gameSessionActive = false
    private var gameSessionPaused = false
    private var gameSessionTitle: String? = null

    private var isFullscreen =
        false

    /*
     * A fullscreen TV channel change must be allowed to replace the
     * ExoPlayer without briefly exposing the catalog UI.
     */
    private var preserveFullscreenOnNextPlayback =
        false

    private val networkExecutor: ExecutorService =
        Executors.newSingleThreadExecutor()

    // PrivyHub Phase A6 box art: artwork loading is isolated from
    // companion control requests so a slow/missing cover can never
    // delay launch, Save/Load, or library navigation.
    private val gameArtworkExecutor: ExecutorService =
        Executors.newFixedThreadPool(2)

    private val gameArtworkCache =
        object : LruCache<String, Bitmap>(
            12 * 1024
        ) {

            override fun sizeOf(
                key: String,
                value: Bitmap
            ): Int {

                return maxOf(
                    1,
                    value.byteCount / 1024
                )
            }
        }

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

    private lateinit var tvRepository:
        TvRepository

    private lateinit var tvEpgRepository:
        TvEpgRepository

    /*
     * Optional NFL Game Finder add-on. This remains outside the base
     * PrivyHub TV feature set.
     */
    private lateinit var nflRepository:
        NflRepository

    private val nflGameActions =
        mutableMapOf<String, NflGameAvailability>()

    private lateinit var tvBackupExportLauncher:
        ActivityResultLauncher<String>

    private lateinit var tvBackupImportLauncher:
        ActivityResultLauncher<Array<String>>

    private var tvPlaybackQueue:
        List<String> =
        emptyList()

    private var tvPlaybackQueueIndex =
        -1

    private val tvPageActions =
        mutableMapOf<String, TvPageRequest>()

    private val tvResultPages =
        mutableMapOf<String, TvPageRequest>()

    private var tvNodeSequence =
        0


    companion object {

        private const val TAG =
            "PrivyHub"

        private const val PREFS_NAME =
            "privyhub_settings"

        private const val PREF_COMPANION_HOST =
            "companion_host"

        // PrivyHub Phase A5: direct game-launch behavior.
        private const val PREF_GAME_AUTO_OPEN_AFTER_LAUNCH =
            "game_auto_open_after_launch"

        private const val PREF_TV_LANGUAGE =
            "tv_language"

        private const val PREF_TV_LANGUAGE_NAME =
            "tv_language_name"

        private const val PREF_TV_COUNTRY =
            "tv_country"

        private const val PREF_TV_COUNTRY_NAME =
            "tv_country_name"

        private const val TV_PAGE_SIZE =
            80

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
         * A public IPTV stream can fail transiently. Remember failures
         * locally on the onn for six hours so browsing can deprioritize
         * channels that just failed without burdening the companion.
         */
        private const val IPTV_FAILURE_TTL_MS =
            6L * 60L * 60L * 1_000L

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
        val path: String,
        val url: String? = null,
        val referrer: String? = null,
        val userAgent: String? = null
    )


    data class SourceNode(
        val id: String,
        val name: String,
        val nodeType: String,
        val children: List<SourceNode> = emptyList(),
        val playback: PlaybackInfo? = null,
        val lazyPath: String? = null,
        val artworkPath: String? = null
    )


    data class PlaybackProgress(
        val positionMs: Long,
        val durationMs: Long,
        val updatedAtMs: Long,
        val completed: Boolean
    )


    data class TvPageRequest(
        val title: String,
        val mode: String,
        val value: String = "",
        val offset: Int = 0,
        val includeHidden: Boolean = false,
        val paginate: Boolean = true,
        val limit: Int = TV_PAGE_SIZE
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

        tvRepository =
            TvRepository(
                this
            )

        tvEpgRepository =
            TvEpgRepository(
                this
            )

        nflRepository =
            NflRepository(
                context = this,
                tvRepository = tvRepository,
                epgRepository = tvEpgRepository
            )

        tvBackupExportLauncher =
            registerForActivityResult(
                ActivityResultContracts.CreateDocument(
                    "application/json"
                )
            ) { uri ->

                if (uri != null) {
                    exportTvBackupToUri(
                        uri
                    )
                }
            }

        tvBackupImportLauncher =
            registerForActivityResult(
                ActivityResultContracts.OpenDocument()
            ) { uri ->

                if (uri != null) {
                    importTvBackupFromUri(
                        uri
                    )
                }
            }


        playerView =
            findViewById(
                R.id.player_view
            )

        previewPlayerHost =
            findViewById(
                R.id.now_playing_preview_host
            )

        fullscreenPlayerHost =
            findViewById(
                R.id.fullscreen_player_host
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

        restartButton =
            findViewById(
                R.id.button_restart
            )


        gameSessionPreview =
            ImageView(this).apply {
                scaleType =
                    ImageView.ScaleType.FIT_CENTER
                setBackgroundColor(
                    0xFF101010.toInt()
                )
                isClickable = true
                isFocusable = true
                visibility = View.GONE
            }

        gameSessionPreviewLabel =
            TextView(this).apply {
                text = "RESUME\nPLAYING"
                textSize = 15f
                gravity = Gravity.CENTER
                setTextColor(
                    0xFFFFFFFF.toInt()
                )
                setBackgroundColor(
                    0x66000000
                )
                isClickable = true
                isFocusable = true
                visibility = View.GONE
            }

        previewPlayerHost.addView(
            gameSessionPreview,
            ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        )

        previewPlayerHost.addView(
            gameSessionPreviewLabel,
            ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        )


        gameSaveButton =
            createGameSessionActionButton(
                "SAVE"
            )

        gameLoadButton =
            createGameSessionActionButton(
                "LOAD"
            )

        gameEndButton =
            createGameSessionActionButton(
                "END"
            )

        nowPlayingBar.addView(
            gameSaveButton
        )

        nowPlayingBar.addView(
            gameLoadButton
        )

        nowPlayingBar.addView(
            gameEndButton
        )


        backButton.setOnClickListener {

            navigateBack()
        }


        refreshButton.setOnClickListener {

            if (isInTv()) {

                refreshTvCatalog(
                    force = true
                )

            } else {

                loadCatalog()
            }
        }


        settingsButton.setOnClickListener {

            showCompanionSettings()
        }


        stopButton.setOnClickListener {

            if (gameSessionActive) {
                showGameEndDialog()
            } else {
                stopPlaybackAndRemoteSource()
            }
        }


        /*
         * The Now Playing video itself is the fullscreen affordance.
         * With the controller disabled in preview mode, DPAD_CENTER/OK
         * activates this click listener instead of opening controls.
         */
        playerView.useController =
            false

        playerView.setOnClickListener {

            if (
                !isFullscreen &&
                player != null
            ) {

                setFullscreenMode(
                    true
                )
            }
        }


        restartButton.setOnClickListener {

            restartCurrentVod()
        }


        gameSessionPreview.setOnClickListener {

            if (gameSessionActive) {
                openNativeGameStream()
            }
        }

        gameSessionPreviewLabel.setOnClickListener {

            if (gameSessionActive) {
                openNativeGameStream()
            }
        }


        nowPlayingTitle.setOnClickListener {

            if (gameSessionActive) {
                openNativeGameStream()
            }
        }


        gameSaveButton.setOnClickListener {

            showGameSlotDialog(
                action = "save-state"
            )
        }


        gameLoadButton.setOnClickListener {

            showGameSlotDialog(
                action = "load-state"
            )
        }


        gameEndButton.setOnClickListener {

            showGameEndDialog()
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


    // PrivyHub Phase A5: new game launches can enter the proven native
    // fullscreen path automatically. The preference defaults on, while
    // keeping the existing paused Game Session handoff available.
    private fun getGameAutoOpenAfterLaunch(): Boolean {

        return getSharedPreferences(
            PREFS_NAME,
            MODE_PRIVATE
        ).getBoolean(
            PREF_GAME_AUTO_OPEN_AFTER_LAUNCH,
            true
        )
    }


    private fun saveGameAutoOpenAfterLaunch(
        enabled: Boolean
    ) {

        getSharedPreferences(
            PREFS_NAME,
            MODE_PRIVATE
        )
            .edit()
            .putBoolean(
                PREF_GAME_AUTO_OPEN_AFTER_LAUNCH,
                enabled
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


        val gameAutoOpenCheckBox =
            CheckBox(this).apply {
                text =
                    "Open games automatically after launch"
                isChecked =
                    getGameAutoOpenAfterLaunch()
            }

        container.addView(
            gameAutoOpenCheckBox,
            ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        )


        val gameAutoOpenHint =
            TextView(this).apply {
                text =
                    "Turn this off to keep newly launched games paused " +
                        "in PrivyHub until you open the Game Session."
                textSize =
                    13f
            }

        container.addView(
            gameAutoOpenHint,
            ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        )


        val dialog =
            AlertDialog.Builder(this)
                .setTitle(
                    "PrivyHub Settings"
                )
                .setMessage(
                    "Set the companion host and game launch behavior."
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
                .setNeutralButton(
                    "Diagnostics",
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

                saveGameAutoOpenAfterLaunch(
                    gameAutoOpenCheckBox.isChecked
                )

                dialog.dismiss()


                releasePlayer()

                activeSourceId =
                    null

                navigationStack.clear()

                loadCatalog()
            }

            // PRIVYHUB_B1_DIAGNOSTICS_NAV_V1
            dialog.getButton(
                AlertDialog.BUTTON_NEUTRAL
            ).setOnClickListener {

                val host =
                    getCompanionHost()

                if (host.isBlank()) {

                    input.error =
                        "Save companion host first"

                } else {

                    startActivity(
                        Intent(
                            this,
                            DiagnosticsActivity::class.java
                        ).apply {
                            putExtra(
                                DiagnosticsActivity.EXTRA_COMPANION_HOST,
                                host
                            )
                        }
                    )
                }
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


    private fun parseLazyNodes(
        jsonText: String
    ): List<SourceNode> {

        val root =
            JSONObject(
                jsonText
            )


        return parseNodeArray(
            root.getJSONArray(
                "nodes"
            )
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

                val childrenJson =
                    json.optJSONArray(
                        "children"
                    )

                val children =
                    if (childrenJson != null) {

                        parseNodeArray(
                            childrenJson
                        )

                    } else {

                        emptyList()
                    }

                val lazyPath =
                    json.optString(
                        "lazy_path",
                        ""
                    ).takeIf {
                        it.isNotBlank()
                    }


                SourceNode(
                    id = id,
                    name = name,
                    nodeType = nodeType,
                    children = children,
                    lazyPath = lazyPath
                )
            }


            "game" -> {

                SourceNode(
                    id = id,
                    name = name,
                    nodeType = nodeType,
                    lazyPath =
                        json.optString(
                            "lazy_path",
                            ""
                        ).takeIf {
                            it.isNotBlank()
                        },
                    artworkPath =
                        json.optString(
                            "artwork_path",
                            ""
                        ).takeIf {
                            it.isNotBlank()
                        }
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
                            playbackJson.optString(
                                "path",
                                ""
                            ),
                        url =
                            playbackJson.optString(
                                "url",
                                ""
                            ).takeIf {
                                it.isNotBlank()
                            },
                        referrer =
                            playbackJson.optString(
                                "referrer",
                                ""
                            ).takeIf {
                                it.isNotBlank()
                            },
                        userAgent =
                            playbackJson.optString(
                                "user_agent",
                                ""
                            ).takeIf {
                                it.isNotBlank()
                            }
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

        /*
         * Preserve the remote's focused item when the same page refreshes
         * (health result, favorite toggle, EPG update, etc.).
         */
        val previouslyFocusedId =
            currentFocus
                ?.tag
                as? String

        sourceGrid.removeAllViews()


        val currentNodes =
            if (
                navigationStack.isEmpty()
            ) {

                buildRootNodesForDisplay()

            } else {

                navigationStack
                    .last()
                    .children
            }

        val nodes =
            if (
                isTvUiPage() ||
                isGamesUiPage()
            ) {

                currentNodes

            } else {

                sortNodesForDisplay(
                    currentNodes
                )
            }


        breadcrumbText.text =
            buildBreadcrumb()


        backButton.isEnabled =
            navigationStack.isNotEmpty()


        if (nodes.isEmpty()) {

            if (isTvUiPage()) {

                backButton.isEnabled =
                    true

                statusText.text =
                    "No channels in this view"

            } else {

                renderEmptyCatalog()
            }

            return
        }


        var firstButton:
            Button? =
            null

        var restoreFocusButton:
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

            if (
                previouslyFocusedId != null &&
                node.id == previouslyFocusedId
            ) {

                restoreFocusButton =
                    button
            }


            sourceGrid.addView(
                button
            )
        }


        sourceGrid.post {

            (
                restoreFocusButton
                    ?: firstButton
            )?.requestFocus()
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

                /*
                 * Recently failed direct IPTV channels sort after healthy
                 * channels. Categories and companion-backed sources are
                 * unaffected.
                 */
                if (
                    node.nodeType == "source" &&
                    node.playback?.url != null &&
                    isIptvRecentlyFailed(
                        node.id
                    )
                ) {

                    1

                } else {

                    0
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


    private fun iptvFailureKey(
        sourceId: String
    ): String {

        return "iptv.failure.$sourceId"
    }


    private fun markIptvFailed(
        sourceId: String
    ) {

        getSharedPreferences(
            PREFS_NAME,
            MODE_PRIVATE
        )
            .edit()
            .putLong(
                iptvFailureKey(
                    sourceId
                ),
                System.currentTimeMillis()
            )
            .apply()
    }


    private fun clearIptvFailure(
        sourceId: String
    ) {

        getSharedPreferences(
            PREFS_NAME,
            MODE_PRIVATE
        )
            .edit()
            .remove(
                iptvFailureKey(
                    sourceId
                )
            )
            .apply()
    }


    private fun isIptvRecentlyFailed(
        sourceId: String
    ): Boolean {

        val prefs =
            getSharedPreferences(
                PREFS_NAME,
                MODE_PRIVATE
            )

        val failedAt =
            prefs.getLong(
                iptvFailureKey(
                    sourceId
                ),
                0L
            )


        if (failedAt <= 0L) {

            return false
        }


        val ageMs =
            System.currentTimeMillis() -
                failedAt

        val recent =
            ageMs >= 0L &&
                ageMs <
                IPTV_FAILURE_TTL_MS


        if (!recent) {

            prefs.edit()
                .remove(
                    iptvFailureKey(
                        sourceId
                    )
                )
                .apply()
        }


        return recent
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

        val isRecentlyFailedIptv =
            node.nodeType ==
                "source" &&
                node.playback?.url != null &&
                isIptvRecentlyFailed(
                    node.id
                )


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


                isRecentlyFailedIptv -> {

                    "${node.name}\nRecently failed"
                }


                else -> {

                    node.name
                }
            }


        button.textSize =
            if (
                isContinueWatchingSource ||
                isRecentlyFailedIptv
            ) {

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

        button.tag =
            node.id

        /*
         * Categories remain centered navigation tiles. Media/channel titles
         * are easier to scan when aligned from a consistent left edge.
         */
        button.gravity =
            if (
                node.nodeType ==
                "category"
            ) {

                Gravity.CENTER

            } else {

                Gravity.START or
                    Gravity.CENTER_VERTICAL
            }

        button.setPadding(
            dp(18),
            dp(4),
            dp(18),
            dp(4)
        )


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
            dp(300)

        layoutParams.height =
            dp(
                when {

                    node.nodeType == "game" &&
                        node.artworkPath != null ->
                        118

                    isContinueWatchingSource ->
                        90

                    else ->
                        78
                }
            )


        val margin =
            dp(6)


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

                    if (
                        handleTvCategoryClick(
                            node
                        )
                    ) {

                        return@setOnClickListener
                    }


                    if (node.lazyPath != null) {

                        loadLazyCategory(
                            node
                        )

                    } else {

                        navigationStack.add(
                            node
                        )

                        renderCurrentPage()
                    }
                }


                "game" -> {

                    if (
                        node.id ==
                        "games_session_status"
                    ) {
                        openGameSessionNode(
                            node
                        )
                    } else if (
                        node.id ==
                        "games_search"
                    ) {
                        showGameSearchDialog()
                    } else {
                        showGameDetails(
                            node
                        )
                    }
                }


                "source" -> {

                    if (
                        tvRepository.isTvStreamId(
                            node.id
                        )
                    ) {

                        prepareTvPlaybackContext(
                            node.id
                        )
                    }

                    startSource(
                        node
                    )
                }
            }
        }


        button.setOnLongClickListener {

            if (
                node.nodeType == "source" &&
                tvRepository.isTvStreamId(
                    node.id
                )
            ) {

                showTvChannelActions(
                    node
                )

                true

            } else {

                false
            }
        }


        if (
            node.nodeType == "game" &&
            node.artworkPath != null
        ) {
            loadGameArtworkIntoButton(
                button,
                node
            )
        }


        return button
    }


    // PrivyHub Phase A6 box art: fetch local cover images through the
    // existing media server. Missing/invalid art is intentionally silent.
    private fun loadGameArtworkIntoButton(
        button: Button,
        node: SourceNode
    ) {

        val artworkPath =
            node.artworkPath
                ?: return

        val cached =
            gameArtworkCache.get(
                artworkPath
            )

        if (cached != null) {
            applyGameArtworkToButton(
                button,
                node.id,
                cached
            )
            return
        }

        val host =
            getCompanionHost()

        if (host.isBlank()) {
            return
        }

        gameArtworkExecutor.execute {

            var connection:
                HttpURLConnection? =
                null

            try {

                val url =
                    URL(
                        "http://$host:$DEFAULT_MEDIA_PORT$artworkPath"
                    )

                connection =
                    url.openConnection()
                        as HttpURLConnection

                connection.requestMethod =
                    "GET"

                connection.connectTimeout =
                    2_500

                connection.readTimeout =
                    5_000

                connection.useCaches =
                    true

                val status =
                    connection.responseCode

                if (
                    status !in
                    200..299
                ) {
                    return@execute
                }

                val decoded =
                    connection.inputStream.use {
                        stream ->

                        BitmapFactory.decodeStream(
                            stream
                        )
                    }
                        ?: return@execute

                val bitmap =
                    scaleGameArtwork(
                        decoded
                    )

                if (bitmap !== decoded) {
                    decoded.recycle()
                }

                gameArtworkCache.put(
                    artworkPath,
                    bitmap
                )

                runOnUiThread {
                    applyGameArtworkToButton(
                        button,
                        node.id,
                        bitmap
                    )
                }

            } catch (error: Exception) {

                Log.d(
                    TAG,
                    "Game box art unavailable: $artworkPath",
                    error
                )

            } finally {
                connection?.disconnect()
            }
        }
    }


    private fun scaleGameArtwork(
        source: Bitmap
    ): Bitmap {

        val maxWidth =
            dp(72)

        val maxHeight =
            dp(96)

        if (
            source.width <= maxWidth &&
            source.height <= maxHeight
        ) {
            return source
        }

        val scale =
            minOf(
                maxWidth.toFloat() /
                    source.width.toFloat(),
                maxHeight.toFloat() /
                    source.height.toFloat()
            )

        val width =
            maxOf(
                1,
                (
                    source.width *
                        scale
                ).toInt()
            )

        val height =
            maxOf(
                1,
                (
                    source.height *
                        scale
                ).toInt()
            )

        return Bitmap.createScaledBitmap(
            source,
            width,
            height,
            true
        )
    }


    private fun applyGameArtworkToButton(
        button: Button,
        expectedNodeId: String,
        bitmap: Bitmap
    ) {

        if (
            button.tag != expectedNodeId
        ) {
            return
        }

        val drawable =
            BitmapDrawable(
                resources,
                bitmap
            )

        drawable.setBounds(
            0,
            0,
            bitmap.width,
            bitmap.height
        )

        button.setCompoundDrawables(
            drawable,
            null,
            null,
            null
        )

        button.compoundDrawablePadding =
            dp(12)
    }

    private fun loadLazyCategory(
        node: SourceNode
    ) {

        val lazyPath =
            node.lazyPath
                ?: return

        val host =
            getCompanionHost()


        if (host.isBlank()) {

            showCompanionSettings()

            return
        }


        statusText.text =
            "Loading ${node.name}..."


        networkExecutor.execute {

            try {

                val response =
                    httpGet(
                        "http://$host:$CONTROL_PORT$lazyPath"
                    )

                val children =
                    parseLazyNodes(
                        response
                    )

                val loadedNode =
                    node.copy(
                        children = children,
                        // PrivyHub A6.1 polish: retain the authoritative
                        // backing path so this exact Games view can be
                        // refreshed after library-state mutations without
                        // discarding the navigation stack.
                        lazyPath = lazyPath
                    )


                runOnUiThread {

                    navigationStack.add(
                        loadedNode
                    )

                    statusText.text =
                        "Connected: $host"

                    renderCurrentPage()
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to load lazy category ${node.id}",
                    error
                )


                runOnUiThread {

                    statusText.text =
                        "Failed: ${node.name}"
                }
            }
        }
    }


    // PrivyHub A6.1 polish: refresh only the currently displayed
    // companion-backed Games category. This preserves the breadcrumb,
    // navigation stack, and focused item instead of falling back to the
    // global catalog Refresh action.
    private fun refreshCurrentGameLibraryView() {

        val currentNode =
            navigationStack.lastOrNull()
                ?: return

        val lazyPath =
            currentNode.lazyPath
                ?: return

        if (
            !lazyPath.startsWith(
                "/plugins/games/"
            )
        ) {
            return
        }

        val host =
            getCompanionHost()

        if (host.isBlank()) {
            return
        }

        val expectedNodeId =
            currentNode.id

        networkExecutor.execute {

            try {

                val response =
                    httpGet(
                        "http://$host:$CONTROL_PORT$lazyPath"
                    )

                val children =
                    parseLazyNodes(
                        response
                    )

                runOnUiThread {

                    val activeNode =
                        navigationStack.lastOrNull()

                    if (
                        activeNode == null ||
                        activeNode.id != expectedNodeId ||
                        activeNode.lazyPath != lazyPath
                    ) {
                        return@runOnUiThread
                    }

                    navigationStack[
                        navigationStack.lastIndex
                    ] =
                        activeNode.copy(
                            children = children,
                            lazyPath = lazyPath
                        )

                    renderCurrentPage()
                }

            } catch (error: Exception) {

                Log.d(
                    TAG,
                    "Games view auto-refresh failed",
                    error
                )
            }
        }
    }

    /*
     * ----------------------------------------------------------------
     * LOCAL TV CATALOG
     * ----------------------------------------------------------------
     */


    private fun getTvLanguageCode(): String {

        return getSharedPreferences(
            PREFS_NAME,
            MODE_PRIVATE
        ).getString(
            PREF_TV_LANGUAGE,
            TvRepository.ENGLISH
        ) ?: TvRepository.ENGLISH
    }


    private fun getTvLanguageName(): String {

        return getSharedPreferences(
            PREFS_NAME,
            MODE_PRIVATE
        ).getString(
            PREF_TV_LANGUAGE_NAME,
            "English"
        ) ?: "English"
    }


    private fun getTvCountryCode(): String {

        return getSharedPreferences(
            PREFS_NAME,
            MODE_PRIVATE
        ).getString(
            PREF_TV_COUNTRY,
            ""
        ) ?: ""
    }


    private fun getTvCountryName(): String {

        return getSharedPreferences(
            PREFS_NAME,
            MODE_PRIVATE
        ).getString(
            PREF_TV_COUNTRY_NAME,
            "All Countries"
        ) ?: "All Countries"
    }


    private fun saveTvLanguage(
        code: String,
        name: String
    ) {

        getSharedPreferences(
            PREFS_NAME,
            MODE_PRIVATE
        )
            .edit()
            .putString(
                PREF_TV_LANGUAGE,
                code
            )
            .putString(
                PREF_TV_LANGUAGE_NAME,
                name
            )
            .apply()
    }


    private fun saveTvCountry(
        code: String,
        name: String
    ) {

        getSharedPreferences(
            PREFS_NAME,
            MODE_PRIVATE
        )
            .edit()
            .putString(
                PREF_TV_COUNTRY,
                code
            )
            .putString(
                PREF_TV_COUNTRY_NAME,
                name
            )
            .apply()
    }


    private fun isTvUiPage(): Boolean {

        return navigationStack
            .lastOrNull()
            ?.id
            ?.startsWith(
                "__tv_"
            ) == true
    }


    private fun isGamesUiPage(): Boolean {

        return navigationStack.any {
            it.id == "games" ||
                it.id.startsWith(
                    "games_"
                )
        }
    }

    private fun isInTv(): Boolean {

        return navigationStack.any {
            it.id == "tv" ||
                it.id.startsWith(
                    "__tv_"
                )
        }
    }


    private fun nextTvNodeId(
        prefix: String
    ): String {

        tvNodeSequence++

        return "__tv_${prefix}_${tvNodeSequence}"
    }


    private fun buildTvHomeNode(): SourceNode {

        val children =
            mutableListOf<SourceNode>()

        children.add(
            SourceNode(
                id = "__tv_favorites",
                name = "Favorites",
                nodeType = "category"
            )
        )

        children.add(
            SourceNode(
                id = "__tv_favorite_groups",
                name = "Favorite Groups",
                nodeType = "category"
            )
        )

        children.add(
            SourceNode(
                id = "__tv_recent",
                name = "Recently Watched",
                nodeType = "category"
            )
        )

        children.add(
            SourceNode(
                id = "__tv_reliable",
                name = "Reliable Channels",
                nodeType = "category"
            )
        )

        if (tvRepository.previousStreamId() != null) {
            children.add(
                SourceNode(
                    id = "__tv_last_channel",
                    name = "Last Channel",
                    nodeType = "category"
                )
            )
        }

        children.add(
            SourceNode(
                id = "__tv_nfl",
                name = "NFL Games",
                nodeType = "category"
            )
        )

        children.add(
            SourceNode(
                id = "__tv_search",
                name = "Search",
                nodeType = "category"
            )
        )

        for (entry in TvRepository.CURATED_GROUPS) {
            children.add(
                SourceNode(
                    id = "__tv_curated_${entry.key}",
                    name = entry.value.first,
                    nodeType = "category"
                )
            )
        }

        children.add(
            SourceNode(
                id = "__tv_categories",
                name = "Browse Categories",
                nodeType = "category"
            )
        )

        children.add(
            SourceNode(
                id = "__tv_all",
                name = "Browse All",
                nodeType = "category"
            )
        )

        children.add(
            SourceNode(
                id = "__tv_hidden",
                name = "Hidden / Unavailable",
                nodeType = "category"
            )
        )

        children.add(
            SourceNode(
                id = "__tv_language",
                name = "Language: ${getTvLanguageName()}",
                nodeType = "category"
            )
        )

        children.add(
            SourceNode(
                id = "__tv_country",
                name = "Country: ${getTvCountryName()}",
                nodeType = "category"
            )
        )

        children.add(
            SourceNode(
                id = "__tv_settings",
                name = "TV Settings",
                nodeType = "category"
            )
        )

        return SourceNode(
            id = "__tv_home",
            name = "TV",
            nodeType = "category",
            children = children
        )
    }


    private fun openTvHome(
        force: Boolean = false
    ) {

        val languageCode =
            getTvLanguageCode()

        statusText.text =
            if (force) {
                "Refreshing TV catalog..."
            } else {
                "Loading TV catalog..."
            }


        networkExecutor.execute {

            try {

                val result =
                    tvRepository.ensureCatalog(
                        languageCode = languageCode,
                        force = force
                    )


                runOnUiThread {

                    navigationStack.add(
                        buildTvHomeNode()
                    )

                    statusText.text =
                        if (result.usedCachedData) {
                            "TV: ${getTvLanguageName()} - cached catalog"
                        } else {
                            "TV: ${getTvLanguageName()} - ${result.channelCount} streams"
                        }

                    renderCurrentPage()
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to load local TV catalog",
                    error
                )


                if (
                    languageCode !=
                    TvRepository.ENGLISH
                ) {

                    try {

                        val fallback =
                            tvRepository.ensureCatalog(
                                languageCode =
                                    TvRepository.ENGLISH,
                                force = false
                            )

                        saveTvLanguage(
                            code = TvRepository.ENGLISH,
                            name = "English"
                        )

                        saveTvCountry(
                            code = "",
                            name = "All Countries"
                        )


                        runOnUiThread {

                            navigationStack.add(
                                buildTvHomeNode()
                            )

                            statusText.text =
                                "TV fallback: English - ${fallback.channelCount} streams"

                            renderCurrentPage()
                        }

                        return@execute

                    } catch (fallbackError: Exception) {

                        Log.e(
                            TAG,
                            "English TV fallback also failed",
                            fallbackError
                        )
                    }
                }


                runOnUiThread {

                    statusText.text =
                        "TV catalog unavailable"
                }
            }
        }
    }


    private fun refreshTvCatalog(
        force: Boolean
    ) {

        while (
            navigationStack
                .lastOrNull()
                ?.id
                ?.startsWith(
                    "__tv_"
                ) == true
        ) {

            navigationStack.removeAt(
                navigationStack.lastIndex
            )
        }

        openTvHome(
            force = force
        )
    }


    private fun handleTvCategoryClick(
        node: SourceNode
    ): Boolean {

        if (node.id == "tv") {
            openTvHome()
            return true
        }

        val registered =
            tvPageActions[node.id]

        if (registered != null) {
            openTvPage(registered)
            return true
        }

        when {
            node.id == "__tv_favorites" -> {
                openTvPage(
                    TvPageRequest(
                        title = "Favorites",
                        mode = TvRepository.MODE_FAVORITES,
                        paginate = true
                    )
                )
                return true
            }

            node.id == "__tv_favorite_groups" -> {
                openTvFavoriteGroups()
                return true
            }

            node.id == "__tv_recent" -> {
                openTvPage(
                    TvPageRequest(
                        title = "Recently Watched",
                        mode = TvRepository.MODE_RECENT,
                        paginate = false,
                        limit = 50
                    )
                )
                return true
            }

            node.id == "__tv_reliable" -> {
                openTvPage(
                    TvPageRequest(
                        title = "Reliable Channels",
                        mode = TvRepository.MODE_RELIABLE,
                        paginate = true
                    )
                )
                return true
            }

            node.id == "__tv_last_channel" -> {
                playPreviousTvChannel()
                return true
            }

            node.id == "__tv_nfl" -> {
                openNflHome()
                return true
            }

            node.id == "__nfl_live" -> {
                loadNflPage(
                    window = NflWindow.LIVE,
                    title = "NFL Live Now"
                )
                return true
            }

            node.id == "__nfl_today" -> {
                loadNflPage(
                    window = NflWindow.TODAY,
                    title = "NFL Today"
                )
                return true
            }

            node.id == "__nfl_week" -> {
                loadNflPage(
                    window = NflWindow.WEEK,
                    title = "NFL Next 8 Days"
                )
                return true
            }

            node.id == "__nfl_refresh" -> {
                nflRepository.clearCache()
                loadNflPage(
                    window = NflWindow.WEEK,
                    title = "NFL Next 8 Days"
                )
                return true
            }

            node.id.startsWith("__nfl_game_") -> {
                showNflGameDetails(
                    node.id
                )
                return true
            }

            node.id == "__tv_search" -> {
                showTvSearchDialog()
                return true
            }

            node.id == "__tv_categories" -> {
                openTvCategoryBrowser()
                return true
            }

            node.id == "__tv_all" -> {
                openTvPage(
                    TvPageRequest(
                        title = "Browse All",
                        mode = TvRepository.MODE_ALL,
                        includeHidden = true
                    )
                )
                return true
            }

            node.id == "__tv_hidden" -> {
                openTvPage(
                    TvPageRequest(
                        title = "Hidden / Unavailable",
                        mode = TvRepository.MODE_HIDDEN,
                        includeHidden = true
                    )
                )
                return true
            }

            node.id == "__tv_language" -> {
                showTvLanguageDialog()
                return true
            }

            node.id == "__tv_country" -> {
                showTvCountryDialog()
                return true
            }

            node.id == "__tv_settings" -> {
                showTvSettings()
                return true
            }

            node.id.startsWith("__tv_curated_") -> {
                val key = node.id.removePrefix("__tv_curated_")
                openTvPage(
                    TvPageRequest(
                        title = node.name,
                        mode = TvRepository.MODE_CURATED,
                        value = key
                    )
                )
                return true
            }
        }

        return node.id.startsWith("__tv_")
    }


    private fun openTvCategoryBrowser() {

        val languageCode =
            getTvLanguageCode()

        val countryCode =
            getTvCountryCode()

        statusText.text =
            "Loading TV categories..."


        networkExecutor.execute {

            try {

                val categories =
                    tvRepository.availableCategories(
                        languageCode = languageCode,
                        countryCode = countryCode
                    )


                runOnUiThread {

                    val children =
                        categories.map { category ->

                            registerTvPageAction(
                                name =
                                    categoryDisplayName(
                                        category
                                    ),
                                request =
                                    TvPageRequest(
                                        title =
                                            categoryDisplayName(
                                                category
                                            ),
                                        mode =
                                            TvRepository.MODE_CATEGORY,
                                        value =
                                            category
                                    )
                            )
                        }

                    navigationStack.add(
                        SourceNode(
                            id = nextTvNodeId(
                                "category_browser"
                            ),
                            name = "Browse Categories",
                            nodeType = "category",
                            children = children
                        )
                    )

                    statusText.text =
                        "TV categories"

                    renderCurrentPage()
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to load TV categories",
                    error
                )


                runOnUiThread {

                    statusText.text =
                        "Failed to load TV categories"
                }
            }
        }
    }


    private fun registerTvPageAction(
        name: String,
        request: TvPageRequest
    ): SourceNode {

        val id =
            nextTvNodeId(
                "action"
            )

        tvPageActions[
            id
        ] =
            request

        return SourceNode(
            id = id,
            name = name,
            nodeType = "category"
        )
    }


    private fun sameTvQuery(
        first: TvPageRequest,
        second: TvPageRequest
    ): Boolean {

        return first.title == second.title &&
            first.mode == second.mode &&
            first.value == second.value &&
            first.includeHidden == second.includeHidden &&
            first.paginate == second.paginate
    }


    private fun buildTvResultChildren(
        channels: List<TvChannel>,
        request: TvPageRequest,
        totalCount: Int
    ): List<SourceNode> {

        val children =
            channels.map {
                tvChannelToNode(
                    it
                )
            }.toMutableList()


        if (
            !request.paginate ||
            totalCount <= TV_PAGE_SIZE
        ) {

            return children
        }


        val pageCount =
            (
                totalCount +
                    TV_PAGE_SIZE -
                    1
            ) /
                TV_PAGE_SIZE

        val currentPage =
            (
                request.offset /
                    TV_PAGE_SIZE
            ) +
                1

        val lastOffset =
            (
                pageCount -
                    1
            ) *
                TV_PAGE_SIZE

        val previousOffset =
            (
                request.offset -
                    TV_PAGE_SIZE
            ).coerceAtLeast(
                0
            )

        val nextOffset =
            (
                request.offset +
                    TV_PAGE_SIZE
            ).coerceAtMost(
                lastOffset
            )


        children.add(
            registerTvPageAction(
                name = "First Page",
                request =
                    request.copy(
                        offset = 0,
                        limit = TV_PAGE_SIZE
                    )
            )
        )

        children.add(
            registerTvPageAction(
                name = "Previous Page",
                request =
                    request.copy(
                        offset = previousOffset,
                        limit = TV_PAGE_SIZE
                    )
            )
        )

        children.add(
            registerTvPageAction(
                name = "Next Page",
                request =
                    request.copy(
                        offset = nextOffset,
                        limit = TV_PAGE_SIZE
                    )
            )
        )

        children.add(
            registerTvPageAction(
                name = "Last Page",
                request =
                    request.copy(
                        offset = lastOffset,
                        limit = TV_PAGE_SIZE
                    )
            )
        )


        return children
    }


    private fun tvPageStatus(
        request: TvPageRequest,
        totalCount: Int,
        visibleCount: Int
    ): String {

        if (
            !request.paginate ||
            totalCount <= TV_PAGE_SIZE
        ) {

            return "$visibleCount channel${if (visibleCount == 1) "" else "s"}"
        }


        val pageCount =
            (
                totalCount +
                    TV_PAGE_SIZE -
                    1
            ) /
                TV_PAGE_SIZE

        val pageNumber =
            (
                request.offset /
                    TV_PAGE_SIZE
            ) +
                1

        val firstChannel =
            if (visibleCount == 0) {
                0
            } else {
                request.offset +
                    1
            }

        val lastChannel =
            request.offset +
                visibleCount


        return "Page $pageNumber of $pageCount  •  " +
            "Channels $firstChannel-$lastChannel of $totalCount"
    }


    private fun openTvPage(
        request: TvPageRequest
    ) {

        val languageCode =
            getTvLanguageCode()

        val countryCode =
            getTvCountryCode()

        statusText.text =
            "Loading ${request.title}..."


        networkExecutor.execute {

            try {

                val count =
                    tvRepository.countChannels(
                        languageCode = languageCode,
                        countryCode = countryCode,
                        mode = request.mode,
                        value = request.value,
                        includeHidden = request.includeHidden
                    )

                val pageCount =
                    if (
                        request.paginate &&
                        count > 0
                    ) {
                        (
                            count +
                                TV_PAGE_SIZE -
                                1
                        ) /
                            TV_PAGE_SIZE
                    } else {
                        1
                    }

                val lastOffset =
                    if (
                        request.paginate &&
                        pageCount > 1
                    ) {
                        (
                            pageCount -
                                1
                        ) *
                            TV_PAGE_SIZE
                    } else {
                        0
                    }

                val normalizedOffset =
                    if (request.paginate) {
                        (
                            request.offset /
                                TV_PAGE_SIZE
                        ) *
                            TV_PAGE_SIZE
                    } else {
                        request.offset
                    }.coerceIn(
                        0,
                        lastOffset.coerceAtLeast(
                            0
                        )
                    )

                val normalizedRequest =
                    request.copy(
                        offset = normalizedOffset,
                        limit =
                            if (request.paginate) {
                                TV_PAGE_SIZE
                            } else {
                                request.limit
                            }
                    )

                val channels =
                    tvRepository.queryChannels(
                        languageCode = languageCode,
                        countryCode = countryCode,
                        mode = normalizedRequest.mode,
                        value = normalizedRequest.value,
                        includeHidden = normalizedRequest.includeHidden,
                        limit = normalizedRequest.limit,
                        offset = normalizedRequest.offset
                    )


                runOnUiThread {

                    val currentNode =
                        navigationStack
                            .lastOrNull()

                    val currentRequest =
                        currentNode
                            ?.let {
                                tvResultPages[
                                    it.id
                                ]
                            }

                    val replaceCurrent =
                        currentRequest != null &&
                            sameTvQuery(
                                currentRequest,
                                normalizedRequest
                            )

                    val resultId =
                        nextTvNodeId(
                            "result"
                        )

                    tvResultPages[
                        resultId
                    ] =
                        normalizedRequest

                    val pageNumber =
                        if (normalizedRequest.paginate) {
                            (
                                normalizedRequest.offset /
                                    TV_PAGE_SIZE
                            ) +
                                1
                        } else {
                            1
                        }

                    val nodeName =
                        if (
                            normalizedRequest.paginate &&
                            count > TV_PAGE_SIZE
                        ) {
                            "${normalizedRequest.title}  •  Page $pageNumber"
                        } else {
                            normalizedRequest.title
                        }

                    val resultNode =
                        SourceNode(
                            id = resultId,
                            name = nodeName,
                            nodeType = "category",
                            children =
                                buildTvResultChildren(
                                    channels = channels,
                                    request = normalizedRequest,
                                    totalCount = count
                                )
                        )

                    if (
                        replaceCurrent &&
                        navigationStack.isNotEmpty()
                    ) {

                        currentNode?.let {
                            tvResultPages.remove(
                                it.id
                            )
                        }

                        navigationStack[
                            navigationStack.lastIndex
                        ] =
                            resultNode

                    } else {

                        navigationStack.add(
                            resultNode
                        )
                    }

                    statusText.text =
                        if (channels.isEmpty()) {
                            "No matching channels"
                        } else {
                            tvPageStatus(
                                request = normalizedRequest,
                                totalCount = count,
                                visibleCount = channels.size
                            )
                        }

                    renderCurrentPage()
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to query TV catalog",
                    error
                )


                runOnUiThread {

                    statusText.text =
                        "TV query failed"
                }
            }
        }
    }


    private fun tvChannelToNode(
        channel: TvChannel
    ): SourceNode {

        val status =
            when {

                channel.manualHidden ->
                    "Hidden"

                channel.autoHidden ->
                    "Unavailable - ${channel.consecutiveFailures} failures"

                channel.consecutiveFailures > 0 ->
                    "Recent failures: ${channel.consecutiveFailures}"

                channel.successCount > 0 ->
                    "Working"

                else ->
                    ""
            }

        val prefix =
            if (channel.favorite) {
                "★ "
            } else {
                ""
            }

        val guide =
            tvEpgRepository.getCachedGuide(
                channel.channelId
            )

        val nowPlaying =
            guide.current
                ?.title
                ?.takeIf {
                    it.isNotBlank()
                }

        val displayName =
            buildString {
                append(
                    "$prefix${channel.name}"
                )

                if (nowPlaying != null) {
                    append("\nNow: ")
                    append(nowPlaying)
                }

                if (status.isNotBlank()) {
                    append("\n")
                    append(status)
                }
            }


        return SourceNode(
            id = channel.streamId,
            name = displayName,
            nodeType = "source",
            playback =
                PlaybackInfo(
                    type = "live",
                    port = 0,
                    path = "",
                    url = channel.url,
                    referrer = channel.referrer,
                    userAgent = channel.userAgent
                )
        )
    }


    private fun showTvSearchDialog() {

        val input =
            EditText(
                this
            )

        input.inputType =
            InputType.TYPE_CLASS_TEXT

        input.setSingleLine(
            true
        )

        input.hint =
            "Channel name"


        val dialog =
            AlertDialog.Builder(
                this
            )
                .setTitle(
                    "Search TV"
                )
                .setView(
                    input
                )
                .setPositiveButton(
                    "Search",
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

                val query =
                    input.text
                        .toString()
                        .trim()

                if (query.isBlank()) {

                    input.error =
                        "Enter a channel name"

                    return@setOnClickListener
                }

                dialog.dismiss()

                openTvPage(
                    TvPageRequest(
                        title = "Search: $query",
                        mode = TvRepository.MODE_SEARCH,
                        value = query,
                        includeHidden = true
                    )
                )
            }
        }


        dialog.show()

        input.requestFocus()
    }


    private fun showTvLanguageDialog() {

        statusText.text =
            "Loading languages..."


        networkExecutor.execute {

            val fetched =
                try {
                    tvRepository.fetchLanguageOptions()
                } catch (error: Exception) {
                    Log.w(
                        TAG,
                        "Unable to fetch IPTV language list",
                        error
                    )
                    emptyList()
                }


            runOnUiThread {

                val english =
                    TvLanguageOption(
                        code = TvRepository.ENGLISH,
                        name = "English"
                    )

                val all =
                    TvLanguageOption(
                        code = TvRepository.ALL_LANGUAGES,
                        name = "All Languages"
                    )

                val options =
                    listOf(
                        english,
                        all
                    ) +
                        fetched.filter {
                            it.code != TvRepository.ENGLISH
                        }

                val names =
                    options.map {
                        it.name
                    }.toTypedArray()


                AlertDialog.Builder(
                    this
                )
                    .setTitle(
                        "TV Language"
                    )
                    .setItems(
                        names
                    ) { _, which ->

                        val selected =
                            options[
                                which
                            ]

                        saveTvLanguage(
                            code = selected.code,
                            name = selected.name
                        )

                        saveTvCountry(
                            code = "",
                            name = "All Countries"
                        )

                        refreshTvCatalog(
                            force = false
                        )
                    }
                    .setNegativeButton(
                        "Cancel",
                        null
                    )
                    .show()

                statusText.text =
                    "Choose TV language"
            }
        }
    }


    private fun showTvCountryDialog() {

        val languageCode =
            getTvLanguageCode()

        statusText.text =
            "Loading countries..."


        networkExecutor.execute {

            try {

                val options =
                    tvRepository.availableCountries(
                        languageCode
                    )
                        .map { code ->
                            code to
                                tvRepository.countryDisplayName(
                                    code
                                )
                        }
                        .sortedBy {
                            it.second.lowercase()
                        }


                runOnUiThread {

                    val labels =
                        listOf(
                            "All Countries"
                        ) +
                            options.map {
                                "${it.second} (${it.first})"
                            }


                    AlertDialog.Builder(
                        this
                    )
                        .setTitle(
                            "TV Country"
                        )
                        .setItems(
                            labels.toTypedArray()
                        ) { _, which ->

                            if (which == 0) {

                                saveTvCountry(
                                    code = "",
                                    name = "All Countries"
                                )

                            } else {

                                val selected =
                                    options[
                                        which - 1
                                    ]

                                saveTvCountry(
                                    code = selected.first,
                                    name = selected.second
                                )
                            }

                            refreshTvCatalog(
                                force = false
                            )
                        }
                        .setNegativeButton(
                            "Cancel",
                            null
                        )
                        .show()

                    statusText.text =
                        "Choose TV country"
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to load TV countries",
                    error
                )


                runOnUiThread {

                    statusText.text =
                        "Failed to load countries"
                }
            }
        }
    }


    private fun openNflHome() {

        val children =
            listOf(
                SourceNode(
                    id = "__nfl_live",
                    name = "Live Now",
                    nodeType = "category"
                ),
                SourceNode(
                    id = "__nfl_today",
                    name = "Today",
                    nodeType = "category"
                ),
                SourceNode(
                    id = "__nfl_week",
                    name = "Next 8 Days",
                    nodeType = "category"
                ),
                SourceNode(
                    id = "__nfl_refresh",
                    name = "Refresh NFL Data",
                    nodeType = "category"
                )
            )

        navigationStack.add(
            SourceNode(
                id = "__nfl_home",
                name = "NFL Games",
                nodeType = "category",
                children = children
            )
        )

        renderCurrentPage()
    }


    private fun loadNflPage(
        window: NflWindow,
        title: String
    ) {

        statusText.text =
            "Loading $title..."

        networkExecutor.execute {

            try {

                val results =
                    nflRepository.load(
                        window = window,
                        languageCode = getTvLanguageCode()
                    )

                runOnUiThread {

                    if (
                        navigationStack
                            .lastOrNull()
                            ?.id !=
                            "__nfl_home"
                    ) {

                        return@runOnUiThread
                    }

                    nflGameActions.clear()

                    val children =
                        if (results.isEmpty()) {

                            listOf(
                                SourceNode(
                                    id = "__nfl_empty",
                                    name = "No NFL games in this window",
                                    nodeType = "category"
                                )
                            )

                        } else {

                            results.map { result ->

                                val id =
                                    "__nfl_game_${result.game.id}"

                                nflGameActions[
                                    id
                                ] =
                                    result

                                SourceNode(
                                    id = id,
                                    name = buildNflGameLabel(
                                        result
                                    ),
                                    nodeType = "category"
                                )
                            }
                        }

                    navigationStack.add(
                        SourceNode(
                            id = "__nfl_page_${window.name.lowercase()}",
                            name = title,
                            nodeType = "category",
                            children = children
                        )
                    )

                    statusText.text =
                        if (results.isEmpty()) {

                            "No NFL games in this window"

                        } else {

                            "${results.size} NFL game(s)"
                        }

                    renderCurrentPage()
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "NFL Game Finder failed",
                    error
                )

                runOnUiThread {

                    statusText.text =
                        "NFL data unavailable"

                    AlertDialog.Builder(this)
                        .setTitle(
                            "NFL Game Finder"
                        )
                        .setMessage(
                            error.message
                                ?: "Could not load NFL schedule data."
                        )
                        .setPositiveButton(
                            "OK",
                            null
                        )
                        .show()
                }
            }
        }
    }


    private fun buildNflGameLabel(
        result: NflGameAvailability
    ): String {

        val symbol =
            when (result.status) {

                NflAvailabilityStatus.AVAILABLE ->
                    "●"

                NflAvailabilityStatus.POSSIBLE ->
                    "◐"

                NflAvailabilityStatus.NO_STREAM ->
                    "○"
            }

        val status =
            when (result.status) {

                NflAvailabilityStatus.AVAILABLE ->
                    "AVAILABLE"

                NflAvailabilityStatus.POSSIBLE ->
                    "POSSIBLE"

                NflAvailabilityStatus.NO_STREAM ->
                    "NO STREAM"
            }

        val time =
            formatNflKickoff(
                result.game.startMs
            )

        val network =
            result.game.networks
                .firstOrNull()
                ?: "Unknown network"

        return "$symbol ${result.game.matchup}\n$time · $network\n$status"
    }


    private fun showNflGameDetails(
        nodeId: String
    ) {

        if (nodeId == "__nfl_empty") {

            return
        }

        val result =
            nflGameActions[
                nodeId
            ]
                ?: return

        val game =
            result.game

        val details =
            StringBuilder()

        details.append(
            formatNflKickoff(
                game.startMs
            )
        )

        details.append(
            "\nNetwork: "
        )

        details.append(
            game.networks
                .joinToString(
                    " / "
                )
                .ifBlank {
                    "Unknown"
                }
        )

        details.append(
            "\n\n"
        )

        details.append(
            result.reason
        )

        if (
            result.channel != null
        ) {

            details.append(
                "\n\nBest-ranked candidate:\n"
            )

            details.append(
                result.channel.name
            )
        }

        if (
            result.candidates.isNotEmpty()
        ) {

            details.append(
                "\n\nCandidate channels: ${result.candidates.size}"
            )
        }

        if (
            !result.coverageSummary.isNullOrBlank()
        ) {

            details.append(
                "\n\nMarket / coverage evidence:\n"
            )

            details.append(
                result.coverageSummary
            )
        }

        if (
            result.affiliateEvidence.isNotEmpty()
        ) {

            details.append(
                "\n\nEPG affiliate evidence:\n"
            )

            details.append(
                result.affiliateEvidence
                    .joinToString(
                        "\n"
                    ) {
                        "• $it"
                    }
            )
        }

        if (
            result.status ==
            NflAvailabilityStatus.NO_STREAM &&
            result.coverageSummary.isNullOrBlank() &&
            result.affiliateEvidence.isEmpty()
        ) {

            details.append(
                "\n\nNo market evidence is available yet. " +
                    "Regional CBS/FOX maps are usually published close to game day."
            )
        }

        val builder =
            AlertDialog.Builder(this)
                .setTitle(
                    game.matchup
                )
                .setMessage(
                    details.toString()
                )
                .setNegativeButton(
                    "Close",
                    null
                )

        if (
            result.candidates.isNotEmpty()
        ) {

            builder.setPositiveButton(
                "Channels (${result.candidates.size})"
            ) { _, _ ->

                showNflChannelCandidates(
                    result
                )
            }
        }

        builder.show()
    }


    private fun showNflChannelCandidates(
        result: NflGameAvailability
    ) {

        val candidates =
            result.candidates

        if (candidates.isEmpty()) {

            AlertDialog.Builder(this)
                .setTitle(
                    result.game.matchup
                )
                .setMessage(
                    "No matching PrivyHub channels were found."
                )
                .setPositiveButton(
                    "OK",
                    null
                )
                .show()

            return
        }

        val labels =
            candidates
                .map { candidate ->

                    val match =
                        if (
                            candidate.exactEpgMatch
                        ) {

                            "EXACT EPG"

                        } else {

                            "NETWORK MATCH"
                        }

                    val market =
                        candidate.channel.country
                            .ifBlank {
                                "market unknown"
                            }

                    "${candidate.channel.name}\n" +
                        "$match · ${candidate.statusLabel} · $market"
                }
                .toTypedArray()

        AlertDialog.Builder(this)
            .setTitle(
                "${result.game.matchup} — Channels"
            )
            .setItems(
                labels
            ) { _, which ->

                val candidate =
                    candidates[
                        which
                    ]

                /*
                 * Intentionally allow every candidate, including user-hidden,
                 * auto-hidden and previously failed channels. The label tells
                 * the user the risk; the chooser does not silently suppress it.
                 */
                playTvStreamById(
                    candidate.channel.streamId
                )
            }
            .setNegativeButton(
                "Cancel",
                null
            )
            .show()
    }


    private fun formatNflKickoff(
        startMs: Long
    ): String {

        val formatter =
            java.text.SimpleDateFormat(
                "EEE MMM d · h:mm a z",
                java.util.Locale.US
            ).apply {

                timeZone =
                    java.util.TimeZone.getTimeZone(
                        "America/New_York"
                    )
            }

        return formatter.format(
            java.util.Date(
                startMs
            )
        )
    }


    override fun dispatchKeyEvent(
        event: KeyEvent
    ): Boolean {

        if (
            event.action == KeyEvent.ACTION_DOWN &&
            event.repeatCount == 0 &&
            currentSourceId?.let {
                tvRepository.isTvStreamId(it)
            } == true
        ) {
            when (event.keyCode) {
                KeyEvent.KEYCODE_CHANNEL_UP -> {
                    surfTvChannel(1)
                    return true
                }

                KeyEvent.KEYCODE_CHANNEL_DOWN -> {
                    surfTvChannel(-1)
                    return true
                }

                KeyEvent.KEYCODE_MEDIA_PREVIOUS -> {
                    playPreviousTvChannel()
                    return true
                }

                KeyEvent.KEYCODE_DPAD_UP -> {
                    if (isFullscreen) {
                        surfTvChannel(1)
                        return true
                    }
                }

                KeyEvent.KEYCODE_DPAD_DOWN -> {
                    if (isFullscreen) {
                        surfTvChannel(-1)
                        return true
                    }
                }
            }
        }

        return super.dispatchKeyEvent(event)
    }


    private fun prepareTvPlaybackContext(
        streamId: String
    ) {
        val visibleIds =
            navigationStack
                .lastOrNull()
                ?.children
                ?.mapNotNull { child ->
                    if (
                        child.nodeType == "source" &&
                        tvRepository.isTvStreamId(child.id)
                    ) {
                        child.id
                    } else {
                        null
                    }
                }
                .orEmpty()

        tvPlaybackQueue =
            if (visibleIds.isEmpty()) {
                listOf(streamId)
            } else {
                visibleIds
            }

        tvPlaybackQueueIndex =
            tvPlaybackQueue.indexOf(streamId)
                .coerceAtLeast(0)
    }


    private fun playTvStreamById(
        streamId: String,
        preserveFullscreen: Boolean = false
    ) {
        val channel =
            tvRepository.getChannel(streamId)
                ?: return

        val keepFullscreen =
            preserveFullscreen &&
                isFullscreen

        prepareTvPlaybackContext(streamId)

        /*
         * Direct IPTV playback reaches playMedia() synchronously through
         * startSource() -> beginPlayback(). playMedia() consumes this flag
         * before releasing the old player.
         */
        preserveFullscreenOnNextPlayback =
            keepFullscreen

        startSource(
            tvChannelToNode(channel)
        )

        /*
         * Defensive reset in case a malformed direct source returns before
         * playMedia() consumes the flag.
         */
        preserveFullscreenOnNextPlayback =
            false
    }


    private fun surfTvChannel(
        direction: Int
    ) {
        val current =
            currentSourceId
                ?: tvRepository.currentStreamId()
                ?: return

        if (
            tvPlaybackQueue.isEmpty() ||
            !tvPlaybackQueue.contains(current)
        ) {
            prepareTvPlaybackContext(current)
        }

        if (tvPlaybackQueue.size <= 1) {
            statusText.text = "No adjacent channel in this page"
            return
        }

        val currentIndex =
            tvPlaybackQueue.indexOf(current)
                .coerceAtLeast(0)

        val nextIndex =
            (currentIndex + direction + tvPlaybackQueue.size) %
                tvPlaybackQueue.size

        tvPlaybackQueueIndex = nextIndex
        playTvStreamById(
            tvPlaybackQueue[nextIndex],
            preserveFullscreen =
                isFullscreen
        )
    }


    private fun playPreviousTvChannel() {
        val previous =
            tvRepository.previousStreamId()

        if (previous == null) {
            statusText.text = "No previous TV channel yet"
            return
        }

        playTvStreamById(
            previous,
            preserveFullscreen =
                isFullscreen
        )
    }


    private fun openTvFavoriteGroups() {
        val groups =
            tvRepository.favoriteGroups()

        val children =
            mutableListOf<SourceNode>()

        children.add(
            registerTvPageAction(
                name = "All Favorites",
                request = TvPageRequest(
                    title = "Favorites",
                    mode = TvRepository.MODE_FAVORITES
                )
            )
        )

        children.add(
            registerTvPageAction(
                name = "Ungrouped",
                request = TvPageRequest(
                    title = "Favorites - Ungrouped",
                    mode = TvRepository.MODE_FAVORITE_GROUP,
                    value = ""
                )
            )
        )

        for (group in groups) {
            children.add(
                registerTvPageAction(
                    name = group,
                    request = TvPageRequest(
                        title = "Favorites - $group",
                        mode = TvRepository.MODE_FAVORITE_GROUP,
                        value = group
                    )
                )
            )
        }

        navigationStack.add(
            SourceNode(
                id = nextTvNodeId("favorite_groups"),
                name = "Favorite Groups",
                nodeType = "category",
                children = children
            )
        )

        statusText.text =
            "${groups.size} favorite group${if (groups.size == 1) "" else "s"}"
        renderCurrentPage()
    }


    private fun showTvFavoriteOptions(
        streamId: String
    ) {
        val channel =
            tvRepository.getChannel(streamId)
                ?: return

        val actions =
            arrayOf(
                "Set Favorite Group",
                "Move Earlier",
                "Move Later"
            )

        AlertDialog.Builder(this)
            .setTitle(
                if (channel.favoriteGroup.isBlank()) {
                    "${channel.name} - Favorites"
                } else {
                    "${channel.name} - ${channel.favoriteGroup}"
                }
            )
            .setItems(actions) { _, which ->
                when (which) {
                    0 -> showTvFavoriteGroupDialog(streamId)
                    1 -> {
                        if (tvRepository.moveFavorite(streamId, -1)) {
                            statusText.text = "Favorite moved earlier"
                            refreshCurrentTvResultPage()
                        }
                    }
                    2 -> {
                        if (tvRepository.moveFavorite(streamId, 1)) {
                            statusText.text = "Favorite moved later"
                            refreshCurrentTvResultPage()
                        }
                    }
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }


    private fun showTvFavoriteGroupDialog(
        streamId: String
    ) {
        val presets =
            listOf("News", "Sports", "Local", "Kids", "Other")

        val groups =
            (tvRepository.favoriteGroups() + presets)
                .distinct()
                .sortedBy { it.lowercase() }

        val labels =
            mutableListOf("Ungrouped")
                .apply {
                    addAll(groups)
                    add("Custom...")
                }

        AlertDialog.Builder(this)
            .setTitle("Favorite Group")
            .setItems(labels.toTypedArray()) { _, which ->
                when {
                    which == 0 -> {
                        tvRepository.setFavoriteGroup(streamId, "")
                        refreshCurrentTvResultPage()
                    }
                    which == labels.lastIndex -> {
                        showCustomFavoriteGroupDialog(streamId)
                    }
                    else -> {
                        tvRepository.setFavoriteGroup(
                            streamId,
                            labels[which]
                        )
                        refreshCurrentTvResultPage()
                    }
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }


    private fun showCustomFavoriteGroupDialog(
        streamId: String
    ) {
        val input = EditText(this)
        input.inputType = InputType.TYPE_CLASS_TEXT
        input.hint = "Group name"

        AlertDialog.Builder(this)
            .setTitle("Custom Favorite Group")
            .setView(input)
            .setPositiveButton("Save") { _, _ ->
                val group = input.text.toString().trim()
                if (group.isNotBlank()) {
                    tvRepository.setFavoriteGroup(streamId, group)
                    refreshCurrentTvResultPage()
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }


    private fun showTvChannelProfile(
        streamId: String
    ) {
        val channel =
            tvRepository.getChannel(streamId)
                ?: return

        val container =
            androidx.appcompat.widget.LinearLayoutCompat(this)
        container.orientation =
            androidx.appcompat.widget.LinearLayoutCompat.VERTICAL
        val padding = dp(20)
        container.setPadding(padding, padding, padding, padding)

        fun field(
            hint: String,
            value: String
        ): EditText {
            return EditText(this).apply {
                this.hint = hint
                setText(value)
                setSingleLine(true)
                container.addView(this)
            }
        }

        val name = field("Display name", channel.name)
        val category = field("Category", channel.category)
        val url = field("Stream URL", channel.url)
        val referrer = field("Referer (optional)", channel.referrer.orEmpty())
        val userAgent = field("User-Agent (optional)", channel.userAgent.orEmpty())
        val protect = CheckBox(this).apply {
            text = "Never auto-hide this channel"
            isChecked = channel.protectAutoHide
            container.addView(this)
        }

        AlertDialog.Builder(this)
            .setTitle("Channel Profile")
            .setView(container)
            .setPositiveButton("Save") { _, _ ->
                tvRepository.updateChannelProfile(
                    streamId = streamId,
                    name = name.text.toString(),
                    category = category.text.toString(),
                    url = url.text.toString(),
                    referrer = referrer.text.toString(),
                    userAgent = userAgent.text.toString(),
                    protectAutoHide = protect.isChecked
                )
                statusText.text = "Channel profile saved"
                refreshCurrentTvResultPage()
            }
            .setNeutralButton("Reset") { _, _ ->
                tvRepository.resetChannelProfile(streamId)
                statusText.text = "Channel profile reset"
                refreshCurrentTvResultPage()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }


    private fun showTvSettings() {
        val actions =
            arrayOf(
                "Diagnostics",
                "Catalog / EPG Status",
                "Refresh Catalog",
                "Refresh Current Channel Guide",
                "TV Sources",
                "Export TV Backup",
                "Import TV Backup",
                "Invalidate Catalog Cache",
                "Clear EPG Cache",
                "Reset All Health History"
            )

        AlertDialog.Builder(this)
            .setTitle("TV Settings")
            .setItems(actions) { _, which ->
                when (which) {
                    0 -> showTvDiagnostics()
                    1 -> showTvCatalogStatus()
                    2 -> refreshTvCatalog(force = true)
                    3 -> {
                        val streamId = currentSourceId
                        if (
                            streamId != null &&
                            tvRepository.isTvStreamId(streamId)
                        ) {
                            refreshTvProgramGuide(streamId)
                        } else {
                            statusText.text = "No TV channel is currently selected"
                        }
                    }
                    4 -> showTvSourcesDialog()
                    5 -> tvBackupExportLauncher.launch("privyhub-tv-backup.json")
                    6 -> tvBackupImportLauncher.launch(
                        arrayOf("application/json", "text/plain")
                    )
                    7 -> {
                        tvRepository.invalidateCatalogCache()
                        statusText.text = "Catalog cache invalidated"
                    }
                    8 -> {
                        tvEpgRepository.clearCache()
                        statusText.text = "EPG cache cleared"
                        refreshCurrentTvResultPage()
                    }
                    9 -> {
                        tvRepository.resetAllHealth()
                        statusText.text = "TV health history reset"
                        refreshCurrentTvResultPage()
                    }
                }
            }
            .setNegativeButton("Close", null)
            .show()
    }


    private fun showTvSourcesDialog() {
        val providers = tvRepository.listProviders()
        val labels = mutableListOf("Add M3U URL...")
        labels.addAll(
            providers.map {
                val state = if (it.enabled) "On" else "Off"
                "${it.name}  •  $state"
            }
        )

        AlertDialog.Builder(this)
            .setTitle("TV Sources")
            .setItems(labels.toTypedArray()) { _, which ->
                if (which == 0) {
                    showAddTvProviderDialog()
                } else {
                    showTvProviderActions(
                        providers[which - 1]
                    )
                }
            }
            .setNegativeButton("Close", null)
            .show()
    }


    private fun showAddTvProviderDialog() {
        val container =
            androidx.appcompat.widget.LinearLayoutCompat(this)
        container.orientation =
            androidx.appcompat.widget.LinearLayoutCompat.VERTICAL
        val padding = dp(20)
        container.setPadding(padding, padding, padding, padding)

        val name = EditText(this).apply {
            hint = "Source name"
            setSingleLine(true)
            container.addView(this)
        }
        val url = EditText(this).apply {
            hint = "https://example/path/playlist.m3u"
            inputType =
                InputType.TYPE_CLASS_TEXT or
                    InputType.TYPE_TEXT_VARIATION_URI
            setSingleLine(true)
            container.addView(this)
        }

        val dialog =
            AlertDialog.Builder(this)
                .setTitle("Add M3U URL")
                .setMessage(
                    "This source will use the currently selected TV language (${getTvLanguageName()})."
                )
                .setView(container)
                .setPositiveButton("Add", null)
                .setNegativeButton("Cancel", null)
                .create()

        dialog.setOnShowListener {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener {
                    try {
                        tvRepository.addCustomProvider(
                            name = name.text.toString(),
                            url = url.text.toString(),
                            languageCode = getTvLanguageCode()
                        )
                        dialog.dismiss()
                        refreshTvCatalog(force = true)
                    } catch (error: Exception) {
                        url.error = error.message ?: "Invalid M3U source"
                    }
                }
        }
        dialog.show()
    }


    private fun showTvProviderActions(
        provider: TvProvider
    ) {
        if (provider.providerId == TvRepository.BUILTIN_PROVIDER_ID) {
            AlertDialog.Builder(this)
                .setTitle(provider.name)
                .setMessage("Built-in IPTV-org source. It remains enabled as the default provider.")
                .setPositiveButton("OK", null)
                .show()
            return
        }

        if (provider.builtin) {
            val action = if (provider.enabled) "Disable" else "Enable"
            AlertDialog.Builder(this)
                .setTitle(provider.name)
                .setMessage(
                    "Optional curated provider. Channels merge into the normal PrivyHub " +
                        "categories, search, favorites and health system."
                )
                .setPositiveButton(action) { _, _ ->
                    tvRepository.setProviderEnabled(provider.providerId, !provider.enabled)
                    refreshTvCatalog(force = true)
                }
                .setNegativeButton("Cancel", null)
                .show()
            return
        }

        val actions = arrayOf(if (provider.enabled) "Disable" else "Enable", "Remove")
        AlertDialog.Builder(this)
            .setTitle(provider.name)
            .setItems(actions) { _, which ->
                when (which) {
                    0 -> {
                        tvRepository.setProviderEnabled(provider.providerId, !provider.enabled)
                        refreshTvCatalog(force = true)
                    }
                    1 -> {
                        AlertDialog.Builder(this)
                            .setTitle("Remove ${provider.name}?")
                            .setMessage("The source can be added again later.")
                            .setPositiveButton("Remove") { _, _ ->
                                tvRepository.removeProvider(provider.providerId)
                                refreshTvCatalog(force = true)
                            }
                            .setNegativeButton("Cancel", null)
                            .show()
                    }
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }


    private fun exportTvBackupToUri(
        uri: android.net.Uri
    ) {
        statusText.text = "Exporting TV backup..."

        networkExecutor.execute {
            try {
                val root = JSONObject()
                    .put("format", "privyhub-tv-backup")
                    .put("version", 1)
                    .put("language_code", getTvLanguageCode())
                    .put("language_name", getTvLanguageName())
                    .put("country_code", getTvCountryCode())
                    .put("country_name", getTvCountryName())
                    .put(
                        "tv",
                        JSONObject(
                            tvRepository.exportSettingsJson()
                        )
                    )

                val output =
                    contentResolver.openOutputStream(uri)
                        ?: throw IllegalStateException("Unable to open backup destination")

                output.bufferedWriter().use {
                    it.write(root.toString(2))
                }

                runOnUiThread {
                    statusText.text = "TV backup exported"
                }
            } catch (error: Exception) {
                Log.e(TAG, "TV backup export failed", error)
                runOnUiThread {
                    statusText.text = "TV backup export failed"
                }
            }
        }
    }


    private fun importTvBackupFromUri(
        uri: android.net.Uri
    ) {
        statusText.text = "Importing TV backup..."

        networkExecutor.execute {
            try {
                val input =
                    contentResolver.openInputStream(uri)
                        ?: throw IllegalStateException("Unable to open backup")

                val text =
                    input.bufferedReader().use {
                        it.readText()
                    }

                val root = JSONObject(text)
                if (root.optString("format") != "privyhub-tv-backup") {
                    throw IllegalArgumentException("Not a PrivyHub TV backup")
                }

                val languageCode =
                    root.optString(
                        "language_code",
                        TvRepository.ENGLISH
                    )
                val tvJson =
                    root.getJSONObject("tv")
                        .toString()

                /*
                 * First pass restores provider definitions. Refreshing then
                 * creates any custom-provider streams, and the second pass
                 * can restore their per-channel state as well.
                 */
                tvRepository.importSettingsJson(tvJson)
                tvRepository.ensureCatalog(
                    languageCode = languageCode,
                    force = true
                )
                tvRepository.importSettingsJson(tvJson)

                saveTvLanguage(
                    languageCode,
                    root.optString("language_name", "English")
                )
                saveTvCountry(
                    root.optString("country_code", ""),
                    root.optString("country_name", "All Countries")
                )

                runOnUiThread {
                    statusText.text = "TV backup imported"
                    refreshTvCatalog(force = false)
                }
            } catch (error: Exception) {
                Log.e(TAG, "TV backup import failed", error)
                runOnUiThread {
                    statusText.text = "TV backup import failed"
                }
            }
        }
    }


    private fun showTvCatalogStatus() {
        val catalog =
            tvRepository.catalogStats(
                getTvLanguageCode()
            )
        val epg =
            tvEpgRepository.stats()

        val refreshed =
            if (catalog.refreshedAtMs <= 0L) {
                "Never"
            } else {
                java.text.DateFormat.getDateTimeInstance()
                    .format(java.util.Date(catalog.refreshedAtMs))
            }

        val message =
            buildString {
                append("Language: ${getTvLanguageName()}\n")
                append("Country: ${getTvCountryName()}\n")
                append("Streams: ${catalog.streams}\n")
                append("Favorites: ${catalog.favorites}\n")
                append("Reliable: ${catalog.reliable}\n")
                append("Hidden: ${catalog.hidden}\n")
                append("Enabled providers: ${catalog.providers}\n")
                append("Catalog refreshed: $refreshed\n")
                append("EPG mappings: ${epg.mappings}\n")
                append("Cached programmes: ${epg.programmes}")
            }

        AlertDialog.Builder(this)
            .setTitle("Catalog / EPG Status")
            .setMessage(message)
            .setPositiveButton("OK", null)
            .show()
    }


    private fun showTvDiagnostics() {
        val exo = player
        val runtime = Runtime.getRuntime()
        val usedMemory = runtime.totalMemory() - runtime.freeMemory()
        val bufferMs =
            if (exo == null) {
                0L
            } else {
                (exo.bufferedPosition - exo.currentPosition)
                    .coerceAtLeast(0L)
            }

        val state =
            when (exo?.playbackState) {
                Player.STATE_IDLE -> "Idle"
                Player.STATE_BUFFERING -> "Buffering"
                Player.STATE_READY -> "Ready"
                Player.STATE_ENDED -> "Ended"
                else -> "No player"
            }

        val videoSize = exo?.videoSize
        val resolution =
            if (
                videoSize != null &&
                videoSize.width > 0 &&
                videoSize.height > 0
            ) {
                "${videoSize.width}x${videoSize.height}"
            } else {
                "Unknown"
            }

        val channel =
            currentSourceId?.let {
                tvRepository.getChannel(it)
            }

        val catalog =
            tvRepository.catalogStats(
                getTvLanguageCode()
            )
        val epg = tvEpgRepository.stats()

        val streamType =
            currentPlayback?.url?.let { url ->
                when {
                    url.contains(".m3u8", ignoreCase = true) -> "HLS"
                    url.startsWith("https://") -> "HTTPS stream"
                    url.startsWith("http://") -> "HTTP stream"
                    else -> currentPlayback?.type ?: "Unknown"
                }
            } ?: currentPlayback?.type ?: "None"

        val message =
            buildString {
                append("Playback: $state\n")
                append("Stream: $streamType\n")
                append("Resolution: $resolution\n")
                append("Buffer: ${bufferMs / 1000.0} s\n")
                append("App heap used: ${usedMemory / (1024 * 1024)} MB\n")
                append("App heap max: ${runtime.maxMemory() / (1024 * 1024)} MB\n")
                append("Catalog streams: ${catalog.streams}\n")
                append("EPG programmes cached: ${epg.programmes}")

                if (channel != null) {
                    append("\n\nChannel: ${channel.name}")
                    append("\nProvider: ${channel.providerId}")
                    append("\nSuccesses: ${channel.successCount}")
                    append("\nFailures: ${channel.failureCount}")
                    append("\nConsecutive failures: ${channel.consecutiveFailures}")
                }
            }

        AlertDialog.Builder(this)
            .setTitle("TV Diagnostics")
            .setMessage(message)
            .setPositiveButton("OK", null)
            .show()
    }


    private fun showTvChannelActions(
        node: SourceNode
    ) {
        val channel =
            tvRepository.getChannel(node.id)
                ?: return

        val hidden =
            channel.manualHidden ||
                channel.autoHidden

        val actions =
            arrayOf(
                "Program Guide",
                if (channel.favorite) {
                    "Remove from Favorites"
                } else {
                    "Add to Favorites"
                },
                "Favorite Options",
                "Channel Profile",
                if (hidden) {
                    "Unhide Channel"
                } else {
                    "Hide Channel"
                },
                "Reset Health History",
                "Channel Details"
            )

        AlertDialog.Builder(this)
            .setTitle(channel.name)
            .setItems(actions) { _, which ->
                when (which) {
                    0 -> showTvProgramGuide(channel.streamId)
                    1 -> {
                        val favorite =
                            tvRepository.toggleFavorite(channel.streamId)
                        statusText.text =
                            if (favorite) {
                                "Added to Favorites"
                            } else {
                                "Removed from Favorites"
                            }
                        refreshCurrentTvResultPage()
                    }
                    2 -> showTvFavoriteOptions(channel.streamId)
                    3 -> showTvChannelProfile(channel.streamId)
                    4 -> {
                        val hiddenNow =
                            tvRepository.toggleHidden(channel.streamId)
                        statusText.text =
                            if (hiddenNow) "Channel hidden" else "Channel restored"
                        refreshCurrentTvResultPage()
                    }
                    5 -> {
                        tvRepository.resetHealth(channel.streamId)
                        statusText.text = "Health history reset"
                        refreshCurrentTvResultPage()
                    }
                    6 -> showTvChannelDetails(channel.streamId)
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }


    private fun formatTvGuideTime(
        timestampMs: Long
    ): String {

        return java.text.SimpleDateFormat(
            "h:mm a",
            java.util.Locale.getDefault()
        ).format(
            java.util.Date(
                timestampMs
            )
        )
    }


    private fun showTvProgramGuide(
        streamId: String
    ) {

        val channel =
            tvRepository.getChannel(
                streamId
            ) ?: return

        statusText.text =
            "Loading guide for ${channel.name}..."


        networkExecutor.execute {

            val guide =
                tvEpgRepository.getGuide(
                    channel.channelId
                )


            runOnUiThread {

                val programmes =
                    buildList<TvProgramme> {

                        guide.current?.let {
                            add(
                                it
                            )
                        }

                        addAll(
                            guide.upcoming
                        )
                    }
                    .distinctBy {
                        it.startMs to
                            it.title
                    }
                    .take(
                        10
                    )

                val message =
                    if (programmes.isEmpty()) {

                        "No schedule is currently available for this channel."

                    } else {

                        buildString {

                            for (
                                programme in programmes
                            ) {

                                val current =
                                    guide.current
                                        ?.startMs ==
                                        programme.startMs

                                if (current) {
                                    append("NOW  ")
                                } else {
                                    append(
                                        formatTvGuideTime(
                                            programme.startMs
                                        )
                                    )
                                    append("  ")
                                }

                                append(
                                    programme.title
                                )

                                if (
                                    current &&
                                    programme.stopMs >
                                    programme.startMs
                                ) {
                                    append("  •  until ")
                                    append(
                                        formatTvGuideTime(
                                            programme.stopMs
                                        )
                                    )
                                }

                                append("\\n")
                            }
                        }.trim()
                    }


                AlertDialog.Builder(
                    this
                )
                    .setTitle(
                        "${channel.name} - Program Guide"
                    )
                    .setMessage(
                        message
                    )
                    .setPositiveButton(
                        "OK",
                        null
                    )
                    .setNeutralButton(
                        "Refresh"
                    ) { _, _ ->

                        refreshTvProgramGuide(
                            streamId
                        )
                    }
                    .show()

                statusText.text =
                    if (programmes.isEmpty()) {
                        "No guide data: ${channel.name}"
                    } else {
                        "Guide loaded: ${channel.name}"
                    }

                refreshCurrentTvResultPage()
            }
        }
    }


    private fun refreshTvProgramGuide(
        streamId: String
    ) {

        val channel =
            tvRepository.getChannel(
                streamId
            ) ?: return

        statusText.text =
            "Refreshing guide for ${channel.name}..."


        networkExecutor.execute {

            tvEpgRepository.getGuide(
                channelId = channel.channelId,
                force = true
            )


            runOnUiThread {

                statusText.text =
                    "Guide refreshed: ${channel.name}"

                showTvProgramGuide(
                    streamId
                )
            }
        }
    }


    private fun refreshTvEpgForStream(
        streamId: String
    ) {

        val channel =
            tvRepository.getChannel(
                streamId
            ) ?: return


        networkExecutor.execute {

            tvEpgRepository.getGuide(
                channel.channelId
            )


            runOnUiThread {

                refreshCurrentTvResultPage()
            }
        }
    }


    private fun showTvChannelDetails(
        streamId: String
    ) {

        val channel =
            tvRepository.getChannel(
                streamId
            ) ?: return

        val hiddenReason =
            when {
                channel.manualHidden ->
                    "Manually hidden"
                channel.autoHidden ->
                    "Auto-hidden after repeated failures"
                else ->
                    "Visible"
            }

        val country =
            if (channel.country.isBlank()) {
                "Unknown"
            } else {
                "${tvRepository.countryDisplayName(channel.country)} (${channel.country})"
            }

        val message =
            buildString {
                append("Category: ")
                append(
                    categoryDisplayName(
                        channel.category
                    )
                )
                append("\nCountry: ")
                append(country)
                append("\nQuality: ")
                append(
                    channel.quality ?: "Unknown"
                )
                append("\nSuccesses: ")
                append(
                    channel.successCount
                )
                append("\nFailures: ")
                append(
                    channel.failureCount
                )
                append("\nConsecutive failures: ")
                append(
                    channel.consecutiveFailures
                )
                append("\nState: ")
                append(hiddenReason)
                append("\nProvider: ")
                append(channel.providerId)
                append("\nFavorite group: ")
                append(channel.favoriteGroup.ifBlank { "Ungrouped" })
                append("\nAuto-hide protected: ")
                append(if (channel.protectAutoHide) "Yes" else "No")

                if (!channel.label.isNullOrBlank()) {
                    append("\nUpstream note: ")
                    append(
                        channel.label
                    )
                }
            }


        AlertDialog.Builder(
            this
        )
            .setTitle(
                channel.name
            )
            .setMessage(
                message
            )
            .setPositiveButton(
                "OK",
                null
            )
            .show()
    }


    private fun refreshCurrentTvResultPage() {

        val current =
            navigationStack
                .lastOrNull()
                ?: return

        val request =
            tvResultPages[
                current.id
            ] ?: return

        val languageCode =
            getTvLanguageCode()

        val countryCode =
            getTvCountryCode()

        val currentId =
            current.id


        networkExecutor.execute {

            val count =
                tvRepository.countChannels(
                    languageCode = languageCode,
                    countryCode = countryCode,
                    mode = request.mode,
                    value = request.value,
                    includeHidden = request.includeHidden
                )

            val channels =
                tvRepository.queryChannels(
                    languageCode = languageCode,
                    countryCode = countryCode,
                    mode = request.mode,
                    value = request.value,
                    includeHidden = request.includeHidden,
                    limit = request.limit,
                    offset = request.offset
                )


            runOnUiThread {

                if (
                    navigationStack
                        .lastOrNull()
                        ?.id != currentId
                ) {
                    return@runOnUiThread
                }

                navigationStack[
                    navigationStack.lastIndex
                ] =
                    current.copy(
                        children =
                            buildTvResultChildren(
                                channels = channels,
                                request = request,
                                totalCount = count
                            )
                    )

                statusText.text =
                    if (channels.isEmpty()) {
                        "No matching channels"
                    } else {
                        tvPageStatus(
                            request = request,
                            totalCount = count,
                            visibleCount = channels.size
                        )
                    }

                renderCurrentPage()
            }
        }
    }


    private fun categoryDisplayName(
        raw: String
    ): String {

        return raw
            .replace(
                "_",
                " "
            )
            .trim()
            .split(
                Regex("\\s+")
            )
            .filter {
                it.isNotBlank()
            }
            .joinToString(
                " "
            ) { word ->
                word.replaceFirstChar {
                    if (it.isLowerCase()) {
                        it.titlecase()
                    } else {
                        it.toString()
                    }
                }
            }
            .ifBlank {
                "Other"
            }
    }


    // PrivyHub A2/A3 patch 03: the Game Session / Resume Playing
    // catalog entry is itself a fullscreen affordance when a game is active.
    private fun openGameSessionNode(
        node: SourceNode
    ) {

        val host =
            getCompanionHost()

        if (host.isBlank()) {
            showCompanionSettings()
            return
        }

        statusText.text =
            "Opening game session..."

        networkExecutor.execute {

            try {
                val json =
                    JSONObject(
                        httpGet(
                            "http://$host:$CONTROL_PORT" +
                                "/plugins/games/status"
                        )
                    )

                val active =
                    json.optBoolean(
                        "active",
                        false
                    )

                val paused =
                    json.optBoolean(
                        "paused",
                        false
                    )

                val title =
                    json.optJSONObject(
                        "game"
                    )
                        ?.optString(
                            "title",
                            "Game"
                        )
                        ?: "Game"

                runOnUiThread {
                    if (active) {
                        showGameSessionBanner(
                            title,
                            paused
                        )
                        openNativeGameStream()
                    } else {
                        showGameDetails(
                            node
                        )
                    }
                }

            } catch (error: Exception) {
                Log.e(
                    TAG,
                    "Failed to open game session",
                    error
                )
                runOnUiThread {
                    statusText.text =
                        "Game session unavailable"
                }
            }
        }
    }


    // PrivyHub Phase A6: companion-backed game search.
    private fun showGameSearchDialog() {

        val input =
            android.widget.EditText(
                this
            )

        input.hint =
            "Title or system"

        input.isSingleLine =
            true

        val dialog =
            AlertDialog.Builder(
                this
            )
                .setTitle(
                    "Search Games"
                )
                .setView(
                    input
                )
                .setPositiveButton(
                    "Search",
                    null
                )
                .setNegativeButton(
                    "Cancel",
                    null
                )
                .create()

        dialog.setOnShowListener {

            dialog
                .getButton(
                    AlertDialog.BUTTON_POSITIVE
                )
                .setOnClickListener {

                    val query =
                        input.text
                            ?.toString()
                            ?.trim()
                            .orEmpty()

                    if (query.isBlank()) {

                        input.error =
                            "Enter a title or system"

                        return@setOnClickListener
                    }

                    val encodedQuery =
                        URLEncoder.encode(
                            query,
                            StandardCharsets.UTF_8.name()
                        )

                    dialog.dismiss()

                    loadLazyCategory(
                        SourceNode(
                            id = "games_search_results",
                            name = "Search: $query",
                            nodeType = "category",
                            lazyPath =
                                "/plugins/games/games?view=search&q=$encodedQuery"
                        )
                    )
                }
        }

        dialog.show()
    }

    private fun showGameDetails(
        node: SourceNode
    ) {

        val detailPath =
            node.lazyPath
                ?: return

        val host =
            getCompanionHost()

        if (host.isBlank()) {

            showCompanionSettings()

            return
        }

        statusText.text =
            "Loading ${node.name}..."

        networkExecutor.execute {

            try {

                val response =
                    httpGet(
                        "http://$host:$CONTROL_PORT$detailPath"
                    )

                val json =
                    JSONObject(
                        response
                    )

                val kind =
                    json.optString(
                        "kind",
                        "game"
                    )

                val title =
                    json.optString(
                        "title",
                        node.name
                    )

                val message =
                    when (kind) {

                        "game_session" ->
                            buildGameSessionMessage(
                                json
                            )

                        "native_stream_host" ->
                            buildNativeStreamMessage(
                                json
                            )

                        else ->
                            buildGameCatalogMessage(
                                json
                            )
                    }

                runOnUiThread {

                    val builder =
                        AlertDialog.Builder(
                            this
                        )
                            .setTitle(
                                title
                            )
                            .setMessage(
                                message
                            )
                            .setNegativeButton(
                                "Close",
                                null
                            )

                    node.artworkPath
                        ?.let { artworkPath ->

                            gameArtworkCache.get(
                                artworkPath
                            )
                        }
                        ?.let { bitmap ->

                            builder.setIcon(
                                BitmapDrawable(
                                    resources,
                                    bitmap
                                )
                            )
                        }

                    when (kind) {

                        "game_session" -> {

                            val active =
                                json.optBoolean(
                                    "active",
                                    false
                                )

                            val paused =
                                json.optBoolean(
                                    "paused",
                                    false
                                )

                            statusText.text =
                                when {
                                    active && paused ->
                                        "Game paused - Resume Playing"

                                    active ->
                                        "Game running on companion"

                                    else ->
                                        "Games ready"
                                }

                            if (
                                active &&
                                paused
                            ) {

                                builder.setPositiveButton(
                                    "Resume Playing"
                                ) { _, _ ->

                                    openNativeGameStream()
                                }

                            }

                            if (active) {

                                val activeTitle =
                                    json.optJSONObject(
                                        "game"
                                    )
                                        ?.optString(
                                            "title",
                                            "Game"
                                        )
                                        ?: "Game"

                                showGameSessionBanner(
                                    activeTitle,
                                    paused
                                )
                            }
                        }

                        "native_stream_host" -> {

                            val active =
                                json.optBoolean(
                                    "active",
                                    false
                                )

                            val ready =
                                json.optBoolean(
                                    "ready",
                                    false
                                )

                            statusText.text =
                                when {
                                    active ->
                                        "Native stream running"

                                    ready ->
                                        "Native stream ready"

                                    else ->
                                        "Native stream setup required"
                                }

                            if (ready) {

                                builder.setPositiveButton(
                                    "Open Native Alpha"
                                ) { _, _ ->

                                    openNativeGameStream()
                                }
                            }

                            if (active) {

                                builder.setNeutralButton(
                                    "Stop Native Alpha"
                                ) { _, _ ->

                                    stopNativeGameStreamHost()
                                }
                            }
                        }

                        else -> {

                            val systemName =
                                json.optString(
                                    "system_name",
                                    "Game"
                                )

                            statusText.text =
                                "Games: $systemName"

                            builder.setPositiveButton(
                                "Launch on Companion"
                            ) { _, _ ->

                                showGameLaunchModeDialog(
                                    node.id,
                                    title
                                )
                            }

                            // PrivyHub Phase A6: library-state actions live
                            // behind one stable Options affordance so the
                            // launch button remains uncluttered.
                            builder.setNeutralButton(
                                "Options"
                            ) { _, _ ->

                                showGameLibraryOptionsDialog(
                                    node,
                                    title,
                                    json
                                )
                            }
                        }
                    }

                    builder.show()
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to load game details",
                    error
                )

                runOnUiThread {

                    statusText.text =
                        "Game details unavailable"
                }
            }
        }
    }




    // PrivyHub Phase A6: persistent library-state controls. Favorites
    // are owned by the companion so they survive Android reinstalls and can
    // be shared by future PrivyHub clients.
    private fun showGameLibraryOptionsDialog(
        node: SourceNode,
        title: String,
        detailJson: JSONObject
    ) {

        val favorite =
            detailJson.optBoolean(
                "favorite",
                false
            )

        val controllerSelectable =
            detailJson.optBoolean(
                "controller_profile_selectable",
                false
            )

        val controllerLabel =
            detailJson.optString(
                "controller_profile_label",
                "Controller"
            )

        // PRIVYHUB_PHASE_A_PS1_MULTITAP_ONOFF_UI
        val multitapSelectable =
            detailJson.optBoolean(
                "ps1_multitap_selectable",
                false
            )

        val multitapEnabled =
            detailJson.optBoolean(
                "ps1_multitap_enabled",
                false
            )

        val multitapLabel =
            detailJson.optString(
                "ps1_multitap_label",
                if (multitapEnabled) {
                    "On"
                } else {
                    "Off"
                }
            )

        val playerMode =
            detailJson.optString(
                "player_mode",
                "unknown"
            )
                .trim()
                .lowercase()

        val playerModeSource =
            detailJson.optString(
                "player_mode_source",
                "unknown"
            )
                .trim()
                .lowercase()

        val maxPlayers =
            detailJson.optInt(
                "max_players",
                0
            )

        val playerLabel =
            when (playerMode) {

                "single" ->
                    "Single Player"

                "multi" ->
                    if (maxPlayers > 1) {
                        "Multiplayer ($maxPlayers)"
                    } else {
                        "Multiplayer"
                    }

                else ->
                    "Unknown"
            }

        val playerSourceLabel =
            when (playerModeSource) {

                "manual" ->
                    "Override"

                "metadata" ->
                    "Metadata"

                else ->
                    ""
            }

        val playerOption =
            if (playerSourceLabel.isBlank()) {
                "Players: $playerLabel"
            } else {
                "Players: $playerLabel - $playerSourceLabel"
            }

        val cheatFileCount =
            detailJson.optInt(
                "cheat_file_count",
                0
            )

        val modFileCount =
            detailJson.optInt(
                "mod_file_count",
                0
            )

        val options =
            mutableListOf(
                if (favorite) {
                    "Remove from Favorites"
                } else {
                    "Add to Favorites"
                },
                playerOption
            )

        val userContentIndex =
            options.size

        options.add(
            "Cheats / Mods: $cheatFileCount / $modFileCount"
        )

        val inputProfileIndex =
            options.size

        options.add(
            "Input Profile"
        )


        val controllerIndex =
            if (controllerSelectable) {

                val index =
                    options.size

                options.add(
                    "Controller: $controllerLabel"
                )

                index

            } else {
                -1
            }

        val multitapIndex =
            if (multitapSelectable) {

                val index =
                    options.size

                options.add(
                    "Multitap: $multitapLabel"
                )

                index

            } else {
                -1
            }

        AlertDialog.Builder(this)
            .setTitle(
                "$title - Options"
            )
            .setItems(
                options.toTypedArray()
            ) { _, which ->

                when {

                    which == 0 -> {

                        toggleGameFavorite(
                            node,
                            title
                        )
                    }

                    which == 1 -> {

                        showGamePlayerModeDialog(
                            node,
                            title,
                            detailJson
                        )
                    }

                    which == userContentIndex -> {

                        showGameUserContentDialog(
                            title,
                            detailJson
                        )
                    }

                    which == inputProfileIndex -> {

                        showGameInputProfileDialog(
                            node.id,
                            title
                        )
                    }


                    controllerSelectable &&
                        which == controllerIndex -> {

                        showGameControllerProfileDialog(
                            node,
                            title,
                            detailJson
                        )
                    }

                    multitapSelectable &&
                        which == multitapIndex -> {

                        showGamePs1MultitapDialog(
                            node,
                            title,
                            detailJson
                        )
                    }
                }
            }
            .setNegativeButton(
                "Cancel",
                null
            )
            .show()
    }

    // PrivyHub Phase A7.1: user-supplied cheat/mod catalog only.
    // Nothing listed by this dialog is enabled or applied yet.
    private fun showGameUserContentDialog(
        title: String,
        detailJson: JSONObject
    ) {

        val cheatFiles =
            detailJson.optJSONArray(
                "cheat_files"
            )

        val modFiles =
            detailJson.optJSONArray(
                "mod_files"
            )

        val cheatCount =
            detailJson.optInt(
                "cheat_file_count",
                cheatFiles?.length()
                    ?: 0
            )

        val modCount =
            detailJson.optInt(
                "mod_file_count",
                modFiles?.length()
                    ?: 0
            )

        val message =
            StringBuilder()
                .append(
                    "Managed user content. Cheats and supported softpatch mods can be launched from Launch on Companion."
                )
                .append(
                    "\n\nCheat files ($cheatCount):"
                )

        if (
            cheatFiles == null ||
            cheatFiles.length() == 0
        ) {

            message.append(
                "\nNone found."
            )

        } else {

            val shown =
                minOf(
                    cheatFiles.length(),
                    20
                )

            for (index in 0 until shown) {

                val item =
                    cheatFiles.optJSONObject(
                        index
                    )

                val name =
                    item
                        ?.optString(
                            "name",
                            ""
                        )
                        ?.takeIf {
                            it.isNotBlank()
                        }
                        ?: "Unnamed cheat file"

                message
                    .append(
                        "\n- "
                    )
                    .append(
                        name
                    )
            }

            if (
                cheatFiles.length() > shown
            ) {

                message
                    .append(
                        "\n- ... "
                    )
                    .append(
                        cheatFiles.length() - shown
                    )
                    .append(
                        " more"
                    )
            }
        }

        message.append(
            "\n\nMod patches ($modCount):"
        )

        if (
            modFiles == null ||
            modFiles.length() == 0
        ) {

            message.append(
                "\nNone found."
            )

        } else {

            val shown =
                minOf(
                    modFiles.length(),
                    20
                )

            for (index in 0 until shown) {

                val item =
                    modFiles.optJSONObject(
                        index
                    )

                val name =
                    item
                        ?.optString(
                            "name",
                            ""
                        )
                        ?.takeIf {
                            it.isNotBlank()
                        }
                        ?: "Unnamed mod patch"

                message
                    .append(
                        "\n- "
                    )
                    .append(
                        name
                    )
            }

            if (
                modFiles.length() > shown
            ) {

                message
                    .append(
                        "\n- ... "
                    )
                    .append(
                        modFiles.length() - shown
                    )
                    .append(
                        " more"
                    )
            }
        }

        val managedHint =
            detailJson.optString(
                "user_content_managed_hint",
                ""
            )

        val sidecarHint =
            detailJson.optString(
                "user_content_sidecar_hint",
                ""
            )

        if (
            managedHint.isNotBlank() ||
            sidecarHint.isNotBlank()
        ) {

            message.append(
                "\n\nPrivyHub locations:"
            )

            if (managedHint.isNotBlank()) {

                message
                    .append(
                        "\nManaged: "
                    )
                    .append(
                        managedHint
                    )
            }

            if (sidecarHint.isNotBlank()) {

                message
                    .append(
                        "\nBeside game: "
                    )
                    .append(
                        sidecarHint
                    )
            }
        }

        AlertDialog.Builder(this)
            .setTitle(
                "$title - Cheats / Mods"
            )
            .setMessage(
                message.toString()
            )
            .setPositiveButton(
                "Close",
                null
            )
            .show()
    }

    private fun toggleGameFavorite(
        node: SourceNode,
        title: String
    ) {

        val host =
            getCompanionHost()

        if (host.isBlank()) {

            showCompanionSettings()

            return
        }

        statusText.text =
            "Updating $title..."

        val encodedId =
            URLEncoder.encode(
                node.id,
                StandardCharsets.UTF_8.name()
            )

        networkExecutor.execute {

            try {

                val response =
                    httpPost(
                        "http://$host:$CONTROL_PORT" +
                            "/plugins/games/favorite?id=$encodedId"
                    )

                val json =
                    JSONObject(
                        response
                    )

                val favorite =
                    json.optBoolean(
                        "favorite",
                        false
                    )

                runOnUiThread {

                    statusText.text =
                        if (favorite) {
                            "Added to Favorites: $title"
                        } else {
                            "Removed from Favorites: $title"
                        }

                    // Refresh the visible Games category immediately.
                    // Reopening this game's details later fetches fresh
                    // favorite/controller metadata from the companion.
                    refreshCurrentGameLibraryView()
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to update game favorite",
                    error
                )

                runOnUiThread {

                    statusText.text =
                        "Favorite update failed"

                    AlertDialog.Builder(
                        this
                    )
                        .setTitle(
                            "Favorite update failed"
                        )
                        .setMessage(
                            error.message
                                ?: "Unknown error"
                        )
                        .setPositiveButton(
                            "OK",
                            null
                        )
                        .show()
                }
            }
        }
    }


    private fun showGamePlayerModeDialog(
        node: SourceNode,
        title: String,
        detailJson: JSONObject
    ) {

        val currentMode =
            detailJson.optString(
                "player_mode",
                "unknown"
            )
                .trim()
                .lowercase()

        val currentSource =
            detailJson.optString(
                "player_mode_source",
                "unknown"
            )
                .trim()
                .lowercase()

        val automaticLabel =
            when (currentMode) {

                "single" ->
                    if (currentSource == "metadata") {
                        "Automatic (Single Player)"
                    } else {
                        "Automatic"
                    }

                "multi" ->
                    if (currentSource == "metadata") {
                        "Automatic (Multiplayer)"
                    } else {
                        "Automatic"
                    }

                else ->
                    "Automatic"
            }

        val labels =
            arrayOf(
                automaticLabel,
                "Single Player override",
                "Multiplayer override"
            )

        val modes =
            arrayOf(
                "unknown",
                "single",
                "multi"
            )

        val checkedIndex =
            if (currentSource == "manual") {

                modes.indexOf(
                    currentMode
                )
                    .takeIf {
                        it > 0
                    }
                    ?: 0

            } else {
                0
            }

        AlertDialog.Builder(this)
            .setTitle(
                "$title - Players"
            )
            .setSingleChoiceItems(
                labels,
                checkedIndex
            ) { dialog, which ->

                dialog.dismiss()

                updateGamePlayerMode(
                    node,
                    title,
                    modes[which],
                    when (which) {
                        0 -> "Automatic"
                        1 -> "Single Player override"
                        else -> "Multiplayer override"
                    }
                )
            }
            .setNegativeButton(
                "Cancel",
                null
            )
            .show()
    }

    private fun updateGamePlayerMode(
        node: SourceNode,
        title: String,
        mode: String,
        label: String
    ) {

        val host =
            getCompanionHost()

        if (host.isBlank()) {

            showCompanionSettings()

            return
        }

        val encodedId =
            URLEncoder.encode(
                node.id,
                StandardCharsets.UTF_8.name()
            )

        val encodedMode =
            URLEncoder.encode(
                mode,
                StandardCharsets.UTF_8.name()
            )

        statusText.text =
            "Updating $title..."

        networkExecutor.execute {

            try {

                httpPost(
                    "http://$host:$CONTROL_PORT" +
                        "/plugins/games/player-mode?id=$encodedId&mode=$encodedMode"
                )

                runOnUiThread {

                    statusText.text =
                        "Players: $label - $title"

                    refreshCurrentGameLibraryView()
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to update game player mode",
                    error
                )

                runOnUiThread {

                    statusText.text =
                        "Player classification update failed"

                    AlertDialog.Builder(
                        this
                    )
                        .setTitle(
                            "Player classification failed"
                        )
                        .setMessage(
                            error.message
                                ?: "Unknown error"
                        )
                        .setPositiveButton(
                            "OK",
                            null
                        )
                        .show()
                }
            }
        }
    }

    // PrivyHub Phase A PS1 controller selector
    private fun showGameControllerProfileDialog(
        node: SourceNode,
        title: String,
        json: JSONObject
    ) {

        val options =
            json.optJSONArray(
                "controller_profile_options"
            ) ?: return

        val profileIds =
            mutableListOf<String>()

        val profileLabels =
            mutableListOf<String>()

        for (
            index in
            0 until options.length()
        ) {

            val option =
                options.optJSONObject(
                    index
                ) ?: continue

            val profileId =
                option.optString(
                    "id",
                    ""
                ).trim()

            val label =
                option.optString(
                    "label",
                    profileId
                ).trim()

            if (
                profileId.isBlank() ||
                label.isBlank()
            ) {
                continue
            }

            profileIds.add(
                profileId
            )

            profileLabels.add(
                label
            )
        }

        if (profileIds.isEmpty()) {
            return
        }

        val currentProfile =
            json.optString(
                "controller_profile",
                ""
            )

        val checkedIndex =
            profileIds.indexOf(
                currentProfile
            ).let {
                if (it >= 0) {
                    it
                } else {
                    0
                }
            }

        AlertDialog.Builder(this)
            .setTitle(
                "$title Controller"
            )
            .setSingleChoiceItems(
                profileLabels.toTypedArray(),
                checkedIndex
            ) { dialog, which ->

                if (
                    which in
                    profileIds.indices
                ) {

                    val profile =
                        profileIds[
                            which
                        ]

                    dialog.dismiss()

                    setGameControllerProfile(
                        node,
                        title,
                        profile
                    )
                }
            }
            .setNegativeButton(
                "Cancel",
                null
            )
            .show()
    }


    private fun setGameControllerProfile(
        node: SourceNode,
        title: String,
        profile: String
    ) {

        val host =
            getCompanionHost()

        if (host.isBlank()) {

            showCompanionSettings()

            return
        }

        statusText.text =
            "Updating controller..."

        networkExecutor.execute {

            try {

                val gameId =
                    URLEncoder.encode(
                        node.id,
                        "UTF-8"
                    )

                val encodedProfile =
                    URLEncoder.encode(
                        profile,
                        "UTF-8"
                    )

                val response =
                    httpPost(
                        "http://$host:$CONTROL_PORT" +
                            "/plugins/games/controller-profile" +
                            "?id=$gameId&profile=$encodedProfile"
                    )

                val result =
                    JSONObject(
                        response
                    )

                val label =
                    result.optString(
                        "label",
                        profile
                    )

                runOnUiThread {

                    statusText.text =
                        "Controller: $label"

                    showGameDetails(
                        node
                    )
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to update game controller profile",
                    error
                )

                runOnUiThread {

                    statusText.text =
                        "Controller update failed"

                    AlertDialog.Builder(
                        this
                    )
                        .setTitle(
                            "$title Controller"
                        )
                        .setMessage(
                            error.message
                                ?: "Unknown error"
                        )
                        .setPositiveButton(
                            "OK",
                            null
                        )
                        .show()
                }
            }
        }
    }


    // PRIVYHUB_PHASE_A_PS1_MULTITAP_ONOFF_UI
    private fun showGamePs1MultitapDialog(
        node: SourceNode,
        title: String,
        json: JSONObject
    ) {

        val enabled =
            json.optBoolean(
                "ps1_multitap_enabled",
                false
            )

        val labels =
            arrayOf(
                "Off",
                "On"
            )

        val checkedIndex =
            if (enabled) {
                1
            } else {
                0
            }

        AlertDialog.Builder(this)
            .setTitle(
                "$title Multitap"
            )
            .setSingleChoiceItems(
                labels,
                checkedIndex
            ) { dialog, which ->

                dialog.dismiss()

                setGamePs1Multitap(
                    node,
                    title,
                    which == 1
                )
            }
            .setNegativeButton(
                "Cancel",
                null
            )
            .show()
    }


    private fun setGamePs1Multitap(
        node: SourceNode,
        title: String,
        enabled: Boolean
    ) {

        val host =
            getCompanionHost()

        if (host.isBlank()) {
            showCompanionSettings()
            return
        }

        statusText.text =
            "Updating multitap..."

        networkExecutor.execute {

            try {

                val gameId =
                    URLEncoder.encode(
                        node.id,
                        "UTF-8"
                    )

                val response =
                    httpPost(
                        "http://$host:$CONTROL_PORT" +
                            "/plugins/games/ps1-multitap" +
                            "?id=$gameId&enabled=$enabled"
                    )

                val result =
                    JSONObject(
                        response
                    )

                val active =
                    result.optBoolean(
                        "enabled",
                        enabled
                    )

                runOnUiThread {

                    statusText.text =
                        if (active) {
                            "Multitap: On"
                        } else {
                            "Multitap: Off"
                        }

                    showGameDetails(
                        node
                    )
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to update PS1 multitap",
                    error
                )

                runOnUiThread {

                    statusText.text =
                        "Multitap update failed"

                    AlertDialog.Builder(
                        this
                    )
                        .setTitle(
                            "$title Multitap"
                        )
                        .setMessage(
                            error.message
                                ?: "Unknown error"
                        )
                        .setPositiveButton(
                            "OK",
                            null
                        )
                        .show()
                }
            }
        }
    }


    private fun buildGameCatalogMessage(
        json: JSONObject
    ): String {

        val systemName =
            json.optString(
                "system_name",
                "Unknown"
            )

        val title =
            json.optString(
                "title",
                ""
            )

        val canonicalTitle =
            json.optString(
                "canonical_title",
                ""
            )

        val metadataAvailable =
            json.optBoolean(
                "metadata_available",
                false
            )

        val details =
            StringBuilder()
                .append(
                    "System: "
                )
                .append(
                    systemName
                )

        if (
            metadataAvailable &&
            canonicalTitle.isNotBlank() &&
            canonicalTitle != title
        ) {

            details
                .append(
                    "\nCatalog title: "
                )
                .append(
                    canonicalTitle
                )
        }

        if (metadataAvailable) {

            val region =
                json.optString(
                    "region",
                    ""
                )

            val releaseYear =
                json.optInt(
                    "release_year",
                    0
                )

            val genre =
                json.optString(
                    "genre",
                    ""
                )

            val developer =
                json.optString(
                    "developer",
                    ""
                )

            val publisher =
                json.optString(
                    "publisher",
                    ""
                )

            val provider =
                json.optString(
                    "metadata_provider",
                    ""
                )

            if (region.isNotBlank()) {

                details
                    .append(
                        "\nRegion: "
                    )
                    .append(
                        region
                    )
            }

            if (releaseYear > 0) {

                details
                    .append(
                        "\nReleased: "
                    )
                    .append(
                        releaseYear
                    )
            }

            if (genre.isNotBlank()) {

                details
                    .append(
                        "\nGenre: "
                    )
                    .append(
                        genre
                    )
            }

            if (developer.isNotBlank()) {

                details
                    .append(
                        "\nDeveloper: "
                    )
                    .append(
                        developer
                    )
            }

            if (publisher.isNotBlank()) {

                details
                    .append(
                        "\nPublisher: "
                    )
                    .append(
                        publisher
                    )
            }

            if (provider.isNotBlank()) {

                val providerLabel =
                    when (
                        provider
                            .trim()
                            .lowercase()
                    ) {

                        "libretro" ->
                            "Libretro"

                        else ->
                            provider
                    }

                details
                    .append(
                        "\nMetadata: "
                    )
                    .append(
                        providerLabel
                    )
            }
        }

        val playerMode =
            json.optString(
                "player_mode",
                "unknown"
            )
                .trim()
                .lowercase()

        val playerModeSource =
            json.optString(
                "player_mode_source",
                "unknown"
            )
                .trim()
                .lowercase()

        val maxPlayers =
            json.optInt(
                "max_players",
                0
            )

        val playerLabel =
            when (playerMode) {

                "single" ->
                    if (maxPlayers == 1) {
                        "1 - Single Player"
                    } else {
                        "Single Player"
                    }

                "multi" ->
                    if (maxPlayers > 1) {
                        "Multiplayer (up to $maxPlayers players)"
                    } else {
                        "Multiplayer"
                    }

                else ->
                    "Unknown"
            }

        details
            .append(
                "\nPlayers: "
            )
            .append(
                playerLabel
            )

        when (playerModeSource) {

            "manual" ->
                details.append(
                    " (override)"
                )

            "metadata" ->
                details.append(
                    " (metadata)"
                )
        }

        val boxArtAvailable =
            json.optBoolean(
                "box_art_available",
                false
            )

        details
            .append(
                "\nBox art: "
            )
            .append(
                if (boxArtAvailable) {
                    "Local cache"
                } else {
                    "Not available"
                }
            )

        if (
            json.optBoolean(
                "user_content_catalog_only",
                false
            )
        ) {

            val cheatFileCount =
                json.optInt(
                    "cheat_file_count",
                    0
                )

            val modFileCount =
                json.optInt(
                    "mod_file_count",
                    0
                )

            details
                .append(
                    "\nCheat files: "
                )
                .append(
                    cheatFileCount
                )
                .append(
                    "\nMod patches: "
                )
                .append(
                    modFileCount
                )
        }

        val format =
            json.optString(
                "format",
                ""
            )

        val sizeBytes =
            json.optLong(
                "size_bytes",
                0L
            )

        val relativePath =
            json.optString(
                "relative_path",
                ""
            )

        if (format.isNotBlank()) {

            details
                .append(
                    "\nFormat: "
                )
                .append(
                    format.uppercase()
                )
        }

        if (sizeBytes > 0L) {

            details
                .append(
                    "\nSize: "
                )
                .append(
                    formatGameSize(
                        sizeBytes
                    )
                )
        }

        if (relativePath.isNotBlank()) {

            details
                .append(
                    "\nLibrary: "
                )
                .append(
                    relativePath
                )
        }

        val favorite =
            json.optBoolean(
                "favorite",
                false
            )

        val playCount =
            json.optInt(
                "play_count",
                0
            )

        val continueAvailable =
            json.optBoolean(
                "continue_available",
                false
            )

        details
            .append(
                "\nFavorite: "
            )
            .append(
                if (favorite) {
                    "Yes"
                } else {
                    "No"
                }
            )

        if (playCount > 0) {

            details
                .append(
                    "\nPlay count: "
                )
                .append(
                    playCount
                )
        }

        if (continueAvailable) {

            details.append(
                "\nPrivyHub save state: Available"
            )
        }

        val controllerLabel =
            json.optString(
                "controller_profile_label",
                ""
            )

        if (controllerLabel.isNotBlank()) {

            details
                .append(
                    "\nController: "
                )
                .append(
                    controllerLabel
                )
        }

        details.append(
            "\n\nLaunch starts the game on the PrivyHub companion. " +
                "Streaming uses PrivyHub's native transport."
        )

        return details.toString()
    }

    private fun buildGameSessionMessage(
        json: JSONObject
    ): String {

        val active =
            json.optBoolean(
                "active",
                false
            )

        val paused =
            json.optBoolean(
                "paused",
                false
            )

        val ready =
            json.optBoolean(
                "ready",
                false
            )

        val details =
            StringBuilder()

        details.append(
            if (
                active &&
                paused
            ) {
                "Game: PAUSED"
            } else if (active) {
                "Game: RUNNING"
            } else if (ready) {
                "Game: READY"
            } else {
                "Game: SETUP REQUIRED"
            }
        )

        val game =
            json.optJSONObject(
                "game"
            )

        if (game != null) {

            details
                .append(
                    "\nTitle: "
                )
                .append(
                    game.optString(
                        "title",
                        "Unknown"
                    )
                )

            details
                .append(
                    "\nSystem: "
                )
                .append(
                    game.optString(
                        "system_name",
                        "Unknown"
                    )
                )
        }

        if (
            !json.isNull(
                "elapsed_seconds"
            )
        ) {

            val elapsed =
                json.optLong(
                    "elapsed_seconds",
                    -1L
                )

            if (elapsed >= 0L) {

                details
                    .append(
                        "\nRuntime: "
                    )
                    .append(
                        formatTime(
                            elapsed * 1000L
                        )
                    )
            }
        }

        val streamHost =
            json.optJSONObject(
                "stream_host"
            )

        if (streamHost != null) {

            details
                .append(
                    "\nStream Host: "
                )
                .append(
                    when {
                        streamHost.optBoolean(
                            "active",
                            false
                        ) ->
                            "RUNNING"

                        streamHost.optBoolean(
                            "ready",
                            false
                        ) ->
                            "READY"

                        else ->
                            "SETUP REQUIRED"
                    }
                )
        }

        val missing =
            json.optJSONArray(
                "missing_cores"
            )

        if (
            missing != null &&
            missing.length() > 0
        ) {

            val names =
                mutableListOf<String>()

            for (
                index in
                0 until missing.length()
            ) {

                names.add(
                    missing.optString(
                        index
                    )
                )
            }

            details
                .append(
                    "\nMissing cores: "
                )
                .append(
                    names.joinToString(
                        ", "
                    )
                )
        }

        val runtimeError =
            json.optString(
                "runtime_error",
                ""
            )

        if (runtimeError.isNotBlank()) {

            details
                .append(
                    "\nEmulator error: "
                )
                .append(
                    runtimeError
                )
        }

        val message =
            json.optString(
                "message",
                ""
            )

        if (message.isNotBlank()) {

            details
                .append(
                    "\n\n"
                )
                .append(
                    message
                )
        }

        return details.toString()
    }


    private fun buildNativeStreamMessage(
        json: JSONObject
    ): String {

        val active =
            json.optBoolean(
                "active",
                false
            )

        val ready =
            json.optBoolean(
                "ready",
                false
            )

        return buildString {
            append(
                "Status: "
            )

            append(
                when {
                    active ->
                        "RUNNING"

                    ready ->
                        "READY"

                    else ->
                        "SETUP REQUIRED"
                }
            )

            append(
                "\nProfile: "
            )
            append(
                json.optInt(
                    "width",
                    1280
                )
            )
            append(
                "x"
            )
            append(
                json.optInt(
                    "height",
                    720
                )
            )
            append(
                "@"
            )
            append(
                json.optInt(
                    "fps",
                    60
                )
            )

            append(
                "\nCodec: H.264 NVENC"
            )

            append(
                "\nTransport: RTP/UDP"
            )

            append(
                "\nAudio: not implemented"
            )

            append(
                "\nController: not implemented"
            )

            val message =
                json.optString(
                    "message",
                    ""
                )

            if (message.isNotBlank()) {
                append(
                    "\n\n"
                )
                append(
                    message
                )
            }
        }
    }


    private fun openNativeGameStream() {

        val host =
            getCompanionHost()

        if (host.isBlank()) {

            showCompanionSettings()

            return
        }

        startActivity(
            Intent(
                this,
                NativeStreamActivity::class.java
            ).apply {
                putExtra(
                    NativeStreamActivity.EXTRA_COMPANION_HOST,
                    host
                )

                putExtra(
                    NativeStreamActivity.EXTRA_GAME_TITLE,
                    gameSessionTitle
                        ?: "Game"
                )
            }
        )
    }


    private fun stopNativeGameStreamHost() {

        val host =
            getCompanionHost()

        if (host.isBlank()) {
            return
        }

        statusText.text =
            "Stopping native stream..."

        networkExecutor.execute {

            try {

                httpPost(
                    "http://$host:$CONTROL_PORT" +
                        "/plugins/games/native-stream-stop"
                )

                runOnUiThread {

                    statusText.text =
                        "Native stream stopped"
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to stop native stream",
                    error
                )

                runOnUiThread {

                    statusText.text =
                        "Native stream stop failed"
                }
            }
        }
    }




    // PrivyHub Phase A5 follow-up: choose the initial game state before
    // performing the normal launch handoff. "Start Fresh" means the core's
    // normal boot path; it does not erase native SRAM or memory-card data.



    // PRIVYHUB_A7_PATCH_11_A7_4_SOFTPATCH_MODS_ADB_FIX
    private fun showGameExtrasMenu(
        gameId: String,
        title: String
    ) {
        AlertDialog.Builder(this)
            .setTitle("Extras — $title")
            .setItems(arrayOf("Cheats", "Mods")) { _, which ->
                when (which) {
                    0 -> showGameCheatSelector(gameId, title)
                    1 -> showGameModSelector(gameId, title)
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun showGameModSelector(
        gameId: String,
        title: String
    ) {
        val host = getCompanionHost()
        if (host.isBlank()) {
            showCompanionSettings()
            return
        }
        statusText.text = "Loading mods for $title..."
        networkExecutor.execute {
            try {
                val profileJson = JSONObject(
                    httpPost(
                        "http://$host:$CONTROL_PORT" +
                            "/plugins/games/mod-profiles?id=$gameId"
                    )
                )
                val catalogJson = JSONObject(
                    httpPost(
                        "http://$host:$CONTROL_PORT" +
                            "/plugins/games/mod-catalog?id=$gameId"
                    )
                )
                val profiles = profileJson.optJSONArray("profiles") ?: JSONArray()
                val mods = catalogJson.optJSONArray("mods") ?: JSONArray()
                val supported = catalogJson.optBoolean("supported", false)
                val reason = catalogJson.optString("reason", "")
                val managedDirectory = catalogJson.optString("managed_directory", "")
                runOnUiThread {
                    statusText.text = "Games ready"
                    if (!supported) {
                        AlertDialog.Builder(this)
                            .setTitle("Mods unavailable")
                            .setMessage(
                                if (reason == "core_softpatching_unsupported") {
                                    "The configured core for this system does not support RetroArch softpatching."
                                } else {
                                    "Softpatch mods are unavailable for this game."
                                }
                            )
                            .setPositiveButton("OK", null)
                            .show()
                    } else if (profiles.length() <= 0 && mods.length() <= 0) {
                        AlertDialog.Builder(this)
                            .setTitle("Mods")
                            .setMessage(
                                "No IPS/BPS/UPS/XDelta mods were found.\n\n" +
                                    "Managed folder:\n$managedDirectory"
                            )
                            .setPositiveButton("OK", null)
                            .show()
                    } else {
                        showGameModProfileMenu(gameId, title, profiles, mods)
                    }
                }
            } catch (error: Exception) {
                Log.e(TAG, "Failed to load game mods", error)
                runOnUiThread {
                    statusText.text = "Mod catalog unavailable"
                    AlertDialog.Builder(this)
                        .setTitle("Mods unavailable")
                        .setMessage(error.message ?: "Unknown error")
                        .setPositiveButton("OK", null)
                        .show()
                }
            }
        }
    }

    private fun showGameModProfileMenu(
        gameId: String,
        title: String,
        profiles: JSONArray,
        mods: JSONArray
    ) {
        val labels = mutableListOf<String>()
        val profileObjects = mutableListOf<JSONObject>()
        for (index in 0 until profiles.length()) {
            val profile = profiles.optJSONObject(index) ?: continue
            val filename = profile.optString("filename", "").trim()
            val modIndex = profile.optInt("mod_index", -1)
            if (filename.isBlank() || modIndex < 0) continue
            val occupied = profile.optJSONArray("occupied_slots") ?: JSONArray()
            val slots = mutableListOf<Int>()
            for (slotIndex in 0 until occupied.length()) {
                val slot = occupied.optInt(slotIndex, -1)
                if (slot > 0) slots.add(slot)
            }
            val suffix = when {
                slots.size == 1 -> " — Slot ${slots[0]}"
                slots.size > 1 -> " — Slots ${slots.joinToString(", ")}"
                profile.optBoolean("persistent_save_present", false) -> " — Game save present"
                else -> " — No state saves"
            }
            labels.add("Mod: $filename$suffix")
            profileObjects.add(profile)
        }
        if (mods.length() > 0) labels.add("New Mod Session")
        if (labels.isEmpty()) {
            AlertDialog.Builder(this)
                .setTitle("Mods")
                .setMessage("No usable mod profiles or patch files are available.")
                .setPositiveButton("OK", null)
                .show()
            return
        }
        AlertDialog.Builder(this)
            .setTitle("Mods — $title")
            .setItems(labels.toTypedArray()) { _, which ->
                if (which < profileObjects.size) {
                    showExistingGameModProfileDialog(
                        gameId = gameId,
                        title = title,
                        profile = profileObjects[which]
                    )
                } else {
                    showGameModEntryDialog(gameId, title, mods)
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun showExistingGameModProfileDialog(
        gameId: String,
        title: String,
        profile: JSONObject
    ) {
        val modIndex = profile.optInt("mod_index", -1)
        val filename = profile.optString("filename", "").trim()
        if (modIndex < 0 || filename.isBlank()) {
            AlertDialog.Builder(this)
                .setTitle("Mod profile unavailable")
                .setMessage("This saved mod profile cannot be reconstructed safely.")
                .setPositiveButton("OK", null)
                .show()
            return
        }
        val profileLabel = "Mod: $filename"
        val occupied = profile.optJSONArray("occupied_slots") ?: JSONArray()
        val slots = mutableListOf<Int>()
        for (index in 0 until occupied.length()) {
            val slot = occupied.optInt(index, -1)
            if (slot > 0) slots.add(slot)
        }
        val details = StringBuilder()
            .append(profileLabel)
            .append("\nFormat: ")
            .append(profile.optString("format", "").uppercase())
            .append("\nSave states: ")
            .append(if (slots.isEmpty()) "None" else slots.joinToString(", ") { "Slot $it" })
            .append("\nPersistent game save: ")
            .append(if (profile.optBoolean("persistent_save_present", false)) "Present" else "None detected")
        val builder = AlertDialog.Builder(this)
            .setTitle("Existing Mod Profile")
            .setMessage(details.toString())
            .setPositiveButton("Start Fresh") { _, _ ->
                launchGameOnCompanion(
                    gameId = gameId,
                    title = title,
                    loadSaveAfterLaunch = false,
                    cheatProfileLabel = profileLabel,
                    modIndex = modIndex
                )
            }
            .setNeutralButton("Cancel", null)
        if (slots.isNotEmpty()) {
            builder.setNegativeButton("Load Save") { _, _ ->
                launchGameOnCompanion(
                    gameId = gameId,
                    title = title,
                    loadSaveAfterLaunch = true,
                    cheatProfileLabel = profileLabel,
                    modIndex = modIndex
                )
            }
        }
        builder.show()
    }

    private fun showGameModEntryDialog(
        gameId: String,
        title: String,
        mods: JSONArray
    ) {
        if (mods.length() <= 0) return
        val usable = mutableListOf<JSONObject>()
        val labels = mutableListOf<String>()
        for (index in 0 until mods.length()) {
            val mod = mods.optJSONObject(index) ?: continue
            val modIndex = mod.optInt("mod_index", -1)
            val filename = mod.optString("filename", "").trim()
            if (modIndex < 0 || filename.isBlank()) continue
            usable.add(mod)
            val format = mod.optString("format", "").uppercase()
            labels.add(if (format.isBlank()) filename else "$filename ($format)")
        }
        if (usable.isEmpty()) return
        AlertDialog.Builder(this)
            .setTitle("New Mod Session — $title")
            .setItems(labels.toTypedArray()) { _, which ->
                val mod = usable[which]
                val modIndex = mod.optInt("mod_index", -1)
                val filename = mod.optString("filename", "Mod")
                val profileLabel = "Mod: $filename"
                AlertDialog.Builder(this)
                    .setTitle("Start $profileLabel?")
                    .setMessage(
                        "This launches an isolated mod profile. Normal saves and cheat profiles are not modified."
                    )
                    .setPositiveButton("Start Mod Session") { _, _ ->
                        launchGameOnCompanion(
                            gameId = gameId,
                            title = title,
                            loadSaveAfterLaunch = false,
                            cheatProfileLabel = profileLabel,
                            modIndex = modIndex
                        )
                    }
                    .setNegativeButton("Cancel", null)
                    .show()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    // PRIVYHUB_A7_PATCH_10V3_ANDROID_CHEAT_GUI
        // PRIVYHUB_A7_PATCH_10V4_EXISTING_CHEAT_PROFILES
    private fun showGameCheatSelector(
        gameId: String,
        title: String
    ) {
        val host = getCompanionHost()
        if (host.isBlank()) {
            showCompanionSettings()
            return
        }

        statusText.text = "Loading cheat profiles for $title..."
        networkExecutor.execute {
            try {
                val profileResponse = httpPost(
                    "http://$host:$CONTROL_PORT" +
                        "/plugins/games/cheat-profiles?id=$gameId"
                )
                val catalogResponse = httpPost(
                    "http://$host:$CONTROL_PORT" +
                        "/plugins/games/cheat-catalog?id=$gameId"
                )
                val profileJson = JSONObject(profileResponse)
                val catalogJson = JSONObject(catalogResponse)
                val profiles = profileJson.optJSONArray("profiles") ?: JSONArray()
                val sources = catalogJson.optJSONArray("sources") ?: JSONArray()

                runOnUiThread {
                    statusText.text = "Games ready"
                    if (profiles.length() <= 0 && sources.length() <= 0) {
                        AlertDialog.Builder(this)
                            .setTitle("Cheats")
                            .setMessage("No validated cheats are available for this game.")
                            .setPositiveButton("OK", null)
                            .show()
                    } else {
                        showGameCheatProfileMenu(
                            gameId = gameId,
                            title = title,
                            profiles = profiles,
                            sources = sources
                        )
                    }
                }
            } catch (error: Exception) {
                Log.e(TAG, "Failed to load game cheat profiles", error)
                runOnUiThread {
                    statusText.text = "Cheat profiles unavailable"
                    AlertDialog.Builder(this)
                        .setTitle("Cheats unavailable")
                        .setMessage(error.message ?: "Unknown error")
                        .setPositiveButton("OK", null)
                        .show()
                }
            }
        }
    }

    private fun showGameCheatProfileMenu(
        gameId: String,
        title: String,
        profiles: JSONArray,
        sources: JSONArray
    ) {
        val labels = mutableListOf<String>()
        val profileObjects = mutableListOf<JSONObject>()

        for (index in 0 until profiles.length()) {
            val profile = profiles.optJSONObject(index) ?: continue
            val enabled = profile.optJSONArray("enabled_cheats") ?: JSONArray()
            val descriptions = mutableListOf<String>()
            for (entryIndex in 0 until enabled.length()) {
                val description = enabled
                    .optJSONObject(entryIndex)
                    ?.optString("description", "")
                    ?.trim()
                    .orEmpty()
                if (description.isNotBlank()) {
                    descriptions.add(description)
                }
            }
            if (descriptions.isEmpty()) {
                continue
            }

            val profileLabel = GameCheatUiState.buildProfileLabel(descriptions)
            val occupied = profile.optJSONArray("occupied_slots") ?: JSONArray()
            val slotNumbers = mutableListOf<Int>()
            for (slotIndex in 0 until occupied.length()) {
                val slot = occupied.optInt(slotIndex, -1)
                if (slot > 0) {
                    slotNumbers.add(slot)
                }
            }
            val suffix = when {
                slotNumbers.size == 1 -> " — Slot ${slotNumbers[0]}"
                slotNumbers.size > 1 -> " — Slots ${slotNumbers.joinToString(", ")}"
                profile.optBoolean("persistent_save_present", false) -> " — Game save present"
                else -> " — No state saves"
            }
            labels.add(profileLabel + suffix)
            profileObjects.add(profile)
        }

        if (sources.length() > 0) {
            labels.add("New Cheat Session")
        }

        if (labels.isEmpty()) {
            AlertDialog.Builder(this)
                .setTitle("Cheats")
                .setMessage("No usable cheat profiles or validated cheat sources are available.")
                .setPositiveButton("OK", null)
                .show()
            return
        }

        AlertDialog.Builder(this)
            .setTitle("Cheats — $title")
            .setItems(labels.toTypedArray()) { _, which ->
                if (which < profileObjects.size) {
                    showExistingGameCheatProfileDialog(
                        gameId = gameId,
                        title = title,
                        profile = profileObjects[which]
                    )
                } else {
                    showGameCheatSourceDialog(gameId, title, sources)
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun showExistingGameCheatProfileDialog(
        gameId: String,
        title: String,
        profile: JSONObject
    ) {
        val sourceIndex = profile.optInt("source_index", -1)
        val rawIndexes = profile.optJSONArray("enabled_cheat_indexes") ?: JSONArray()
        val enabledIndexes = mutableListOf<Int>()
        for (index in 0 until rawIndexes.length()) {
            val value = rawIndexes.optInt(index, -1)
            if (value >= 0) {
                enabledIndexes.add(value)
            }
        }

        val enabled = profile.optJSONArray("enabled_cheats") ?: JSONArray()
        val descriptions = mutableListOf<String>()
        for (index in 0 until enabled.length()) {
            val description = enabled
                .optJSONObject(index)
                ?.optString("description", "")
                ?.trim()
                .orEmpty()
            if (description.isNotBlank()) {
                descriptions.add(description)
            }
        }

        if (sourceIndex < 0 || enabledIndexes.isEmpty() || descriptions.isEmpty()) {
            AlertDialog.Builder(this)
                .setTitle("Cheat profile unavailable")
                .setMessage("This saved cheat profile is incomplete and cannot be launched safely.")
                .setPositiveButton("OK", null)
                .show()
            return
        }

        val profileLabel = GameCheatUiState.buildProfileLabel(descriptions)
        val occupied = profile.optJSONArray("occupied_slots") ?: JSONArray()
        val occupiedSlots = mutableListOf<Int>()
        for (index in 0 until occupied.length()) {
            val slot = occupied.optInt(index, -1)
            if (slot > 0) {
                occupiedSlots.add(slot)
            }
        }

        val details = StringBuilder()
            .append(profileLabel)
            .append("\nSource: ")
            .append(profile.optString("source_filename", "Validated cheat source"))
            .append("\nSave states: ")
            .append(
                if (occupiedSlots.isEmpty()) {
                    "None"
                } else {
                    occupiedSlots.joinToString(", ") { "Slot $it" }
                }
            )
            .append("\nPersistent game save: ")
            .append(
                if (profile.optBoolean("persistent_save_present", false)) {
                    "Present"
                } else {
                    "None detected"
                }
            )

        val builder = AlertDialog.Builder(this)
            .setTitle("Existing Cheat Profile")
            .setMessage(details.toString())
            .setPositiveButton("Start Fresh") { _, _ ->
                launchGameOnCompanion(
                    gameId = gameId,
                    title = title,
                    loadSaveAfterLaunch = false,
                    cheatSourceIndex = sourceIndex,
                    cheatEnabledIndexes = enabledIndexes,
                    cheatProfileLabel = profileLabel
                )
            }
            .setNeutralButton("Cancel", null)

        if (occupiedSlots.isNotEmpty()) {
            builder.setNegativeButton("Load Save") { _, _ ->
                launchGameOnCompanion(
                    gameId = gameId,
                    title = title,
                    loadSaveAfterLaunch = true,
                    cheatSourceIndex = sourceIndex,
                    cheatEnabledIndexes = enabledIndexes,
                    cheatProfileLabel = profileLabel
                )
            }
        }

        builder.show()
    }

    private fun showGameCheatSourceDialog(
        gameId: String,
        title: String,
        sources: JSONArray
    ) {
        if (sources.length() == 1) {
            showGameCheatEntryDialog(gameId, title, sources.getJSONObject(0))
            return
        }

        var selectedSource = 0
        val labels = Array(sources.length()) { index ->
            val source = sources.getJSONObject(index)
            val filename = source.optString("filename", "Cheat source ${index + 1}")
            val count = source.optJSONArray("entries")?.length() ?: 0
            "$filename ($count cheats)"
        }

        AlertDialog.Builder(this)
            .setTitle("Cheat source — $title")
            .setSingleChoiceItems(labels, 0) { _, which -> selectedSource = which }
            .setPositiveButton("Next") { _, _ ->
                showGameCheatEntryDialog(
                    gameId,
                    title,
                    sources.getJSONObject(selectedSource)
                )
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun showGameCheatEntryDialog(
        gameId: String,
        title: String,
        source: JSONObject
    ) {
        val sourceIndex = source.optInt("source_index", -1)
        val entries = source.optJSONArray("entries") ?: JSONArray()
        if (sourceIndex < 0 || entries.length() <= 0) {
            AlertDialog.Builder(this)
                .setTitle("Cheats unavailable")
                .setMessage("This cheat source has no selectable entries.")
                .setPositiveButton("OK", null)
                .show()
            return
        }

        val labels = Array(entries.length()) { index ->
            entries.getJSONObject(index).optString("description", "Cheat ${index + 1}")
        }
        val indexes = IntArray(entries.length()) { index ->
            entries.getJSONObject(index).optInt("index", -1)
        }
        val checked = BooleanArray(entries.length())

        AlertDialog.Builder(this)
            .setTitle("Cheats — $title")
            .setMultiChoiceItems(labels, checked) { _, which, enabled ->
                checked[which] = enabled
            }
            .setPositiveButton("Launch Cheat Session") { _, _ ->
                val selectedIndexes = mutableListOf<Int>()
                val selectedDescriptions = mutableListOf<String>()
                for (index in checked.indices) {
                    if (checked[index] && indexes[index] >= 0) {
                        selectedIndexes.add(indexes[index])
                        selectedDescriptions.add(labels[index])
                    }
                }

                if (selectedIndexes.isEmpty()) {
                    AlertDialog.Builder(this)
                        .setTitle("No cheats selected")
                        .setMessage("Select at least one cheat, or use Start Fresh for a normal session.")
                        .setPositiveButton("OK", null)
                        .show()
                } else {
                    val profileLabel =
                        GameCheatUiState.buildProfileLabel(selectedDescriptions)
                    launchGameOnCompanion(
                        gameId = gameId,
                        title = title,
                        loadSaveAfterLaunch = false,
                        cheatSourceIndex = sourceIndex,
                        cheatEnabledIndexes = selectedIndexes,
                        cheatProfileLabel = profileLabel
                    )
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    // PRIVYHUB_A8_PATCH_03_ANDROID_INPUT_PROFILE_EDITOR
    private fun inputProfileQuery(
        values: Map<String, String>
    ): String {

        return values.entries.joinToString("&") { entry ->

            URLEncoder.encode(
                entry.key,
                StandardCharsets.UTF_8.name()
            ) +
                "=" +
                URLEncoder.encode(
                    entry.value,
                    StandardCharsets.UTF_8.name()
                )
        }
    }


    private fun postInputProfileAction(
        action: String,
        values: Map<String, String>
    ): JSONObject {

        val host =
            getCompanionHost()

        if (host.isBlank()) {

            throw IllegalStateException(
                "Companion host is not configured."
            )
        }

        val query =
            inputProfileQuery(
                values
            )

        return JSONObject(
            httpPost(
                "http://$host:$CONTROL_PORT" +
                    "/plugins/games/$action?$query"
            )
        )
    }


    private fun inputProfileStrings(
        array: JSONArray?
    ): List<String> {

        if (array == null) {
            return emptyList()
        }

        val values =
            mutableListOf<String>()

        for (index in 0 until array.length()) {

            val value =
                array.optString(
                    index,
                    ""
                )
                    .trim()
                    .lowercase()

            if (value.isNotBlank()) {
                values.add(value)
            }
        }

        return values
    }


    // PRIVYHUB_PHASE_A_FOUR_PLAYER_A8_PROFILE_EXTENSION
    private fun inputProfilePlayers(
        payload: JSONObject
    ): List<String> {

        return inputProfileStrings(
            payload.optJSONObject(
                "capabilities"
            )
                ?.optJSONArray(
                    "players"
                )
        )
    }


    private fun inputProfilePlayerLabel(
        player: String
    ): String {

        val normalized =
            player.trim()
                .lowercase()

        val number =
            normalized.removePrefix(
                "player"
            )
                .toIntOrNull()

        return if (
            number != null &&
            normalized == "player$number"
        ) {
            "Player $number"
        } else {
            player
        }
    }


    private fun inputProfileTargetLabel(
        target: String
    ): String {

        return when (
            target.trim().lowercase()
        ) {

            "up" -> "D-pad Up"
            "down" -> "D-pad Down"
            "left" -> "D-pad Left"
            "right" -> "D-pad Right"
            "a" -> "A"
            "b" -> "B"
            "x" -> "X"
            "y" -> "Y"
            "l" -> "LB"
            "r" -> "RB"
            "l2" -> "LT"
            "r2" -> "RT"
            "l3" -> "L3"
            "r3" -> "R3"
            "select" -> "Back"
            "start" -> "Start"
            "left_stick_left" -> "Left Stick Left"
            "left_stick_right" -> "Left Stick Right"
            "left_stick_up" -> "Left Stick Up"
            "left_stick_down" -> "Left Stick Down"
            "right_stick_left" -> "Right Stick Left"
            "right_stick_right" -> "Right Stick Right"
            "right_stick_up" -> "Right Stick Up"
            "right_stick_down" -> "Right Stick Down"
            else -> target
        }
    }

    private fun inputProfileSourceLabel(
        source: String
    ): String {

        return when (
            source.trim().lowercase()
        ) {

            "up" -> "D-pad Up"
            "down" -> "D-pad Down"
            "left" -> "D-pad Left"
            "right" -> "D-pad Right"
            "a" -> "A"
            "b" -> "B"
            "x" -> "X"
            "y" -> "Y"
            "l" -> "LB"
            "r" -> "RB"
            "l2" -> "LT"
            "r2" -> "RT"
            "l3" -> "L3"
            "r3" -> "R3"
            "select" -> "Back"
            "start" -> "Start"
            "left_stick_left" -> "Left Stick Left"
            "left_stick_right" -> "Left Stick Right"
            "left_stick_up" -> "Left Stick Up"
            "left_stick_down" -> "Left Stick Down"
            "right_stick_left" -> "Right Stick Left"
            "right_stick_right" -> "Right Stick Right"
            "right_stick_up" -> "Right Stick Up"
            "right_stick_down" -> "Right Stick Down"
            else -> source
        }
    }

    private fun inputProfileMappingCopy(
        profile: JSONObject
    ): JSONObject {

        val existing =
            profile.optJSONObject(
                "mapping"
            )

        return if (existing == null) {
            JSONObject()
        } else {
            JSONObject(
                existing.toString()
            )
        }
    }


    // PRIVYHUB_A8_PATCH_03V4_COMPLETE_DIRECTIONAL_EDITOR
    // PRIVYHUB_A8_PATCH_03V5_EDITOR_UI_REACHABILITY
    private fun inputProfileEditorTargets(
        payload: JSONObject
    ): List<String> {

        return inputProfileStrings(
            payload.optJSONObject(
                "capabilities"
            )
                ?.optJSONArray(
                    "editor_targets"
                )
        )
    }


    private fun inputProfileEditorSources(
        payload: JSONObject
    ): List<String> {

        return inputProfileStrings(
            payload.optJSONObject(
                "capabilities"
            )
                ?.optJSONArray(
                    "editor_sources"
                )
        )
    }


    private fun inputProfileEditorDefaultMapping(
        payload: JSONObject
    ): LinkedHashMap<String, String> {

        val targets =
            inputProfileEditorTargets(
                payload
            )

        val sources =
            inputProfileEditorSources(
                payload
            )

        val rawDefault =
            payload.optJSONObject(
                "capabilities"
            )
                ?.optJSONObject(
                    "editor_default_mapping"
                )
                ?: throw IllegalStateException(
                    "Companion did not provide the default directional mapping."
                )

        if (
            targets.isEmpty() ||
            sources.isEmpty() ||
            targets.size != sources.size
        ) {

            throw IllegalStateException(
                "Companion directional input capabilities are incomplete."
            )
        }

        val result =
            linkedMapOf<String, String>()

        for (target in targets) {

            val source =
                rawDefault.optString(
                    target,
                    ""
                )
                    .trim()
                    .lowercase()

            if (source !in sources) {

                throw IllegalStateException(
                    "Default input mapping is invalid for $target."
                )
            }

            result[target] = source
        }

        if (
            result.values.toSet().size !=
            sources.size
        ) {

            throw IllegalStateException(
                "Default input mapping is not one-to-one."
            )
        }

        return result
    }


    private fun inputProfileMappingJson(
        mapping: Map<String, String>
    ): JSONObject {

        val result = JSONObject()

        for ((target, source) in mapping) {
            result.put(
                target,
                source
            )
        }

        return result
    }


    private fun inputProfileCompleteDefaultJson(
        payload: JSONObject
    ): JSONObject {

        val defaultMapping =
            inputProfileEditorDefaultMapping(
                payload
            )

        val players =
            inputProfilePlayers(
                payload
            )

        if (players.isEmpty()) {
            throw IllegalStateException(
                "Companion did not provide supported input-profile players."
            )
        }

        val result =
            JSONObject()

        for (player in players) {
            result.put(
                player,
                inputProfileMappingJson(
                    defaultMapping
                )
            )
        }

        return result
    }

    private fun inputProfileWorkingPlayerMapping(
        profile: JSONObject,
        payload: JSONObject,
        player: String
    ): LinkedHashMap<String, String> {

        val working =
            inputProfileEditorDefaultMapping(
                payload
            )

        val rawPlayer =
            profile.optJSONObject(
                "mapping"
            )
                ?.optJSONObject(
                    player
                )
                ?: return working

        for (target in working.keys.toList()) {

            if (rawPlayer.has(target)) {

                working[target] =
                    rawPlayer.optString(
                        target,
                        ""
                    )
                        .trim()
                        .lowercase()
            }
        }

        val legacyAxes =
            mapOf(
                "left_x" to Pair(
                    "left_stick_left",
                    "left_stick_right"
                ),
                "left_y" to Pair(
                    "left_stick_up",
                    "left_stick_down"
                ),
                "right_x" to Pair(
                    "right_stick_left",
                    "right_stick_right"
                ),
                "right_y" to Pair(
                    "right_stick_up",
                    "right_stick_down"
                )
            )

        for ((legacyTarget, targetPair) in legacyAxes) {

            if (!rawPlayer.has(legacyTarget)) {
                continue
            }

            val legacySource =
                rawPlayer.optString(
                    legacyTarget,
                    ""
                )
                    .trim()
                    .lowercase()

            val sourcePair =
                legacyAxes[
                    legacySource
                ]
                    ?: continue

            working[targetPair.first] =
                sourcePair.first

            working[targetPair.second] =
                sourcePair.second
        }

        return working
    }


    private fun inputProfileInvalidTargets(
        targets: List<String>,
        sources: List<String>,
        working: Map<String, String>
    ): Set<String> {

        val counts =
            mutableMapOf<String, Int>()

        for (target in targets) {

            val source =
                working[target]
                    .orEmpty()

            if (source.isNotBlank()) {
                counts[source] =
                    (counts[source] ?: 0) + 1
            }
        }

        return targets.filter { target ->

            val source =
                working[target]
                    .orEmpty()

            source.isBlank() ||
                source !in sources ||
                counts[source] != 1
        }.toSet()
    }


    private fun inputProfileSavedMapping(
        profile: JSONObject,
        payload: JSONObject,
        player: String,
        working: Map<String, String>
    ): JSONObject {

        val result =
            inputProfileMappingCopy(
                profile
            )

        val playerMapping =
            result.optJSONObject(
                player
            )
                ?: JSONObject()

        val removable =
            mutableListOf<String>()

        val iterator =
            playerMapping.keys()

        while (iterator.hasNext()) {

            val key =
                iterator.next()

            if (
                key in inputProfileEditorTargets(
                    payload
                ) ||
                key in setOf(
                    "left_x",
                    "left_y",
                    "right_x",
                    "right_y"
                )
            ) {
                removable.add(key)
            }
        }

        for (key in removable) {
            playerMapping.remove(key)
        }

        for ((target, source) in working) {
            playerMapping.put(
                target,
                source
            )
        }

        result.put(
            player,
            playerMapping
        )

        return result
    }

    private fun showGameInputProfileDialog(
        gameId: String,
        title: String
    ) {

        val host =
            getCompanionHost()

        if (host.isBlank()) {

            showCompanionSettings()

            return
        }

        statusText.text =
            "Loading input profiles for $title..."

        val encodedId =
            URLEncoder.encode(
                gameId,
                StandardCharsets.UTF_8.name()
            )

        networkExecutor.execute {

            try {

                val payload =
                    JSONObject(
                        httpGet(
                            "http://$host:$CONTROL_PORT" +
                                "/plugins/games/input-profiles?id=$encodedId"
                        )
                    )

                runOnUiThread {

                    statusText.text =
                        "Games ready"

                    showGameInputProfileMenu(
                        gameId,
                        title,
                        payload
                    )
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to load input profiles",
                    error
                )

                runOnUiThread {

                    statusText.text =
                        "Input profiles unavailable"

                    AlertDialog.Builder(this)
                        .setTitle(
                            "Input profiles unavailable"
                        )
                        .setMessage(
                            error.message
                                ?: "Unknown error"
                        )
                        .setPositiveButton(
                            "OK",
                            null
                        )
                        .show()
                }
            }
        }
    }


    private fun showGameInputProfileMenu(
        gameId: String,
        title: String,
        payload: JSONObject
    ) {

        val profiles =
            payload.optJSONArray(
                "profiles"
            )
                ?: JSONArray()

        val effective =
            payload.optJSONObject(
                "effective"
            )

        val effectiveId =
            effective
                ?.optString(
                    "profile_id",
                    "default"
                )
                ?.trim()
                ?.lowercase()
                ?: "default"

        val effectiveName =
            effective
                ?.optString(
                    "profile_name",
                    "Default"
                )
                ?.takeIf {
                    it.isNotBlank()
                }
                ?: "Default"

        val profileObjects =
            mutableListOf<JSONObject>()

        val labels =
            mutableListOf<String>()

        for (
            index in
            0 until profiles.length()
        ) {

            val profile =
                profiles.optJSONObject(
                    index
                )
                    ?: continue

            val profileId =
                profile.optString(
                    "id",
                    ""
                )
                    .trim()
                    .lowercase()

            val profileName =
                profile.optString(
                    "name",
                    profileId
                )
                    .takeIf {
                        it.isNotBlank()
                    }
                    ?: profileId

            if (
                profileId.isBlank()
            ) {
                continue
            }

            labels.add(
                if (
                    profileId == effectiveId
                ) {
                    "Assign $profileName (Current)"
                } else {
                    "Assign $profileName"
                }
            )

            profileObjects.add(
                profile
            )
        }

        val effectiveCustomProfile =
            profileObjects.firstOrNull { profile ->

                profile.optString(
                    "id",
                    ""
                )
                    .trim()
                    .lowercase() == effectiveId &&
                    !profile.optBoolean(
                        "builtin",
                        false
                    )
            }

        val editPlayerIndexes =
            linkedMapOf<Int, String>()

        if (effectiveCustomProfile != null) {

            for (player in inputProfilePlayers(payload)) {

                val index =
                    labels.size

                labels.add(
                    "Edit Current ${inputProfilePlayerLabel(player)} Mapping"
                )

                editPlayerIndexes[index] =
                    player
            }
        }

        val createIndex =
            labels.size

        labels.add(
            "Create New Profile"
        )

        val manageIndex =
            labels.size

        labels.add(
            "Manage Custom Profiles"
        )

        // PRIVYHUB_A8_PATCH_03V3_DIALOG_LIST_FIX
        AlertDialog.Builder(this)
            .setTitle(
                "Input Profile - Current: $effectiveName"
            )
            .setItems(
                labels.toTypedArray()
            ) { _, which ->

                when {

                    which <
                        profileObjects.size -> {

                        val profile =
                            profileObjects[
                                which
                            ]

                        assignGameInputProfile(
                            gameId,
                            title,
                            profile.optString(
                                "id",
                                "default"
                            )
                        )
                    }

                    effectiveCustomProfile != null &&
                        editPlayerIndexes.containsKey(
                            which
                        ) -> {

                        val player =
                            editPlayerIndexes[
                                which
                            ]

                        if (player != null) {
                            showEditInputProfilePlayerDialog(
                                gameId,
                                title,
                                effectiveCustomProfile,
                                payload,
                                player
                            )
                        }
                    }

                    which ==
                        createIndex -> {

                        showCreateInputProfileDialog(
                            gameId,
                            title,
                            payload
                        )
                    }

                    which ==
                        manageIndex -> {

                        showManageInputProfilesDialog(
                            gameId,
                            title,
                            payload
                        )
                    }
                }
            }
            .setNegativeButton(
                "Cancel",
                null
            )
            .show()
    }


    private fun assignGameInputProfile(
        gameId: String,
        title: String,
        profileId: String
    ) {

        statusText.text =
            "Assigning input profile..."

        networkExecutor.execute {

            try {

                val result =
                    postInputProfileAction(
                        "input-profile-assign",
                        mapOf(
                            "id" to gameId,
                            "profile_id" to profileId
                        )
                    )

                val profileName =
                    result.optString(
                        "profile_name",
                        "Input profile"
                    )

                runOnUiThread {

                    statusText.text =
                        "Input profile: $profileName"

                    AlertDialog.Builder(this)
                        .setTitle(
                            "Input profile assigned"
                        )
                        .setMessage(
                            "$profileName will be used the next time $title launches."
                        )
                        .setPositiveButton(
                            "OK",
                            null
                        )
                        .show()
                }

            } catch (error: Exception) {

                showInputProfileNetworkError(
                    "Unable to assign input profile",
                    error
                )
            }
        }
    }


    private fun showCreateInputProfileDialog(
        gameId: String,
        title: String,
        payload: JSONObject
    ) {

        val input =
            EditText(
                this
            )

        input.setText(
            "Custom Profile"
        )

        input.selectAll()

        AlertDialog.Builder(this)
            .setTitle(
                "Create Input Profile"
            )
            .setMessage(
                "Creates a complete one-to-one gameplay mapping from the validated Default layout."
            )
            .setView(
                input
            )
            .setPositiveButton(
                "Create"
            ) { _, _ ->

                val name =
                    input.text
                        .toString()
                        .trim()

                if (name.isBlank()) {

                    AlertDialog.Builder(this)
                        .setTitle(
                            "Invalid profile name"
                        )
                        .setMessage(
                            "Profile name cannot be blank."
                        )
                        .setPositiveButton(
                            "OK",
                            null
                        )
                        .show()

                } else {

                    createAndAssignInputProfile(
                        gameId,
                        title,
                        name,
                        payload
                    )
                }
            }
            .setNegativeButton(
                "Cancel",
                null
            )
            .show()
    }

    private fun createAndAssignInputProfile(
        gameId: String,
        title: String,
        name: String,
        payload: JSONObject
    ) {

        statusText.text =
            "Creating input profile..."

        val mapping =
            try {
                inputProfileCompleteDefaultJson(
                    payload
                )
            } catch (error: Exception) {
                showInputProfileNetworkError(
                    "Unable to build default input mapping",
                    error
                )
                return
            }

        networkExecutor.execute {

            try {

                val created =
                    postInputProfileAction(
                        "input-profile-create",
                        mapOf(
                            "name" to name,
                            "mapping" to mapping.toString()
                        )
                    )

                val profile =
                    created.optJSONObject(
                        "profile"
                    )
                        ?: throw IllegalStateException(
                            "Companion did not return the created input profile."
                        )

                val profileId =
                    profile.optString(
                        "id",
                        ""
                    )
                        .trim()

                if (profileId.isBlank()) {
                    throw IllegalStateException(
                        "Created input profile is missing an id."
                    )
                }

                postInputProfileAction(
                    "input-profile-assign",
                    mapOf(
                        "id" to gameId,
                        "profile_id" to profileId
                    )
                )

                runOnUiThread {

                    statusText.text =
                        "Input profile: $name"

                    showEditInputProfilePlayerDialog(
                        gameId,
                        title,
                        profile,
                        payload,
                        "player1"
                    )
                }

            } catch (error: Exception) {

                showInputProfileNetworkError(
                    "Unable to create input profile",
                    error
                )
            }
        }
    }

    private fun showManageInputProfilesDialog(
        gameId: String,
        title: String,
        payload: JSONObject
    ) {

        val profiles =
            payload.optJSONArray(
                "profiles"
            )
                ?: JSONArray()

        val customProfiles =
            mutableListOf<JSONObject>()

        val labels =
            mutableListOf<String>()

        for (
            index in
            0 until profiles.length()
        ) {

            val profile =
                profiles.optJSONObject(
                    index
                )
                    ?: continue

            if (
                profile.optBoolean(
                    "builtin",
                    false
                )
            ) {
                continue
            }

            val name =
                profile.optString(
                    "name",
                    "Custom Profile"
                )

            customProfiles.add(
                profile
            )

            labels.add(
                name
            )
        }

        if (customProfiles.isEmpty()) {

            AlertDialog.Builder(this)
                .setTitle(
                    "Custom Input Profiles"
                )
                .setMessage(
                    "No custom input profiles exist yet."
                )
                .setPositiveButton(
                    "Create"
                ) { _, _ ->

                    showCreateInputProfileDialog(
                        gameId,
                        title,
                        payload
                    )
                }
                .setNegativeButton(
                    "Cancel",
                    null
                )
                .show()

            return
        }

        AlertDialog.Builder(this)
            .setTitle(
                "Custom Input Profiles"
            )
            .setItems(
                labels.toTypedArray()
            ) { _, which ->

                if (
                    which in
                    customProfiles.indices
                ) {

                    showInputProfileActionsDialog(
                        gameId,
                        title,
                        customProfiles[
                            which
                        ],
                        payload
                    )
                }
            }
            .setPositiveButton(
                "Create New"
            ) { _, _ ->

                showCreateInputProfileDialog(
                    gameId,
                    title,
                    payload
                )
            }
            .setNegativeButton(
                "Cancel",
                null
            )
            .show()
    }


    private fun showInputProfileActionsDialog(
        gameId: String,
        title: String,
        profile: JSONObject,
        payload: JSONObject
    ) {

        val profileName =
            profile.optString(
                "name",
                "Custom Profile"
            )

        val options =
            mutableListOf<String>()

        val editPlayerIndexes =
            linkedMapOf<Int, String>()

        options.add(
            "Assign to This Game"
        )

        for (player in inputProfilePlayers(payload)) {

            val index =
                options.size

            options.add(
                "Edit ${inputProfilePlayerLabel(player)} Mapping"
            )

            editPlayerIndexes[index] =
                player
        }

        val renameIndex =
            options.size
        options.add(
            "Rename"
        )

        val duplicateIndex =
            options.size
        options.add(
            "Duplicate"
        )

        val resetIndex =
            options.size
        options.add(
            "Reset Mapping to Default"
        )

        val deleteIndex =
            options.size
        options.add(
            "Delete"
        )

        AlertDialog.Builder(this)
            .setTitle(
                "$profileName - Actions"
            )
            .setItems(
                options.toTypedArray()
            ) { _, which ->

                when {

                    which == 0 ->
                        assignGameInputProfile(
                            gameId,
                            title,
                            profile.optString(
                                "id",
                                ""
                            )
                        )

                    editPlayerIndexes.containsKey(
                        which
                    ) -> {

                        val player =
                            editPlayerIndexes[
                                which
                            ]

                        if (player != null) {
                            showEditInputProfilePlayerDialog(
                                gameId,
                                title,
                                profile,
                                payload,
                                player
                            )
                        }
                    }

                    which == renameIndex ->
                        showRenameInputProfileDialog(
                            gameId,
                            title,
                            profile
                        )

                    which == duplicateIndex ->
                        showDuplicateInputProfileDialog(
                            gameId,
                            title,
                            profile,
                            payload
                        )

                    which == resetIndex ->
                        confirmResetInputProfile(
                            gameId,
                            title,
                            profile,
                            payload
                        )

                    which == deleteIndex ->
                        confirmDeleteInputProfile(
                            gameId,
                            title,
                            profile
                        )
                }
            }
            .setNegativeButton(
                "Cancel",
                null
            )
            .show()
    }

    private fun showRenameInputProfileDialog(
        gameId: String,
        title: String,
        profile: JSONObject
    ) {

        val input =
            EditText(
                this
            )

        input.setText(
            profile.optString(
                "name",
                ""
            )
        )

        input.selectAll()

        AlertDialog.Builder(this)
            .setTitle(
                "Rename Input Profile"
            )
            .setView(
                input
            )
            .setPositiveButton(
                "Rename"
            ) { _, _ ->

                val name =
                    input.text
                        .toString()
                        .trim()

                if (name.isNotBlank()) {

                    updateInputProfileName(
                        gameId,
                        title,
                        profile.optString(
                            "id",
                            ""
                        ),
                        name
                    )
                }
            }
            .setNegativeButton(
                "Cancel",
                null
            )
            .show()
    }


    private fun updateInputProfileName(
        gameId: String,
        title: String,
        profileId: String,
        name: String
    ) {

        statusText.text =
            "Renaming input profile..."

        networkExecutor.execute {

            try {

                postInputProfileAction(
                    "input-profile-update",
                    mapOf(
                        "profile_id" to profileId,
                        "name" to name
                    )
                )

                runOnUiThread {

                    statusText.text =
                        "Games ready"

                    showGameInputProfileDialog(
                        gameId,
                        title
                    )
                }

            } catch (error: Exception) {

                showInputProfileNetworkError(
                    "Unable to rename input profile",
                    error
                )
            }
        }
    }


    private fun showDuplicateInputProfileDialog(
        gameId: String,
        title: String,
        profile: JSONObject,
        payload: JSONObject
    ) {

        val input =
            EditText(
                this
            )

        input.setText(
            profile.optString(
                "name",
                "Custom Profile"
            ) + " Copy"
        )

        input.selectAll()

        AlertDialog.Builder(this)
            .setTitle(
                "Duplicate Input Profile"
            )
            .setMessage(
                "The duplicate keeps the same gameplay mapping for all supported players."
            )
            .setView(
                input
            )
            .setPositiveButton(
                "Duplicate"
            ) { _, _ ->

                val name =
                    input.text
                        .toString()
                        .trim()

                if (name.isNotBlank()) {

                    duplicateInputProfile(
                        gameId,
                        title,
                        profile,
                        payload,
                        name
                    )
                }
            }
            .setNegativeButton(
                "Cancel",
                null
            )
            .show()
    }

    private fun duplicateInputProfile(
        gameId: String,
        title: String,
        profile: JSONObject,
        payload: JSONObject,
        name: String
    ) {

        statusText.text =
            "Duplicating input profile..."

        val mapping =
            inputProfileMappingCopy(
                profile
            )

        if (mapping.length() == 0) {
            val defaults =
                inputProfileCompleteDefaultJson(
                    payload
                )

            for (player in inputProfilePlayers(payload)) {
                mapping.put(
                    player,
                    defaults.optJSONObject(
                        player
                    )
                )
            }
        }

        networkExecutor.execute {

            try {

                postInputProfileAction(
                    "input-profile-create",
                    mapOf(
                        "name" to name,
                        "mapping" to mapping.toString()
                    )
                )

                runOnUiThread {

                    statusText.text =
                        "Games ready"

                    showGameInputProfileDialog(
                        gameId,
                        title
                    )
                }

            } catch (error: Exception) {

                showInputProfileNetworkError(
                    "Unable to duplicate input profile",
                    error
                )
            }
        }
    }

    // PRIVYHUB_A8_PATCH_03V6_SIMPLE_CURRENT_MAPPING_EDITOR
    // PRIVYHUB_A8_PATCH_03V7_XBOX_LABELS_PLAYER_SYNC
    // PRIVYHUB_A8_PATCH_03V8_CONFLICT_CHOICES_RED
    private fun showEditInputProfilePlayerDialog(
        gameId: String,
        title: String,
        profile: JSONObject,
        payload: JSONObject,
        player: String
    ) {

        val targets =
            inputProfileEditorTargets(
                payload
            )

        val sources =
            inputProfileEditorSources(
                payload
            )

        if (
            targets.isEmpty() ||
            sources.isEmpty()
        ) {

            AlertDialog.Builder(this)
                .setTitle(
                    "Input mapping unavailable"
                )
                .setMessage(
                    "The companion did not provide directional mapping capabilities."
                )
                .setPositiveButton(
                    "OK",
                    null
                )
                .show()

            return
        }

        val working =
            try {
                inputProfileWorkingPlayerMapping(
                    profile,
                    payload,
                    player
                )
            } catch (error: Exception) {
                showInputProfileNetworkError(
                    "Unable to open input mapping",
                    error
                )
                return
            }

        val playerLabel =
            inputProfilePlayerLabel(
                player
            )

        val container =
            android.widget.LinearLayout(
                this
            ).apply {
                orientation =
                    android.widget.LinearLayout.VERTICAL
                setPadding(
                    24,
                    16,
                    24,
                    16
                )
            }

        val heading =
            TextView(
                this
            ).apply {
                text =
                    "Current mapping"
                textSize =
                    18f
                setPadding(
                    8,
                    8,
                    8,
                    8
                )
            }

        container.addView(
            heading
        )

        val status =
            TextView(
                this
            ).apply {
                text =
                    "Tap Change for the control you want to update."
                setPadding(
                    8,
                    0,
                    8,
                    20
                )
            }

        val defaultStatusColors =
            status.textColors

        container.addView(
            status
        )

        val otherPlayers =
            inputProfilePlayers(
                payload
            )
                .filter { candidate ->
                    candidate != player
                }

        val syncButton =
            Button(
                this
            ).apply {
                text =
                    "Copy Mapping From Another Player"
                isAllCaps =
                    false
                isEnabled =
                    otherPlayers.isNotEmpty()
            }

        container.addView(
            syncButton,
            android.widget.LinearLayout.LayoutParams(
                android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                android.view.ViewGroup.LayoutParams.WRAP_CONTENT
            )
        )

        val targetLabels =
            linkedMapOf<String, TextView>()

        val currentLabels =
            linkedMapOf<String, TextView>()

        val changeButtons =
            linkedMapOf<String, Button>()

        val defaultTargetColors =
            mutableMapOf<String, android.content.res.ColorStateList>()

        val defaultCurrentColors =
            mutableMapOf<String, android.content.res.ColorStateList>()

        val defaultButtonColors =
            mutableMapOf<String, android.content.res.ColorStateList>()

        for (target in targets) {

            val row =
                android.widget.LinearLayout(
                    this
                ).apply {
                    orientation =
                        android.widget.LinearLayout.VERTICAL
                    setPadding(
                        8,
                        8,
                        8,
                        20
                    )
                }

            val targetLabel =
                TextView(
                    this
                ).apply {
                    text =
                        inputProfileTargetLabel(
                            target
                        )
                    textSize =
                        17f
                }

            val currentLabel =
                TextView(
                    this
                ).apply {
                    setPadding(
                        0,
                        4,
                        0,
                        8
                    )
                }

            val changeButton =
                Button(
                    this
                ).apply {
                    text =
                        "Change"
                    isAllCaps =
                        false
                }

            targetLabels[target] =
                targetLabel

            currentLabels[target] =
                currentLabel

            changeButtons[target] =
                changeButton

            defaultTargetColors[target] =
                targetLabel.textColors

            defaultCurrentColors[target] =
                currentLabel.textColors

            defaultButtonColors[target] =
                changeButton.textColors

            row.addView(
                targetLabel
            )

            row.addView(
                currentLabel
            )

            row.addView(
                changeButton,
                android.widget.LinearLayout.LayoutParams(
                    android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                    android.view.ViewGroup.LayoutParams.WRAP_CONTENT
                )
            )

            container.addView(
                row,
                android.widget.LinearLayout.LayoutParams(
                    android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                    android.view.ViewGroup.LayoutParams.WRAP_CONTENT
                )
            )
        }

        val scroll =
            android.widget.ScrollView(
                this
            ).apply {
                addView(
                    container
                )
            }

        val dialog =
            AlertDialog.Builder(this)
                .setTitle(
                    "${profile.optString("name", "Input Profile")} - $playerLabel"
                )
                .setView(
                    scroll
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

        fun invalidTargets(): Set<String> {
            return inputProfileInvalidTargets(
                targets,
                sources,
                working
            )
        }

        fun refreshRows() {

            val invalid =
                invalidTargets()

            for (target in targets) {

                val source =
                    working[target]
                        .orEmpty()

                val targetLabel =
                    targetLabels[target]
                        ?: continue

                val currentLabel =
                    currentLabels[target]
                        ?: continue

                val changeButton =
                    changeButtons[target]
                        ?: continue

                currentLabel.text =
                    "Current: " +
                        if (source.isBlank()) {
                            "UNMAPPED"
                        } else {
                            inputProfileSourceLabel(
                                source
                            )
                        }

                if (target in invalid) {
                    targetLabel.setTextColor(
                        0xFFFF5252.toInt()
                    )
                    currentLabel.setTextColor(
                        0xFFFF5252.toInt()
                    )
                    changeButton.setTextColor(
                        0xFFFF5252.toInt()
                    )
                } else {
                    targetLabel.setTextColor(
                        defaultTargetColors[target]
                            ?: targetLabel.textColors
                    )
                    currentLabel.setTextColor(
                        defaultCurrentColors[target]
                            ?: currentLabel.textColors
                    )
                    changeButton.setTextColor(
                        defaultButtonColors[target]
                            ?: changeButton.textColors
                    )
                }
            }

            if (invalid.isEmpty()) {
                status.text =
                    "Mapping valid - Save is enabled."
                status.setTextColor(
                    defaultStatusColors
                )
            } else {
                status.text =
                    "${invalid.size} row(s) need attention. Fix red rows before Save."
                status.setTextColor(
                    0xFFFF5252.toInt()
                )
            }

            dialog.getButton(
                android.content.DialogInterface.BUTTON_POSITIVE
            )?.isEnabled =
                invalid.isEmpty()
        }

        syncButton.setOnClickListener {

            val labels =
                otherPlayers.map { candidate ->
                    inputProfilePlayerLabel(
                        candidate
                    )
                }.toTypedArray()

            AlertDialog.Builder(this)
                .setTitle(
                    "Copy $playerLabel Mapping From"
                )
                .setItems(
                    labels
                ) { _, which ->

                    if (which in otherPlayers.indices) {

                        val sourcePlayer =
                            otherPlayers[
                                which
                            ]

                        try {
                            val sourceMapping =
                                inputProfileWorkingPlayerMapping(
                                    profile,
                                    payload,
                                    sourcePlayer
                                )

                            working.clear()
                            working.putAll(
                                sourceMapping
                            )

                            refreshRows()

                        } catch (error: Exception) {
                            showInputProfileNetworkError(
                                "Unable to copy player mapping",
                                error
                            )
                        }
                    }
                }
                .setNegativeButton(
                    "Cancel",
                    null
                )
                .show()
        }

        for (target in targets) {

            changeButtons[target]
                ?.setOnClickListener {

                    val currentSource =
                        working[target]
                            .orEmpty()

                    val overlapSources =
                        working.entries
                            .filter { entry ->
                                entry.key != target &&
                                    entry.value.isNotBlank()
                            }
                            .map { entry ->
                                entry.value
                            }
                            .toSet()

                    val labels =
                        mutableListOf(
                            if (currentSource.isBlank()) {
                                "UNMAPPED (Current)"
                            } else {
                                "UNMAPPED"
                            }
                        )

                    for (source in sources) {

                        labels.add(
                            inputProfileSourceLabel(
                                source
                            ) +
                                if (source == currentSource) {
                                    " (Current)"
                                } else {
                                    ""
                                }
                        )
                    }

                    val currentLabel =
                        if (currentSource.isBlank()) {
                            "UNMAPPED"
                        } else {
                            inputProfileSourceLabel(
                                currentSource
                            )
                        }

                    val normalTextValue =
                        android.util.TypedValue()

                    theme.resolveAttribute(
                        android.R.attr.textColorPrimary,
                        normalTextValue,
                        true
                    )

                    val normalTextColor =
                        if (normalTextValue.resourceId != 0) {
                            ContextCompat.getColor(
                                this,
                                normalTextValue.resourceId
                            )
                        } else {
                            normalTextValue.data
                        }

                    val sourceAdapter =
                        object : android.widget.ArrayAdapter<String>(
                            this,
                            android.R.layout.simple_list_item_1,
                            labels
                        ) {

                            override fun getView(
                                position: Int,
                                convertView: View?,
                                parent: ViewGroup
                            ): View {

                                val view =
                                    super.getView(
                                        position,
                                        convertView,
                                        parent
                                    )

                                val textView =
                                    view as? TextView

                                val source =
                                    if (position == 0) {
                                        null
                                    } else {
                                        sources.getOrNull(
                                            position - 1
                                        )
                                    }

                                textView?.setTextColor(
                                    if (
                                        source != null &&
                                        source in overlapSources
                                    ) {
                                        0xFFFF5252.toInt()
                                    } else {
                                        normalTextColor
                                    }
                                )

                                return view
                            }
                        }

                    AlertDialog.Builder(this)
                        .setTitle(
                            "Change ${inputProfileTargetLabel(target)} - Current: $currentLabel"
                        )
                        .setAdapter(
                            sourceAdapter
                        ) { _, which ->

                            working[target] =
                                if (which == 0) {
                                    ""
                                } else {
                                    sources[
                                        which - 1
                                    ]
                                }

                            refreshRows()
                        }
                        .setNegativeButton(
                            "Cancel",
                            null
                        )
                        .show()
                }
        }

        dialog.setOnShowListener {

            dialog.getButton(
                android.content.DialogInterface.BUTTON_POSITIVE
            ).setOnClickListener {

                val invalid =
                    invalidTargets()

                if (invalid.isNotEmpty()) {
                    refreshRows()
                    return@setOnClickListener
                }

                val mapping =
                    inputProfileSavedMapping(
                        profile,
                        payload,
                        player,
                        working
                    )

                dialog.dismiss()

                saveInputProfileMapping(
                    gameId,
                    title,
                    profile.optString(
                        "id",
                        ""
                    ),
                    mapping
                )
            }

            refreshRows()
        }

        dialog.show()
    }

    private fun saveInputProfileMapping(
        gameId: String,
        title: String,
        profileId: String,
        mapping: JSONObject
    ) {

        statusText.text =
            "Saving input mapping..."

        networkExecutor.execute {

            try {

                postInputProfileAction(
                    "input-profile-update",
                    mapOf(
                        "profile_id" to profileId,
                        "mapping" to mapping.toString()
                    )
                )

                runOnUiThread {

                    statusText.text =
                        "Input mapping saved"

                    showGameInputProfileDialog(
                        gameId,
                        title
                    )
                }

            } catch (error: Exception) {

                showInputProfileNetworkError(
                    "Unable to save input mapping",
                    error
                )
            }
        }
    }

    private fun confirmResetInputProfile(
        gameId: String,
        title: String,
        profile: JSONObject,
        payload: JSONObject
    ) {

        AlertDialog.Builder(this)
            .setTitle(
                "Reset ${profile.optString("name", "Input Profile")}?"
            )
            .setMessage(
                "Restore the complete validated Default gameplay mapping for all supported players?"
            )
            .setPositiveButton(
                "Reset"
            ) { _, _ ->

                resetInputProfile(
                    gameId,
                    title,
                    profile.optString(
                        "id",
                        ""
                    ),
                    payload
                )
            }
            .setNegativeButton(
                "Cancel",
                null
            )
            .show()
    }

    private fun resetInputProfile(
        gameId: String,
        title: String,
        profileId: String,
        payload: JSONObject
    ) {

        statusText.text =
            "Resetting input profile..."

        val mapping =
            try {
                inputProfileCompleteDefaultJson(
                    payload
                )
            } catch (error: Exception) {
                showInputProfileNetworkError(
                    "Unable to build default input mapping",
                    error
                )
                return
            }

        networkExecutor.execute {

            try {

                postInputProfileAction(
                    "input-profile-update",
                    mapOf(
                        "profile_id" to profileId,
                        "mapping" to mapping.toString()
                    )
                )

                runOnUiThread {

                    statusText.text =
                        "Games ready"

                    showGameInputProfileDialog(
                        gameId,
                        title
                    )
                }

            } catch (error: Exception) {

                showInputProfileNetworkError(
                    "Unable to reset input profile",
                    error
                )
            }
        }
    }

    private fun confirmDeleteInputProfile(
        gameId: String,
        title: String,
        profile: JSONObject
    ) {

        AlertDialog.Builder(this)
            .setTitle(
                "Delete ${profile.optString("name", "Input Profile")}?"
            )
            .setMessage(
                "Assigned profiles cannot be deleted. Reassign any games using this profile first."
            )
            .setPositiveButton(
                "Delete"
            ) { _, _ ->

                deleteInputProfile(
                    gameId,
                    title,
                    profile.optString(
                        "id",
                        ""
                    )
                )
            }
            .setNegativeButton(
                "Cancel",
                null
            )
            .show()
    }


    private fun deleteInputProfile(
        gameId: String,
        title: String,
        profileId: String
    ) {

        statusText.text =
            "Deleting input profile..."

        networkExecutor.execute {

            try {

                postInputProfileAction(
                    "input-profile-delete",
                    mapOf(
                        "profile_id" to profileId
                    )
                )

                runOnUiThread {

                    statusText.text =
                        "Games ready"

                    showGameInputProfileDialog(
                        gameId,
                        title
                    )
                }

            } catch (error: Exception) {

                showInputProfileNetworkError(
                    "Unable to delete input profile",
                    error
                )
            }
        }
    }


    private fun showInputProfileNetworkError(
        title: String,
        error: Exception
    ) {

        Log.e(
            TAG,
            title,
            error
        )

        runOnUiThread {

            statusText.text =
                "Input profile operation failed"

            AlertDialog.Builder(this)
                .setTitle(
                    title
                )
                .setMessage(
                    error.message
                        ?: "Unknown error"
                )
                .setPositiveButton(
                    "OK",
                    null
                )
                .show()
        }
    }


    private fun showGameLaunchModeDialog(
        gameId: String,
        title: String
    ) {

        AlertDialog.Builder(this)
            .setTitle(
                "Start $title"
            )
            .setMessage(
                "Start from the game's normal boot, or load one of its " +
                    "PrivyHub save states?"
            )
            .setPositiveButton(
                "Start Fresh"
            ) { _, _ ->

                launchGameOnCompanion(
                    gameId = gameId,
                    title = title,
                    loadSaveAfterLaunch = false
                )
            }
            .setNegativeButton(
                "Load Save"
            ) { _, _ ->

                launchGameOnCompanion(
                    gameId = gameId,
                    title = title,
                    loadSaveAfterLaunch = true
                )
            }
            .setNeutralButton(
                "Extras"
            ) { _, _ ->
                showGameExtrasMenu(
                    gameId,
                    title
                )
            }
            .show()
    }


    private fun launchGameOnCompanion(
        gameId: String,
        title: String,
        loadSaveAfterLaunch: Boolean = false,
        cheatSourceIndex: Int? = null,
        cheatEnabledIndexes: List<Int> = emptyList(),
        cheatProfileLabel: String = "Normal",
        modIndex: Int? = null
    ) {

        val host =
            getCompanionHost()

        if (host.isBlank()) {

            showCompanionSettings()

            return
        }

        statusText.text =
            "Launching $title..."

        val cheatQuerySuffix =
            if (
                cheatSourceIndex != null &&
                cheatSourceIndex >= 0 &&
                cheatEnabledIndexes.isNotEmpty()
            ) {
                "&cheat_source=$cheatSourceIndex&cheat_indexes=" +
                    cheatEnabledIndexes
                        .distinct()
                        .sorted()
                        .joinToString(",")
            } else {
                ""
            }

        val modQuerySuffix =
            if (modIndex != null && modIndex >= 0) {
                "&mod_index=$modIndex"
            } else {
                ""
            }

        networkExecutor.execute {

            try {

                val response =
                    httpPost(
                        "http://$host:$CONTROL_PORT" +
                            "/plugins/games/launch?id=$gameId$cheatQuerySuffix$modQuerySuffix"
                    )

                val json =
                    JSONObject(
                        response
                    )

                val active =
                    json.optBoolean(
                        "active",
                        false
                    )

                val paused =
                    json.optBoolean(
                        "paused",
                        false
                    )


                if (active) {
                    GameCheatUiState.setProfileLabel(
                        this@MainActivity,
                        cheatProfileLabel
                    )
                }
                val streamWarning =
                    ""

                // PrivyHub Phase A5: the launch request already waits for
                // RetroArch command readiness, establishes the paused A3
                // handoff, and returns native/A4 readiness metadata. Use
                // that existing evidence before entering fullscreen.
                val nativeStream =
                    json.optJSONObject(
                        "native_stream"
                    )

                val nativeReady =
                    nativeStream
                        ?.optBoolean(
                            "ready",
                            false
                        )
                        ?: false

                val nativeMessage =
                    nativeStream
                        ?.optString(
                            "message",
                            ""
                        )
                        .orEmpty()

                val hostWindowPolicy =
                    json.optJSONObject(
                        "host_window_policy"
                    )

                val hostWindowFound =
                    hostWindowPolicy
                        ?.optBoolean(
                            "window_found",
                            false
                        )
                        ?: false

                val autoOpen =
                    getGameAutoOpenAfterLaunch()

                runOnUiThread {

                    if (
                        active &&
                        paused
                    ) {

                        showGameSessionBanner(
                            title,
                            paused = true
                        )

                        if (loadSaveAfterLaunch) {

                            statusText.text =
                                "Choose a save for $title"

                            showGameSlotDialog(
                                action = "load-state",
                                onSuccess = {

                                    completeGameLaunchHandoff(
                                        title = title,
                                        autoOpen = autoOpen,
                                        nativeReady = nativeReady,
                                        nativeMessage = nativeMessage,
                                        hostWindowFound = hostWindowFound,
                                        streamWarning = streamWarning
                                    )
                                }
                            )

                        } else {

                            completeGameLaunchHandoff(
                                title = title,
                                autoOpen = autoOpen,
                                nativeReady = nativeReady,
                                nativeMessage = nativeMessage,
                                hostWindowFound = hostWindowFound,
                                streamWarning = streamWarning
                            )
                        }

                    } else if (active) {

                        statusText.text =
                            "Game launch handoff unavailable"

                        AlertDialog.Builder(
                            this
                        )
                            .setTitle(
                                "Game launch incomplete"
                            )
                            .setMessage(
                                "The game launched, but PrivyHub did not " +
                                    "receive the required paused handoff. " +
                                    "It was not opened automatically."
                            )
                            .setPositiveButton(
                                "OK",
                                null
                            )
                            .show()

                    } else {

                        statusText.text =
                            "Game launch did not remain active"

                        if (streamWarning.isNotBlank()) {

                            AlertDialog.Builder(
                                this
                            )
                                .setTitle(
                                    "Game launch unavailable"
                                )
                                .setMessage(
                                    streamWarning
                                )
                                .setPositiveButton(
                                    "OK",
                                    null
                                )
                                .show()
                        }
                    }
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to launch game",
                    error
                )

                runOnUiThread {

                    statusText.text =
                        "Game launch failed"

                    AlertDialog.Builder(
                        this
                    )
                        .setTitle(
                            "Game launch failed"
                        )
                        .setMessage(
                            error.message
                                ?: "Unknown error"
                        )
                        .setPositiveButton(
                            "OK",
                            null
                        )
                        .show()
                }
            }
        }
    }


    // PrivyHub A2/A3 patch 01: Live-TV-style paused game-session controls.
    private fun createGameSessionActionButton(
        label: String
    ): Button {

        val button =
            Button(this)

        button.text =
            label

        button.textSize =
            13f

        button.setTextColor(
            ContextCompat.getColorStateList(
                this,
                R.color.mode_button_text
            )
        )

        button.setBackgroundResource(
            R.drawable.mode_button_background
        )

        button.isFocusable =
            true

        button.visibility =
            View.GONE

        button.layoutParams =
            android.widget.LinearLayout.LayoutParams(
                dp(104),
                dp(52)
            ).apply {
                marginStart =
                    dp(8)
            }

        return button
    }


    private fun showGameSessionBanner(
        title: String,
        paused: Boolean
    ) {

        gameSessionActive =
            true

        gameSessionPaused =
            paused

        gameSessionTitle =
            title.ifBlank {
                "Game"
            }

        if (player == null) {
            updateNowPlayingUi()
        }
    }


    private fun clearGameSessionBanner() {

        clearGamePausedFrame()

        gameSessionActive =
            false

        gameSessionPaused =
            false

        gameSessionTitle =
            null

        updateNowPlayingUi()
    }


    private fun refreshGameSessionBanner(
        retry: Int = 0
    ) {

        val host =
            getCompanionHost()

        if (host.isBlank()) {
            return
        }

        networkExecutor.execute {

            try {

                val json =
                    JSONObject(
                        httpGet(
                            "http://$host:$CONTROL_PORT" +
                                "/plugins/games/status"
                        )
                    )

                val active =
                    json.optBoolean(
                        "active",
                        false
                    )

                val paused =
                    json.optBoolean(
                        "paused",
                        false
                    )

                val title =
                    json.optJSONObject(
                        "game"
                    )
                        ?.optString(
                            "title",
                            "Game"
                        )
                        ?: "Game"

                runOnUiThread {

                    if (active) {

                        showGameSessionBanner(
                            title,
                            paused
                        )

                        if (
                            !paused &&
                            retry < 4
                        ) {

                            playbackUiHandler.postDelayed(
                                {
                                    refreshGameSessionBanner(
                                        retry + 1
                                    )
                                },
                                350L
                            )
                        }

                    } else {

                        clearGameSessionBanner()
                    }
                }

            } catch (error: Exception) {

                if (retry == 0) {
                    Log.d(
                        TAG,
                        "Game-session refresh unavailable",
                        error
                    )
                }
            }
        }
    }


    private fun completeGameLaunchHandoff(
        title: String,
        autoOpen: Boolean,
        nativeReady: Boolean,
        nativeMessage: String,
        hostWindowFound: Boolean,
        streamWarning: String
    ) {

        if (
            autoOpen &&
            nativeReady &&
            hostWindowFound
        ) {

            statusText.text =
                "Opening $title..."

            openNativeGameStream()

        } else if (autoOpen) {

            statusText.text =
                "Game paused - stream preflight unavailable"

            val reasons =
                mutableListOf<String>()

            if (!nativeReady) {
                reasons.add(
                    nativeMessage.ifBlank {
                        "Native streaming is not ready."
                    }
                )
            }

            if (!hostWindowFound) {
                reasons.add(
                    "The managed RetroArch window was not " +
                        "confirmed by the host-coexistence preflight."
                )
            }

            if (
                reasons.isEmpty() &&
                streamWarning.isNotBlank()
            ) {
                reasons.add(
                    streamWarning
                )
            }

            AlertDialog.Builder(
                this
            )
                .setTitle(
                    "Game ready, stream not opened"
                )
                .setMessage(
                    reasons.joinToString(
                        separator = "\n\n"
                    ).ifBlank {
                        "The game remains safely paused in PrivyHub."
                    }
                )
                .setPositiveButton(
                    "OK",
                    null
                )
                .show()

        } else {

            statusText.text =
                "Paused on companion: $title"
        }
    }


    private fun showGameSlotDialog(
        action: String,
        endAfterSave: Boolean = false,
        onSuccess: (() -> Unit)? = null
    ) {

        val saving =
            action == "save-state"

        val loading =
            action == "load-state"

        if (!saving && !loading) {
            return
        }

        if (!gameSessionActive) {
            return
        }

        val host =
            getCompanionHost()

        if (host.isBlank()) {
            showCompanionSettings()
            return
        }

        statusText.text =
            "Checking save slots..."

        networkExecutor.execute {

            var details: JSONArray? =
                null

            try {
                val status =
                    JSONObject(
                        httpGet(
                            "http://$host:$CONTROL_PORT" +
                                "/plugins/games/status"
                        )
                    )

                details =
                    status.optJSONArray(
                        "save_state_slot_details"
                    )
            } catch (error: Exception) {
                Log.d(
                    TAG,
                    "Save-slot metadata unavailable",
                    error
                )
            }

            runOnUiThread {
                showGameSlotDialogResolved(
                    action = action,
                    endAfterSave = endAfterSave,
                    details = details,
                    onSuccess = onSuccess
                )
            }
        }
    }


    private fun showGameSlotDialogResolved(
        action: String,
        endAfterSave: Boolean,
        details: JSONArray?,
        onSuccess: (() -> Unit)?
    ) {

        val saving =
            action == "save-state"

        val slots =
            Array(3) { index ->
                buildGameSlotLabel(
                    slot = index + 1,
                    details = details
                )
            }

        statusText.text =
            if (gameSessionPaused) {
                "Game paused"
            } else {
                "Game running"
            }

        AlertDialog.Builder(this)
            .setTitle(
                GameCheatUiState.dialogTitle(
                    this,
                    if (saving) {
                        "Save State"
                    } else {
                        "Load State"
                    }
                )
            )
            .setItems(
                slots
            ) { _, which ->

                val slot =
                    which + 1

                val detail =
                    findGameSlotDetail(
                        slot,
                        details
                    )

                if (
                    !saving &&
                    detail != null &&
                    !detail.optBoolean(
                        "exists",
                        false
                    )
                ) {
                    statusText.text =
                        "Slot $slot is empty"
                    return@setItems
                }

                requestGameStateAction(
                    action = action,
                    slot = slot,
                    onSuccess =
                        if (
                            saving &&
                            endAfterSave
                        ) {
                            {
                                stopGameOnCompanion()
                            }
                        } else {
                            onSuccess
                        }
                )
            }
            .setNegativeButton(
                "Cancel",
                null
            )
            .show()
    }


    private fun findGameSlotDetail(
        slot: Int,
        details: JSONArray?
    ): JSONObject? {

        if (details == null) {
            return null
        }

        for (index in 0 until details.length()) {
            val item =
                details.optJSONObject(
                    index
                ) ?: continue

            if (
                item.optInt(
                    "slot",
                    0
                ) == slot
            ) {
                return item
            }
        }

        return null
    }


    // PrivyHub A2/A3 patch 07: game-qualified slot labels
    private fun buildGameSlotLabel(
        slot: Int,
        details: JSONArray?
    ): String {

        val item =
            findGameSlotDetail(
                slot,
                details
            )

        if (item == null) {
            return "Slot $slot"
        }

        val gameTitle =
            item.optString(
                "game_title",
                ""
            ).trim()

        val prefix =
            if (gameTitle.isNotBlank()) {
                "Slot $slot - $gameTitle"
            } else {
                "Slot $slot"
            }

        if (
            item.optBoolean(
                "ambiguous",
                false
            )
        ) {
            return "$prefix - Multiple matching saves"
        }

        if (
            !item.optBoolean(
                "exists",
                false
            )
        ) {
            return "$prefix - Empty"
        }

        val modifiedMs =
            item.optLong(
                "modified_unix_ms",
                0L
            )

        val sizeBytes =
            item.optLong(
                "size_bytes",
                0L
            )

        val savedText =
            if (modifiedMs > 0L) {
                java.text.DateFormat
                    .getDateTimeInstance(
                        java.text.DateFormat.SHORT,
                        java.text.DateFormat.SHORT
                    )
                    .format(
                        java.util.Date(
                            modifiedMs
                        )
                    )
            } else {
                "Saved"
            }

        val sizeText =
            formatGameStateSize(
                sizeBytes
            )

        return "$prefix - $savedText - $sizeText"
    }


    private fun formatGameStateSize(
        sizeBytes: Long
    ): String {

        if (sizeBytes <= 0L) {
            return "unknown size"
        }

        val megabyte =
            1024.0 * 1024.0

        return if (
            sizeBytes >= megabyte
        ) {
            String.format(
                java.util.Locale.US,
                "%.1f MB",
                sizeBytes / megabyte
            )
        } else {
            val kilobytes =
                maxOf(
                    1L,
                    sizeBytes / 1024L
                )

            "$kilobytes KB"
        }
    }


    private fun showGameEndDialog() {

        if (!gameSessionActive) {
            return
        }

        AlertDialog.Builder(this)
            .setTitle(
                "End Game"
            )
            .setMessage(
                "Save a state before ending?"
            )
            .setPositiveButton(
                "Save"
            ) { _, _ ->

                showGameSlotDialog(
                    action = "save-state",
                    endAfterSave = true
                )
            }
            .setNegativeButton(
                "Don't Save"
            ) { _, _ ->

                stopGameOnCompanion()
            }
            .setNeutralButton(
                "Cancel",
                null
            )
            .show()
    }


        // PRIVYHUB_A7_PATCH_10V5_CHEAT_SAVE_REPLACE_CONFIRMATION
private fun requestGameStateAction(
        action: String,
        slot: Int,
        onSuccess: (() -> Unit)? = null,
        replace: Boolean = false
    ) {

        val endpoint =
            when (action) {
                "save-state" -> "save-state"
                "load-state" -> "load-state"
                else -> return
            }

        if (slot !in 1..3) {
            return
        }

        val host =
            getCompanionHost()

        if (host.isBlank()) {
            showCompanionSettings()
            return
        }

        val loading =
            endpoint == "load-state"

        statusText.text =
            if (loading) {
                "Loading state slot $slot..."
            } else {
                "Saving state slot $slot..."
            }

        val replaceQuerySuffix =
            if (endpoint == "save-state" && replace) {
                "&replace=true"
            } else {
                ""
            }

        networkExecutor.execute {

            try {

                val result =
                    JSONObject(
                        httpPost(
                            "http://$host:$CONTROL_PORT" +
                                "/plugins/games/$endpoint" +
                                "?slot=$slot$replaceQuerySuffix"
                        )
                    )

                val slotDetail =
                    result.optJSONObject(
                        "slot_detail"
                    )

                val detailLabel =
                    buildGameSlotLabel(
                        slot = slot,
                        details =
                            if (slotDetail != null) {
                                JSONArray().apply {
                                    put(slotDetail)
                                }
                            } else {
                                null
                            }
                    )

                runOnUiThread {
                    statusText.text =
                        if (loading) {
                            "Loaded $detailLabel"
                        } else {
                            "Saved $detailLabel"
                        }

                    if (!loading) {
                        refreshCurrentGameLibraryView()
                    }

                    onSuccess?.invoke()
                }

            } catch (error: Exception) {
                Log.e(
                    TAG,
                    "Game state action failed",
                    error
                )

                val replacementRequired =
                    endpoint == "save-state" &&
                        !replace &&
                        error.message
                            ?.contains(
                                "explicit replacement confirmation is required",
                                ignoreCase = true
                            ) == true

                runOnUiThread {
                    if (replacementRequired) {
                        val profileLabel =
                            GameCheatUiState.currentProfileLabel(this)

                        statusText.text =
                            "Profile save slot $slot is occupied"

                        AlertDialog.Builder(this)
                            .setTitle("Replace Profile Save?")
                            .setMessage(
                                "Slot $slot already contains a save in:\n\n" +
                                    "$profileLabel\n\n" +
                                    "Replace this slot completely?\n\n" +
                                    "Normal saves and other profiles " +
                                    "are not affected."
                            )
                            .setPositiveButton(
                                "Replace Completely"
                            ) { _, _ ->
                                requestGameStateAction(
                                    action = action,
                                    slot = slot,
                                    onSuccess = onSuccess,
                                    replace = true
                                )
                            }
                            .setNegativeButton(
                                "Cancel",
                                null
                            )
                            .show()
                    } else {
                        statusText.text =
                            if (loading) {
                                "Load state failed"
                            } else {
                                "Save state failed"
                            }

                        AlertDialog.Builder(this)
                            .setTitle(
                                "Game State"
                            )
                            .setMessage(
                                error.message
                                    ?: "Unknown error"
                            )
                            .setPositiveButton(
                                "OK",
                                null
                            )
                            .show()
                    }
                }
            }
        }
    }


    private fun stopGameOnCompanion() {

        val host =
            getCompanionHost()

        if (host.isBlank()) {
            return
        }

        statusText.text =
            "Ending game..."

        gameSaveButton.isEnabled =
            false

        gameLoadButton.isEnabled =
            false

        gameEndButton.isEnabled =
            false

        networkExecutor.execute {

            try {

                val json =
                    JSONObject(
                        httpPost(
                            "http://$host:$CONTROL_PORT" +
                                "/plugins/games/stop"
                        )
                    )

                val graceful =
                    json.optBoolean(
                        "graceful",
                        false
                    )

                runOnUiThread {

                    clearGameSessionBanner()

                    statusText.text =
                        if (graceful) {
                            "Game ended"
                        } else {
                            "Game ended with forced shutdown"
                        }

                    if (!graceful) {

                        AlertDialog.Builder(this)
                            .setTitle(
                                "Game Ended"
                            )
                            .setMessage(
                                "RetroArch required a forced shutdown. " +
                                    "Normal in-game save persistence is not " +
                                    "considered verified for this run."
                            )
                            .setPositiveButton(
                                "OK",
                                null
                            )
                            .show()
                    }
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to end game",
                    error
                )

                runOnUiThread {

                    gameSaveButton.isEnabled =
                        gameSessionPaused

                    gameLoadButton.isEnabled =
                        gameSessionPaused

                    gameEndButton.isEnabled =
                        true

                    statusText.text =
                        "Game end failed"

                    AlertDialog.Builder(this)
                        .setTitle(
                            "End Game"
                        )
                        .setMessage(
                            error.message
                                ?: "Unknown error"
                        )
                        .setPositiveButton(
                            "OK",
                            null
                        )
                        .show()
                }
            }
        }
    }






    private fun formatGameSize(
        sizeBytes: Long
    ): String {

        if (sizeBytes < 1024L) {

            return "$sizeBytes B"
        }

        val kib =
            sizeBytes /
                1024.0

        if (kib < 1024.0) {

            return String.format(
                "%.1f KB",
                kib
            )
        }

        val mib =
            kib /
                1024.0

        if (mib < 1024.0) {

            return String.format(
                "%.1f MB",
                mib
            )
        }

        return String.format(
            "%.2f GB",
            mib /
                1024.0
        )
    }


    /*
     * ----------------------------------------------------------------
     * SOURCE CONTROL
     * ----------------------------------------------------------------
     */


    private fun startSource(
        node: SourceNode
    ) {

        val directPlayback =
            node.playback

        val directUrl =
            directPlayback?.url


        if (
            directPlayback != null &&
            !directUrl.isNullOrBlank()
        ) {

            statusText.text =
                "Starting ${node.name}..."


            beginPlayback(
                node = node,
                playback = directPlayback,
                mediaUrl = directUrl,
                startPositionMs = 0L,
                clearSavedProgress = false
            )


            val companionHost =
                getCompanionHost()

            if (companionHost.isNotBlank()) {

                networkExecutor.execute {

                    try {

                        httpPost(
                            "http://$companionHost:$CONTROL_PORT/stop"
                        )

                    } catch (error: Exception) {

                        Log.w(
                            TAG,
                            "Unable to stop previous companion source",
                            error
                        )
                    }
                }
            }

            return
        }


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
                ),
            url =
                playback.optString(
                    "url",
                    ""
                ).takeIf {
                    it.isNotBlank()
                },
            referrer =
                playback.optString(
                    "referrer",
                    ""
                ).takeIf {
                    it.isNotBlank()
                },
            userAgent =
                playback.optString(
                    "user_agent",
                    ""
                ).takeIf {
                    it.isNotBlank()
                }
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


    private fun movePlayerViewTo(
        host: ViewGroup
    ) {

        val currentParent =
            playerView.parent
                as? ViewGroup


        if (currentParent === host) {

            return
        }


        currentParent?.removeView(
            playerView
        )


        host.addView(
            playerView,
            ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        )
    }


    private fun setFullscreenMode(
        fullscreen: Boolean
    ) {

        if (
            fullscreen &&
            player == null
        ) {

            return
        }


        if (
            fullscreen ==
            isFullscreen
        ) {

            return
        }


        isFullscreen =
            fullscreen


        if (fullscreen) {

            /*
             * Move the same PlayerView instead of creating a second decoder
             * or video surface. The catalog never participates in sizing the
             * video while browsing.
             */
            movePlayerViewTo(
                fullscreenPlayerHost
            )

            fullscreenPlayerHost.visibility =
                View.VISIBLE

            topControlBar.visibility =
                View.GONE

            statusText.visibility =
                View.GONE

            sourceScroll.visibility =
                View.GONE

            nowPlayingBar.visibility =
                View.GONE


            playerView.useController =
                true

            playerView.requestFocus()

            playerView.showController()

        } else {

            playerView.hideController()

            playerView.useController =
                false


            movePlayerViewTo(
                previewPlayerHost
            )

            fullscreenPlayerHost.visibility =
                View.GONE

            topControlBar.visibility =
                View.VISIBLE

            statusText.visibility =
                View.VISIBLE

            sourceScroll.visibility =
                View.VISIBLE


            updateNowPlayingUi()


            playerView.post {

                playerView.requestFocus()
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

        playerView.visibility =
            View.VISIBLE

        gameSessionPreview.visibility =
            View.GONE

        gameSessionPreviewLabel.visibility =
            View.GONE

        releaseGamePausedFrameBitmap()

        restartButton.visibility =
            View.VISIBLE

        restartButton.isEnabled =
            false

        gameSaveButton.visibility =
            View.GONE

        gameLoadButton.visibility =
            View.GONE

        gameEndButton.visibility =
            View.GONE
    }


    // PrivyHub A3 patch 11v2: frozen gameplay banner frame.
    private fun gamePausedFrameFile():
        File? {

        val title =
            gameSessionTitle
                ?.trim()
                .orEmpty()

        if (title.isBlank()) {
            return null
        }

        return File(
            cacheDir,
            NativeStreamActivity.pausedFrameFileName(
                title
            )
        )
    }


    private fun releaseGamePausedFrameBitmap() {

        gameSessionPreview.setImageDrawable(
            null
        )

        gameSessionPreviewBitmap
            ?.recycle()

        gameSessionPreviewBitmap =
            null
    }


    private fun clearGamePausedFrame() {

        releaseGamePausedFrameBitmap()

        try {
            gamePausedFrameFile()
                ?.delete()
        } catch (_: Exception) {
        }
    }


    private fun loadGamePausedFrame():
        Boolean {

        if (!gameSessionPaused) {
            releaseGamePausedFrameBitmap()
            return false
        }

        val frame =
            gamePausedFrameFile()
                ?: run {
                    releaseGamePausedFrameBitmap()
                    return false
                }

        if (
            !frame.isFile ||
            frame.length() <= 0L
        ) {
            releaseGamePausedFrameBitmap()
            return false
        }

        val bitmap =
            try {
                BitmapFactory.decodeFile(
                    frame.absolutePath
                )
            } catch (_: Exception) {
                null
            }

        if (bitmap == null) {
            releaseGamePausedFrameBitmap()
            return false
        }

        releaseGamePausedFrameBitmap()

        gameSessionPreviewBitmap =
            bitmap

        gameSessionPreview.setImageBitmap(
            bitmap
        )

        return true
    }


    private fun showGameSessionBannerUi() {

        showNowPlaying()

        nowPlayingTitle.text =
            gameSessionTitle
                ?: "Game"

        nowPlayingProgress.text =
            if (gameSessionPaused) {
                "PAUSED"
            } else {
                "RUNNING"
            }

        playerView.visibility =
            View.GONE

        gameSessionPreview.visibility =
            View.VISIBLE

        val hasPausedFrame =
            loadGamePausedFrame()

        gameSessionPreviewLabel.text =
            if (gameSessionPaused) {
                "RESUME\nPLAYING"
            } else {
                "GAME\nRUNNING"
            }

        gameSessionPreviewLabel.visibility =
            if (hasPausedFrame) {
                View.GONE
            } else {
                View.VISIBLE
            }

        gameSessionPreview.isEnabled =
            gameSessionActive

        gameSessionPreviewLabel.isEnabled =
            gameSessionActive

        restartButton.visibility =
            View.GONE

        gameSaveButton.visibility =
            View.VISIBLE

        gameLoadButton.visibility =
            View.VISIBLE

        gameEndButton.visibility =
            View.VISIBLE

        gameSaveButton.isEnabled =
            gameSessionPaused

        gameLoadButton.isEnabled =
            gameSessionPaused

        gameEndButton.isEnabled =
            gameSessionActive
    }


    private fun showMediaNowPlayingControls() {

        playerView.visibility =
            View.VISIBLE

        gameSessionPreview.visibility =
            View.GONE

        gameSessionPreviewLabel.visibility =
            View.GONE

        releaseGamePausedFrameBitmap()

        restartButton.visibility =
            View.VISIBLE

        gameSaveButton.visibility =
            View.GONE

        gameLoadButton.visibility =
            View.GONE

        gameEndButton.visibility =
            View.GONE
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

            if (gameSessionActive) {
                showGameSessionBannerUi()
            } else {
                hideNowPlaying()
            }

            return
        }


        showNowPlaying()

        showMediaNowPlayingControls()


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

        val keepFullscreen =
            preserveFullscreenOnNextPlayback &&
                isFullscreen

        preserveFullscreenOnNextPlayback =
            false

        releasePlayer(
            preserveFullscreen =
                keepFullscreen
        )


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


        val httpDataSourceFactory =
            DefaultHttpDataSource.Factory()

        if (
            !playback.userAgent.isNullOrBlank()
        ) {

            httpDataSourceFactory.setUserAgent(
                playback.userAgent
            )
        }

        if (
            !playback.referrer.isNullOrBlank()
        ) {

            httpDataSourceFactory.setDefaultRequestProperties(
                mapOf(
                    "Referer" to playback.referrer
                )
            )
        }

        val mediaSourceFactory =
            DefaultMediaSourceFactory(
                this
            ).setDataSourceFactory(
                httpDataSourceFactory
            )


        player =
            ExoPlayer.Builder(this)
                .setMediaSourceFactory(
                    mediaSourceFactory
                )
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


                                if (
                                    !playback.url.isNullOrBlank()
                                ) {

                                    if (
                                        tvRepository.isTvStreamId(
                                            sourceId
                                        )
                                    ) {

                                        tvRepository.recordFailure(
                                            sourceId
                                        )

                                        statusText.text =
                                            "Playback error - health updated"

                                        refreshCurrentTvResultPage()

                                    } else {

                                        markIptvFailed(
                                            sourceId
                                        )

                                        statusText.text =
                                            "Playback error - marked recently failed"
                                    }

                                } else {

                                    statusText.text =
                                        "Playback error"
                                }
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
                                    Player.STATE_READY &&
                                    !playback.url.isNullOrBlank()
                                ) {

                                    if (
                                        tvRepository.isTvStreamId(
                                            sourceId
                                        )
                                    ) {

                                        tvRepository.recordSuccess(
                                            sourceId
                                        )

                                        tvRepository.recordWatched(
                                            sourceId
                                        )

                                        refreshTvEpgForStream(
                                            sourceId
                                        )

                                    } else {

                                        clearIptvFailure(
                                            sourceId
                                        )
                                    }
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


    private fun releasePlayer(
        preserveFullscreen: Boolean = false
    ) {

        saveCurrentProgress()

        stopPlaybackUiTicker()


        if (
            isFullscreen &&
            !preserveFullscreen
        ) {

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


    override fun onResume() {

        super.onResume()

        playbackUiHandler.postDelayed(
            {
                refreshGameSessionBanner()
                refreshCurrentGameLibraryView()
            },
            350L
        )
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

        releaseGamePausedFrameBitmap()

        networkExecutor.shutdownNow()
        gameArtworkExecutor.shutdownNow()

        super.onDestroy()
    }
}
