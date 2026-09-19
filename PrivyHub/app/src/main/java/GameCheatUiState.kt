package com.safeiot.privyhub

import android.content.Context

object GameCheatUiState {
    private const val PREFS_NAME = "privyhub_settings"
    private const val PREF_PROFILE_LABEL = "game_save_profile_label"

    fun setProfileLabel(context: Context, label: String) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putString(PREF_PROFILE_LABEL, label.ifBlank { "Normal" })
            .apply()
    }

    fun currentProfileLabel(context: Context): String =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getString(PREF_PROFILE_LABEL, "Normal")
            ?.takeIf { it.isNotBlank() }
            ?: "Normal"

    fun buildProfileLabel(descriptions: List<String>): String {
        val cleaned = descriptions.map { it.trim() }.filter { it.isNotBlank() }
        if (cleaned.isEmpty()) return "Normal"
        return when (cleaned.size) {
            1 -> "Cheat: ${cleaned[0]}"
            2 -> "Cheat: ${cleaned[0]} + ${cleaned[1]}"
            else -> "Cheat: ${cleaned[0]} + ${cleaned.size - 1} more"
        }
    }

    fun dialogTitle(context: Context, action: String): String =
        "$action — ${currentProfileLabel(context)}"
}
