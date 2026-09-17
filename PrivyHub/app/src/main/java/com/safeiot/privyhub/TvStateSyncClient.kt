package com.safeiot.privyhub

import android.content.Context

import org.json.JSONObject

import java.net.HttpURLConnection
import java.net.URL
import java.nio.charset.StandardCharsets
import java.util.UUID


data class TvStateSyncResult(
    val ok: Boolean,
    val action: String,
    val serverRevision: Long,
    val localStateChanged: Boolean,
    val conflict: Boolean = false
)


class TvStateSyncClient(
    context: Context,
    private val repository: TvRepository
) {

    companion object {
        private const val PREFS_NAME =
            "privyhub_settings"

        private const val PREF_TV_LANGUAGE =
            "tv_language"

        private const val PREF_TV_LANGUAGE_NAME =
            "tv_language_name"

        private const val PREF_TV_COUNTRY =
            "tv_country"

        private const val PREF_TV_COUNTRY_NAME =
            "tv_country_name"

        private const val PREF_TV_STATE_CLIENT_ID =
            "tv_state_client_id"

        private const val PREF_TV_STATE_SERVER_REVISION =
            "tv_state_server_revision"

        private const val CONTROL_PORT =
            8765

        private const val CONNECT_TIMEOUT_MS =
            3_000

        private const val READ_TIMEOUT_MS =
            20_000

        private const val MAX_RESPONSE_CHARS =
            2_000_000

        private const val ENVELOPE_SCHEMA =
            "privyhub_tv_state_envelope_v1"

        private const val UPDATE_SCHEMA =
            "privyhub_tv_state_update_v1"

        private const val USER_STATE_SCHEMA =
            "privyhub_tv_user_state_v1"
    }


    private val appContext =
        context.applicationContext

    private val prefs =
        appContext.getSharedPreferences(
            PREFS_NAME,
            Context.MODE_PRIVATE
        )


    private fun normalizedBaseUrl(
        host: String
    ): String? {
        val clean =
            host
                .trim()
                .trimEnd('/')

        if (clean.isBlank()) {
            return null
        }

        if (
            clean.startsWith("http://") ||
            clean.startsWith("https://")
        ) {
            return try {
                val parsed =
                    URL(
                        clean
                    )

                if (parsed.port >= 0) {
                    clean
                } else {
                    "${parsed.protocol}://${parsed.host}:$CONTROL_PORT"
                }
            } catch (_: Exception) {
                null
            }
        }

        return try {
            val parsed =
                URL(
                    "http://$clean"
                )

            if (parsed.port >= 0) {
                "http://$clean"
            } else {
                "http://$clean:$CONTROL_PORT"
            }
        } catch (_: Exception) {
            null
        }
    }


    private fun clientId(): String {
        val existing =
            prefs.getString(
                PREF_TV_STATE_CLIENT_ID,
                ""
            )?.trim().orEmpty()

        if (existing.isNotBlank()) {
            return existing
        }

        val created =
            "onn-" +
                UUID.randomUUID()
                    .toString()
                    .replace(
                        "-",
                        ""
                    )
                    .take(24)

        prefs.edit()
            .putString(
                PREF_TV_STATE_CLIENT_ID,
                created
            )
            .apply()

        return created
    }


    private fun readResponse(
        connection: HttpURLConnection
    ): JSONObject {
        val status =
            connection.responseCode

        val stream =
            if (
                status in 200..299
            ) {
                connection.inputStream
            } else {
                connection.errorStream
                    ?: connection.inputStream
            }

        val text =
            stream
                .bufferedReader()
                .use {
                    it.readText()
                }

        if (
            text.length >
            MAX_RESPONSE_CHARS
        ) {
            throw IllegalStateException(
                "TV state response is too large"
            )
        }

        val payload =
            JSONObject(
                text
            )

        if (
            status !in 200..299
        ) {
            throw IllegalStateException(
                payload.optString(
                    "error",
                    "TV state request failed"
                )
            )
        }

        return payload
    }


    private fun getEnvelope(
        baseUrl: String
    ): JSONObject {
        val connection =
            URL(
                "$baseUrl/plugins/tv_state/state"
            ).openConnection()
                as HttpURLConnection

        return try {
            connection.requestMethod =
                "GET"

            connection.connectTimeout =
                CONNECT_TIMEOUT_MS

            connection.readTimeout =
                READ_TIMEOUT_MS

            connection.useCaches =
                false

            connection.setRequestProperty(
                "Accept",
                "application/json"
            )

            readResponse(
                connection
            )
        } finally {
            connection.disconnect()
        }
    }


    private fun putState(
        baseUrl: String,
        baseRevision: Long,
        state: JSONObject
    ): JSONObject {
        val payload =
            JSONObject()
                .put(
                    "schema",
                    UPDATE_SCHEMA
                )
                .put(
                    "base_revision",
                    baseRevision
                )
                .put(
                    "client_id",
                    clientId()
                )
                .put(
                    "state",
                    state
                )

        val bytes =
            payload
                .toString()
                .toByteArray(
                    StandardCharsets.UTF_8
                )

        val connection =
            URL(
                "$baseUrl/plugins/tv_state/state"
            ).openConnection()
                as HttpURLConnection

        return try {
            connection.requestMethod =
                "POST"

            connection.doOutput =
                true

            connection.connectTimeout =
                CONNECT_TIMEOUT_MS

            connection.readTimeout =
                READ_TIMEOUT_MS

            connection.useCaches =
                false

            connection.setRequestProperty(
                "Accept",
                "application/json"
            )

            connection.setRequestProperty(
                "Content-Type",
                "application/json; charset=utf-8"
            )

            connection.setFixedLengthStreamingMode(
                bytes.size
            )

            connection.outputStream.use {
                it.write(
                    bytes
                )
            }

            readResponse(
                connection
            )
        } finally {
            connection.disconnect()
        }
    }


    private fun localState(): JSONObject {
        return JSONObject(
            repository.exportDurableStateJson(
                languageCode =
                    prefs.getString(
                        PREF_TV_LANGUAGE,
                        TvRepository.ENGLISH
                    ) ?: TvRepository.ENGLISH,
                languageName =
                    prefs.getString(
                        PREF_TV_LANGUAGE_NAME,
                        "English"
                    ) ?: "English",
                countryCode =
                    prefs.getString(
                        PREF_TV_COUNTRY,
                        ""
                    ) ?: "",
                countryName =
                    prefs.getString(
                        PREF_TV_COUNTRY_NAME,
                        "All Countries"
                    ) ?: "All Countries"
            )
        )
    }


    private fun rememberRevision(
        revision: Long
    ) {
        prefs.edit()
            .putLong(
                PREF_TV_STATE_SERVER_REVISION,
                revision
            )
            .apply()
    }


    private fun applyEnvelope(
        envelope: JSONObject
    ): TvStateSyncResult {
        if (
            envelope.optString(
                "schema"
            ) != ENVELOPE_SCHEMA ||
            !envelope.optBoolean(
                "ok",
                false
            ) ||
            !envelope.optBoolean(
                "initialized",
                false
            )
        ) {
            throw IllegalStateException(
                "Linux TV state envelope is invalid"
            )
        }

        val revision =
            envelope.optLong(
                "server_revision",
                -1L
            )

        if (revision < 1L) {
            throw IllegalStateException(
                "Linux TV state revision is invalid"
            )
        }

        val state =
            envelope.optJSONObject(
                "state"
            )
                ?: throw IllegalStateException(
                    "Linux TV state is missing"
                )

        if (
            state.optString(
                "schema"
            ) != USER_STATE_SCHEMA
        ) {
            throw IllegalStateException(
                "Linux TV user-state schema is unsupported"
            )
        }

        val preferences =
            state.optJSONObject(
                "preferences"
            ) ?: JSONObject()

        val languageCode =
            preferences.optString(
                "language_code",
                TvRepository.ENGLISH
            )
                .trim()
                .ifBlank {
                    TvRepository.ENGLISH
                }

        repository.importDurableStateJson(
            jsonText =
                state.toString(),
            catalogLanguageCode =
                languageCode
        )

        prefs.edit()
            .putString(
                PREF_TV_LANGUAGE,
                languageCode
            )
            .putString(
                PREF_TV_LANGUAGE_NAME,
                preferences.optString(
                    "language_name",
                    "English"
                )
            )
            .putString(
                PREF_TV_COUNTRY,
                preferences.optString(
                    "country_code",
                    ""
                )
            )
            .putString(
                PREF_TV_COUNTRY_NAME,
                preferences.optString(
                    "country_name",
                    "All Countries"
                )
            )
            .putLong(
                PREF_TV_STATE_SERVER_REVISION,
                revision
            )
            .apply()

        return TvStateSyncResult(
            ok = true,
            action = "pulled",
            serverRevision = revision,
            localStateChanged = true
        )
    }


    fun synchronize(
        host: String
    ): TvStateSyncResult {
        val baseUrl =
            normalizedBaseUrl(
                host
            )
                ?: return TvStateSyncResult(
                    ok = false,
                    action = "local_only",
                    serverRevision =
                        prefs.getLong(
                            PREF_TV_STATE_SERVER_REVISION,
                            0L
                        ),
                    localStateChanged = false
                )

        val envelope =
            getEnvelope(
                baseUrl
            )

        if (
            envelope.optString(
                "schema"
            ) != ENVELOPE_SCHEMA ||
            !envelope.optBoolean(
                "ok",
                false
            )
        ) {
            throw IllegalStateException(
                "Linux TV state endpoint returned an invalid envelope"
            )
        }

        if (
            !envelope.optBoolean(
                "initialized",
                false
            )
        ) {
            val seeded =
                putState(
                    baseUrl = baseUrl,
                    baseRevision = 0L,
                    state = localState()
                )

            if (
                seeded.optBoolean(
                    "conflict",
                    false
                )
            ) {
                val current =
                    seeded.optJSONObject(
                        "current"
                    )
                        ?: getEnvelope(
                            baseUrl
                        )

                return applyEnvelope(
                    current
                )
            }

            if (
                !seeded.optBoolean(
                    "ok",
                    false
                )
            ) {
                throw IllegalStateException(
                    "Linux TV state seed was rejected"
                )
            }

            val revision =
                seeded.optLong(
                    "server_revision",
                    -1L
                )

            if (revision < 1L) {
                throw IllegalStateException(
                    "Linux TV state seed returned an invalid revision"
                )
            }

            rememberRevision(
                revision
            )

            return TvStateSyncResult(
                ok = true,
                action = "seeded",
                serverRevision = revision,
                localStateChanged = false
            )
        }

        return applyEnvelope(
            envelope
        )
    }


    fun push(
        host: String
    ): TvStateSyncResult {
        val baseUrl =
            normalizedBaseUrl(
                host
            )
                ?: return TvStateSyncResult(
                    ok = false,
                    action = "local_only",
                    serverRevision =
                        prefs.getLong(
                            PREF_TV_STATE_SERVER_REVISION,
                            0L
                        ),
                    localStateChanged = false
                )

        val baseRevision =
            prefs.getLong(
                PREF_TV_STATE_SERVER_REVISION,
                0L
            )

        if (baseRevision <= 0L) {
            return synchronize(
                host
            )
        }

        val result =
            putState(
                baseUrl = baseUrl,
                baseRevision = baseRevision,
                state = localState()
            )

        if (
            result.optBoolean(
                "conflict",
                false
            )
        ) {
            return TvStateSyncResult(
                ok = false,
                action = "conflict",
                serverRevision =
                    result.optLong(
                        "server_revision",
                        baseRevision
                    ),
                localStateChanged = false,
                conflict = true
            )
        }

        if (
            !result.optBoolean(
                "ok",
                false
            )
        ) {
            throw IllegalStateException(
                "Linux TV state update was rejected"
            )
        }

        val revision =
            result.optLong(
                "server_revision",
                -1L
            )

        if (revision < 1L) {
            throw IllegalStateException(
                "Linux TV state update returned an invalid revision"
            )
        }

        rememberRevision(
            revision
        )

        return TvStateSyncResult(
            ok = true,
            action =
                if (
                    result.optBoolean(
                        "changed",
                        false
                    )
                ) {
                    "pushed"
                } else {
                    "unchanged"
                },
            serverRevision = revision,
            localStateChanged = false
        )
    }
}
