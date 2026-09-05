package com.safeiot.privyhub

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper

import org.json.JSONArray
import org.xmlpull.v1.XmlPullParser
import org.xmlpull.v1.XmlPullParserFactory

import java.io.InputStream
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone


data class TvProgramme(
    val channelId: String,
    val startMs: Long,
    val stopMs: Long,
    val title: String,
    val description: String?
)


data class TvGuideSummary(
    val channelId: String,
    val current: TvProgramme?,
    val upcoming: List<TvProgramme>,
    val cached: Boolean
)


data class TvEpgStats(
    val mappings: Int,
    val programmes: Int,
    val mappingsRefreshedAtMs: Long
)


private data class TvGuideMapping(
    val channelId: String,
    val siteId: String,
    val sourceUrl: String,
    val language: String
)


private class TvEpgDatabase(
    context: Context
) : SQLiteOpenHelper(
    context,
    DATABASE_NAME,
    null,
    DATABASE_VERSION
) {

    companion object {
        private const val DATABASE_NAME = "privyhub_epg.db"
        private const val DATABASE_VERSION = 1
    }


    override fun onCreate(
        db: SQLiteDatabase
    ) {
        db.execSQL(
            """
            CREATE TABLE guide_mappings (
                channel_id TEXT PRIMARY KEY,
                site_id TEXT NOT NULL,
                source_url TEXT NOT NULL,
                language TEXT NOT NULL,
                updated_at INTEGER NOT NULL DEFAULT 0
            )
            """.trimIndent()
        )

        db.execSQL(
            """
            CREATE TABLE programmes (
                channel_id TEXT NOT NULL,
                start_ms INTEGER NOT NULL,
                stop_ms INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                updated_at INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (channel_id, start_ms, title)
            )
            """.trimIndent()
        )

        db.execSQL(
            """
            CREATE TABLE meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """.trimIndent()
        )

        db.execSQL(
            "CREATE INDEX idx_programmes_channel_time " +
                "ON programmes(channel_id, start_ms, stop_ms)"
        )
    }


    override fun onUpgrade(
        db: SQLiteDatabase,
        oldVersion: Int,
        newVersion: Int
    ) {
        if (oldVersion == newVersion) {
            return
        }

        db.execSQL("DROP TABLE IF EXISTS guide_mappings")
        db.execSQL("DROP TABLE IF EXISTS programmes")
        db.execSQL("DROP TABLE IF EXISTS meta")
        onCreate(db)
    }


    fun setMeta(
        key: String,
        value: String
    ) {
        val values =
            ContentValues().apply {
                put("key", key)
                put("value", value)
            }

        writableDatabase.insertWithOnConflict(
            "meta",
            null,
            values,
            SQLiteDatabase.CONFLICT_REPLACE
        )
    }


    fun getMeta(
        key: String
    ): String? {
        readableDatabase.query(
            "meta",
            arrayOf("value"),
            "key = ?",
            arrayOf(key),
            null,
            null,
            null,
            "1"
        ).use { cursor ->
            if (!cursor.moveToFirst()) {
                return null
            }

            return cursor.getString(0)
        }
    }
}


class TvEpgRepository(
    context: Context
) {

    companion object {
        private const val GUIDES_URL =
            "https://iptv-org.github.io/api/guides.json"

        private const val FETCH_TIMEOUT_MS = 20_000

        private const val MAPPING_REFRESH_INTERVAL_MS =
            24L * 60L * 60L * 1_000L

        private const val PROGRAMME_REFRESH_INTERVAL_MS =
            6L * 60L * 60L * 1_000L

        private const val GUIDE_PAST_WINDOW_MS =
            2L * 60L * 60L * 1_000L

        private const val GUIDE_FUTURE_WINDOW_MS =
            48L * 60L * 60L * 1_000L

        private const val MAX_PROGRAMMES_PER_CHANNEL = 120
    }


    private val db =
        TvEpgDatabase(
            context.applicationContext
        )


    fun getCachedGuide(
        channelId: String,
        nowMs: Long = System.currentTimeMillis()
    ): TvGuideSummary {
        val programmes =
            readProgrammes(
                channelId = channelId,
                nowMs = nowMs
            )

        return buildSummary(
            channelId = channelId,
            programmes = programmes,
            nowMs = nowMs,
            cached = true
        )
    }


    fun getGuide(
        channelId: String,
        force: Boolean = false
    ): TvGuideSummary {
        val now =
            System.currentTimeMillis()

        val cached =
            getCachedGuide(
                channelId = channelId,
                nowMs = now
            )

        val refreshedAt =
            db.getMeta(
                channelRefreshKey(
                    channelId
                )
            )?.toLongOrNull() ?: 0L

        val age =
            now - refreshedAt

        if (
            !force &&
            refreshedAt > 0L &&
            age in 0 until PROGRAMME_REFRESH_INTERVAL_MS &&
            (
                cached.current != null ||
                cached.upcoming.isNotEmpty()
            )
        ) {
            return cached
        }

        return try {
            ensureMappings(
                force = force
            )

            val mapping =
                getMapping(
                    channelId
                )
                    ?: return cached

            val programmes =
                fetchProgrammes(
                    mapping = mapping,
                    nowMs = now
                )

            replaceProgrammes(
                channelId = channelId,
                programmes = programmes,
                nowMs = now
            )

            db.setMeta(
                channelRefreshKey(
                    channelId
                ),
                now.toString()
            )

            buildSummary(
                channelId = channelId,
                programmes = programmes,
                nowMs = now,
                cached = false
            )

        } catch (error: Exception) {
            cached
        }
    }


    private fun ensureMappings(
        force: Boolean
    ) {
        val now =
            System.currentTimeMillis()

        val refreshedAt =
            db.getMeta(
                "guide_mappings_refreshed_at"
            )?.toLongOrNull() ?: 0L

        val count =
            mappingCount()

        val age =
            now - refreshedAt

        if (
            !force &&
            count > 0 &&
            refreshedAt > 0L &&
            age in 0 until MAPPING_REFRESH_INTERVAL_MS
        ) {
            return
        }

        val mappings =
            parseMappings(
                fetchText(
                    GUIDES_URL
                )
            )

        if (mappings.isEmpty()) {
            if (count > 0) {
                return
            }

            throw IllegalStateException(
                "No IPTV guide mappings were returned"
            )
        }

        replaceMappings(
            mappings = mappings,
            nowMs = now
        )

        db.setMeta(
            "guide_mappings_refreshed_at",
            now.toString()
        )
    }


    private fun parseMappings(
        text: String
    ): List<TvGuideMapping> {
        val json =
            JSONArray(
                text
            )

        val best =
            linkedMapOf<String, TvGuideMapping>()

        for (index in 0 until json.length()) {
            val item =
                json.getJSONObject(
                    index
                )

            val channelId =
                item.optString(
                    "channel"
                ).trim()

            if (channelId.isBlank()) {
                continue
            }

            val language =
                item.optString(
                    "lang"
                ).trim()

            val siteId =
                item.optString(
                    "site_id"
                ).trim()

            val sources =
                item.optJSONArray(
                    "sources"
                ) ?: continue

            var sourceUrl: String? =
                null

            for (
                sourceIndex in 0 until sources.length()
            ) {
                val source =
                    sources.getJSONObject(
                        sourceIndex
                    )

                val format =
                    source.optString(
                        "format"
                    ).trim()

                val url =
                    source.optString(
                        "url"
                    ).trim()

                if (
                    format.equals(
                        "XML",
                        ignoreCase = true
                    ) &&
                    (
                        url.startsWith("http://") ||
                        url.startsWith("https://")
                    )
                ) {
                    sourceUrl =
                        url
                    break
                }
            }

            val selectedUrl =
                sourceUrl
                    ?: continue

            val candidate =
                TvGuideMapping(
                    channelId = channelId,
                    siteId = siteId,
                    sourceUrl = selectedUrl,
                    language = language
                )

            val existing =
                best[
                    channelId
                ]

            if (
                existing == null ||
                (
                    !existing.language.equals(
                        "en",
                        ignoreCase = true
                    ) &&
                    language.equals(
                        "en",
                        ignoreCase = true
                    )
                )
            ) {
                best[
                    channelId
                ] = candidate
            }
        }

        return best.values.toList()
    }


    private fun replaceMappings(
        mappings: List<TvGuideMapping>,
        nowMs: Long
    ) {
        val database =
            db.writableDatabase

        database.beginTransaction()

        try {
            database.delete(
                "guide_mappings",
                null,
                null
            )

            for (mapping in mappings) {
                val values =
                    ContentValues().apply {
                        put(
                            "channel_id",
                            mapping.channelId
                        )
                        put(
                            "site_id",
                            mapping.siteId
                        )
                        put(
                            "source_url",
                            mapping.sourceUrl
                        )
                        put(
                            "language",
                            mapping.language
                        )
                        put(
                            "updated_at",
                            nowMs
                        )
                    }

                database.insertWithOnConflict(
                    "guide_mappings",
                    null,
                    values,
                    SQLiteDatabase.CONFLICT_REPLACE
                )
            }

            database.setTransactionSuccessful()

        } finally {
            database.endTransaction()
        }
    }


    private fun mappingCount(): Int {
        db.readableDatabase.rawQuery(
            "SELECT COUNT(*) FROM guide_mappings",
            null
        ).use { cursor ->
            return if (cursor.moveToFirst()) {
                cursor.getInt(0)
            } else {
                0
            }
        }
    }


    private fun getMapping(
        channelId: String
    ): TvGuideMapping? {
        db.readableDatabase.query(
            "guide_mappings",
            arrayOf(
                "channel_id",
                "site_id",
                "source_url",
                "language"
            ),
            "channel_id = ?",
            arrayOf(channelId),
            null,
            null,
            null,
            "1"
        ).use { cursor ->
            if (!cursor.moveToFirst()) {
                return null
            }

            return TvGuideMapping(
                channelId = cursor.getString(0),
                siteId = cursor.getString(1) ?: "",
                sourceUrl = cursor.getString(2),
                language = cursor.getString(3) ?: ""
            )
        }
    }


    private fun fetchProgrammes(
        mapping: TvGuideMapping,
        nowMs: Long
    ): List<TvProgramme> {
        val connection =
            URL(
                mapping.sourceUrl
            ).openConnection()
                as HttpURLConnection

        return try {
            connection.requestMethod =
                "GET"

            connection.connectTimeout =
                FETCH_TIMEOUT_MS

            connection.readTimeout =
                FETCH_TIMEOUT_MS

            connection.instanceFollowRedirects =
                true

            connection.useCaches =
                false

            connection.setRequestProperty(
                "User-Agent",
                "PrivyHub/1.0"
            )

            val response =
                connection.responseCode

            if (
                response < 200 ||
                response >= 300
            ) {
                throw IllegalStateException(
                    "EPG HTTP $response"
                )
            }

            parseXmlTv(
                input = connection.inputStream,
                mapping = mapping,
                nowMs = nowMs
            )

        } finally {
            connection.disconnect()
        }
    }


    private fun parseXmlTv(
        input: InputStream,
        mapping: TvGuideMapping,
        nowMs: Long
    ): List<TvProgramme> {
        val earliest =
            nowMs -
                GUIDE_PAST_WINDOW_MS

        val latest =
            nowMs +
                GUIDE_FUTURE_WINDOW_MS

        val result =
            mutableListOf<TvProgramme>()

        val parser =
            XmlPullParserFactory
                .newInstance()
                .newPullParser()

        parser.setInput(
            InputStreamReader(
                input,
                Charsets.UTF_8
            )
        )

        var event =
            parser.eventType

        while (
            event != XmlPullParser.END_DOCUMENT &&
            result.size < MAX_PROGRAMMES_PER_CHANNEL
        ) {
            if (
                event == XmlPullParser.START_TAG &&
                parser.name == "programme"
            ) {
                val xmlChannel =
                    parser.getAttributeValue(
                        null,
                        "channel"
                    ).orEmpty()

                val startMs =
                    parseXmlTvDate(
                        parser.getAttributeValue(
                            null,
                            "start"
                        ).orEmpty()
                    )

                val stopMs =
                    parseXmlTvDate(
                        parser.getAttributeValue(
                            null,
                            "stop"
                        ).orEmpty()
                    )

                val channelMatches =
                    xmlChannel == mapping.channelId ||
                        (
                            mapping.siteId.isNotBlank() &&
                            xmlChannel == mapping.siteId
                        )

                if (
                    channelMatches &&
                    startMs > 0L &&
                    stopMs > earliest &&
                    startMs < latest
                ) {
                    var title =
                        ""

                    var description: String? =
                        null

                    val programmeDepth =
                        parser.depth

                    var innerEvent =
                        parser.next()

                    while (
                        !(
                            innerEvent == XmlPullParser.END_TAG &&
                            parser.depth == programmeDepth &&
                            parser.name == "programme"
                        )
                    ) {
                        if (
                            innerEvent == XmlPullParser.START_TAG
                        ) {
                            when (parser.name) {
                                "title" ->
                                    title =
                                        parser.nextText()
                                            .trim()

                                "desc" ->
                                    description =
                                        parser.nextText()
                                            .trim()
                                            .takeIf {
                                                it.isNotBlank()
                                            }
                            }
                        }

                        innerEvent =
                            parser.next()
                    }

                    if (title.isNotBlank()) {
                        result.add(
                            TvProgramme(
                                channelId = mapping.channelId,
                                startMs = startMs,
                                stopMs = stopMs,
                                title = title,
                                description = description
                            )
                        )
                    }

                    event =
                        innerEvent
                }
            }

            event =
                parser.next()
        }

        return result
            .distinctBy {
                Triple(
                    it.channelId,
                    it.startMs,
                    it.title
                )
            }
            .sortedBy {
                it.startMs
            }
    }


    private fun parseXmlTvDate(
        raw: String
    ): Long {
        val value =
            raw.trim()

        if (value.isBlank()) {
            return 0L
        }

        val patterns =
            listOf(
                "yyyyMMddHHmmss Z",
                "yyyyMMddHHmm Z",
                "yyyyMMddHHmmss",
                "yyyyMMddHHmm"
            )

        for (pattern in patterns) {
            try {
                val format =
                    SimpleDateFormat(
                        pattern,
                        Locale.US
                    )

                format.isLenient =
                    false

                if (!pattern.contains("Z")) {
                    format.timeZone =
                        TimeZone.getTimeZone(
                            "UTC"
                        )
                }

                val parsed =
                    format.parse(
                        value
                    )

                if (parsed != null) {
                    return parsed.time
                }
            } catch (_: Exception) {
            }
        }

        return 0L
    }


    private fun replaceProgrammes(
        channelId: String,
        programmes: List<TvProgramme>,
        nowMs: Long
    ) {
        val database =
            db.writableDatabase

        database.beginTransaction()

        try {
            database.delete(
                "programmes",
                "channel_id = ?",
                arrayOf(channelId)
            )

            for (programme in programmes) {
                val values =
                    ContentValues().apply {
                        put(
                            "channel_id",
                            programme.channelId
                        )
                        put(
                            "start_ms",
                            programme.startMs
                        )
                        put(
                            "stop_ms",
                            programme.stopMs
                        )
                        put(
                            "title",
                            programme.title
                        )
                        put(
                            "description",
                            programme.description
                        )
                        put(
                            "updated_at",
                            nowMs
                        )
                    }

                database.insertWithOnConflict(
                    "programmes",
                    null,
                    values,
                    SQLiteDatabase.CONFLICT_REPLACE
                )
            }

            database.setTransactionSuccessful()

        } finally {
            database.endTransaction()
        }
    }


    private fun readProgrammes(
        channelId: String,
        nowMs: Long
    ): List<TvProgramme> {
        val earliest =
            nowMs -
                GUIDE_PAST_WINDOW_MS

        db.readableDatabase.query(
            "programmes",
            arrayOf(
                "channel_id",
                "start_ms",
                "stop_ms",
                "title",
                "description"
            ),
            "channel_id = ? AND stop_ms > ?",
            arrayOf(
                channelId,
                earliest.toString()
            ),
            null,
            null,
            "start_ms ASC",
            "40"
        ).use { cursor ->
            val result =
                mutableListOf<TvProgramme>()

            while (cursor.moveToNext()) {
                result.add(
                    TvProgramme(
                        channelId = cursor.getString(0),
                        startMs = cursor.getLong(1),
                        stopMs = cursor.getLong(2),
                        title = cursor.getString(3),
                        description = cursor.getString(4)
                    )
                )
            }

            return result
        }
    }


    private fun buildSummary(
        channelId: String,
        programmes: List<TvProgramme>,
        nowMs: Long,
        cached: Boolean
    ): TvGuideSummary {
        val current =
            programmes.firstOrNull {
                it.startMs <= nowMs &&
                    it.stopMs > nowMs
            }

        val upcoming =
            programmes.filter {
                it.startMs > nowMs
            }.take(12)

        return TvGuideSummary(
            channelId = channelId,
            current = current,
            upcoming = upcoming,
            cached = cached
        )
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

            connection.instanceFollowRedirects =
                true

            connection.useCaches =
                false

            connection.setRequestProperty(
                "User-Agent",
                "PrivyHub/1.0"
            )

            val response =
                connection.responseCode

            if (
                response < 200 ||
                response >= 300
            ) {
                throw IllegalStateException(
                    "HTTP $response from $urlString"
                )
            }

            connection.inputStream
                .bufferedReader()
                .use {
                    it.readText()
                }

        } finally {
            connection.disconnect()
        }
    }


    fun clearCache() {
        val database =
            db.writableDatabase

        database.beginTransaction()

        try {
            database.delete(
                "programmes",
                null,
                null
            )
            database.delete(
                "guide_mappings",
                null,
                null
            )
            database.delete(
                "meta",
                null,
                null
            )
            database.setTransactionSuccessful()
        } finally {
            database.endTransaction()
        }
    }


    fun stats(): TvEpgStats {
        val mappings =
            db.readableDatabase.rawQuery(
                "SELECT COUNT(*) FROM guide_mappings",
                null
            ).use { cursor ->
                if (cursor.moveToFirst()) {
                    cursor.getInt(0)
                } else {
                    0
                }
            }

        val programmes =
            db.readableDatabase.rawQuery(
                "SELECT COUNT(*) FROM programmes",
                null
            ).use { cursor ->
                if (cursor.moveToFirst()) {
                    cursor.getInt(0)
                } else {
                    0
                }
            }

        return TvEpgStats(
            mappings = mappings,
            programmes = programmes,
            mappingsRefreshedAtMs =
                db.getMeta(
                    "guide_mappings_refreshed_at"
                )?.toLongOrNull() ?: 0L
        )
    }


    private fun channelRefreshKey(
        channelId: String
    ): String {
        return "channel_refresh:$channelId"
    }
}
