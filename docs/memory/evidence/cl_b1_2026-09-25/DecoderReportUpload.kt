package com.safeiot.privyhub.streaming

/**
 * CL-B1: the end-of-session decoder report travels as a POST body.
 *
 * It used to be URL-encoded into the request target (`?report=`), where the
 * companion's `http.server` caps the request line at 65,536 bytes (~41K
 * decoded characters). As a body it is bounded only by the companion's
 * `MAX_REPORT_CHARS`. The companion still accepts the old form, so either
 * APK works against it.
 */
object DecoderReportUpload {
    const val PATH = "/plugins/games/decoder-session-log"
    const val CONTENT_TYPE = "application/json; charset=utf-8"

    fun encode(report: String): ByteArray = report.toByteArray(Charsets.UTF_8)
}
