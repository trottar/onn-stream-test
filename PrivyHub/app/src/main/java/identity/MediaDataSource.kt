package com.safeiot.privyhub.identity

import android.content.Context
import androidx.media3.common.util.UnstableApi
import androidx.media3.datasource.DataSource
import androidx.media3.datasource.ResolvingDataSource

/**
 * G3-S3: the player's requests to the hub's range server carry the session
 * header (Media3 can set headers, so the media token is not needed). The
 * resolver adds it only when the URI's host and port are the hub's media
 * endpoint; a third-party stream (IPTV) is never given a token. Built only
 * with `identity_v2` on; off, the player keeps today's factory untouched.
 */
@UnstableApi
fun hubMediaDataSourceFactory(
    context: Context,
    upstream: DataSource.Factory,
    hubHost: String,
): DataSource.Factory {
    val app = context.applicationContext
    return ResolvingDataSource.Factory(upstream) { dataSpec ->
        val header = PrivyHubIdentity.mediaHeader(app, dataSpec.uri.toString(), hubHost)
        if (header == null) dataSpec else dataSpec.withAdditionalHeaders(mapOf(SessionProtocol.HEADER to header))
    }
}
