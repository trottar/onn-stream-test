package com.safeiot.privyhub

import android.content.Context

import org.json.JSONArray
import org.json.JSONObject

import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale
import java.util.TimeZone


enum class NflWindow {
    LIVE,
    TODAY,
    WEEK
}


enum class NflAvailabilityStatus {
    AVAILABLE,
    POSSIBLE,
    NO_STREAM
}


data class NflTeam(
    val abbreviation: String,
    val displayName: String,
    val shortName: String,
    val location: String,
    val nickname: String
)


data class NflGame(
    val id: String,
    val startMs: Long,
    val away: NflTeam,
    val home: NflTeam,
    val networks: List<String>,
    val state: String,
    val statusText: String,
    val regional: Boolean
) {
    val matchup: String
        get() = "${away.shortName} @ ${home.shortName}"
}


data class NflChannelCandidate(
    val channel: TvChannel,
    val exactEpgMatch: Boolean,
    val statusLabel: String
)


data class NflGameAvailability(
    val game: NflGame,
    val status: NflAvailabilityStatus,
    val channel: TvChannel?,
    val candidates: List<NflChannelCandidate>,
    val reason: String,
    val affiliateEvidence: List<String>,
    val coverageSummary: String?
)


class NflRepository(
    context: Context,
    private val tvRepository: TvRepository,
    private val epgRepository: TvEpgRepository
) {

    companion object {
        private const val ESPN_SCOREBOARD =
            "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

        private const val NFL_SCHEDULE =
            "https://www.nfl.com/schedules"

        private const val SPORTS_MAPS =
            "https://thesportsmaps.com/nfl/"

        private const val FETCH_TIMEOUT_MS =
            15_000

        private const val SCHEDULE_CACHE_MS =
            30L * 60L * 1_000L

        private const val MAX_NETWORK_CHANNELS =
            300

        private const val MAX_GUIDE_REFRESHES_PER_GAME =
            6

        private const val EPG_LOOKAHEAD_MS =
            60L * 60L * 60L * 1_000L

        private const val LIVE_GRACE_MS =
            5L * 60L * 60L * 1_000L
    }


    @Suppress("unused")
    private val appContext =
        context.applicationContext

    private var cachedSchedule:
        List<NflGame> =
        emptyList()

    private var cachedScheduleAtMs =
        0L

    private var cachedCoverageText:
        String? =
        null

    private var cachedCoverageAtMs =
        0L


    fun clearCache() {
        cachedSchedule =
            emptyList()

        cachedScheduleAtMs =
            0L

        cachedCoverageText =
            null

        cachedCoverageAtMs =
            0L
    }


    fun load(
        window: NflWindow,
        languageCode: String
    ): List<NflGameAvailability> {

        val now =
            System.currentTimeMillis()

        val games =
            loadSchedule(
                nowMs = now
            )

        val selected =
            games.filter {
                matchesWindow(
                    game = it,
                    window = window,
                    nowMs = now
                )
            }

        val coverageText =
            if (
                selected.any {
                    it.regional
                }
            ) {

                loadCoverageText(
                    nowMs = now
                )

            } else {

                null
            }

        return selected
            .sortedBy {
                it.startMs
            }
            .map {
                analyzeGame(
                    game = it,
                    languageCode = languageCode,
                    nowMs = now,
                    coverageText = coverageText
                )
            }
    }


    private fun loadSchedule(
        nowMs: Long
    ): List<NflGame> {

        val age =
            nowMs -
                cachedScheduleAtMs

        if (
            cachedSchedule.isNotEmpty() &&
            cachedScheduleAtMs > 0L &&
            age in 0 until SCHEDULE_CACHE_MS
        ) {

            return cachedSchedule
        }

        val eastern =
            TimeZone.getTimeZone(
                "America/New_York"
            )

        val dayFormat =
            SimpleDateFormat(
                "yyyyMMdd",
                Locale.US
            ).apply {
                timeZone =
                    eastern
            }

        val startCalendar =
            Calendar.getInstance(
                eastern
            ).apply {
                timeInMillis =
                    nowMs

                add(
                    Calendar.DAY_OF_YEAR,
                    -1
                )
            }

        val endCalendar =
            Calendar.getInstance(
                eastern
            ).apply {
                timeInMillis =
                    nowMs

                add(
                    Calendar.DAY_OF_YEAR,
                    9
                )
            }

        val range =
            dayFormat.format(
                Date(
                    startCalendar.timeInMillis
                )
            ) +
                "-" +
                dayFormat.format(
                    Date(
                        endCalendar.timeInMillis
                    )
                )

        val scoreboardUrl =
            "$ESPN_SCOREBOARD?limit=100&dates=$range"

        val parsed =
            parseEspnGames(
                fetchText(
                    scoreboardUrl
                )
            )

        val officialText =
            try {

                htmlToPlainText(
                    fetchText(
                        NFL_SCHEDULE
                    )
                )

            } catch (_: Exception) {

                ""
            }

        val verified =
            parsed.map {
                applyOfficialNetworkVerification(
                    game = it,
                    officialText = officialText
                )
            }

        cachedSchedule =
            verified

        cachedScheduleAtMs =
            nowMs

        return verified
    }


    private fun parseEspnGames(
        text: String
    ): List<NflGame> {

        val root =
            JSONObject(
                text
            )

        val events =
            root.optJSONArray(
                "events"
            ) ?: JSONArray()

        val result =
            mutableListOf<NflGame>()

        for (
            index in 0 until events.length()
        ) {

            val event =
                events.optJSONObject(
                    index
                ) ?: continue

            val competition =
                event.optJSONArray(
                    "competitions"
                )
                    ?.optJSONObject(
                        0
                    )
                    ?: continue

            val competitors =
                competition.optJSONArray(
                    "competitors"
                ) ?: continue

            var home:
                NflTeam? =
                null

            var away:
                NflTeam? =
                null

            for (
                competitorIndex in
                0 until competitors.length()
            ) {

                val competitor =
                    competitors.optJSONObject(
                        competitorIndex
                    ) ?: continue

                val teamJson =
                    competitor.optJSONObject(
                        "team"
                    ) ?: continue

                val team =
                    NflTeam(
                        abbreviation =
                            teamJson.optString(
                                "abbreviation"
                            ).trim(),
                        displayName =
                            teamJson.optString(
                                "displayName"
                            ).trim(),
                        shortName =
                            teamJson.optString(
                                "shortDisplayName"
                            ).trim(),
                        location =
                            teamJson.optString(
                                "location"
                            ).trim(),
                        nickname =
                            teamJson.optString(
                                "name"
                            ).trim()
                    )

                if (
                    competitor.optString(
                        "homeAway"
                    ).equals(
                        "home",
                        ignoreCase = true
                    )
                ) {

                    home =
                        team

                } else {

                    away =
                        team
                }
            }

            val selectedHome =
                home
                    ?: continue

            val selectedAway =
                away
                    ?: continue

            val startMs =
                parseIsoDate(
                    event.optString(
                        "date"
                    )
                )
                    ?: continue

            val networks =
                parseNetworks(
                    competition
                )

            val statusType =
                competition
                    .optJSONObject(
                        "status"
                    )
                    ?.optJSONObject(
                        "type"
                    )

            val state =
                statusType
                    ?.optString(
                        "state"
                    )
                    ?.trim()
                    .orEmpty()

            val statusText =
                statusType
                    ?.optString(
                        "shortDetail"
                    )
                    ?.trim()
                    .orEmpty()

            result.add(
                NflGame(
                    id =
                        event.optString(
                            "id"
                        ).ifBlank {
                            "${selectedAway.abbreviation}_${selectedHome.abbreviation}_$startMs"
                        },
                    startMs =
                        startMs,
                    away =
                        selectedAway,
                    home =
                        selectedHome,
                    networks =
                        networks,
                    state =
                        state,
                    statusText =
                        statusText,
                    regional =
                        isRegionalSundayGame(
                            startMs = startMs,
                            networks = networks
                        )
                )
            )
        }

        return result
            .distinctBy {
                it.id
            }
    }


    private fun parseNetworks(
        competition: JSONObject
    ): List<String> {

        val result =
            mutableListOf<String>()

        val broadcasts =
            competition.optJSONArray(
                "broadcasts"
            )

        if (broadcasts != null) {

            for (
                index in
                0 until broadcasts.length()
            ) {

                val names =
                    broadcasts
                        .optJSONObject(
                            index
                        )
                        ?.optJSONArray(
                            "names"
                        )
                        ?: continue

                for (
                    nameIndex in
                    0 until names.length()
                ) {

                    val name =
                        names
                            .optString(
                                nameIndex
                            )
                            .trim()

                    if (name.isNotBlank()) {

                        result.add(
                            normalizeNetwork(
                                name
                            )
                        )
                    }
                }
            }
        }

        val simple =
            competition.optString(
                "broadcast"
            ).trim()

        if (simple.isNotBlank()) {

            result.add(
                normalizeNetwork(
                    simple
                )
            )
        }

        val geo =
            competition.optJSONArray(
                "geoBroadcasts"
            )

        if (geo != null) {

            for (
                index in
                0 until geo.length()
            ) {

                val name =
                    geo
                        .optJSONObject(
                            index
                        )
                        ?.optJSONObject(
                            "media"
                        )
                        ?.optString(
                            "shortName"
                        )
                        ?.trim()
                        .orEmpty()

                if (name.isNotBlank()) {

                    result.add(
                        normalizeNetwork(
                            name
                        )
                    )
                }
            }
        }

        return result
            .filter {
                it.isNotBlank()
            }
            .distinct()
    }


    private fun applyOfficialNetworkVerification(
        game: NflGame,
        officialText: String
    ): NflGame {

        if (officialText.isBlank()) {

            return game
        }

        val normalizedText =
            normalizeText(
                officialText
            )

        val awayToken =
            normalizeText(
                game.away.displayName
            )

        val homeToken =
            normalizeText(
                game.home.displayName
            )

        val awayIndex =
            normalizedText.indexOf(
                awayToken
            )

        if (awayIndex < 0) {

            return game
        }

        val windowEnd =
            (
                awayIndex +
                    700
                )
                .coerceAtMost(
                    normalizedText.length
                )

        val window =
            normalizedText.substring(
                awayIndex,
                windowEnd
            )

        if (
            !window.contains(
                homeToken
            )
        ) {

            return game
        }

        val officialNetworks =
            listOf(
                "prime video",
                "nfl network",
                "netflix",
                "peacock",
                "espn2",
                "espn",
                "abc",
                "nbc",
                "cbs",
                "fox"
            )
                .filter {
                    window.contains(
                        it
                    )
                }
                .map {
                    normalizeNetwork(
                        it
                    )
                }
                .distinct()

        if (
            officialNetworks.isEmpty()
        ) {

            return game
        }

        val merged =
            (
                officialNetworks +
                    game.networks
                )
                .distinct()

        return game.copy(
            networks =
                merged,
            regional =
                isRegionalSundayGame(
                    startMs =
                        game.startMs,
                    networks =
                        merged
                )
        )
    }


    private fun analyzeGame(
        game: NflGame,
        languageCode: String,
        nowMs: Long,
        coverageText: String?
    ): NflGameAvailability {

        val channels =
            findNetworkChannels(
                game = game,
                languageCode = languageCode
            )

        val exactMatches =
            mutableListOf<
                Pair<
                    TvChannel,
                    TvProgramme
                >
            >()

        var refreshes =
            0

        for (channel in channels) {

            var guide =
                epgRepository.getCachedGuide(
                    channel.channelId
                )

            var matchingProgramme =
                findMatchingProgramme(
                    guide = guide,
                    game = game
                )

            val closeEnoughForGuide =
                game.startMs -
                    nowMs in
                    0L..EPG_LOOKAHEAD_MS

            if (
                matchingProgramme == null &&
                closeEnoughForGuide &&
                refreshes <
                    MAX_GUIDE_REFRESHES_PER_GAME
            ) {

                refreshes++

                try {

                    guide =
                        epgRepository.getGuide(
                            channel.channelId
                        )

                    matchingProgramme =
                        findMatchingProgramme(
                            guide = guide,
                            game = game
                        )

                } catch (_: Exception) {

                    // Candidate remains visible even when guide refresh fails.
                }
            }

            if (matchingProgramme != null) {

                exactMatches.add(
                    channel to
                        matchingProgramme
                )
            }
        }

        val exactIds =
            exactMatches
                .map {
                    it.first.streamId
                }
                .toSet()

        /*
         * Candidate visibility and playback confidence are intentionally
         * separate. A user-hidden stream remains a valid NFL candidate.
         * Failed/auto-hidden streams also remain visible and selectable,
         * but are ranked lower and marked clearly.
         */
        val candidates =
            channels
                .map { channel ->

                    NflChannelCandidate(
                        channel =
                            channel,
                        exactEpgMatch =
                            channel.streamId in
                                exactIds,
                        statusLabel =
                            candidateStatusLabel(
                                channel
                            )
                    )
                }
                .sortedWith(
                    compareByDescending<NflChannelCandidate> {
                        it.exactEpgMatch
                    }
                        .thenByDescending {
                            candidateHealthRank(
                                it.channel
                            )
                        }
                        .thenByDescending {
                            it.channel.favorite
                        }
                        .thenByDescending {
                            it.channel.lastSuccess
                        }
                        .thenBy {
                            it.channel.name
                        }
                )

        val exactHealthy =
            candidates.firstOrNull {
                it.exactEpgMatch &&
                    isHealthyCandidate(
                        it.channel
                    )
            }

        val exactUnverified =
            candidates.firstOrNull {
                it.exactEpgMatch &&
                    isUnverifiedCandidate(
                        it.channel
                    )
            }

        val networkHealthy =
            candidates.firstOrNull {
                isHealthyCandidate(
                    it.channel
                )
            }

        val bestCandidate =
            exactHealthy
                ?: exactUnverified
                ?: networkHealthy
                ?: candidates.firstOrNull()

        val status:
            NflAvailabilityStatus

        val reason:
            String

        when {

            exactHealthy != null -> {

                status =
                    NflAvailabilityStatus.AVAILABLE

                reason =
                    if (
                        exactHealthy.channel.manualHidden
                    ) {

                        "Exact EPG match on a previously successful channel. " +
                            "The channel is hidden by the user, but remains playable here."

                    } else {

                        "Exact EPG match on a channel with successful playback history."
                    }
            }

            exactUnverified != null -> {

                status =
                    NflAvailabilityStatus.POSSIBLE

                reason =
                    "Exact EPG match found on an unverified channel."
            }

            networkHealthy != null -> {

                status =
                    NflAvailabilityStatus.POSSIBLE

                reason =
                    if (game.regional) {

                        "A healthy ${primaryNetwork(game)} candidate exists, " +
                            "but the regional assignment is not EPG-confirmed."

                    } else {

                        "A healthy ${primaryNetwork(game)} candidate exists, " +
                            "but the exact game is not yet EPG-confirmed."
                    }
            }

            candidates.isNotEmpty() -> {

                status =
                    NflAvailabilityStatus.NO_STREAM

                reason =
                    "Candidate channels were found, but all are currently " +
                        "unverified, failed, or auto-hidden. Every candidate " +
                        "is still available under Channels."
            }

            else -> {

                status =
                    NflAvailabilityStatus.NO_STREAM

                reason =
                    "No matching PrivyHub channel was found for ${primaryNetwork(game)}."
            }
        }

        val affiliateEvidence =
            exactMatches
                .map {
                    buildAffiliateEvidence(
                        it.first
                    )
                }
                .distinct()
                .take(
                    12
                )

        val coverageSummary =
            if (game.regional) {

                extractCoverageSummary(
                    game = game,
                    coverageText = coverageText
                )

            } else {

                "National/streaming broadcast: ${game.networks.joinToString(" / ")}"
            }

        return NflGameAvailability(
            game =
                game,
            status =
                status,
            channel =
                bestCandidate
                    ?.channel,
            candidates =
                candidates,
            reason =
                reason,
            affiliateEvidence =
                affiliateEvidence,
            coverageSummary =
                coverageSummary
        )
    }


    private fun isHealthyCandidate(
        channel: TvChannel
    ): Boolean {

        return !channel.autoHidden &&
            channel.successCount >
                0 &&
            channel.consecutiveFailures ==
                0
    }


    private fun isUnverifiedCandidate(
        channel: TvChannel
    ): Boolean {

        return !channel.autoHidden &&
            channel.successCount ==
                0 &&
            channel.consecutiveFailures ==
                0
    }


    private fun candidateHealthRank(
        channel: TvChannel
    ): Int {

        return when {

            isHealthyCandidate(
                channel
            ) ->
                5

            isUnverifiedCandidate(
                channel
            ) ->
                4

            channel.manualHidden &&
                !channel.autoHidden ->
                3

            channel.consecutiveFailures in
                1..2 ->
                2

            channel.autoHidden ||
                channel.consecutiveFailures >=
                    3 ->
                1

            else ->
                0
        }
    }


    private fun candidateStatusLabel(
        channel: TvChannel
    ): String {

        return when {

            channel.autoHidden -> {

                if (
                    channel.consecutiveFailures >=
                    3
                ) {

                    "AUTO-HIDDEN · REPEATED FAILURES"

                } else {

                    "AUTO-HIDDEN"
                }
            }

            channel.consecutiveFailures >=
                3 ->
                "REPEATED FAILURES"

            channel.consecutiveFailures >
                0 ->
                "RECENT FAILURE"

            channel.successCount >
                0 &&
                channel.manualHidden ->
                "USER HIDDEN · WORKING HISTORY"

            channel.successCount >
                0 ->
                "WORKING HISTORY"

            channel.manualHidden ->
                "USER HIDDEN · UNVERIFIED"

            else ->
                "UNVERIFIED"
        }
    }


    private fun findNetworkChannels(
        game: NflGame,
        languageCode: String
    ): List<TvChannel> {

        val terms =
            game.networks
                .flatMap {
                    networkSearchTerms(
                        it
                    )
                }
                .distinct()

        val result =
            mutableListOf<TvChannel>()

        for (term in terms) {

            val channels =
                tvRepository.queryChannels(
                    languageCode =
                        languageCode,
                    countryCode =
                        "",
                    mode =
                        TvRepository.MODE_SEARCH,
                    value =
                        term,
                    includeHidden =
                        true,
                    limit =
                        MAX_NETWORK_CHANNELS,
                    offset =
                        0,
                    deduplicate =
                        false
                )

            result.addAll(
                channels.filter {
                    looksLikeNetworkChannel(
                        channel = it,
                        network = term
                    )
                }
            )
        }

        return result
            .distinctBy {
                it.streamId
            }
            .sortedWith(
                compareByDescending<TvChannel> {
                    it.favorite
                }
                    .thenByDescending {
                        isKnownWorking(
                            it
                        )
                    }
                    .thenByDescending {
                        it.lastSuccess
                    }
                    .thenByDescending {
                        it.successCount
                    }
                    .thenBy {
                        it.failureCount
                    }
            )
    }


    private fun looksLikeNetworkChannel(
        channel: TvChannel,
        network: String
    ): Boolean {

        val name =
            normalizeText(
                channel.name
            )

        val term =
            normalizeText(
                network
            )

        if (
            !name.contains(
                term
            )
        ) {

            return false
        }

        val category =
            channel.category
                .lowercase(
                    Locale.US
                )

        if (
            category == "news" &&
            term in
                setOf(
                    "cbs",
                    "fox",
                    "nbc",
                    "abc"
                )
        ) {

            return false
        }

        return true
    }


    private fun findMatchingProgramme(
        guide: TvGuideSummary,
        game: NflGame
    ): TvProgramme? {

        val programmes =
            mutableListOf<TvProgramme>()

        guide.current?.let {
            programmes.add(it)
        }

        programmes.addAll(
            guide.upcoming
        )

        return programmes.firstOrNull {
            programmeMatchesGame(
                programme = it,
                game = game
            )
        }
    }


    private fun programmeMatchesGame(
        programme: TvProgramme,
        game: NflGame
    ): Boolean {

        val text =
            normalizeText(
                programme.title +
                    " " +
                    (
                        programme.description
                            ?: ""
                        )
            )

        return containsTeam(
            text = text,
            team = game.away
        ) &&
            containsTeam(
                text = text,
                team = game.home
            )
    }


    private fun containsTeam(
        text: String,
        team: NflTeam
    ): Boolean {

        val tokens =
            listOf(
                team.displayName,
                team.shortName,
                team.nickname,
                team.location,
                team.abbreviation
            )
                .map {
                    normalizeText(
                        it
                    )
                }
                .filter {
                    it.length >= 2
                }
                .distinct()

        return tokens.any {
            text.contains(
                it
            )
        }
    }


    private fun isUsable(
        channel: TvChannel
    ): Boolean {

        return !channel.manualHidden &&
            !channel.autoHidden
    }


    private fun isKnownWorking(
        channel: TvChannel
    ): Boolean {

        return !channel.autoHidden &&
            channel.successCount >
                0 &&
            channel.consecutiveFailures ==
                0
    }


    private fun buildAffiliateEvidence(
        channel: TvChannel
    ): String {

        val state =
            when {

                isKnownWorking(
                    channel
                ) ->
                    "working"

                channel.autoHidden ->
                    "auto-hidden after failures"

                channel.manualHidden ->
                    "hidden by user"

                channel.consecutiveFailures >
                    0 ->
                    "recent failures"

                else ->
                    "unverified"
            }

        return "${channel.name} (${channel.country.ifBlank { "unknown market" }}, $state)"
    }


    private fun loadCoverageText(
        nowMs: Long
    ): String? {

        val age =
            nowMs -
                cachedCoverageAtMs

        if (
            cachedCoverageText != null &&
            cachedCoverageAtMs > 0L &&
            age in 0 until SCHEDULE_CACHE_MS
        ) {

            return cachedCoverageText
        }

        return try {

            htmlToPlainText(
                fetchText(
                    SPORTS_MAPS
                )
            ).also {

                cachedCoverageText =
                    it

                cachedCoverageAtMs =
                    nowMs
            }

        } catch (_: Exception) {

            null
        }
    }


    private fun extractCoverageSummary(
        game: NflGame,
        coverageText: String?
    ): String? {

        val text =
            coverageText
                ?.trim()
                .orEmpty()

        if (text.isBlank()) {

            return null
        }

        val lower =
            text.lowercase(
                Locale.US
            )

        val marker =
            lower.indexOf(
                "coverage map description"
            )

        if (marker < 0) {

            return null
        }

        val afterMarker =
            text.substring(
                marker
            )

        val normalized =
            normalizeText(
                afterMarker
            )

        val away =
            normalizeText(
                game.away.shortName
            )

        val home =
            normalizeText(
                game.home.shortName
            )

        val awayIndex =
            normalized.indexOf(
                away
            )

        if (awayIndex < 0) {

            return null
        }

        val homeIndex =
            normalized.indexOf(
                home,
                awayIndex
            )

        if (
            homeIndex < 0 ||
            homeIndex -
                awayIndex >
                300
        ) {

            return null
        }

        val rawAwayIndex =
            afterMarker.lowercase(
                Locale.US
            ).indexOf(
                game.away.shortName.lowercase(
                    Locale.US
                )
            )

        if (rawAwayIndex < 0) {

            return null
        }

        val start =
            (
                rawAwayIndex -
                    60
                )
                .coerceAtLeast(
                    0
                )

        val end =
            (
                rawAwayIndex +
                    430
                )
                .coerceAtMost(
                    afterMarker.length
                )

        return afterMarker
            .substring(
                start,
                end
            )
            .replace(
                Regex(
                    "\\s+"
                ),
                " "
            )
            .trim()
    }


    private fun matchesWindow(
        game: NflGame,
        window: NflWindow,
        nowMs: Long
    ): Boolean {

        val eastern =
            TimeZone.getTimeZone(
                "America/New_York"
            )

        return when (window) {

            NflWindow.LIVE -> {

                game.state.equals(
                    "in",
                    ignoreCase = true
                ) ||
                    (
                        game.startMs <=
                            nowMs +
                                LIVE_GRACE_MS &&
                        game.startMs >=
                            nowMs -
                                LIVE_GRACE_MS &&
                        !game.state.equals(
                            "post",
                            ignoreCase = true
                        )
                    )
            }

            NflWindow.TODAY -> {

                sameEasternDay(
                    firstMs =
                        game.startMs,
                    secondMs =
                        nowMs,
                    timeZone =
                        eastern
                )
            }

            NflWindow.WEEK -> {

                game.startMs >=
                    nowMs -
                        LIVE_GRACE_MS &&
                    game.startMs <=
                        nowMs +
                            8L *
                            24L *
                            60L *
                            60L *
                            1_000L
            }
        }
    }


    private fun sameEasternDay(
        firstMs: Long,
        secondMs: Long,
        timeZone: TimeZone
    ): Boolean {

        val first =
            Calendar.getInstance(
                timeZone
            ).apply {
                timeInMillis =
                    firstMs
            }

        val second =
            Calendar.getInstance(
                timeZone
            ).apply {
                timeInMillis =
                    secondMs
            }

        return first.get(
            Calendar.YEAR
        ) ==
            second.get(
                Calendar.YEAR
            ) &&
            first.get(
                Calendar.DAY_OF_YEAR
            ) ==
            second.get(
                Calendar.DAY_OF_YEAR
            )
    }


    private fun isRegionalSundayGame(
        startMs: Long,
        networks: List<String>
    ): Boolean {

        val calendar =
            Calendar.getInstance(
                TimeZone.getTimeZone(
                    "America/New_York"
                )
            ).apply {
                timeInMillis =
                    startMs
            }

        val sunday =
            calendar.get(
                Calendar.DAY_OF_WEEK
            ) ==
                Calendar.SUNDAY

        val hour =
            calendar.get(
                Calendar.HOUR_OF_DAY
            )

        val regionalNetwork =
            networks.any {
                val normalized =
                    normalizeNetwork(
                        it
                    )

                normalized ==
                    "CBS" ||
                    normalized ==
                    "FOX"
            }

        return sunday &&
            hour <
                19 &&
            regionalNetwork
    }


    private fun primaryNetwork(
        game: NflGame
    ): String {

        return game.networks
            .firstOrNull()
            ?: "Unknown network"
    }


    private fun networkSearchTerms(
        network: String
    ): List<String> {

        return when (
            normalizeNetwork(
                network
            )
        ) {

            "CBS" ->
                listOf(
                    "CBS"
                )

            "FOX" ->
                listOf(
                    "FOX"
                )

            "NBC" ->
                listOf(
                    "NBC"
                )

            "ABC" ->
                listOf(
                    "ABC"
                )

            "ESPN",
            "ESPN2" ->
                listOf(
                    "ESPN"
                )

            "NFL Network" ->
                listOf(
                    "NFL Network",
                    "NFLN"
                )

            "Prime Video" ->
                listOf(
                    "Prime Video"
                )

            "Netflix" ->
                listOf(
                    "Netflix"
                )

            "Peacock" ->
                listOf(
                    "Peacock"
                )

            else ->
                listOf(
                    network
                )
        }
    }


    private fun normalizeNetwork(
        raw: String
    ): String {

        return when (
            raw.trim()
                .lowercase(
                    Locale.US
                )
        ) {

            "nfln",
            "nfl net",
            "nfl network" ->
                "NFL Network"

            "prime",
            "amazon prime",
            "prime video" ->
                "Prime Video"

            "espn 2",
            "espn2" ->
                "ESPN2"

            "cbs" ->
                "CBS"

            "fox" ->
                "FOX"

            "nbc" ->
                "NBC"

            "abc" ->
                "ABC"

            "espn" ->
                "ESPN"

            "netflix" ->
                "Netflix"

            "peacock" ->
                "Peacock"

            else ->
                raw.trim()
        }
    }


    private fun normalizeText(
        raw: String
    ): String {

        return raw
            .lowercase(
                Locale.US
            )
            .replace(
                Regex(
                    "[^a-z0-9]+"
                ),
                " "
            )
            .trim()
    }


    private fun parseIsoDate(
        raw: String
    ): Long? {

        if (raw.isBlank()) {

            return null
        }

        val formats =
            listOf(
                "yyyy-MM-dd'T'HH:mmX",
                "yyyy-MM-dd'T'HH:mm:ssX",
                "yyyy-MM-dd'T'HH:mm:ss.SSSX"
            )

        for (pattern in formats) {

            try {

                val parser =
                    SimpleDateFormat(
                        pattern,
                        Locale.US
                    ).apply {
                        timeZone =
                            TimeZone.getTimeZone(
                                "UTC"
                            )
                    }

                val parsed =
                    parser.parse(
                        raw
                    )

                if (parsed != null) {

                    return parsed.time
                }

            } catch (_: Exception) {

                // Try the next known ESPN timestamp format.
            }
        }

        return null
    }


    private fun htmlToPlainText(
        html: String
    ): String {

        return html
            .replace(
                Regex(
                    "(?is)<script.*?</script>"
                ),
                " "
            )
            .replace(
                Regex(
                    "(?is)<style.*?</style>"
                ),
                " "
            )
            .replace(
                Regex(
                    "(?is)<[^>]+>"
                ),
                " "
            )
            .replace(
                "&amp;",
                "&"
            )
            .replace(
                "&nbsp;",
                " "
            )
            .replace(
                "&#39;",
                "'"
            )
            .replace(
                "&quot;",
                "\""
            )
            .replace(
                Regex(
                    "\\s+"
                ),
                " "
            )
            .trim()
    }


    private fun fetchText(
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
                FETCH_TIMEOUT_MS

            connection.readTimeout =
                FETCH_TIMEOUT_MS

            connection.useCaches =
                false

            connection.instanceFollowRedirects =
                true

            connection.setRequestProperty(
                "Accept",
                "application/json,text/html,text/plain,*/*"
            )

            connection.setRequestProperty(
                "Accept-Language",
                "en-US,en;q=0.9"
            )

            connection.setRequestProperty(
                "User-Agent",
                "Mozilla/5.0 (Android TV) PrivyHub/1.0"
            )

            val responseCode =
                connection.responseCode

            val stream =
                if (
                    responseCode in
                    200..299
                ) {

                    connection.inputStream

                } else {

                    connection.errorStream
                }

            val body =
                stream
                    ?.bufferedReader()
                    ?.use {
                        it.readText()
                    }
                    .orEmpty()

            if (
                responseCode !in
                200..299
            ) {

                throw IllegalStateException(
                    "HTTP $responseCode from $urlString"
                )
            }

            body

        } finally {

            connection.disconnect()
        }
    }
}
