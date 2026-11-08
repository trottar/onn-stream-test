package com.safeiot.privyhub.streaming

import android.content.Context

/**
 * B46: the title's last chooser pick on the onn, a private preference keyed by [PlayerPrompt.gameKey] (sha256 of the
 * host's game id, 12 hex; no title or id stored). Built only with the prompt on; a failed read is no choice.
 * B54: hold-to-join keeps the title's highest joined count (1-4) in its own file, [FILE_JOINED]; B46's picks are not
 * read.
 */
class PrefsPlayerChoiceStore(context: Context, file: String = FILE_JOINED) : PlayerChoiceStore {
    private val prefs = context.applicationContext.getSharedPreferences(file, Context.MODE_PRIVATE)

    override fun get(key: String): Int? =
        try {
            prefs.getInt(key, 0).takeIf { it in 1..PlayerPrompt.MAX_PLAYERS }
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
        const val FILE_JOINED = "privyhub_players_joined"
    }
}
