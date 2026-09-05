package com.safeiot.privyhub

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper


class TvDatabase(
    context: Context
) : SQLiteOpenHelper(
    context,
    DATABASE_NAME,
    null,
    DATABASE_VERSION
) {

    companion object {
        private const val DATABASE_NAME = "privyhub_tv.db"
        private const val DATABASE_VERSION = 2
        const val BUILTIN_PROVIDER_ID = "iptv_org"
    }


    override fun onConfigure(
        db: SQLiteDatabase
    ) {
        super.onConfigure(db)
        db.setForeignKeyConstraintsEnabled(true)
    }


    override fun onCreate(
        db: SQLiteDatabase
    ) {
        createStreamsTable(db)
        createLanguageTable(db)
        createMetaTable(db)
        createProvidersTable(db)
        createIndexes(db)
        ensureBuiltinProvider(db)
    }


    override fun onUpgrade(
        db: SQLiteDatabase,
        oldVersion: Int,
        newVersion: Int
    ) {
        if (oldVersion < 2) {
            addColumn(db, "streams", "provider_id TEXT NOT NULL DEFAULT '$BUILTIN_PROVIDER_ID'")
            addColumn(db, "streams", "custom_name TEXT")
            addColumn(db, "streams", "custom_category TEXT")
            addColumn(db, "streams", "custom_url TEXT")
            addColumn(db, "streams", "custom_referrer TEXT")
            addColumn(db, "streams", "custom_user_agent TEXT")
            addColumn(db, "streams", "favorite_group TEXT NOT NULL DEFAULT ''")
            addColumn(db, "streams", "favorite_order INTEGER NOT NULL DEFAULT 0")
            addColumn(db, "streams", "protect_auto_hide INTEGER NOT NULL DEFAULT 0")

            createProvidersTable(db)
            createIndexes(db)
            ensureBuiltinProvider(db)
        }
    }


    private fun createStreamsTable(
        db: SQLiteDatabase
    ) {
        db.execSQL(
            """
            CREATE TABLE streams (
                stream_id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                referrer TEXT,
                user_agent TEXT,
                category TEXT,
                country TEXT,
                quality TEXT,
                label TEXT,
                favorite INTEGER NOT NULL DEFAULT 0,
                manual_hidden INTEGER NOT NULL DEFAULT 0,
                auto_hidden INTEGER NOT NULL DEFAULT 0,
                success_count INTEGER NOT NULL DEFAULT 0,
                failure_count INTEGER NOT NULL DEFAULT 0,
                consecutive_failures INTEGER NOT NULL DEFAULT 0,
                last_success INTEGER NOT NULL DEFAULT 0,
                last_failure INTEGER NOT NULL DEFAULT 0,
                last_watched INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL DEFAULT 0,
                provider_id TEXT NOT NULL DEFAULT '$BUILTIN_PROVIDER_ID',
                custom_name TEXT,
                custom_category TEXT,
                custom_url TEXT,
                custom_referrer TEXT,
                custom_user_agent TEXT,
                favorite_group TEXT NOT NULL DEFAULT '',
                favorite_order INTEGER NOT NULL DEFAULT 0,
                protect_auto_hide INTEGER NOT NULL DEFAULT 0
            )
            """.trimIndent()
        )
    }


    private fun createLanguageTable(
        db: SQLiteDatabase
    ) {
        db.execSQL(
            """
            CREATE TABLE stream_languages (
                stream_id TEXT NOT NULL,
                language TEXT NOT NULL,
                PRIMARY KEY (stream_id, language),
                FOREIGN KEY (stream_id)
                    REFERENCES streams(stream_id)
                    ON DELETE CASCADE
            )
            """.trimIndent()
        )
    }


    private fun createMetaTable(
        db: SQLiteDatabase
    ) {
        db.execSQL(
            """
            CREATE TABLE meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """.trimIndent()
        )
    }


    private fun createProvidersTable(
        db: SQLiteDatabase
    ) {
        db.execSQL(
            """
            CREATE TABLE IF NOT EXISTS providers (
                provider_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                url TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                language_code TEXT NOT NULL DEFAULT 'eng',
                builtin INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL DEFAULT 0
            )
            """.trimIndent()
        )
    }


    private fun createIndexes(
        db: SQLiteDatabase
    ) {
        db.execSQL(
            "CREATE INDEX IF NOT EXISTS idx_streams_name ON streams(name COLLATE NOCASE)"
        )
        db.execSQL(
            "CREATE INDEX IF NOT EXISTS idx_streams_category ON streams(category)"
        )
        db.execSQL(
            "CREATE INDEX IF NOT EXISTS idx_streams_country ON streams(country)"
        )
        db.execSQL(
            "CREATE INDEX IF NOT EXISTS idx_streams_last_watched ON streams(last_watched DESC)"
        )
        db.execSQL(
            "CREATE INDEX IF NOT EXISTS idx_streams_favorites ON streams(favorite, favorite_group, favorite_order)"
        )
        db.execSQL(
            "CREATE INDEX IF NOT EXISTS idx_streams_provider ON streams(provider_id)"
        )
        db.execSQL(
            "CREATE INDEX IF NOT EXISTS idx_stream_languages_language ON stream_languages(language)"
        )
    }


    private fun addColumn(
        db: SQLiteDatabase,
        table: String,
        declaration: String
    ) {
        try {
            db.execSQL(
                "ALTER TABLE $table ADD COLUMN $declaration"
            )
        } catch (_: Exception) {
            // A partially-applied development build may already contain it.
        }
    }


    private fun ensureBuiltinProvider(
        db: SQLiteDatabase
    ) {
        val values =
            ContentValues().apply {
                put("provider_id", BUILTIN_PROVIDER_ID)
                put("name", "IPTV-org")
                put("type", "builtin")
                put("url", "")
                put("enabled", 1)
                put("language_code", "*")
                put("builtin", 1)
                put("updated_at", System.currentTimeMillis())
            }

        db.insertWithOnConflict(
            "providers",
            null,
            values,
            SQLiteDatabase.CONFLICT_IGNORE
        )
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


    fun deleteMeta(
        key: String
    ) {
        writableDatabase.delete(
            "meta",
            "key = ?",
            arrayOf(key)
        )
    }
}
