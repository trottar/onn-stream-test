package com.safeiot.privyhub

import android.content.ContentValues
import android.content.Context
import android.database.Cursor
import android.database.sqlite.SQLiteDatabase

import org.json.JSONArray
import org.json.JSONObject

import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.util.Locale


data class TvChannel(
    val streamId: String,
    val channelId: String,
    val name: String,
    val url: String,
    val referrer: String?,
    val userAgent: String?,
    val category: String,
    val country: String,
    val quality: String?,
    val label: String?,
    val favorite: Boolean,
    val manualHidden: Boolean,
    val autoHidden: Boolean,
    val successCount: Int,
    val failureCount: Int,
    val consecutiveFailures: Int,
    val lastSuccess: Long,
    val lastFailure: Long,
    val lastWatched: Long,
    val providerId: String,
    val sourceName: String,
    val sourceUrl: String,
    val sourceCategory: String,
    val favoriteGroup: String,
    val favoriteOrder: Int,
    val protectAutoHide: Boolean
)


data class TvLanguageOption(
    val code: String,
    val name: String
)


data class TvRefreshResult(
    val languageCode: String,
    val channelCount: Int,
    val refreshed: Boolean,
    val usedCachedData: Boolean
)


data class TvProvider(
    val providerId: String,
    val name: String,
    val type: String,
    val url: String,
    val enabled: Boolean,
    val languageCode: String,
    val builtin: Boolean
)


data class TvCatalogStats(
    val streams: Int,
    val favorites: Int,
    val hidden: Int,
    val reliable: Int,
    val providers: Int,
    val refreshedAtMs: Long
)


class TvRepository(
    context: Context
) {

    companion object {
        const val ALL_LANGUAGES = "*"
        const val ENGLISH = "eng"

        const val MODE_ALL = "all"
        const val MODE_FAVORITES = "favorites"
        const val MODE_FAVORITE_GROUP = "favorite_group"
        const val MODE_RECENT = "recent"
        const val MODE_RELIABLE = "reliable"
        const val MODE_HIDDEN = "hidden"
        const val MODE_SEARCH = "search"
        const val MODE_CATEGORY = "category"
        const val MODE_CURATED = "curated"

        const val BUILTIN_PROVIDER_ID = TvDatabase.BUILTIN_PROVIDER_ID

        const val FREE_TV_PROVIDER_ID =
            "free_tv"

        const val FREECASTHUB_PROVIDER_ID =
            "freecasthub"

        private const val PLAYLIST_BASE =
            "https://iptv-org.github.io/iptv"

        private const val FREE_TV_URL =
            "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"

        private const val FREECASTHUB_URL =
            "https://raw.githubusercontent.com/freecasthub/public-iptv/main/playlist.m3u"

        private const val LANGUAGES_URL =
            "https://iptv-org.github.io/api/languages.json"

        private const val FETCH_TIMEOUT_MS = 15_000
        private const val REFRESH_INTERVAL_MS =
            12L * 60L * 60L * 1_000L
        private const val AUTO_HIDE_AFTER_FAILURES = 3

        private const val MAX_PROVIDER_STREAMS = 5_000
        private const val MAX_PLAYLIST_CHARS = 8_000_000

        /*
         * Count + page rendering often issue the same logical catalog query
         * back-to-back. Keep only a few short-lived results so the onn does
         * not rebuild thousands of TvChannel objects twice.
         */
        private const val DEDUPE_CACHE_TTL_MS = 5_000L
        private const val MAX_DEDUPE_CACHE_ENTRIES = 3

        private val ENGLISH_COUNTRIES =
            setOf("US", "CA", "GB", "IE", "AU", "NZ")

        val CURATED_GROUPS = linkedMapOf(
            "news" to Pair("News", setOf("news", "legislative", "public")),
            "sports" to Pair("Sports", setOf("sports")),
            "movies_series" to Pair("Movies & Series", setOf("movies", "series", "classic")),
            "documentary_science" to Pair("Documentary & Science", setOf("documentary", "science", "education")),
            "kids_family" to Pair("Kids & Family", setOf("kids", "family", "animation")),
            "entertainment" to Pair("Entertainment", setOf("entertainment", "comedy", "music", "culture")),
            "lifestyle" to Pair("Lifestyle", setOf("lifestyle", "cooking", "travel", "outdoor", "auto", "relax")),
            "business" to Pair("Business", setOf("business")),
            "weather" to Pair("Weather", setOf("weather")),
            "religious" to Pair("Religious", setOf("religious")),
            "shopping" to Pair("Shopping", setOf("shop")),
            "other" to Pair("Other", setOf("general", "interactive", "undefined"))
        )

        private val CHANNEL_SELECT = listOf(
            "s.stream_id",
            "s.channel_id",
            "COALESCE(NULLIF(s.custom_name, ''), s.name)",
            "COALESCE(NULLIF(s.custom_url, ''), s.url)",
            "COALESCE(NULLIF(s.custom_referrer, ''), s.referrer)",
            "COALESCE(NULLIF(s.custom_user_agent, ''), s.user_agent)",
            "COALESCE(NULLIF(s.custom_category, ''), s.category)",
            "s.country",
            "s.quality",
            "s.label",
            "s.favorite",
            "s.manual_hidden",
            "s.auto_hidden",
            "s.success_count",
            "s.failure_count",
            "s.consecutive_failures",
            "s.last_success",
            "s.last_failure",
            "s.last_watched",
            "s.provider_id",
            "s.name",
            "s.url",
            "s.category",
            "s.favorite_group",
            "s.favorite_order",
            "s.protect_auto_hide"
        ).joinToString(", ")
    }


    private val db =
        TvDatabase(
            context.applicationContext
        )


    init {
        ensureManagedProviders()
    }


    private data class KnownChannelIdentity(
        val channelId: String,
        val category: String,
        val country: String
    )


    private data class DedupeCacheKey(
        val languageCode: String,
        val countryCode: String,
        val mode: String,
        val value: String,
        val includeHidden: Boolean
    )


    private data class DedupeCacheEntry(
        val createdAtMs: Long,
        val channels: List<TvChannel>
    )


    private val dedupeQueryCache =
        linkedMapOf<DedupeCacheKey, DedupeCacheEntry>()


    private data class ParsedStream(
        val streamId: String,
        val channelId: String,
        val name: String,
        val url: String,
        val referrer: String?,
        val userAgent: String?,
        val category: String,
        val country: String,
        val quality: String?,
        val label: String?,
        val providerId: String
    )


    fun ensureCatalog(
        languageCode: String,
        force: Boolean = false
    ): TvRefreshResult {
        val existing = countForLanguage(languageCode)
        val refreshedAt =
            db.getMeta(
                refreshKey(languageCode)
            )?.toLongOrNull() ?: 0L

        val age =
            System.currentTimeMillis() - refreshedAt

        if (
            !force &&
            existing > 0 &&
            refreshedAt > 0L &&
            age in 0 until REFRESH_INTERVAL_MS
        ) {
            return TvRefreshResult(
                languageCode,
                existing,
                refreshed = false,
                usedCachedData = true
            )
        }

        var anyRefresh = false
        var builtInSucceeded = false

        try {
            val parsed =
                parsePlaylist(
                    text = fetchText(playlistUrl(languageCode)),
                    providerId = BUILTIN_PROVIDER_ID,
                    requestedLanguageCode = languageCode
                )

            replaceProviderLanguageCatalog(
                providerId = BUILTIN_PROVIDER_ID,
                languageCode = languageCode,
                streams = parsed
            )

            builtInSucceeded = true
            anyRefresh = true
        } catch (error: Exception) {
            if (existing <= 0) {
                throw error
            }
        }

        for (provider in listProviders()) {
            if (
                provider.providerId == BUILTIN_PROVIDER_ID ||
                !provider.enabled ||
                provider.url.isBlank()
            ) {
                continue
            }

            if (
                languageCode != ALL_LANGUAGES &&
                provider.languageCode != ALL_LANGUAGES &&
                provider.languageCode != languageCode
            ) {
                continue
            }

            try {
                val parsed =
                    parsePlaylist(
                        text = fetchText(provider.url),
                        providerId = provider.providerId,
                        requestedLanguageCode = languageCode
                    )

                val membershipLanguage =
                    if (languageCode == ALL_LANGUAGES) {
                        ALL_LANGUAGES
                    } else if (provider.languageCode == ALL_LANGUAGES) {
                        languageCode
                    } else {
                        provider.languageCode
                    }

                replaceProviderLanguageCatalog(
                    providerId = provider.providerId,
                    languageCode = membershipLanguage,
                    streams = parsed
                )
                anyRefresh = true
            } catch (_: Exception) {
                // A custom provider may be temporarily unavailable. Preserve cache.
            }
        }

        if (builtInSucceeded || anyRefresh) {
            db.setMeta(
                refreshKey(languageCode),
                System.currentTimeMillis().toString()
            )
        }

        return TvRefreshResult(
            languageCode = languageCode,
            channelCount = countForLanguage(languageCode),
            refreshed = anyRefresh,
            usedCachedData = !anyRefresh
        )
    }


    fun fetchLanguageOptions(): List<TvLanguageOption> {
        val json =
            JSONArray(
                fetchText(LANGUAGES_URL)
            )

        val result = mutableListOf<TvLanguageOption>()

        for (index in 0 until json.length()) {
            val item = json.getJSONObject(index)
            val code = item.optString("code").trim()
            val name = item.optString("name").trim()
            if (code.isBlank() || name.isBlank()) continue
            result.add(TvLanguageOption(code, name))
        }

        return result
            .distinctBy { it.code }
            .sortedBy { it.name.lowercase() }
    }


    fun availableCountries(
        languageCode: String
    ): List<String> {
        val result = mutableListOf<String>()
        db.readableDatabase.rawQuery(
            """
            SELECT DISTINCT s.country
            FROM streams s
            INNER JOIN stream_languages sl ON sl.stream_id = s.stream_id
            WHERE sl.language = ?
              AND s.country <> ''
              AND EXISTS (
                  SELECT 1 FROM providers p
                  WHERE p.provider_id = s.provider_id AND p.enabled = 1
              )
            ORDER BY s.country COLLATE NOCASE
            """.trimIndent(),
            arrayOf(languageCode)
        ).use { cursor ->
            while (cursor.moveToNext()) result.add(cursor.getString(0))
        }
        return result
    }


    fun availableCategories(
        languageCode: String,
        countryCode: String
    ): List<String> {
        val args = mutableListOf(languageCode)
        val where = mutableListOf(
            "sl.language = ?",
            "EXISTS (SELECT 1 FROM providers p WHERE p.provider_id = s.provider_id AND p.enabled = 1)",
            "COALESCE(NULLIF(s.custom_category, ''), s.category) <> ''",
            "s.manual_hidden = 0",
            "s.auto_hidden = 0"
        )
        if (countryCode.isNotBlank()) {
            where.add("s.country = ?")
            args.add(countryCode)
        }

        val result = mutableListOf<String>()
        db.readableDatabase.rawQuery(
            """
            SELECT DISTINCT COALESCE(NULLIF(s.custom_category, ''), s.category)
            FROM streams s
            INNER JOIN stream_languages sl ON sl.stream_id = s.stream_id
            WHERE ${where.joinToString(" AND ")}
            ORDER BY 1 COLLATE NOCASE
            """.trimIndent(),
            args.toTypedArray()
        ).use { cursor ->
            while (cursor.moveToNext()) result.add(cursor.getString(0))
        }
        return result
    }


    fun countChannels(
        languageCode: String,
        countryCode: String,
        mode: String,
        value: String = "",
        includeHidden: Boolean = false
    ): Int {
        if (shouldDeduplicate(mode) && enabledProviderCount() > 1) {
            return dedupedChannelsFor(
                languageCode,
                countryCode,
                mode,
                value,
                includeHidden
            ).size
        }

        val query = buildQuery(
            languageCode, countryCode, mode, value, includeHidden,
            countOnly = true, limit = null, offset = null
        )
        db.readableDatabase.rawQuery(
            query.first, query.second.toTypedArray()
        ).use { cursor ->
            return if (cursor.moveToFirst()) cursor.getInt(0) else 0
        }
    }


    fun queryChannels(
        languageCode: String,
        countryCode: String,
        mode: String,
        value: String = "",
        includeHidden: Boolean = false,
        limit: Int = 80,
        offset: Int = 0,
        deduplicate: Boolean = true
    ): List<TvChannel> {
        if (deduplicate && shouldDeduplicate(mode) && enabledProviderCount() > 1) {
            return dedupedChannelsFor(
                languageCode,
                countryCode,
                mode,
                value,
                includeHidden
            ).drop(offset).take(limit)
        }

        return queryRawChannels(
            languageCode, countryCode, mode, value, includeHidden, limit, offset
        )
    }


    private fun dedupedChannelsFor(
        languageCode: String,
        countryCode: String,
        mode: String,
        value: String,
        includeHidden: Boolean
    ): List<TvChannel> {
        val key = DedupeCacheKey(
            languageCode,
            countryCode,
            mode,
            value,
            includeHidden
        )

        val now = System.currentTimeMillis()
        val cached = dedupeQueryCache[key]

        if (
            cached != null &&
            now - cached.createdAtMs in 0 until DEDUPE_CACHE_TTL_MS
        ) {
            return cached.channels
        }

        val channels = deduplicateChannels(
            queryRawChannels(
                languageCode,
                countryCode,
                mode,
                value,
                includeHidden,
                null,
                null
            )
        )

        if (dedupeQueryCache.size >= MAX_DEDUPE_CACHE_ENTRIES) {
            val oldest = dedupeQueryCache
                .minByOrNull { it.value.createdAtMs }
                ?.key

            if (oldest != null) {
                dedupeQueryCache.remove(oldest)
            }
        }

        dedupeQueryCache[key] = DedupeCacheEntry(
            now,
            channels
        )

        return channels
    }


    private fun invalidateDedupeCache() {
        dedupeQueryCache.clear()
    }


    private fun queryRawChannels(
        languageCode: String,
        countryCode: String,
        mode: String,
        value: String,
        includeHidden: Boolean,
        limit: Int?,
        offset: Int?
    ): List<TvChannel> {
        val query = buildQuery(
            languageCode, countryCode, mode, value, includeHidden,
            countOnly = false, limit = limit, offset = offset
        )
        val result = mutableListOf<TvChannel>()
        db.readableDatabase.rawQuery(
            query.first, query.second.toTypedArray()
        ).use { cursor ->
            while (cursor.moveToNext()) {
                result.add(channelFromCursor(cursor))
            }
        }
        return result
    }


    fun getChannel(
        streamId: String
    ): TvChannel? {
        db.readableDatabase.rawQuery(
            "SELECT $CHANNEL_SELECT FROM streams s WHERE s.stream_id = ? LIMIT 1",
            arrayOf(streamId)
        ).use { cursor ->
            return if (cursor.moveToFirst()) channelFromCursor(cursor) else null
        }
    }


    fun isTvStreamId(
        streamId: String
    ): Boolean {
        if (!streamId.startsWith("tv_stream_")) return false
        db.readableDatabase.rawQuery(
            "SELECT 1 FROM streams WHERE stream_id = ? LIMIT 1",
            arrayOf(streamId)
        ).use { cursor -> return cursor.moveToFirst() }
    }


    fun recordWatched(
        streamId: String
    ) {
        val previousCurrent = db.getMeta("tv_current_stream")
        if (!previousCurrent.isNullOrBlank() && previousCurrent != streamId) {
            db.setMeta("tv_previous_stream", previousCurrent)
        }
        db.setMeta("tv_current_stream", streamId)

        val values = ContentValues().apply {
            put("last_watched", System.currentTimeMillis())
        }
        db.writableDatabase.update(
            "streams",
            values,
            "stream_id = ?",
            arrayOf(streamId)
        )
    }


    fun previousStreamId(): String? =
        db.getMeta("tv_previous_stream")
            ?.takeIf { isTvStreamId(it) }


    fun currentStreamId(): String? =
        db.getMeta("tv_current_stream")
            ?.takeIf { isTvStreamId(it) }


    fun recordSuccess(
        streamId: String
    ) {
        val current = getChannel(streamId) ?: return
        val values = ContentValues().apply {
            put("success_count", current.successCount + 1)
            put("consecutive_failures", 0)
            put("auto_hidden", 0)
            put("last_success", System.currentTimeMillis())
        }
        db.writableDatabase.update(
            "streams",
            values,
            "stream_id = ?",
            arrayOf(streamId)
        )
    }


    fun recordFailure(
        streamId: String
    ) {
        val current = getChannel(streamId) ?: return
        val consecutive = current.consecutiveFailures + 1
        val shouldAutoHide =
            !current.favorite &&
            !current.protectAutoHide &&
            consecutive >= AUTO_HIDE_AFTER_FAILURES

        val values = ContentValues().apply {
            put("failure_count", current.failureCount + 1)
            put("consecutive_failures", consecutive)
            put("last_failure", System.currentTimeMillis())
            if (shouldAutoHide) put("auto_hidden", 1)
        }
        db.writableDatabase.update(
            "streams",
            values,
            "stream_id = ?",
            arrayOf(streamId)
        )
    }


    fun toggleFavorite(
        streamId: String
    ): Boolean {
        val current = getChannel(streamId) ?: return false
        val favorite = !current.favorite
        val values = ContentValues().apply {
            put("favorite", if (favorite) 1 else 0)
            if (favorite) {
                put("manual_hidden", 0)
                put("auto_hidden", 0)
                if (current.favoriteOrder <= 0) {
                    put("favorite_order", nextFavoriteOrder(current.favoriteGroup))
                }
            }
        }
        db.writableDatabase.update(
            "streams",
            values,
            "stream_id = ?",
            arrayOf(streamId)
        )
        invalidateDedupeCache()
        return favorite
    }


    fun toggleHidden(
        streamId: String
    ): Boolean {
        val current = getChannel(streamId) ?: return false
        val currentlyHidden = current.manualHidden || current.autoHidden
        val values = ContentValues().apply {
            if (currentlyHidden) {
                put("manual_hidden", 0)
                put("auto_hidden", 0)
            } else {
                put("manual_hidden", 1)
            }
        }
        db.writableDatabase.update(
            "streams",
            values,
            "stream_id = ?",
            arrayOf(streamId)
        )
        invalidateDedupeCache()
        return !currentlyHidden
    }


    fun resetHealth(
        streamId: String
    ) {
        val values = ContentValues().apply {
            put("success_count", 0)
            put("failure_count", 0)
            put("consecutive_failures", 0)
            put("last_success", 0)
            put("last_failure", 0)
            put("auto_hidden", 0)
        }
        db.writableDatabase.update(
            "streams",
            values,
            "stream_id = ?",
            arrayOf(streamId)
        )
    }


    fun resetAllHealth() {
        val values = ContentValues().apply {
            put("success_count", 0)
            put("failure_count", 0)
            put("consecutive_failures", 0)
            put("last_success", 0)
            put("last_failure", 0)
            put("auto_hidden", 0)
        }
        db.writableDatabase.update("streams", values, null, null)
    }


    fun setFavoriteGroup(
        streamId: String,
        group: String
    ) {
        val normalized = group.trim()
        val values = ContentValues().apply {
            put("favorite", 1)
            put("favorite_group", normalized)
            put("favorite_order", nextFavoriteOrder(normalized))
            put("manual_hidden", 0)
            put("auto_hidden", 0)
        }
        db.writableDatabase.update(
            "streams",
            values,
            "stream_id = ?",
            arrayOf(streamId)
        )
    }


    fun favoriteGroups(): List<String> {
        val result = mutableListOf<String>()
        db.readableDatabase.rawQuery(
            """
            SELECT DISTINCT favorite_group
            FROM streams
            WHERE favorite = 1 AND favorite_group <> ''
            ORDER BY favorite_group COLLATE NOCASE
            """.trimIndent(),
            null
        ).use { cursor ->
            while (cursor.moveToNext()) result.add(cursor.getString(0))
        }
        return result
    }


    fun moveFavorite(
        streamId: String,
        direction: Int
    ): Boolean {
        val current = getChannel(streamId) ?: return false
        if (!current.favorite || direction == 0) return false

        normalizeFavoriteOrder(current.favoriteGroup)
        val ordered = queryFavoriteIds(current.favoriteGroup)
        val index = ordered.indexOf(streamId)
        if (index < 0) return false
        val target = (index + direction).coerceIn(0, ordered.lastIndex)
        if (target == index) return false

        val otherId = ordered[target]
        val firstOrder = favoriteOrder(streamId)
        val secondOrder = favoriteOrder(otherId)
        val database = db.writableDatabase
        database.beginTransaction()
        try {
            updateFavoriteOrder(database, streamId, secondOrder)
            updateFavoriteOrder(database, otherId, firstOrder)
            database.setTransactionSuccessful()
        } finally {
            database.endTransaction()
        }
        return true
    }


    fun updateChannelProfile(
        streamId: String,
        name: String,
        category: String,
        url: String,
        referrer: String,
        userAgent: String,
        protectAutoHide: Boolean
    ) {
        val values = ContentValues().apply {
            put("custom_name", name.trim())
            put("custom_category", category.trim().lowercase())
            put("custom_url", url.trim())
            put("custom_referrer", referrer.trim())
            put("custom_user_agent", userAgent.trim())
            put("protect_auto_hide", if (protectAutoHide) 1 else 0)
            if (protectAutoHide) put("auto_hidden", 0)
        }
        db.writableDatabase.update(
            "streams",
            values,
            "stream_id = ?",
            arrayOf(streamId)
        )
    }


    fun resetChannelProfile(
        streamId: String
    ) {
        val values = ContentValues().apply {
            putNull("custom_name")
            putNull("custom_category")
            putNull("custom_url")
            putNull("custom_referrer")
            putNull("custom_user_agent")
            put("protect_auto_hide", 0)
        }
        db.writableDatabase.update(
            "streams",
            values,
            "stream_id = ?",
            arrayOf(streamId)
        )
    }


    fun listProviders(): List<TvProvider> {
        val result = mutableListOf<TvProvider>()
        db.readableDatabase.query(
            "providers",
            arrayOf("provider_id", "name", "type", "url", "enabled", "language_code", "builtin"),
            null,
            null,
            null,
            null,
            "builtin DESC, name COLLATE NOCASE"
        ).use { cursor ->
            while (cursor.moveToNext()) {
                result.add(
                    TvProvider(
                        providerId = cursor.getString(0),
                        name = cursor.getString(1),
                        type = cursor.getString(2),
                        url = cursor.getString(3),
                        enabled = cursor.getInt(4) != 0,
                        languageCode = cursor.getString(5),
                        builtin = cursor.getInt(6) != 0
                    )
                )
            }
        }
        return result
    }


    fun addCustomProvider(
        name: String,
        url: String,
        languageCode: String
    ): TvProvider {
        val cleanName = name.trim().ifBlank { "Custom M3U" }
        val cleanUrl = url.trim()
        require(cleanUrl.startsWith("http://") || cleanUrl.startsWith("https://")) {
            "Custom M3U must use http:// or https://"
        }
        val id = "m3u_${hashId("$cleanName|$cleanUrl").take(16)}"
        val values = ContentValues().apply {
            put("provider_id", id)
            put("name", cleanName)
            put("type", "m3u_url")
            put("url", cleanUrl)
            put("enabled", 1)
            put("language_code", languageCode.ifBlank { ENGLISH })
            put("builtin", 0)
            put("updated_at", System.currentTimeMillis())
        }
        db.writableDatabase.insertWithOnConflict(
            "providers",
            null,
            values,
            SQLiteDatabase.CONFLICT_REPLACE
        )
        invalidateCatalogCache()
        return listProviders().first { it.providerId == id }
    }


    fun setProviderEnabled(
        providerId: String,
        enabled: Boolean
    ) {
        if (providerId == BUILTIN_PROVIDER_ID) return
        val values = ContentValues().apply {
            put("enabled", if (enabled) 1 else 0)
        }
        db.writableDatabase.update(
            "providers",
            values,
            "provider_id = ?",
            arrayOf(providerId)
        )
        invalidateCatalogCache()
    }


    fun removeProvider(
        providerId: String
    ) {
        val provider = listProviders().firstOrNull { it.providerId == providerId }
        if (provider == null || provider.builtin) return
        val database = db.writableDatabase
        database.beginTransaction()
        try {
            database.execSQL(
                "DELETE FROM stream_languages WHERE stream_id IN (SELECT stream_id FROM streams WHERE provider_id = ?)",
                arrayOf(providerId)
            )
            database.delete("streams", "provider_id = ?", arrayOf(providerId))
            database.delete("providers", "provider_id = ?", arrayOf(providerId))
            database.setTransactionSuccessful()
        } finally {
            database.endTransaction()
        }
        invalidateCatalogCache()
    }


    fun providerDisplayName(
        providerId: String
    ): String =
        listProviders().firstOrNull { it.providerId == providerId }?.name ?: providerId


    fun invalidateCatalogCache() {
        invalidateDedupeCache()

        db.writableDatabase.delete(
            "meta",
            "key LIKE ?",
            arrayOf("playlist_refresh_%")
        )
    }


    fun catalogStats(
        languageCode: String
    ): TvCatalogStats {
        return TvCatalogStats(
            streams = scalarInt("SELECT COUNT(*) FROM streams"),
            favorites = scalarInt("SELECT COUNT(*) FROM streams WHERE favorite = 1"),
            hidden = scalarInt("SELECT COUNT(*) FROM streams WHERE manual_hidden = 1 OR auto_hidden = 1"),
            reliable = scalarInt("SELECT COUNT(*) FROM streams WHERE success_count > 0 AND consecutive_failures = 0"),
            providers = scalarInt("SELECT COUNT(*) FROM providers WHERE enabled = 1"),
            refreshedAtMs = db.getMeta(refreshKey(languageCode))?.toLongOrNull() ?: 0L
        )
    }


    fun exportSettingsJson(): String {
        val root = JSONObject()
        root.put("version", 2)

        val managedProviders = JSONArray()
        for (provider in listProviders().filter {
            it.builtin && it.providerId != BUILTIN_PROVIDER_ID
        }) {
            managedProviders.put(
                JSONObject()
                    .put("provider_id", provider.providerId)
                    .put("enabled", provider.enabled)
            )
        }
        root.put("managed_providers", managedProviders)

        val providers = JSONArray()
        for (provider in listProviders().filter { !it.builtin }) {
            providers.put(
                JSONObject()
                    .put("name", provider.name)
                    .put("url", provider.url)
                    .put("language_code", provider.languageCode)
                    .put("enabled", provider.enabled)
            )
        }
        root.put("providers", providers)

        val channels = JSONArray()
        db.readableDatabase.rawQuery(
            """
            SELECT stream_id, favorite, manual_hidden, success_count, failure_count,
                   consecutive_failures, last_success, last_failure, last_watched,
                   custom_name, custom_category, custom_url, custom_referrer,
                   custom_user_agent, favorite_group, favorite_order, protect_auto_hide
            FROM streams
            WHERE favorite = 1 OR manual_hidden = 1 OR auto_hidden = 1 OR
                  success_count > 0 OR failure_count > 0 OR last_watched > 0 OR
                  custom_name IS NOT NULL OR custom_category IS NOT NULL OR
                  custom_url IS NOT NULL OR custom_referrer IS NOT NULL OR
                  custom_user_agent IS NOT NULL OR favorite_group <> '' OR
                  protect_auto_hide = 1
            """.trimIndent(),
            null
        ).use { cursor ->
            while (cursor.moveToNext()) {
                channels.put(
                    JSONObject()
                        .put("stream_id", cursor.getString(0))
                        .put("favorite", cursor.getInt(1) != 0)
                        .put("manual_hidden", cursor.getInt(2) != 0)
                        .put("success_count", cursor.getInt(3))
                        .put("failure_count", cursor.getInt(4))
                        .put("consecutive_failures", cursor.getInt(5))
                        .put("last_success", cursor.getLong(6))
                        .put("last_failure", cursor.getLong(7))
                        .put("last_watched", cursor.getLong(8))
                        .put("custom_name", cursor.getStringOrEmpty(9))
                        .put("custom_category", cursor.getStringOrEmpty(10))
                        .put("custom_url", cursor.getStringOrEmpty(11))
                        .put("custom_referrer", cursor.getStringOrEmpty(12))
                        .put("custom_user_agent", cursor.getStringOrEmpty(13))
                        .put("favorite_group", cursor.getStringOrEmpty(14))
                        .put("favorite_order", cursor.getInt(15))
                        .put("protect_auto_hide", cursor.getInt(16) != 0)
                )
            }
        }
        root.put("channels", channels)
        return root.toString(2)
    }


    fun importSettingsJson(
        jsonText: String
    ) {
        val root = JSONObject(jsonText)

        val managedProviders = root.optJSONArray("managed_providers") ?: JSONArray()
        for (index in 0 until managedProviders.length()) {
            val item = managedProviders.getJSONObject(index)
            val providerId = item.optString("provider_id")
            if (providerId == FREE_TV_PROVIDER_ID || providerId == FREECASTHUB_PROVIDER_ID) {
                setProviderEnabled(providerId, item.optBoolean("enabled", false))
            }
        }

        val providers = root.optJSONArray("providers") ?: JSONArray()
        for (index in 0 until providers.length()) {
            val item = providers.getJSONObject(index)
            val provider = addCustomProvider(
                item.optString("name", "Custom M3U"),
                item.optString("url"),
                item.optString("language_code", ENGLISH)
            )
            setProviderEnabled(
                provider.providerId,
                item.optBoolean("enabled", true)
            )
        }

        val channels = root.optJSONArray("channels") ?: JSONArray()
        val database = db.writableDatabase
        database.beginTransaction()
        try {
            for (index in 0 until channels.length()) {
                val item = channels.getJSONObject(index)
                val streamId = item.optString("stream_id")
                if (streamId.isBlank() || !isTvStreamId(streamId)) continue
                val values = ContentValues().apply {
                    put("favorite", if (item.optBoolean("favorite")) 1 else 0)
                    put("manual_hidden", if (item.optBoolean("manual_hidden")) 1 else 0)
                    put("success_count", item.optInt("success_count"))
                    put("failure_count", item.optInt("failure_count"))
                    put("consecutive_failures", item.optInt("consecutive_failures"))
                    put("last_success", item.optLong("last_success"))
                    put("last_failure", item.optLong("last_failure"))
                    put("last_watched", item.optLong("last_watched"))
                    put("custom_name", item.optString("custom_name"))
                    put("custom_category", item.optString("custom_category"))
                    put("custom_url", item.optString("custom_url"))
                    put("custom_referrer", item.optString("custom_referrer"))
                    put("custom_user_agent", item.optString("custom_user_agent"))
                    put("favorite_group", item.optString("favorite_group"))
                    put("favorite_order", item.optInt("favorite_order"))
                    put("protect_auto_hide", if (item.optBoolean("protect_auto_hide")) 1 else 0)
                    put("auto_hidden", 0)
                }
                database.update("streams", values, "stream_id = ?", arrayOf(streamId))
            }
            database.setTransactionSuccessful()
        } finally {
            database.endTransaction()
        }
        invalidateCatalogCache()
    }


    fun countryDisplayName(
        countryCode: String
    ): String {
        if (countryCode.isBlank()) return "Unknown"
        val normalized = if (countryCode.uppercase() == "UK") "GB" else countryCode.uppercase()
        return try {
            Locale.Builder()
                .setRegion(normalized)
                .build()
                .displayCountry
                .takeIf { it.isNotBlank() }
                ?: countryCode.uppercase()
        } catch (_: Exception) {
            countryCode.uppercase()
        }
    }


    private fun ensureManagedProviders() {
        val managed = listOf(
            TvProvider(
                FREE_TV_PROVIDER_ID, "Free-TV", "managed_m3u", FREE_TV_URL,
                false, ALL_LANGUAGES, true
            ),
            TvProvider(
                FREECASTHUB_PROVIDER_ID, "FreeCastHub", "managed_m3u", FREECASTHUB_URL,
                false, ALL_LANGUAGES, true
            )
        )
        val database = db.writableDatabase
        for (provider in managed) {
            val values = ContentValues().apply {
                put("provider_id", provider.providerId)
                put("name", provider.name)
                put("type", provider.type)
                put("url", provider.url)
                put("enabled", if (provider.enabled) 1 else 0)
                put("language_code", provider.languageCode)
                put("builtin", 1)
                put("updated_at", 0L)
            }
            database.insertWithOnConflict(
                "providers", null, values, SQLiteDatabase.CONFLICT_IGNORE
            )
        }
    }


    private fun enabledProviderCount(): Int =
        scalarInt("SELECT COUNT(*) FROM providers WHERE enabled = 1")


    private fun shouldDeduplicate(mode: String): Boolean =
        mode != MODE_HIDDEN


    private fun deduplicateChannels(
        channels: List<TvChannel>
    ): List<TvChannel> {
        /*
         * The original multi-provider pass used indexOfFirst() for every
         * channel, making it O(n^2). These identity maps preserve the same
         * URL / tvg-id / normalized-name matching in approximately O(n).
         */
        val result = mutableListOf<TvChannel>()

        val byUrl = mutableMapOf<String, Int>()
        val byChannelId = mutableMapOf<String, Int>()
        val byNameCountry = mutableMapOf<String, Int>()
        val byNameBlankCountry = mutableMapOf<String, Int>()
        val byNameAny = mutableMapOf<String, Int>()

        fun register(
            channel: TvChannel,
            index: Int
        ) {
            val url = normalizeStreamIdentity(channel.url)

            if (url.isNotBlank()) {
                byUrl[url] = index
            }

            val channelId = meaningfulChannelId(channel.channelId)
                ?.lowercase()

            if (!channelId.isNullOrBlank()) {
                byChannelId[channelId] = index
            }

            val name = normalizeChannelName(channel.name)

            if (name.isBlank()) {
                return
            }

            byNameAny.putIfAbsent(name, index)

            val country = channel.country
                .trim()
                .lowercase()

            if (country.isBlank()) {
                byNameBlankCountry[name] = index
            } else {
                byNameCountry["$name|$country"] = index
            }
        }

        for (candidate in channels) {
            val url = normalizeStreamIdentity(candidate.url)
            val channelId = meaningfulChannelId(candidate.channelId)
                ?.lowercase()
            val name = normalizeChannelName(candidate.name)
            val country = candidate.country
                .trim()
                .lowercase()

            val index =
                byUrl[url]
                    ?: channelId?.let { byChannelId[it] }
                    ?: if (name.isBlank()) {
                        null
                    } else if (country.isBlank()) {
                        byNameAny[name]
                    } else {
                        byNameBlankCountry[name]
                            ?: byNameCountry["$name|$country"]
                    }

            if (index == null) {
                val newIndex = result.size
                result.add(candidate)
                register(candidate, newIndex)
                continue
            }

            val existing = result[index]

            if (
                candidateScore(candidate) >
                candidateScore(existing)
            ) {
                result[index] = candidate
            }

            /*
             * Preserve aliases from both providers even when one replaces
             * the other as the preferred logical-channel stream.
             */
            register(existing, index)
            register(candidate, index)
        }

        return result
    }


    private fun sameLogicalChannel(first: TvChannel, second: TvChannel): Boolean {
        if (normalizeStreamIdentity(first.url) == normalizeStreamIdentity(second.url)) return true
        val firstId = meaningfulChannelId(first.channelId)
        val secondId = meaningfulChannelId(second.channelId)
        if (firstId != null && secondId != null && firstId.equals(secondId, true)) return true
        val firstName = normalizeChannelName(first.name)
        val secondName = normalizeChannelName(second.name)
        if (firstName.isBlank() || firstName != secondName) return false
        return first.country.isBlank() || second.country.isBlank() ||
            first.country.equals(second.country, true)
    }


    private fun meaningfulChannelId(channelId: String): String? {
        val clean = channelId.trim()
        return clean.takeIf { it.isNotBlank() && !it.startsWith("tv_stream_") }
    }


    private fun normalizeChannelName(name: String): String =
        name.lowercase().replace(Regex("[^a-z0-9]+"), "")


    private fun normalizeStreamIdentity(url: String): String =
        url.trim().substringBefore("|").substringBefore("#")


    private fun candidateScore(channel: TvChannel): Long {
        var score = 0L
        if (channel.favorite) score += 1_000_000L
        if (!channel.manualHidden && !channel.autoHidden) score += 100_000L
        if (channel.successCount > 0 && channel.consecutiveFailures == 0) score += 50_000L
        score += channel.successCount.coerceAtMost(1_000) * 20L
        score -= channel.consecutiveFailures.coerceAtMost(100) * 1_000L
        score += when (channel.providerId) {
            BUILTIN_PROVIDER_ID -> 300L
            FREE_TV_PROVIDER_ID -> 200L
            FREECASTHUB_PROVIDER_ID -> 100L
            else -> 0L
        }
        return score
    }


    private fun buildQuery(
        languageCode: String,
        countryCode: String,
        mode: String,
        value: String,
        includeHidden: Boolean,
        countOnly: Boolean,
        limit: Int?,
        offset: Int?
    ): Pair<String, List<String>> {
        val args = mutableListOf<String>()
        val where = mutableListOf<String>(
            "EXISTS (SELECT 1 FROM providers p WHERE p.provider_id = s.provider_id AND p.enabled = 1)"
        )
        var joinLanguage = true

        val effectiveName = "COALESCE(NULLIF(s.custom_name, ''), s.name)"
        val effectiveCategory = "COALESCE(NULLIF(s.custom_category, ''), s.category)"

        when (mode) {
            MODE_FAVORITES -> {
                joinLanguage = false
                where.add("s.favorite = 1")
            }
            MODE_FAVORITE_GROUP -> {
                joinLanguage = false
                where.add("s.favorite = 1")
                where.add("s.favorite_group = ?")
                args.add(value)
            }
            MODE_RECENT -> {
                joinLanguage = false
                where.add("s.last_watched > 0")
            }
            MODE_HIDDEN -> {
                joinLanguage = false
                where.add("(s.manual_hidden = 1 OR s.auto_hidden = 1)")
            }
            MODE_RELIABLE -> {
                where.add("s.success_count > 0")
                where.add("s.consecutive_failures = 0")
            }
            MODE_SEARCH -> {
                where.add("$effectiveName LIKE ? COLLATE NOCASE")
                args.add("%${value.trim()}%")
            }
            MODE_CATEGORY -> {
                where.add("LOWER($effectiveCategory) = ?")
                args.add(value.lowercase())
            }
            MODE_CURATED -> {
                val categories = CURATED_GROUPS[value]?.second ?: emptySet()
                if (categories.isEmpty()) {
                    where.add("1 = 0")
                } else {
                    where.add(
                        "LOWER($effectiveCategory) IN (${categories.joinToString(",") { "?" }})"
                    )
                    args.addAll(categories)
                }
            }
            MODE_ALL -> Unit
            else -> where.add("1 = 0")
        }

        if (joinLanguage) {
            where.add("sl.language = ?")
            args.add(languageCode)
            if (countryCode.isNotBlank()) {
                where.add("s.country = ?")
                args.add(countryCode)
            }
        }

        if (!includeHidden && mode != MODE_HIDDEN) {
            where.add("s.manual_hidden = 0")
            where.add("s.auto_hidden = 0")
        }

        val select = if (countOnly) "COUNT(*)" else CHANNEL_SELECT
        val join = if (joinLanguage) {
            "INNER JOIN stream_languages sl ON sl.stream_id = s.stream_id"
        } else ""

        val order = if (countOnly) "" else when (mode) {
            MODE_FAVORITES, MODE_FAVORITE_GROUP ->
                "ORDER BY s.favorite_group COLLATE NOCASE, CASE WHEN s.favorite_order <= 0 THEN 2147483647 ELSE s.favorite_order END, s.last_watched DESC, $effectiveName COLLATE NOCASE"
            MODE_RECENT -> "ORDER BY s.last_watched DESC"
            MODE_HIDDEN -> "ORDER BY s.auto_hidden DESC, s.last_failure DESC, $effectiveName COLLATE NOCASE"
            MODE_RELIABLE -> "ORDER BY s.last_success DESC, s.success_count DESC, s.failure_count ASC, $effectiveName COLLATE NOCASE"
            else -> "ORDER BY s.favorite DESC, s.consecutive_failures ASC, s.last_success DESC, s.success_count DESC, $effectiveName COLLATE NOCASE"
        }

        val paging = if (!countOnly && limit != null && offset != null) {
            "LIMIT $limit OFFSET $offset"
        } else ""

        return """
            SELECT $select
            FROM streams s
            $join
            WHERE ${where.joinToString(" AND ")}
            $order
            $paging
        """.trimIndent() to args
    }


    private fun channelFromCursor(
        cursor: Cursor
    ): TvChannel {
        var i = 0
        return TvChannel(
            streamId = cursor.getString(i++),
            channelId = cursor.getString(i++),
            name = cursor.getString(i++),
            url = cursor.getString(i++),
            referrer = cursor.getStringOrNull(i++),
            userAgent = cursor.getStringOrNull(i++),
            category = cursor.getString(i++) ?: "",
            country = cursor.getString(i++) ?: "",
            quality = cursor.getStringOrNull(i++),
            label = cursor.getStringOrNull(i++),
            favorite = cursor.getInt(i++) != 0,
            manualHidden = cursor.getInt(i++) != 0,
            autoHidden = cursor.getInt(i++) != 0,
            successCount = cursor.getInt(i++),
            failureCount = cursor.getInt(i++),
            consecutiveFailures = cursor.getInt(i++),
            lastSuccess = cursor.getLong(i++),
            lastFailure = cursor.getLong(i++),
            lastWatched = cursor.getLong(i++),
            providerId = cursor.getString(i++),
            sourceName = cursor.getString(i++),
            sourceUrl = cursor.getString(i++),
            sourceCategory = cursor.getString(i++),
            favoriteGroup = cursor.getString(i++) ?: "",
            favoriteOrder = cursor.getInt(i++),
            protectAutoHide = cursor.getInt(i) != 0
        )
    }


    private fun replaceProviderLanguageCatalog(
        providerId: String,
        languageCode: String,
        streams: List<ParsedStream>
    ) {
        val database = db.writableDatabase
        database.beginTransaction()
        try {
            database.execSQL(
                "DELETE FROM stream_languages WHERE language = ? AND stream_id IN (SELECT stream_id FROM streams WHERE provider_id = ?)",
                arrayOf(languageCode, providerId)
            )
            val now = System.currentTimeMillis()
            for (stream in streams) {
                val insert = ContentValues().apply {
                    put("stream_id", stream.streamId)
                    put("channel_id", stream.channelId)
                    put("name", stream.name)
                    put("url", stream.url)
                    put("referrer", stream.referrer)
                    put("user_agent", stream.userAgent)
                    put("category", stream.category)
                    put("country", stream.country)
                    put("quality", stream.quality)
                    put("label", stream.label)
                    put("provider_id", stream.providerId)
                    put("updated_at", now)
                }
                database.insertWithOnConflict(
                    "streams",
                    null,
                    insert,
                    SQLiteDatabase.CONFLICT_IGNORE
                )
                database.update(
                    "streams",
                    insert,
                    "stream_id = ?",
                    arrayOf(stream.streamId)
                )

                val lang = ContentValues().apply {
                    put("stream_id", stream.streamId)
                    put("language", languageCode)
                }
                database.insertWithOnConflict(
                    "stream_languages",
                    null,
                    lang,
                    SQLiteDatabase.CONFLICT_REPLACE
                )
            }
            database.setTransactionSuccessful()
        } finally {
            database.endTransaction()
        }
    }


    private fun countForLanguage(
        languageCode: String
    ): Int =
        scalarInt(
            "SELECT COUNT(*) FROM stream_languages WHERE language = ?",
            arrayOf(languageCode)
        )


    private fun playlistUrl(
        languageCode: String
    ): String =
        if (languageCode == ALL_LANGUAGES) {
            "$PLAYLIST_BASE/index.m3u"
        } else {
            "$PLAYLIST_BASE/languages/$languageCode.m3u"
        }


    private fun refreshKey(
        languageCode: String
    ): String =
        "playlist_refresh_$languageCode"


    private fun fetchText(
        urlString: String
    ): String {
        val connection = URL(urlString).openConnection() as HttpURLConnection
        return try {
            connection.requestMethod = "GET"
            connection.connectTimeout = FETCH_TIMEOUT_MS
            connection.readTimeout = FETCH_TIMEOUT_MS
            connection.useCaches = false
            connection.instanceFollowRedirects = true
            connection.setRequestProperty("User-Agent", "PrivyHub/1.0 AndroidTV")
            connection.setRequestProperty("Cache-Control", "no-cache")
            val response = connection.responseCode
            if (response !in 200..299) {
                throw IllegalStateException("HTTP $response from $urlString")
            }
            connection.inputStream.bufferedReader().use { it.readText() }
        } finally {
            connection.disconnect()
        }
    }


    private fun parsePlaylist(
        text: String,
        providerId: String,
        requestedLanguageCode: String
    ): List<ParsedStream> {
        require(text.length <= MAX_PLAYLIST_CHARS) { "M3U source is too large" }

        val result = linkedMapOf<String, ParsedStream>()
        var name: String? = null
        var channelId = ""
        var rawCategory = "undefined"
        var referrer: String? = null
        var userAgent: String? = null
        var quality: String? = null
        var label: String? = null
        var explicitCountry = ""

        fun reset() {
            name = null
            channelId = ""
            rawCategory = "undefined"
            referrer = null
            userAgent = null
            quality = null
            label = null
            explicitCountry = ""
        }

        for (raw in text.lineSequence()) {
            val line = raw.trim()
            if (line.isBlank()) continue

            if (line.startsWith("#EXTINF:")) {
                val attrs = parseAttributes(line)
                channelId = attrs["tvg-id"].orEmpty().trim()
                rawCategory = attrs["group-title"].orEmpty().trim().ifBlank { "undefined" }.lowercase()
                explicitCountry = attrs["tvg-country"].orEmpty().trim().uppercase()
                referrer = attrs["http-referrer"]?.trim()?.takeIf { it.isNotBlank() }
                userAgent = attrs["http-user-agent"]?.trim()?.takeIf { it.isNotBlank() }
                val comma = findMetadataDelimiter(line)
                name = if (comma >= 0 && comma + 1 < line.length) {
                    cleanProviderName(line.substring(comma + 1))
                } else {
                    "Channel"
                }
                quality = Regex("\\((\\d{3,4}[pi])\\)", RegexOption.IGNORE_CASE)
                    .find(name.orEmpty())?.groupValues?.getOrNull(1)
                label = Regex("\\[([^]]+)]")
                    .findAll(name.orEmpty())
                    .joinToString("; ") { it.groupValues[1] }
                    .takeIf { it.isNotBlank() }
                continue
            }

            if (line.startsWith("#EXTVLCOPT:http-referrer=", true)) {
                referrer = line.substringAfter("=").trim()
                continue
            }
            if (line.startsWith("#EXTVLCOPT:http-user-agent=", true)) {
                userAgent = line.substringAfter("=").trim()
                continue
            }
            if (line.startsWith("#")) continue

            val pendingName = name ?: continue
            val parsed = parseStreamUrlAndHeaders(line)
            val streamUrl = parsed.first
            if (!streamUrl.startsWith("http://") && !streamUrl.startsWith("https://")) {
                reset(); continue
            }
            if (providerId != BUILTIN_PROVIDER_ID && !isDirectMediaCandidate(streamUrl)) {
                reset(); continue
            }

            val stableId = stableStreamId(providerId, streamUrl)
            val initialCountry = explicitCountry.ifBlank { countryFromChannelId(channelId) }
            if (!shouldIncludeManagedStream(providerId, requestedLanguageCode, initialCountry)) {
                reset(); continue
            }

            val known = if (providerId == BUILTIN_PROVIDER_ID) null else
                resolveBuiltinIdentity(channelId, pendingName, initialCountry)
            val finalChannelId = known?.channelId?.takeIf { it.isNotBlank() }
                ?: channelId.ifBlank { stableId }
            val country = initialCountry.ifBlank { known?.country.orEmpty() }
            val category = normalizeProviderCategory(
                providerId, rawCategory, pendingName, known?.category
            )
            val headers = parsed.second

            result.putIfAbsent(
                stableId,
                ParsedStream(
                    streamId = stableId,
                    channelId = finalChannelId,
                    name = pendingName,
                    url = streamUrl,
                    referrer = headers["referer"] ?: headers["referrer"] ?: referrer,
                    userAgent = headers["user-agent"] ?: headers["user_agent"] ?: userAgent,
                    category = category,
                    country = country,
                    quality = quality,
                    label = label,
                    providerId = providerId
                )
            )
            if (result.size >= MAX_PROVIDER_STREAMS) break
            reset()
        }
        return result.values.toList()
    }


    private fun cleanProviderName(raw: String): String =
        raw.replace("Ⓢ", "")
            .replace("Ⓖ", "")
            .replace("Ⓨ", "")
            .replace("Ⓣ", "")
            .replace(Regex("\\s+"), " ")
            .trim()
            .ifBlank { "Channel" }


    private fun shouldIncludeManagedStream(
        providerId: String,
        requestedLanguageCode: String,
        countryCode: String
    ): Boolean {
        if (requestedLanguageCode == ALL_LANGUAGES) return true
        return when (providerId) {
            FREE_TV_PROVIDER_ID ->
                requestedLanguageCode == ENGLISH && countryCode.uppercase() in ENGLISH_COUNTRIES
            FREECASTHUB_PROVIDER_ID -> requestedLanguageCode == ENGLISH
            else -> true
        }
    }


    private fun resolveBuiltinIdentity(
        proposedChannelId: String,
        channelName: String,
        countryCode: String
    ): KnownChannelIdentity? {
        if (proposedChannelId.isNotBlank()) {
            db.readableDatabase.rawQuery(
                "SELECT channel_id, category, country FROM streams " +
                    "WHERE provider_id = ? AND channel_id = ? LIMIT 1",
                arrayOf(BUILTIN_PROVIDER_ID, proposedChannelId)
            ).use { cursor ->
                if (cursor.moveToFirst()) {
                    return KnownChannelIdentity(
                        cursor.getString(0), cursor.getString(1) ?: "", cursor.getString(2) ?: ""
                    )
                }
            }
        }

        val args = mutableListOf(BUILTIN_PROVIDER_ID, channelName)
        val countryClause = if (countryCode.isNotBlank()) {
            args.add(countryCode); "AND country = ?"
        } else ""
        db.readableDatabase.rawQuery(
            "SELECT channel_id, category, country FROM streams " +
                "WHERE provider_id = ? AND name = ? COLLATE NOCASE $countryClause " +
                "ORDER BY success_count DESC, last_success DESC LIMIT 1",
            args.toTypedArray()
        ).use { cursor ->
            if (cursor.moveToFirst()) {
                return KnownChannelIdentity(
                    cursor.getString(0), cursor.getString(1) ?: "", cursor.getString(2) ?: ""
                )
            }
        }
        return null
    }


    private fun normalizeProviderCategory(
        providerId: String,
        rawCategory: String,
        channelName: String,
        knownCategory: String?
    ): String {
        val known = knownCategory?.trim()?.lowercase().orEmpty()
        if (known.isNotBlank() && known != "undefined") return known

        val direct = when (rawCategory.trim().lowercase()) {
            "news" -> "news"
            "sports", "sport" -> "sports"
            "weather" -> "weather"
            "education", "educational" -> "education"
            "movies", "movie", "cinema", "film" -> "movies"
            "documentary", "documentaries" -> "documentary"
            "kids", "children", "family" -> "kids"
            "music" -> "music"
            "business" -> "business"
            "religious", "religion" -> "religious"
            "shopping", "shop" -> "shop"
            "entertainment" -> "entertainment"
            else -> ""
        }
        if (direct.isNotBlank()) return direct
        if (providerId == FREE_TV_PROVIDER_ID || providerId == FREECASTHUB_PROVIDER_ID) {
            return inferCategoryFromName(channelName)
        }
        return rawCategory.trim().lowercase().ifBlank { "undefined" }
    }


    private fun inferCategoryFromName(name: String): String {
        val text = name.lowercase()
        fun has(vararg words: String) = words.any { text.contains(it) }
        return when {
            has("sport", "stadium", "golf", "racing", "soccer", "football", "baseball",
                "basketball", "hockey", "fifa", "nfl", "nba", "mlb", "nhl") -> "sports"
            has("news", "cnn", "euronews", "al jazeera") -> "news"
            has("weather") -> "weather"
            has("kids", "cartoon", "junior") -> "kids"
            has("movie", "cinema", "film") -> "movies"
            has("documentary", "science", "history", "nature") -> "documentary"
            has("education", "university", "learning") -> "education"
            has("music", "radio") -> "music"
            has("qvc", "shopping", "shop", "hsn") -> "shop"
            else -> "general"
        }
    }


    private fun isDirectMediaCandidate(url: String): Boolean {
        return try {
            val parsed = URL(url)
            val host = parsed.host.lowercase()
            val pageHost = host.endsWith("youtube.com") || host.endsWith("youtu.be") ||
                host.endsWith("twitch.tv") || host.endsWith("dailymotion.com")
            if (!pageHost) true else {
                val lower = url.lowercase()
                lower.contains(".m3u8") || lower.contains(".mpd")
            }
        } catch (_: Exception) {
            false
        }
    }


    private fun findMetadataDelimiter(
        line: String
    ): Int {
        var inQuotes = false
        for (index in line.indices) {
            when (line[index]) {
                '"' -> inQuotes = !inQuotes
                ',' -> if (!inQuotes) return index
            }
        }
        return -1
    }


    private fun parseAttributes(
        line: String
    ): Map<String, String> {
        val result = mutableMapOf<String, String>()
        val regex = Regex("([A-Za-z0-9_-]+)=\\\"([^\\\"]*)\\\"")
        for (match in regex.findAll(line)) {
            result[match.groupValues[1].lowercase()] = match.groupValues[2]
        }
        return result
    }


    private fun parseStreamUrlAndHeaders(
        line: String
    ): Pair<String, Map<String, String>> {
        val parts = line.split("|")
        val url = parts.first().trim()
        val headers = mutableMapOf<String, String>()
        for (part in parts.drop(1)) {
            val separator = part.indexOf("=")
            if (separator <= 0) continue
            val key = part.substring(0, separator).trim().lowercase()
            var value = part.substring(separator + 1).trim()
            if (value.length >= 2 && value.startsWith("\"") && value.endsWith("\"")) {
                value = value.substring(1, value.length - 1)
            }
            headers[key] = value
        }
        return url to headers
    }


    private fun countryFromChannelId(
        channelId: String
    ): String {
        if (channelId.isBlank()) return ""
        val base = channelId.substringBefore("@")
        val dot = base.lastIndexOf(".")
        if (dot < 0 || dot + 1 >= base.length) return ""
        val suffix = base.substring(dot + 1)
        if (suffix.length !in 2..3 || !suffix.all { it.isLetter() }) return ""
        return suffix.uppercase()
    }


    private fun stableStreamId(
        providerId: String,
        url: String
    ): String {
        val identity =
            if (providerId == BUILTIN_PROVIDER_ID) {
                /* Preserve v1 IPTV-org stream ids so favorites/history migrate. */
                url
            } else {
                "$providerId|$url"
            }

        return "tv_stream_${hashId(identity).take(16)}"
    }


    private fun hashId(
        value: String
    ): String {
        val digest = MessageDigest.getInstance("SHA-1").digest(value.toByteArray(Charsets.UTF_8))
        return digest.joinToString("") { "%02x".format(it) }
    }


    private fun nextFavoriteOrder(
        group: String
    ): Int {
        db.readableDatabase.rawQuery(
            "SELECT COALESCE(MAX(favorite_order), 0) + 10 FROM streams WHERE favorite = 1 AND favorite_group = ?",
            arrayOf(group)
        ).use { cursor ->
            return if (cursor.moveToFirst()) cursor.getInt(0) else 10
        }
    }


    private fun normalizeFavoriteOrder(
        group: String
    ) {
        val ids = queryFavoriteIds(group)
        val database = db.writableDatabase
        database.beginTransaction()
        try {
            ids.forEachIndexed { index, id ->
                updateFavoriteOrder(database, id, (index + 1) * 10)
            }
            database.setTransactionSuccessful()
        } finally {
            database.endTransaction()
        }
    }


    private fun queryFavoriteIds(
        group: String
    ): List<String> {
        val ids = mutableListOf<String>()
        db.readableDatabase.rawQuery(
            """
            SELECT stream_id
            FROM streams
            WHERE favorite = 1 AND favorite_group = ?
            ORDER BY CASE WHEN favorite_order <= 0 THEN 2147483647 ELSE favorite_order END,
                     last_watched DESC, name COLLATE NOCASE
            """.trimIndent(),
            arrayOf(group)
        ).use { cursor ->
            while (cursor.moveToNext()) ids.add(cursor.getString(0))
        }
        return ids
    }


    private fun favoriteOrder(
        streamId: String
    ): Int =
        scalarInt(
            "SELECT favorite_order FROM streams WHERE stream_id = ?",
            arrayOf(streamId)
        )


    private fun updateFavoriteOrder(
        database: SQLiteDatabase,
        streamId: String,
        order: Int
    ) {
        val values = ContentValues().apply { put("favorite_order", order) }
        database.update("streams", values, "stream_id = ?", arrayOf(streamId))
    }


    private fun scalarInt(
        sql: String,
        args: Array<String>? = null
    ): Int {
        db.readableDatabase.rawQuery(sql, args).use { cursor ->
            return if (cursor.moveToFirst()) cursor.getInt(0) else 0
        }
    }


    private fun Cursor.getStringOrNull(
        index: Int
    ): String? =
        if (isNull(index)) null else getString(index)?.takeIf { it.isNotBlank() }


    private fun Cursor.getStringOrEmpty(
        index: Int
    ): String =
        if (isNull(index)) "" else getString(index) ?: ""
}
