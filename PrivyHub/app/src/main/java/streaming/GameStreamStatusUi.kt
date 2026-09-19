package com.safeiot.privyhub.streaming

import java.util.Locale

data class GameStreamStatusSnapshot(
    val gameTitle: String,
    val phase: String,
    val width: Int,
    val height: Int,
    val fps: Int,
    val bitrateKbps: Int,
    val fecEnabled: Boolean,
    val fecGroupSize: Int,
    val videoState: String,
    val audioActive: Boolean,
    val controllerActive: Boolean,
    val updatedAtMs: Long
)

object GameStreamStatusUi {

    @Volatile
    private var latestSnapshot:
        GameStreamStatusSnapshot? =
        null

    fun publish(
        snapshot: GameStreamStatusSnapshot
    ) {
        latestSnapshot =
            snapshot
    }

    fun latestFor(
        gameTitle: String?
    ): GameStreamStatusSnapshot? {

        val expected =
            gameTitle
                ?.trim()
                .orEmpty()

        val snapshot =
            latestSnapshot
                ?: return null

        if (
            expected.isNotBlank() &&
            !snapshot.gameTitle.equals(
                expected,
                ignoreCase = true
            )
        ) {
            return null
        }

        return snapshot
    }

    fun compactMetadata(
        snapshot: GameStreamStatusSnapshot
    ): String {

        val bitrate =
            if (
                snapshot.bitrateKbps >
                0
            ) {
                String.format(
                    Locale.US,
                    "%.1f Mbps",
                    snapshot.bitrateKbps /
                        1000.0
                )
            } else {
                "waiting"
            }

        val fec =
            if (
                snapshot.fecEnabled
            ) {
                if (
                    snapshot.fecGroupSize >
                    0
                ) {
                    "${snapshot.fecGroupSize}+1 active"
                } else {
                    "active"
                }
            } else {
                "off"
            }

        return buildString {
            append(
                "${snapshot.width}×${snapshot.height} @ ${snapshot.fps} FPS"
            )
            append(
                "\nBitrate: $bitrate  •  FEC: $fec"
            )
            append(
                "\nVideo: ${snapshot.videoState}  •  Audio: " +
                    if (
                        snapshot.audioActive
                    ) {
                        "Active"
                    } else {
                        "Waiting"
                    }
            )
            append(
                "\nController: " +
                    if (
                        snapshot.controllerActive
                    ) {
                        "Connected"
                    } else {
                        "Waiting"
                    }
            )
        }
    }
}
