package com.safeiot.privyhub.streaming

import java.io.ByteArrayOutputStream
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.SocketTimeoutException
import java.util.LinkedHashMap
import java.util.concurrent.atomic.AtomicLong
import kotlin.concurrent.thread

data class NativeStreamMetrics(
    val packets: Long,
    val bytes: Long,
    val lostPackets: Long,
    val frames: Long,
    val droppedFrames: Long,
    val robustMissingPackets: Long,
    val forwardGapEvents: Long,
    val lateOrReorderedPackets: Long,
    val duplicateHighestPackets: Long,
    val maxForwardGapPackets: Long,
    val sequenceGapAccessUnitDrops: Long,
    val incompleteAccessUnitDrops: Long,
    val fecParityPackets: Long,
    val fecParityBytes: Long,
    val fecGroupsReceived: Long,
    val fecRecoveredPackets: Long,
    val fecRecoveredMarkerPackets: Long,
    val fecRecoveredIdrPackets: Long,
    val fecGapHolds: Long,
    val fecHoldTimeouts: Long,
    val fecMaxHoldMs: Long,
    val fecMaxHeldPackets: Long,
    val fecUnrecoverableGroups: Long,
    val ssrcChanges: Long,
    val sequenceResyncs: Long,
    val largestResyncJumpPackets: Long,
    val packetsDroppedWaitingForIdr: Long,
    val resyncToIdrMs: Long,
    val maxResyncToIdrMs: Long,
    val firstCleanIdrMs: Long,
    val waitingForIdr: Boolean,
    val idrFrames: Long,
    val maxFramesBetweenIdr: Long,
    val currentFramesSinceIdr: Long,
    val hasSps: Boolean,
    val hasPps: Boolean
)

class RtpH264Receiver(
    private val port: Int,
    private val payloadType: Int = 96,
    private val onParameterSets: (ByteArray, ByteArray) -> Unit,
    private val onAccessUnit: (ByteArray, Long) -> Unit
) {
    companion object {
        private const val FEC_HEADER_SIZE =
            23

        private const val FEC_VERSION =
            1

        private const val FEC_HOLD_TIMEOUT_NS =
            12_000_000L

        private const val FEC_GROUP_MAX_AGE_NS =
            40_000_000L

        private const val MAX_RECENT_PACKETS =
            512

        private const val MAX_FEC_GROUPS =
            96

        // A forward discontinuity this large cannot be repaired by an 8-packet
        // XOR group and is more useful treated as a new stream epoch.
        private const val RESYNC_FORWARD_GAP_PACKETS =
            128

        private val FEC_MAGIC =
            byteArrayOf(
                'P'.code.toByte(),
                'H'.code.toByte(),
                'F'.code.toByte(),
                '1'.code.toByte()
            )
    }

    private data class PacketKey(
        val timestamp: Long,
        val sequence: Int
    )

    private data class FecGroup(
        val count: Int,
        val baseSequence: Int,
        val timestamp: Long,
        val ssrc: Long,
        val markerMask: Int,
        val rtpByte0: Int,
        val payloadType: Int,
        val lengthXor: Int,
        val parity: ByteArray,
        val receivedAtNs: Long
    )

    private val packets =
        AtomicLong(0)

    private val bytes =
        AtomicLong(0)

    private val lostPackets =
        AtomicLong(0)

    private val frames =
        AtomicLong(0)

    private val droppedFrames =
        AtomicLong(0)

    private val robustMissingPackets =
        AtomicLong(0)

    private val forwardGapEvents =
        AtomicLong(0)

    private val lateOrReorderedPackets =
        AtomicLong(0)

    private val duplicateHighestPackets =
        AtomicLong(0)

    private val maxForwardGapPackets =
        AtomicLong(0)

    private val sequenceGapAccessUnitDrops =
        AtomicLong(0)

    private val incompleteAccessUnitDrops =
        AtomicLong(0)

    private val fecParityPackets =
        AtomicLong(0)

    private val fecParityBytes =
        AtomicLong(0)

    private val fecGroupsReceived =
        AtomicLong(0)

    private val fecRecoveredPackets =
        AtomicLong(0)

    private val fecRecoveredMarkerPackets =
        AtomicLong(0)

    private val fecRecoveredIdrPackets =
        AtomicLong(0)

    private val fecGapHolds =
        AtomicLong(0)

    private val fecHoldTimeouts =
        AtomicLong(0)

    private val fecMaxHoldMs =
        AtomicLong(0)

    private val fecMaxHeldPackets =
        AtomicLong(0)

    private val fecUnrecoverableGroups =
        AtomicLong(0)

    private val ssrcChanges =
        AtomicLong(0)

    private val sequenceResyncs =
        AtomicLong(0)

    private val largestResyncJumpPackets =
        AtomicLong(0)

    private val packetsDroppedWaitingForIdr =
        AtomicLong(0)

    private val resyncToIdrMs =
        AtomicLong(0)

    private val maxResyncToIdrMs =
        AtomicLong(0)

    private val firstCleanIdrMs =
        AtomicLong(-1)

    private val idrFrames =
        AtomicLong(0)

    private val maxFramesBetweenIdr =
        AtomicLong(0)

    private val currentFramesSinceIdr =
        AtomicLong(0)

    @Volatile
    private var running =
        false

    @Volatile
    private var socket:
        DatagramSocket? =
        null

    private var worker:
        Thread? =
        null

    // Ordered-delivery front end. The ordinary no-loss path calls the v0.9
    // RTP parser immediately. Only a detected sequence hole starts a short
    // hold while parity has a chance to reconstruct the missing packet.
    private var orderedLastSequence =
        -1

    private var activeSsrc =
        -1L

    private var waitingForIdr =
        true

    private var receiverStartedNs =
        System.nanoTime()

    private var resyncStartedNs =
        0L

    private var gapHoldStartedNs =
        0L

    private val heldPackets =
        HashMap<Int, ByteArray>()

    private val recentPackets =
        LinkedHashMap<PacketKey, ByteArray>()

    private val fecGroups =
        LinkedHashMap<String, FecGroup>()

    // Original v0.9 H.264 depacketizer state.
    private var lastSequence =
        -1

    private var diagnosticHighestSequence =
        -1

    private var currentTimestamp =
        -1L

    private var currentCorrupt =
        false

    private var currentSequenceGap =
        false

    private var currentAccessUnitPacketCount =
        0L

    private var accessUnit =
        ByteArrayOutputStream(
            256 * 1024
        )

    @Volatile
    private var sps:
        ByteArray? =
        null

    @Volatile
    private var pps:
        ByteArray? =
        null

    fun start() {
        if (running) {
            return
        }

        running =
            true

        receiverStartedNs =
            System.nanoTime()

        waitingForIdr =
            true

        resyncStartedNs =
            0L

        worker =
            thread(
                start = true,
                isDaemon = true,
                name = "PrivyHub-RTP-H264-FEC"
            ) {
                receiveLoop()
            }
    }

    fun stop() {
        running =
            false

        try {
            socket?.close()
        } catch (_: Exception) {
        }

        try {
            worker?.join(
                1000
            )
        } catch (_: InterruptedException) {
            Thread.currentThread()
                .interrupt()
        }

        worker =
            null

        socket =
            null
    }

    fun snapshot():
        NativeStreamMetrics {
        return NativeStreamMetrics(
            packets =
                packets.get(),
            bytes =
                bytes.get(),
            lostPackets =
                lostPackets.get(),
            frames =
                frames.get(),
            droppedFrames =
                droppedFrames.get(),
            robustMissingPackets =
                robustMissingPackets.get(),
            forwardGapEvents =
                forwardGapEvents.get(),
            lateOrReorderedPackets =
                lateOrReorderedPackets.get(),
            duplicateHighestPackets =
                duplicateHighestPackets.get(),
            maxForwardGapPackets =
                maxForwardGapPackets.get(),
            sequenceGapAccessUnitDrops =
                sequenceGapAccessUnitDrops.get(),
            incompleteAccessUnitDrops =
                incompleteAccessUnitDrops.get(),
            fecParityPackets =
                fecParityPackets.get(),
            fecParityBytes =
                fecParityBytes.get(),
            fecGroupsReceived =
                fecGroupsReceived.get(),
            fecRecoveredPackets =
                fecRecoveredPackets.get(),
            fecRecoveredMarkerPackets =
                fecRecoveredMarkerPackets.get(),
            fecRecoveredIdrPackets =
                fecRecoveredIdrPackets.get(),
            fecGapHolds =
                fecGapHolds.get(),
            fecHoldTimeouts =
                fecHoldTimeouts.get(),
            fecMaxHoldMs =
                fecMaxHoldMs.get(),
            fecMaxHeldPackets =
                fecMaxHeldPackets.get(),
            fecUnrecoverableGroups =
                fecUnrecoverableGroups.get(),
            ssrcChanges =
                ssrcChanges.get(),
            sequenceResyncs =
                sequenceResyncs.get(),
            largestResyncJumpPackets =
                largestResyncJumpPackets.get(),
            packetsDroppedWaitingForIdr =
                packetsDroppedWaitingForIdr.get(),
            resyncToIdrMs =
                resyncToIdrMs.get(),
            maxResyncToIdrMs =
                maxResyncToIdrMs.get(),
            firstCleanIdrMs =
                firstCleanIdrMs.get(),
            waitingForIdr =
                waitingForIdr,
            idrFrames =
                idrFrames.get(),
            maxFramesBetweenIdr =
                maxFramesBetweenIdr.get(),
            currentFramesSinceIdr =
                currentFramesSinceIdr.get(),
            hasSps =
                sps != null,
            hasPps =
                pps != null
        )
    }

    private fun receiveLoop() {
        val localSocket =
            DatagramSocket(
                port
            )

        // Required only so a loss hold can expire even during a brief packet
        // pause. This is not a normal-path presentation buffer.
        localSocket.soTimeout =
            2

        localSocket.receiveBufferSize =
            2 * 1024 * 1024

        socket =
            localSocket

        val buffer =
            ByteArray(
                64 * 1024
            )

        val packet =
            DatagramPacket(
                buffer,
                buffer.size
            )

        try {
            while (running) {
                try {
                    packet.length =
                        buffer.size

                    localSocket.receive(
                        packet
                    )

                    processIncomingDatagram(
                        packet.data,
                        packet.length
                    )
                } catch (_: SocketTimeoutException) {
                    flushGapIfExpired(
                        System.nanoTime()
                    )
                }
            }
        } catch (_: Exception) {
            if (running) {
                droppedFrames
                    .incrementAndGet()
            }
        } finally {
            try {
                localSocket.close()
            } catch (_: Exception) {
            }
        }
    }

    private fun processIncomingDatagram(
        data: ByteArray,
        length: Int
    ) {
        val nowNs =
            System.nanoTime()

        if (
            isFecPacket(
                data,
                length
            )
        ) {
            processFecPacket(
                data,
                length,
                nowNs
            )

            flushGapIfExpired(
                nowNs
            )

            pruneCaches(
                nowNs
            )

            return
        }

        val packetInfo =
            basicRtpInfo(
                data,
                length
            ) ?:
                return

        if (
            packetInfo.third !=
            payloadType
        ) {
            return
        }

        val sequence =
            packetInfo.first

        val timestamp =
            packetInfo.second

        val ssrc =
            readU32(
                data,
                8
            )

        if (
            activeSsrc <
            0L
        ) {
            activeSsrc =
                ssrc
        } else if (
            ssrc !=
            activeSsrc
        ) {
            ssrcChanges
                .incrementAndGet()

            beginStreamResync(
                newSsrc =
                    ssrc,
                jumpPackets =
                    0L,
                nowNs =
                    nowNs
            )
        } else if (
            shouldResyncForSequenceJump(
                sequence
            )
        ) {
            val expected =
                (
                    orderedLastSequence +
                        1
                ) and
                    0xffff

            val jump =
                (
                    sequence -
                        expected
                ) and
                    0xffff

            beginStreamResync(
                newSsrc =
                    ssrc,
                jumpPackets =
                    jump.toLong(),
                nowNs =
                    nowNs
            )
        }

        packets
            .incrementAndGet()

        bytes
            .addAndGet(
                length.toLong()
            )

        val copy =
            data.copyOfRange(
                0,
                length
            )

        recentPackets[
            PacketKey(
                timestamp,
                sequence
            )
        ] =
            copy

        trimRecentPackets()

        // A late original packet can turn a previously unrecoverable parity
        // group into a single-erasure group.
        attemptFecGroupsForTimestamp(
            timestamp,
            nowNs
        )

        acceptOrderedPacket(
            copy,
            nowNs
        )

        flushGapIfExpired(
            nowNs
        )

        pruneCaches(
            nowNs
        )
    }

    private fun shouldResyncForSequenceJump(
        sequence: Int
    ): Boolean {
        if (
            orderedLastSequence <
            0
        ) {
            return false
        }

        val expected =
            (
                orderedLastSequence +
                    1
            ) and
                0xffff

        val forward =
            (
                sequence -
                    expected
            ) and
                0xffff

        return (
            forward in
            RESYNC_FORWARD_GAP_PACKETS..32767
        )
    }

    private fun beginStreamResync(
        newSsrc: Long,
        jumpPackets: Long,
        nowNs: Long
    ) {
        sequenceResyncs
            .incrementAndGet()

        updateMax(
            largestResyncJumpPackets,
            jumpPackets
        )

        activeSsrc =
            newSsrc

        orderedLastSequence =
            -1

        gapHoldStartedNs =
            0L

        heldPackets
            .clear()

        recentPackets
            .clear()

        fecGroups
            .clear()

        lastSequence =
            -1

        diagnosticHighestSequence =
            -1

        currentTimestamp =
            -1L

        currentCorrupt =
            false

        currentSequenceGap =
            false

        currentAccessUnitPacketCount =
            0L

        accessUnit
            .reset()

        waitingForIdr =
            true

        resyncStartedNs =
            nowNs
    }

    private fun acceptOrderedPacket(
        packet: ByteArray,
        nowNs: Long
    ) {
        val info =
            basicRtpInfo(
                packet,
                packet.size
            ) ?:
                return

        val sequence =
            info.first

        if (
            orderedLastSequence <
            0
        ) {
            parseRtpPacket(
                packet,
                packet.size
            )

            orderedLastSequence =
                sequence

            return
        }

        val expected =
            (
                orderedLastSequence +
                    1
            ) and
                0xffff

        if (
            sequence ==
            expected
        ) {
            parseRtpPacket(
                packet,
                packet.size
            )

            orderedLastSequence =
                sequence

            drainHeldContiguous(
                nowNs
            )

            return
        }

        val forward =
            (
                sequence -
                    expected
            ) and
                0xffff

        if (
            forward in
            1..32767
        ) {
            heldPackets[
                sequence
            ] =
                packet

            if (
                gapHoldStartedNs ==
                0L
            ) {
                gapHoldStartedNs =
                    nowNs

                fecGapHolds
                    .incrementAndGet()
            }

            updateMax(
                fecMaxHeldPackets,
                heldPackets
                    .size
                    .toLong()
            )

            return
        }

        // Behind the ordered frontier: duplicate, late original after FEC
        // recovery, or a recovered packet whose timeout already expired.
    }

    private fun drainHeldContiguous(
        nowNs: Long
    ) {
        while (true) {
            val expected =
                (
                    orderedLastSequence +
                        1
                ) and
                    0xffff

            val packet =
                heldPackets.remove(
                    expected
                ) ?:
                    break

            parseRtpPacket(
                packet,
                packet.size
            )

            orderedLastSequence =
                expected
        }

        if (
            heldPackets
                .isEmpty()
        ) {
            if (
                gapHoldStartedNs !=
                0L
            ) {
                val holdMs =
                    (
                        nowNs -
                            gapHoldStartedNs
                    ).coerceAtLeast(
                        0L
                    ) /
                        1_000_000L

                updateMax(
                    fecMaxHoldMs,
                    holdMs
                )
            }

            gapHoldStartedNs =
                0L
        }
    }

    private fun flushGapIfExpired(
        nowNs: Long
    ) {
        val started =
            gapHoldStartedNs

        if (
            started ==
            0L ||
            nowNs -
                started <
            FEC_HOLD_TIMEOUT_NS
        ) {
            return
        }

        fecHoldTimeouts
            .incrementAndGet()

        val holdMs =
            (
                nowNs -
                    started
            ).coerceAtLeast(
                0L
            ) /
                1_000_000L

        updateMax(
            fecMaxHoldMs,
            holdMs
        )

        val expected =
            (
                orderedLastSequence +
                    1
            ) and
                0xffff

        val ordered =
            heldPackets
                .values
                .sortedBy {
                    val info =
                        basicRtpInfo(
                            it,
                            it.size
                        )

                    if (
                        info ==
                        null
                    ) {
                        65536
                    } else {
                        (
                            info.first -
                                expected
                        ) and
                            0xffff
                    }
                }

        heldPackets
            .clear()

        gapHoldStartedNs =
            0L

        for (
            packet in
            ordered
        ) {
            val info =
                basicRtpInfo(
                    packet,
                    packet.size
                ) ?:
                    continue

            parseRtpPacket(
                packet,
                packet.size
            )

            orderedLastSequence =
                info.first
        }
    }

    private fun processFecPacket(
        data: ByteArray,
        length: Int,
        nowNs: Long
    ) {
        if (
            length <
            FEC_HEADER_SIZE
        ) {
            return
        }

        val version =
            data[4]
                .toInt() and
                0xff

        if (
            version !=
            FEC_VERSION
        ) {
            return
        }

        val count =
            data[5]
                .toInt() and
                0xff

        if (
            count <=
            0 ||
            count >
            8
        ) {
            return
        }

        val baseSequence =
            readU16(
                data,
                6
            )

        val timestamp =
            readU32(
                data,
                8
            )

        val ssrc =
            readU32(
                data,
                12
            )

        val markerMask =
            data[16]
                .toInt() and
                0xff

        val rtpByte0 =
            data[17]
                .toInt() and
                0xff

        val groupPayloadType =
            data[18]
                .toInt() and
                0x7f

        val lengthXor =
            readU16(
                data,
                19
            )

        val parityLength =
            readU16(
                data,
                21
            )

        if (
            parityLength <=
            0 ||
            FEC_HEADER_SIZE +
                parityLength >
            length
        ) {
            return
        }

        fecParityPackets
            .incrementAndGet()

        fecParityBytes
            .addAndGet(
                length.toLong()
            )

        fecGroupsReceived
            .incrementAndGet()

        val group =
            FecGroup(
                count =
                    count,
                baseSequence =
                    baseSequence,
                timestamp =
                    timestamp,
                ssrc =
                    ssrc,
                markerMask =
                    markerMask,
                rtpByte0 =
                    rtpByte0,
                payloadType =
                    groupPayloadType,
                lengthXor =
                    lengthXor,
                parity =
                    data.copyOfRange(
                        FEC_HEADER_SIZE,
                        FEC_HEADER_SIZE +
                            parityLength
                    ),
                receivedAtNs =
                    nowNs
            )

        if (
            activeSsrc >=
            0L &&
            group.ssrc !=
            activeSsrc
        ) {
            return
        }

        val key =
            fecGroupKey(
                group
            )

        fecGroups[
            key
        ] =
            group

        trimFecGroups()

        attemptRecoverGroup(
            key,
            group,
            nowNs
        )
    }

    private fun attemptFecGroupsForTimestamp(
        timestamp: Long,
        nowNs: Long
    ) {
        val candidates =
            fecGroups
                .entries
                .filter {
                    it.value.timestamp ==
                        timestamp
                }
                .map {
                    Pair(
                        it.key,
                        it.value
                    )
                }

        for (
            candidate in
            candidates
        ) {
            attemptRecoverGroup(
                candidate.first,
                candidate.second,
                nowNs
            )
        }
    }

    private fun attemptRecoverGroup(
        key: String,
        group: FecGroup,
        nowNs: Long
    ) {
        val missingIndexes =
            ArrayList<Int>()

        for (
            index in
            0 until
            group.count
        ) {
            val sequence =
                (
                    group.baseSequence +
                        index
                ) and
                    0xffff

            if (
                !recentPackets
                    .containsKey(
                        PacketKey(
                            group.timestamp,
                            sequence
                        )
                    )
            ) {
                missingIndexes.add(
                    index
                )
            }
        }

        if (
            missingIndexes
                .isEmpty()
        ) {
            fecGroups
                .remove(
                    key
                )

            return
        }

        if (
            missingIndexes
                .size >
            1
        ) {
            return
        }

        val missingIndex =
            missingIndexes[0]

        var missingLength =
            group.lengthXor

        val recoveredPayload =
            group.parity
                .copyOf()

        for (
            index in
            0 until
            group.count
        ) {
            if (
                index ==
                missingIndex
            ) {
                continue
            }

            val sequence =
                (
                    group.baseSequence +
                        index
                ) and
                    0xffff

            val packet =
                recentPackets[
                    PacketKey(
                        group.timestamp,
                        sequence
                    )
                ] ?:
                    return

            if (
                packet.size <
                13
            ) {
                return
            }

            val payloadLength =
                packet.size -
                    12

            missingLength =
                missingLength xor
                    payloadLength

            val limit =
                minOf(
                    payloadLength,
                    recoveredPayload.size
                )

            for (
                offset in
                0 until
                limit
            ) {
                recoveredPayload[
                    offset
                ] =
                    (
                        recoveredPayload[
                            offset
                        ].toInt() xor
                            packet[
                                12 +
                                    offset
                            ].toInt()
                    ).toByte()
            }
        }

        if (
            missingLength <=
            0 ||
            missingLength >
            recoveredPayload.size
        ) {
            fecGroups
                .remove(
                    key
                )

            fecUnrecoverableGroups
                .incrementAndGet()

            return
        }

        val sequence =
            (
                group.baseSequence +
                    missingIndex
            ) and
                0xffff

        val marker =
            (
                group.markerMask and
                    (
                        1 shl
                            missingIndex
                    )
            ) !=
                0

        val reconstructed =
            ByteArray(
                12 +
                    missingLength
            )

        reconstructed[0] =
            group.rtpByte0
                .toByte()

        reconstructed[1] =
            (
                group.payloadType or
                    (
                        if (marker) {
                            0x80
                        } else {
                            0
                        }
                    )
            ).toByte()

        writeU16(
            reconstructed,
            2,
            sequence
        )

        writeU32(
            reconstructed,
            4,
            group.timestamp
        )

        writeU32(
            reconstructed,
            8,
            group.ssrc
        )

        System.arraycopy(
            recoveredPayload,
            0,
            reconstructed,
            12,
            missingLength
        )

        recentPackets[
            PacketKey(
                group.timestamp,
                sequence
            )
        ] =
            reconstructed

        trimRecentPackets()

        fecGroups
            .remove(
                key
            )

        fecRecoveredPackets
            .incrementAndGet()

        if (marker) {
            fecRecoveredMarkerPackets
                .incrementAndGet()
        }

        if (
            rtpPayloadLooksLikeIdr(
                reconstructed
            )
        ) {
            fecRecoveredIdrPackets
                .incrementAndGet()
        }

        acceptOrderedPacket(
            reconstructed,
            nowNs
        )
    }

    private fun pruneCaches(
        nowNs: Long
    ) {
        val iterator =
            fecGroups
                .entries
                .iterator()

        while (
            iterator.hasNext()
        ) {
            val entry =
                iterator.next()

            if (
                nowNs -
                    entry.value
                        .receivedAtNs >
                FEC_GROUP_MAX_AGE_NS
            ) {
                iterator.remove()

                fecUnrecoverableGroups
                    .incrementAndGet()
            }
        }
    }

    private fun trimRecentPackets() {
        while (
            recentPackets
                .size >
            MAX_RECENT_PACKETS
        ) {
            val firstKey =
                recentPackets
                    .entries
                    .first()
                    .key

            recentPackets
                .remove(
                    firstKey
                )
        }
    }

    private fun trimFecGroups() {
        while (
            fecGroups
                .size >
            MAX_FEC_GROUPS
        ) {
            val firstKey =
                fecGroups
                    .entries
                    .first()
                    .key

            fecGroups
                .remove(
                    firstKey
                )

            fecUnrecoverableGroups
                .incrementAndGet()
        }
    }

    private fun fecGroupKey(
        group: FecGroup
    ): String {
        return (
            group.timestamp
                .toString() +
                ":" +
                group.baseSequence
                    .toString()
        )
    }

    private fun isFecPacket(
        data: ByteArray,
        length: Int
    ): Boolean {
        if (
            length <
            FEC_HEADER_SIZE
        ) {
            return false
        }

        for (
            index in
            FEC_MAGIC.indices
        ) {
            if (
                data[index] !=
                FEC_MAGIC[index]
            ) {
                return false
            }
        }

        return true
    }

    private fun basicRtpInfo(
        data: ByteArray,
        length: Int
    ): Triple<Int, Long, Int>? {
        if (
            length <
            12
        ) {
            return null
        }

        val version =
            (
                data[0]
                    .toInt() ushr
                    6
            ) and
                0x03

        if (
            version !=
            2
        ) {
            return null
        }

        val sequence =
            readU16(
                data,
                2
            )

        val timestamp =
            readU32(
                data,
                4
            )

        val packetPayloadType =
            data[1]
                .toInt() and
                0x7f

        return Triple(
            sequence,
            timestamp,
            packetPayloadType
        )
    }

    private fun rtpPayloadLooksLikeIdr(
        packet: ByteArray
    ): Boolean {
        if (
            packet.size <
            13
        ) {
            return false
        }

        val nalType =
            packet[12]
                .toInt() and
                0x1f

        if (
            nalType ==
            5
        ) {
            return true
        }

        if (
            nalType ==
            28 &&
            packet.size >=
            14
        ) {
            return (
                packet[13]
                    .toInt() and
                    0x1f
            ) ==
                5
        }

        if (
            nalType ==
            24
        ) {
            var cursor =
                13

            while (
                cursor +
                    2 <=
                packet.size
            ) {
                val size =
                    readU16(
                        packet,
                        cursor
                    )

                cursor +=
                    2

                if (
                    size <=
                    0 ||
                    cursor +
                        size >
                    packet.size
                ) {
                    return false
                }

                if (
                    (
                        packet[cursor]
                            .toInt() and
                            0x1f
                    ) ==
                    5
                ) {
                    return true
                }

                cursor +=
                    size
            }
        }

        return false
    }

    private fun parseRtpPacket(
        data: ByteArray,
        length: Int
    ) {
        if (length < 12) {
            return
        }

        val version = (data[0].toInt() ushr 6) and 0x03
        if (version != 2) {
            return
        }

        val marker = (data[1].toInt() and 0x80) != 0
        val packetPayloadType = data[1].toInt() and 0x7f
        if (packetPayloadType != payloadType) {
            return
        }

        val sequence =
            ((data[2].toInt() and 0xff) shl 8) or
                (data[3].toInt() and 0xff)

        val timestamp =
            ((data[4].toLong() and 0xffL) shl 24) or
                ((data[5].toLong() and 0xffL) shl 16) or
                ((data[6].toLong() and 0xffL) shl 8) or
                (data[7].toLong() and 0xffL)

        var headerLength =
            12 + ((data[0].toInt() and 0x0f) * 4)

        if (headerLength > length) {
            return
        }

        val hasExtension = (data[0].toInt() and 0x10) != 0
        if (hasExtension) {
            if (headerLength + 4 > length) {
                return
            }

            val extensionWords =
                ((data[headerLength + 2].toInt() and 0xff) shl 8) or
                    (data[headerLength + 3].toInt() and 0xff)

            headerLength += 4 + extensionWords * 4
            if (headerLength > length) {
                return
            }
        }

        var payloadLength = length - headerLength
        val hasPadding = (data[0].toInt() and 0x20) != 0
        if (hasPadding) {
            val padding = data[length - 1].toInt() and 0xff
            if (padding <= 0 || padding > payloadLength) {
                return
            }
            payloadLength -= padding
        }

        if (payloadLength <= 0) {
            return
        }

        observeDiagnosticSequence(
            sequence
        )

        var sequenceGap = false

        if (lastSequence >= 0) {
            val expected = (lastSequence + 1) and 0xffff
            if (sequence != expected) {
                val missing = (sequence - expected) and 0xffff
                if (missing in 1..32767) {
                    lostPackets.addAndGet(missing.toLong())
                    sequenceGap = true
                }
            }
        }
        lastSequence = sequence

        if (currentTimestamp != timestamp) {
            if (currentTimestamp >= 0 && accessUnit.size() > 0) {
                droppedFrames.incrementAndGet()
                incompleteAccessUnitDrops.incrementAndGet()

                if (waitingForIdr) {
                    packetsDroppedWaitingForIdr
                        .addAndGet(
                            currentAccessUnitPacketCount
                        )
                }

                if (currentSequenceGap) {
                    sequenceGapAccessUnitDrops.incrementAndGet()
                }
            }

            currentTimestamp = timestamp
            currentCorrupt = sequenceGap
            currentSequenceGap = sequenceGap
            currentAccessUnitPacketCount = 0L
            accessUnit.reset()
        } else if (sequenceGap) {
            currentCorrupt = true
            currentSequenceGap = true
        }

        currentAccessUnitPacketCount +=
            1L

        val offset = headerLength
        val nalType = data[offset].toInt() and 0x1f

        when {
            nalType in 1..23 -> {
                observeParameterSet(
                    data = data,
                    offset = offset,
                    length = payloadLength
                )

                appendStartCode()
                accessUnit.write(data, offset, payloadLength)
            }

            nalType == 24 -> {
                parseStapA(
                    data = data,
                    offset = offset,
                    payloadLength = payloadLength
                )
            }

            nalType == 28 -> {
                parseFuA(
                    data = data,
                    offset = offset,
                    payloadLength = payloadLength
                )
            }

            else -> {
                currentCorrupt = true
            }
        }

        if (marker) {
            if (!currentCorrupt && accessUnit.size() > 0) {
                val frame = accessUnit.toByteArray()
                val isIdr =
                    containsNalType(
                        frame,
                        5
                    )

                if (
                    waitingForIdr &&
                    !isIdr
                ) {
                    droppedFrames
                        .incrementAndGet()

                    packetsDroppedWaitingForIdr
                        .addAndGet(
                            currentAccessUnitPacketCount
                        )
                } else {
                    if (
                        waitingForIdr &&
                        isIdr
                    ) {
                        completeStreamResync(
                            System.nanoTime()
                        )
                    }

                    frames.incrementAndGet()

                    observeDeliveredAccessUnit(
                        frame
                    )

                    onAccessUnit(
                        frame,
                        System.nanoTime() / 1000L
                    )
                }
            } else {
                droppedFrames.incrementAndGet()

                if (waitingForIdr) {
                    packetsDroppedWaitingForIdr
                        .addAndGet(
                            currentAccessUnitPacketCount
                        )
                }

                if (currentSequenceGap) {
                    sequenceGapAccessUnitDrops.incrementAndGet()
                }
            }

            accessUnit.reset()
            currentTimestamp = -1L
            currentCorrupt = false
            currentSequenceGap = false
            currentAccessUnitPacketCount = 0L
        }
    }

    private fun observeDiagnosticSequence(
        sequence: Int
    ) {
        val highest =
            diagnosticHighestSequence

        if (highest < 0) {
            diagnosticHighestSequence =
                sequence
            return
        }

        val delta =
            (
                sequence -
                    highest
            ) and
                0xffff

        when {
            delta == 0 -> {
                duplicateHighestPackets
                    .incrementAndGet()
            }

            delta in 1..32767 -> {
                if (delta > 1) {
                    val missing =
                        delta - 1

                    robustMissingPackets
                        .addAndGet(
                            missing.toLong()
                        )

                    forwardGapEvents
                        .incrementAndGet()

                    updateMax(
                        maxForwardGapPackets,
                        missing.toLong()
                    )
                }

                diagnosticHighestSequence =
                    sequence
            }

            else -> {
                lateOrReorderedPackets
                    .incrementAndGet()
            }
        }
    }

    private fun completeStreamResync(
        nowNs: Long
    ) {
        waitingForIdr =
            false

        if (
            firstCleanIdrMs
                .get() <
            0L
        ) {
            firstCleanIdrMs
                .set(
                    (
                        nowNs -
                            receiverStartedNs
                    ).coerceAtLeast(
                        0L
                    ) /
                        1_000_000L
                )
        }

        val startNs =
            resyncStartedNs

        if (
            startNs >
            0L
        ) {
            val elapsedMs =
                (
                    nowNs -
                        startNs
                ).coerceAtLeast(
                    0L
                ) /
                    1_000_000L

            resyncToIdrMs
                .set(
                    elapsedMs
                )

            updateMax(
                maxResyncToIdrMs,
                elapsedMs
            )
        }

        resyncStartedNs =
            0L
    }

    private fun observeDeliveredAccessUnit(
        frame: ByteArray
    ) {
        if (
            containsNalType(
                frame,
                5
            )
        ) {
            idrFrames.incrementAndGet()

            updateMax(
                maxFramesBetweenIdr,
                currentFramesSinceIdr.get()
            )

            currentFramesSinceIdr.set(
                0
            )
        } else {
            val since =
                currentFramesSinceIdr
                    .incrementAndGet()

            updateMax(
                maxFramesBetweenIdr,
                since
            )
        }
    }

    private fun containsNalType(
        data: ByteArray,
        wantedType: Int
    ): Boolean {
        var index =
            0

        while (index + 4 < data.size) {
            var headerIndex =
                -1

            if (
                index + 4 < data.size &&
                data[index] == 0.toByte() &&
                data[index + 1] == 0.toByte() &&
                data[index + 2] == 0.toByte() &&
                data[index + 3] == 1.toByte()
            ) {
                headerIndex =
                    index + 4
                index =
                    headerIndex
            } else if (
                index + 3 < data.size &&
                data[index] == 0.toByte() &&
                data[index + 1] == 0.toByte() &&
                data[index + 2] == 1.toByte()
            ) {
                headerIndex =
                    index + 3
                index =
                    headerIndex
            } else {
                index += 1
                continue
            }

            if (
                headerIndex >= 0 &&
                headerIndex < data.size
            ) {
                val nalType =
                    data[headerIndex]
                        .toInt() and
                        0x1f

                if (nalType == wantedType) {
                    return true
                }
            }
        }

        return false
    }

    private fun parseStapA(
        data: ByteArray,
        offset: Int,
        payloadLength: Int
    ) {
        var cursor = offset + 1
        val end = offset + payloadLength

        while (cursor + 2 <= end) {
            val nalSize =
                ((data[cursor].toInt() and 0xff) shl 8) or
                    (data[cursor + 1].toInt() and 0xff)
            cursor += 2

            if (nalSize <= 0 || cursor + nalSize > end) {
                currentCorrupt = true
                return
            }

            observeParameterSet(
                data = data,
                offset = cursor,
                length = nalSize
            )

            appendStartCode()
            accessUnit.write(data, cursor, nalSize)
            cursor += nalSize
        }

        if (cursor != end) {
            currentCorrupt = true
        }
    }

    private fun parseFuA(
        data: ByteArray,
        offset: Int,
        payloadLength: Int
    ) {
        if (payloadLength < 2) {
            currentCorrupt = true
            return
        }

        val indicator = data[offset].toInt() and 0xff
        val header = data[offset + 1].toInt() and 0xff
        val start = (header and 0x80) != 0
        val nalType = header and 0x1f

        if (start) {
            appendStartCode()

            val reconstructedHeader =
                (indicator and 0xe0) or nalType

            accessUnit.write(
                reconstructedHeader
            )
        }

        if (payloadLength > 2) {
            accessUnit.write(
                data,
                offset + 2,
                payloadLength - 2
            )
        }
    }

    private fun observeParameterSet(
        data: ByteArray,
        offset: Int,
        length: Int
    ) {
        if (length <= 0) {
            return
        }

        when (data[offset].toInt() and 0x1f) {
            7 -> {
                sps =
                    data.copyOfRange(
                        offset,
                        offset + length
                    )
            }

            8 -> {
                pps =
                    data.copyOfRange(
                        offset,
                        offset + length
                    )
            }
        }

        val currentSps = sps
        val currentPps = pps

        if (
            currentSps != null &&
            currentPps != null
        ) {
            onParameterSets(
                currentSps.copyOf(),
                currentPps.copyOf()
            )
        }
    }

    private fun appendStartCode() {
        accessUnit.write(
            byteArrayOf(
                0,
                0,
                0,
                1
            )
        )
    }

    private fun readU16(
        data: ByteArray,
        offset: Int
    ): Int {
        return (
            (
                data[offset]
                    .toInt() and
                    0xff
            ) shl
                8
        ) or
            (
                data[
                    offset +
                        1
                ].toInt() and
                    0xff
            )
    }

    private fun readU32(
        data: ByteArray,
        offset: Int
    ): Long {
        return (
            (
                data[offset]
                    .toLong() and
                    0xffL
            ) shl
                24
        ) or
            (
                (
                    data[
                        offset +
                            1
                    ].toLong() and
                        0xffL
                ) shl
                    16
            ) or
            (
                (
                    data[
                        offset +
                            2
                    ].toLong() and
                        0xffL
                ) shl
                    8
            ) or
            (
                data[
                    offset +
                        3
                ].toLong() and
                    0xffL
            )
    }

    private fun writeU16(
        data: ByteArray,
        offset: Int,
        value: Int
    ) {
        data[offset] =
            (
                value ushr
                    8
            ).toByte()

        data[
            offset +
                1
        ] =
            value.toByte()
    }

    private fun writeU32(
        data: ByteArray,
        offset: Int,
        value: Long
    ) {
        data[offset] =
            (
                value ushr
                    24
            ).toByte()

        data[
            offset +
                1
        ] =
            (
                value ushr
                    16
            ).toByte()

        data[
            offset +
                2
        ] =
            (
                value ushr
                    8
            ).toByte()

        data[
            offset +
                3
        ] =
            value.toByte()
    }

    private fun updateMax(
        target: AtomicLong,
        value: Long
    ) {
        while (true) {
            val old =
                target.get()

            if (
                value <= old ||
                target.compareAndSet(
                    old,
                    value
                )
            ) {
                return
            }
        }
    }
}
