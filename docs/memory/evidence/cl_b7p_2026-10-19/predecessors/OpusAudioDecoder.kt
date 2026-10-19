package com.safeiot.privyhub.streaming

import android.media.AudioFormat
import android.media.MediaCodec
import android.media.MediaFormat
import java.nio.ByteBuffer

/**
 * CL-B4: MediaCodec `audio/opus`, synchronous, on the audio receive thread
 * (so the queue keeps its one producer). 48 kHz stereo; csd-0 the OpusHead
 * (pre-skip 120), csd-1 the pre-skip and csd-2 the seek pre-roll in ns.
 *
 * One input is queued per frame and its output drained before returning
 * (bounded by [DRAIN_WAIT_NS]); an output that has not come by then is
 * counted and picked up by the next call. Output is s16 interleaved PCM.
 *
 * CL-B5: called on [OpusDecodePipeline]'s decode thread, not the receive thread.
 */
class OpusAudioDecoder(private val frameSamples: Int) : OpusDecodePipeline.FrameDecoder {
    companion object {
        private const val MIME = "audio/opus"
        private const val INPUT_WAIT_US = 10_000L
        private const val DRAIN_WAIT_NS = 4_000_000L
    }

    private val codec: MediaCodec = MediaCodec.createDecoderByType(MIME)
    private val info = MediaCodec.BufferInfo()
    private val frameUs = frameSamples * 1_000_000L / OpusFraming.SAMPLE_RATE
    private var ptsUs = 0L
    private var inputs = 0L
    private var outputs = 0L

    override val name: String
    var decodeErrors = 0L
        private set
    var drainTimeouts = 0L
        private set
    var formatErrors = 0L
        private set
    var decodeNsTotal = 0L
        private set
    var decodeNsMax = 0L
        private set
    var decodeCalls = 0L
        private set

    init {
        val format = MediaFormat.createAudioFormat(MIME, OpusFraming.SAMPLE_RATE, OpusFraming.CHANNELS)
        format.setByteBuffer("csd-0", ByteBuffer.wrap(OpusFraming.opusHead()))
        format.setByteBuffer("csd-1", ByteBuffer.wrap(OpusFraming.nsBuffer(OpusFraming.preSkipNs())))
        format.setByteBuffer("csd-2", ByteBuffer.wrap(OpusFraming.nsBuffer(OpusFraming.SEEK_PRE_ROLL_NS)))
        try {
            codec.configure(format, null, null, 0)
            codec.start()
        } catch (e: Exception) {
            codec.release()
            throw e
        }
        name = codec.name
    }

    override fun decode(packet: ByteArray, out: (ByteArray, Int) -> Unit): Boolean =
        decode(packet, 0, packet.size, out)

    /** Decode one Opus packet; [out] gets each PCM output (bytes, length). False if it could not be queued. */
    fun decode(packet: ByteArray, offset: Int, length: Int, out: (ByteArray, Int) -> Unit): Boolean {
        val t0 = System.nanoTime()
        try {
            val index = codec.dequeueInputBuffer(INPUT_WAIT_US)
            if (index < 0) {
                decodeErrors += 1
                drain(out)
                return false
            }
            val buffer = codec.getInputBuffer(index)
            if (buffer == null) {
                decodeErrors += 1
                return false
            }
            buffer.clear()
            buffer.put(packet, offset, length)
            codec.queueInputBuffer(index, 0, length, ptsUs, 0)
            ptsUs += frameUs
            inputs += 1
            drain(out)
            return true
        } catch (_: Exception) {
            decodeErrors += 1
            return false
        } finally {
            val ns = System.nanoTime() - t0
            decodeNsTotal += ns
            decodeCalls += 1
            if (ns > decodeNsMax) decodeNsMax = ns
        }
    }

    private fun drain(out: (ByteArray, Int) -> Unit) {
        val deadline = System.nanoTime() + DRAIN_WAIT_NS
        while (true) {
            val pending = inputs - outputs
            val waitUs = if (pending > 0) maxOf(0L, (deadline - System.nanoTime()) / 1000L) else 0L
            val index = codec.dequeueOutputBuffer(info, waitUs)
            when {
                index >= 0 -> {
                    if (info.size > 0) {
                        val buffer = codec.getOutputBuffer(index)
                        if (buffer != null) {
                            buffer.position(info.offset)
                            buffer.limit(info.offset + info.size)
                            val pcm = ByteArray(info.size)
                            buffer.get(pcm)
                            out(pcm, pcm.size)
                        }
                    }
                    codec.releaseOutputBuffer(index, false)
                    outputs += 1
                }
                index == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                    val f = codec.outputFormat
                    val ch = if (f.containsKey(MediaFormat.KEY_CHANNEL_COUNT)) f.getInteger(MediaFormat.KEY_CHANNEL_COUNT) else 2
                    val enc = if (f.containsKey(MediaFormat.KEY_PCM_ENCODING)) {
                        f.getInteger(MediaFormat.KEY_PCM_ENCODING)
                    } else {
                        AudioFormat.ENCODING_PCM_16BIT
                    }
                    if (ch != OpusFraming.CHANNELS || enc != AudioFormat.ENCODING_PCM_16BIT) formatErrors += 1
                }
                index == MediaCodec.INFO_TRY_AGAIN_LATER -> {
                    if (pending > 0) {
                        // Not come within the wait: picked up by a later call.
                        drainTimeouts += 1
                        outputs = inputs
                    }
                    return
                }
                else -> Unit
            }
        }
    }

    override fun release() {
        try {
            codec.stop()
        } catch (_: Exception) {
        }
        try {
            codec.release()
        } catch (_: Exception) {
        }
    }
}
