package com.safeiot.privyhub

import android.content.Intent

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.text.InputType
import android.util.Log
import android.view.Gravity
import android.view.KeyEvent
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.GridLayout
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

import java.net.HttpURLConnection
import java.net.URL
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

    private lateinit var nowPlayingBar: View
    private lateinit var nowPlayingTitle: TextView
    private lateinit var nowPlayingProgress: TextView
    private lateinit var restartButton: Button

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
        val lazyPath: String? = null
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

            stopPlaybackAndRemoteSource()
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
            if (isTvUiPage()) {

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
                if (isContinueWatchingSource) {

                    90

                } else {

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

                    showGameDetails(
                        node
                    )
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


        return button
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
                        lazyPath = null
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

                        "stream_host" ->
                            buildStreamHostMessage(
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

                    when (kind) {

                        "game_session" -> {

                            val active =
                                json.optBoolean(
                                    "active",
                                    false
                                )

                            val streamHost =
                                json.optJSONObject(
                                    "stream_host"
                                )

                            val streaming =
                                streamHost
                                    ?.optBoolean(
                                        "active",
                                        false
                                    )
                                    ?: false

                            statusText.text =
                                if (active) {
                                    "Game running on companion"
                                } else {
                                    "Games ready"
                                }

                            if (
                                active &&
                                streaming
                            ) {

                                builder.setPositiveButton(
                                    "Open Stream"
                                ) { _, _ ->

                                    openGameStreamClient()
                                }
                            }

                            if (active) {

                                builder.setNeutralButton(
                                    "Stop Game"
                                ) { _, _ ->

                                    stopGameOnCompanion()
                                }
                            }
                        }

                        "stream_host" -> {

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
                                        "Streaming host running"

                                    ready ->
                                        "Streaming host ready"

                                    else ->
                                        "Streaming host setup required"
                                }

                            if (active) {

                                builder.setPositiveButton(
                                    "Open Stream"
                                ) { _, _ ->

                                    openGameStreamClient()
                                }

                                if (
                                    json.optBoolean(
                                        "managed",
                                        false
                                    )
                                ) {

                                    builder.setNeutralButton(
                                        "Stop Host"
                                    ) { _, _ ->

                                        setGameStreamHost(
                                            false
                                        )
                                    }
                                }

                            } else if (ready) {

                                builder.setPositiveButton(
                                    "Start Host"
                                ) { _, _ ->

                                    setGameStreamHost(
                                        true
                                    )
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

                                launchGameOnCompanion(
                                    node.id,
                                    title
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


    private fun buildGameCatalogMessage(
        json: JSONObject
    ): String {

        val systemName =
            json.optString(
                "system_name",
                "Unknown"
            )

        val relativePath =
            json.optString(
                "relative_path",
                ""
            )

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

        val details =
            StringBuilder()
                .append(
                    "System: "
                )
                .append(
                    systemName
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

        details.append(
            "\n\nLaunch starts the game on the PrivyHub companion. " +
                "If the Sunshine transport is configured, PrivyHub " +
                "starts it automatically."
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

        val ready =
            json.optBoolean(
                "ready",
                false
            )

        val details =
            StringBuilder()

        details.append(
            if (active) {
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


    private fun buildStreamHostMessage(
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

        val details =
            StringBuilder()

        details
            .append(
                "Status: "
            )
            .append(
                when {
                    active ->
                        "RUNNING"

                    ready ->
                        "READY"

                    else ->
                        "SETUP REQUIRED"
                }
            )

        if (
            json.optBoolean(
                "external",
                false
            )
        ) {

            details.append(
                "\nOwnership: external/unmanaged"
            )
        } else if (
            json.optBoolean(
                "managed",
                false
            )
        ) {

            details.append(
                "\nOwnership: PrivyHub"
            )
        }

        details.append(
            "\nController forwarding: DISABLED"
        )

        details.append(
            "\nWeb UI: PC localhost only"
        )

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


    private fun launchGameOnCompanion(
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
            "Launching $title..."

        networkExecutor.execute {

            try {

                val response =
                    httpPost(
                        "http://$host:$CONTROL_PORT" +
                            "/plugins/games/launch?id=$gameId"
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

                val streamHost =
                    json.optJSONObject(
                        "stream_host"
                    )

                val streaming =
                    streamHost
                        ?.optBoolean(
                            "active",
                            false
                        )
                        ?: false

                val streamWarning =
                    json.optString(
                        "stream_warning",
                        ""
                    )

                runOnUiThread {

                    statusText.text =
                        if (active) {
                            "Running on companion: $title"
                        } else {
                            "Game launch did not remain active"
                        }

                    if (
                        active &&
                        streaming
                    ) {

                        AlertDialog.Builder(
                            this
                        )
                            .setTitle(
                                "Game running"
                            )
                            .setMessage(
                                "$title is running on the companion. " +
                                    "Open the streaming transport?"
                            )
                            .setPositiveButton(
                                "Open Stream"
                            ) { _, _ ->

                                openGameStreamClient()
                            }
                            .setNegativeButton(
                                "Stay in PrivyHub",
                                null
                            )
                            .show()

                    } else if (
                        streamWarning.isNotBlank()
                    ) {

                        AlertDialog.Builder(
                            this
                        )
                            .setTitle(
                                "Game running locally"
                            )
                            .setMessage(
                                "The game launched, but the streaming " +
                                    "host is not ready:\n\n$streamWarning"
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


    private fun stopGameOnCompanion() {

        val host =
            getCompanionHost()

        if (host.isBlank()) {
            return
        }

        statusText.text =
            "Stopping game..."

        networkExecutor.execute {

            try {

                httpPost(
                    "http://$host:$CONTROL_PORT" +
                        "/plugins/games/stop"
                )

                runOnUiThread {

                    statusText.text =
                        "Game stopped"
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to stop game",
                    error
                )

                runOnUiThread {

                    statusText.text =
                        "Game stop failed"
                }
            }
        }
    }


    private fun setGameStreamHost(
        start: Boolean
    ) {

        val host =
            getCompanionHost()

        if (host.isBlank()) {
            return
        }

        statusText.text =
            if (start) {
                "Starting streaming host..."
            } else {
                "Stopping streaming host..."
            }

        networkExecutor.execute {

            try {

                httpPost(
                    "http://$host:$CONTROL_PORT" +
                        if (start) {
                            "/plugins/games/stream-start"
                        } else {
                            "/plugins/games/stream-stop"
                        }
                )

                runOnUiThread {

                    statusText.text =
                        if (start) {
                            "Streaming host running"
                        } else {
                            "Streaming host stopped"
                        }
                }

            } catch (error: Exception) {

                Log.e(
                    TAG,
                    "Failed to change stream host",
                    error
                )

                runOnUiThread {

                    statusText.text =
                        "Streaming host control failed"

                    AlertDialog.Builder(
                        this
                    )
                        .setTitle(
                            "Streaming host"
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


    private fun openGameStreamClient() {

        val packageName =
            "com.limelight"

        val launchIntent =
            packageManager
                .getLaunchIntentForPackage(
                    packageName
                )

        val intent =
            launchIntent
                ?: Intent().apply {
                    setClassName(
                        packageName,
                        "com.limelight.PcView"
                    )
                    addFlags(
                        Intent.FLAG_ACTIVITY_NEW_TASK
                    )
                }

        try {

            startActivity(
                intent
            )

        } catch (
            error: Exception
        ) {

            Log.e(
                TAG,
                "Moonlight launch failed",
                error
            )

            AlertDialog.Builder(
                this
            )
                .setTitle(
                    "Streaming client unavailable"
                )
                .setMessage(
                    "Moonlight is installed but could not be launched. " +
                        "Reinstall the PrivyHub-selected Moonlight APK."
                )
                .setPositiveButton(
                    "OK",
                    null
                )
                .show()
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
