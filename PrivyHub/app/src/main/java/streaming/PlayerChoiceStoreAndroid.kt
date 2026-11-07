package com.safeiot.privyhub.streaming

import android.content.Context

/**
 * B46: the title's last chooser pick on the onn, a private preference keyed by [PlayerPrompt.gameKey] (sha256 of the
 * host's game id, 12 hex; no title or id stored). Built only with the prompt on; a failed read is no choice.
 */
class PrefsPlayerChoiceStore(context: Context) : PlayerChoiceStore {
    private val prefs = context.applicationContext.getSharedPreferences(FILE, Context.MODE_PRIVATE)

    override fun get(key: String): Int? =
        try {
            prefs.getInt(key, 0).takeIf { it in PlayerPrompt.OPTIONS }
        } catch (_: Exception) {
            null
        }

    override fun put(key: String, players: Int) {
        try {
            prefs.edit().putInt(key, players).apply()
        } catch (_: Exception) {
        }
    }

    companion object {
        const val FILE = "privyhub_players_chosen"
    }
}
