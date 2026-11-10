package com.safeiot.privyhub.streaming

/**
 * B80: a PS2 title's PCSX2 patches (widescreen, no interlacing, 60 fps) offered in the launch's Extras when the hub's
 * details say its bundle has one for the title (`ps2_patches.available`). The ticks are remembered on the hub
 * (`/plugins/games/ps2-patches`) and read at the title's next launch; the launch itself is unchanged.
 * `debug.privyhub.ps2_patches=0` = today's Extras (no entry).
 */
object Ps2Patches {
    const val PROPERTY = "debug.privyhub.ps2_patches"
    const val ENTRY_LABEL = "Patches…"
    const val TITLE = "Patches"
    const val SAVE = "Save"
    const val SAVED = "Saved — used the next time this game starts"

    /** The host's keys in the order shown, and their words on the TV. */
    val KEYS = listOf("ws", "ni", "60")
    private val LABELS = mapOf("ws" to "Widescreen", "ni" to "No interlacing", "60" to "60 fps")
    private val QUERY_NAMES = mapOf("ws" to "ws", "ni" to "ni", "60" to "fps60")

    fun label(key: String): String = LABELS[key] ?: key

    /** Only the keys the app knows, in the app's order (an unknown key from a newer hub is not shown). */
    fun known(keys: List<String>): List<String> = KEYS.filter { it in keys }

    fun showEntry(on: Boolean, available: List<String>): Boolean = on && known(available).isNotEmpty()

    /** The Extras list: today's items, then "Start on disc…" for a set (B74), then "Patches…" when offered. */
    fun extrasItems(startOnDisc: Boolean, patches: Boolean): List<String> =
        listOf("Cheats", "Mods") + (if (startOnDisc) listOf(DiscSafe.START_LABEL) else emptyList()) +
            (if (patches) listOf(ENTRY_LABEL) else emptyList())

    /** The save's query: every offered key as 0 / 1 (a key not offered is not sent). */
    fun query(gameId: String, available: List<String>, checked: Set<String>): String =
        "id=$gameId" + known(available).joinToString("") { "&${QUERY_NAMES.getValue(it)}=${if (it in checked) 1 else 0}" }

    fun parse(value: String?): Boolean = value?.trim().let { it != "0" && it != "off" }

    fun fromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            parse(null)
        }
}
