package com.safeiot.privyhub.streaming

/**
 * CL-B7P: the Opus decoder's drain mode, a runtime client flag. System
 * property `debug.privyhub.opus_decode`: `lean` = [LEAN]; absent, empty or
 * anything else = [TODAY], CL-B5's drain unchanged. Not persistent: a reboot
 * clears it.
 *
 * [LEAN] returns from the drain as soon as the outputs have caught up with
 * the inputs, instead of one more `dequeueOutputBuffer(0)` that almost always
 * comes back empty: 4 synchronous MediaCodec calls per frame instead of 5.
 */
enum class OpusDecodeMode(val reportName: String) {
    TODAY(""),
    LEAN("lean");

    /** After an output buffer: poll the codec again? [pending] = inputs - outputs. */
    fun pollAfterOutput(pending: Long): Boolean =
        when (this) {
            TODAY -> true
            LEAN -> pending > 0
        }

    companion object {
        const val PROPERTY = "debug.privyhub.opus_decode"

        fun parse(value: String?): OpusDecodeMode =
            if (value?.trim()?.lowercase() == "lean") LEAN else TODAY

        /** The property, read through reflection; any failure is [TODAY]. */
        fun fromSystem(): OpusDecodeMode =
            try {
                val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
                parse(get.invoke(null, PROPERTY) as? String)
            } catch (_: Throwable) {
                TODAY
            }
    }
}
