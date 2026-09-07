using System.Buffers.Binary;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Text.Json;
using NAudio.CoreAudioApi;
using NAudio.Wave;

internal static class Program
{
    private const int SampleRate = 48_000;
    private const int Channels = 2;
    private const int BytesPerSample = 2;
    private const int FramesPerPacket = 240; // 5 ms
    private const int PayloadBytes = FramesPerPacket * Channels * BytesPerSample;
    private const int HeaderBytes = 16;
    private const int QueueCapacityChunks = 256;
    private const string ProbeVersion = "process_loopback_pair_pacer_v0.22";

    private sealed record CaptureChunk(
        long CallbackTicks,
        long DevicePosition,
        long QpcPosition100ns,
        int Flags,
        byte[] Data
    );

    private sealed class ProbeStats
    {
        public readonly object Gate = new();

        public long StartedTimestamp;
        public long LastCallbackTimestamp;
        public long LastSendTimestamp;

        public long CallbackCount;
        public long CallbackFrames;
        public long CallbackBytes;
        public long SilentCallbacks;
        public long CallbackBurstsUnder2ms;
        public long CallbackGapsGe10ms;
        public long CallbackIntervalTotalTicks;
        public long CallbackIntervalMinTicks;
        public long CallbackIntervalMaxTicks;
        public readonly Dictionary<int, long> CallbackFramesHistogram = new();
        public readonly Dictionary<string, long> CallbackFlags = new();

        public long DevicePositionDiscontinuities;
        public long QpcRegressions;
        public long LastDevicePosition = -1;
        public long LastQpcPosition100ns = -1;

        public long QueueMaxDepth;
        public long QueueDroppedChunks;
        public long QueueDroppedBytes;

        public long ChunksConsumed;
        public long MaxAccumulatorBytes;
        public long MaxPacketsFromOneCallback;
        public long PartialBytesAtStop;

        public long PacketsSent;
        public long PayloadBytesSent;
        public long SendErrors;
        public long SendCalls;
        public long SendCallTotalTicks;
        public long SendCallMaxTicks;
        public long SendIntervalTotalTicks;
        public long SendIntervalMinTicks;
        public long SendIntervalMaxTicks;
        public long SendBurstsUnder2ms;
        public long SendGapsGe10ms;

        public long NonBlockingWouldBlockDrops;
        public long NonBlockingNoBufferDrops;
        public long NonBlockingOtherSocketErrors;

        public long PairPacingWaits;
        public long PairPacingLateGe1ms;
        public long PairPacingMaxLateTicks;
        public long IntraCallbackSpacingCount;
        public long IntraCallbackSpacingTotalTicks;
        public long IntraCallbackSpacingMinTicks;
        public long IntraCallbackSpacingMaxTicks;
        public readonly long[] IntraCallbackSpacingHistogram = new long[9];

        public readonly long[] CallbackIntervalHistogram = new long[9];
        public readonly long[] SendIntervalHistogram = new long[9];

        public string? StopError;
        public string? RecordingStoppedError;
    }

    private static int BucketForMilliseconds(double ms)
    {
        if (ms < 1.0) return 0;
        if (ms < 2.0) return 1;
        if (ms < 4.0) return 2;
        if (ms < 6.0) return 3;
        if (ms < 8.0) return 4;
        if (ms < 12.0) return 5;
        if (ms < 20.0) return 6;
        if (ms < 30.0) return 7;
        return 8;
    }

    private static Dictionary<string, long> HistogramObject(long[] values) =>
        new()
        {
            ["lt_1ms"] = values[0],
            ["1_2ms"] = values[1],
            ["2_4ms"] = values[2],
            ["4_6ms"] = values[3],
            ["6_8ms"] = values[4],
            ["8_12ms"] = values[5],
            ["12_20ms"] = values[6],
            ["20_30ms"] = values[7],
            ["ge_30ms"] = values[8],
        };

    private static double TicksToMs(long ticks) =>
        ticks * 1000.0 / Stopwatch.Frequency;

    private static double AverageTicksMs(long total, long count) =>
        count > 0 ? Math.Round(TicksToMs(total) / count, 4) : 0.0;

    private static Dictionary<string, string> ParseArgs(string[] args)
    {
        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

        for (var i = 0; i < args.Length; i++)
        {
            var arg = args[i];

            if (!arg.StartsWith("--", StringComparison.Ordinal))
                throw new ArgumentException($"Unexpected argument: {arg}");

            if (i + 1 >= args.Length)
                throw new ArgumentException($"Missing value for {arg}");

            result[arg[2..]] = args[++i];
        }

        return result;
    }

    private static void WriteJsonAtomic(string path, object payload)
    {
        var full = Path.GetFullPath(path);
        var parent = Path.GetDirectoryName(full);

        if (!string.IsNullOrWhiteSpace(parent))
            Directory.CreateDirectory(parent);

        var temp = full + ".tmp";
        var json = JsonSerializer.Serialize(
            payload,
            new JsonSerializerOptions { WriteIndented = true }
        );
        File.WriteAllText(temp, json);
        File.Move(temp, full, true);
    }

    private static object BuildStatus(
        ProbeStats stats,
        int targetPid,
        string clientIp,
        int port,
        string logPath,
        bool ready,
        bool final,
        string? error,
        string captureFormat)
    {
        lock (stats.Gate)
        {
            var elapsedMs = stats.StartedTimestamp > 0
                ? TicksToMs(Stopwatch.GetTimestamp() - stats.StartedTimestamp)
                : 0.0;

            var callbackIntervals = Math.Max(0, stats.CallbackCount - 1);
            var sendIntervals = Math.Max(0, stats.SendCalls - 1);

            return new
            {
                schema = "privyhub_native_process_loopback_audio_probe_v1",
                probe_version = ProbeVersion,
                ready,
                final,
                error = error ?? "",
                duration_ms = Math.Round(elapsedMs, 3),
                backend = "windows_wasapi_process_loopback_naudio",
                target = new
                {
                    pid = targetPid,
                    include_process_tree = true,
                },
                destination = new
                {
                    client_ip = clientIp,
                    port,
                },
                format = new
                {
                    sample_rate = SampleRate,
                    channels = Channels,
                    sample_format = "pcm_s16le",
                    frames_per_packet = FramesPerPacket,
                    packet_ms = 5,
                    payload_bytes = PayloadBytes,
                    capture_format = captureFormat,
                },
                callback = new
                {
                    count = stats.CallbackCount,
                    frames_total = stats.CallbackFrames,
                    bytes_total = stats.CallbackBytes,
                    silent_callbacks = stats.SilentCallbacks,
                    interval_count = callbackIntervals,
                    interval_avg_ms = AverageTicksMs(
                        stats.CallbackIntervalTotalTicks,
                        callbackIntervals
                    ),
                    interval_min_ms = Math.Round(
                        TicksToMs(stats.CallbackIntervalMinTicks), 4
                    ),
                    interval_max_ms = Math.Round(
                        TicksToMs(stats.CallbackIntervalMaxTicks), 4
                    ),
                    interval_histogram = HistogramObject(
                        stats.CallbackIntervalHistogram
                    ),
                    bursts_lt_2ms = stats.CallbackBurstsUnder2ms,
                    gaps_ge_10ms = stats.CallbackGapsGe10ms,
                    frames_per_callback_histogram =
                        stats.CallbackFramesHistogram.ToDictionary(
                            kv => kv.Key.ToString(),
                            kv => kv.Value
                        ),
                    flags = new Dictionary<string, long>(stats.CallbackFlags),
                    device_position_discontinuities =
                        stats.DevicePositionDiscontinuities,
                    qpc_regressions = stats.QpcRegressions,
                },
                queue = new
                {
                    capacity_chunks = QueueCapacityChunks,
                    max_depth = stats.QueueMaxDepth,
                    dropped_chunks = stats.QueueDroppedChunks,
                    dropped_bytes = stats.QueueDroppedBytes,
                },
                packetizer = new
                {
                    chunks_consumed = stats.ChunksConsumed,
                    max_accumulator_bytes = stats.MaxAccumulatorBytes,
                    max_packets_from_one_callback =
                        stats.MaxPacketsFromOneCallback,
                    partial_bytes_at_stop = stats.PartialBytesAtStop,
                },
                sender_policy = new
                {
                    architecture = "callback_local_pair_pacer_v0.22",
                    target_packet_spacing_ms = 5,
                    cumulative_clock = false,
                    rebasing = false,
                    reservoir = false,
                    socket_blocking = false,
                    pacing_waits = stats.PairPacingWaits,
                    late_ge_1ms = stats.PairPacingLateGe1ms,
                    max_late_ms = Math.Round(
                        TicksToMs(stats.PairPacingMaxLateTicks), 4
                    ),
                    intra_callback_spacing_count =
                        stats.IntraCallbackSpacingCount,
                    intra_callback_spacing_avg_ms = AverageTicksMs(
                        stats.IntraCallbackSpacingTotalTicks,
                        stats.IntraCallbackSpacingCount
                    ),
                    intra_callback_spacing_min_ms = Math.Round(
                        TicksToMs(stats.IntraCallbackSpacingMinTicks), 4
                    ),
                    intra_callback_spacing_max_ms = Math.Round(
                        TicksToMs(stats.IntraCallbackSpacingMaxTicks), 4
                    ),
                    intra_callback_spacing_histogram = HistogramObject(
                        stats.IntraCallbackSpacingHistogram
                    ),
                },
                send = new
                {
                    packets = stats.PacketsSent,
                    payload_bytes = stats.PayloadBytesSent,
                    errors = stats.SendErrors,
                    nonblocking_would_block_drops =
                        stats.NonBlockingWouldBlockDrops,
                    nonblocking_no_buffer_drops =
                        stats.NonBlockingNoBufferDrops,
                    nonblocking_other_socket_errors =
                        stats.NonBlockingOtherSocketErrors,
                    call_avg_ms = AverageTicksMs(
                        stats.SendCallTotalTicks,
                        stats.SendCalls
                    ),
                    call_max_ms = Math.Round(
                        TicksToMs(stats.SendCallMaxTicks), 4
                    ),
                    interval_count = sendIntervals,
                    interval_avg_ms = AverageTicksMs(
                        stats.SendIntervalTotalTicks,
                        sendIntervals
                    ),
                    interval_min_ms = Math.Round(
                        TicksToMs(stats.SendIntervalMinTicks), 4
                    ),
                    interval_max_ms = Math.Round(
                        TicksToMs(stats.SendIntervalMaxTicks), 4
                    ),
                    interval_histogram = HistogramObject(
                        stats.SendIntervalHistogram
                    ),
                    bursts_lt_2ms = stats.SendBurstsUnder2ms,
                    gaps_ge_10ms = stats.SendGapsGe10ms,
                },
                recording_stopped_error = stats.RecordingStoppedError ?? "",
                stop_error = stats.StopError ?? "",
                os = Environment.OSVersion.VersionString,
                process_architecture =
                    System.Runtime.InteropServices.RuntimeInformation
                        .ProcessArchitecture.ToString(),
                log_path = Path.GetFullPath(logPath),
            };
        }
    }

    private static void ObserveCallback(
        ProbeStats stats,
        int frames,
        int bytes,
        AudioClientBufferFlags flags,
        long devicePosition,
        long qpcPosition)
    {
        var now = Stopwatch.GetTimestamp();

        lock (stats.Gate)
        {
            stats.CallbackCount++;
            stats.CallbackFrames += frames;
            stats.CallbackBytes += bytes;

            if ((flags & AudioClientBufferFlags.Silent) != 0)
                stats.SilentCallbacks++;

            stats.CallbackFramesHistogram.TryGetValue(frames, out var frameCount);
            stats.CallbackFramesHistogram[frames] = frameCount + 1;

            var flagName = flags.ToString();
            stats.CallbackFlags.TryGetValue(flagName, out var flagCount);
            stats.CallbackFlags[flagName] = flagCount + 1;

            if (stats.LastCallbackTimestamp > 0)
            {
                var delta = Math.Max(0, now - stats.LastCallbackTimestamp);
                stats.CallbackIntervalTotalTicks += delta;
                if (stats.CallbackIntervalMinTicks == 0 ||
                    delta < stats.CallbackIntervalMinTicks)
                    stats.CallbackIntervalMinTicks = delta;
                stats.CallbackIntervalMaxTicks =
                    Math.Max(stats.CallbackIntervalMaxTicks, delta);

                var ms = TicksToMs(delta);
                stats.CallbackIntervalHistogram[BucketForMilliseconds(ms)]++;
                if (ms < 2.0) stats.CallbackBurstsUnder2ms++;
                if (ms >= 10.0) stats.CallbackGapsGe10ms++;
            }

            if (stats.LastDevicePosition >= 0 &&
                devicePosition > 0 &&
                devicePosition < stats.LastDevicePosition)
                stats.DevicePositionDiscontinuities++;

            if (stats.LastQpcPosition100ns >= 0 &&
                qpcPosition > 0 &&
                qpcPosition < stats.LastQpcPosition100ns)
                stats.QpcRegressions++;

            stats.LastCallbackTimestamp = now;

            if (devicePosition > 0)
                stats.LastDevicePosition = devicePosition;

            if (qpcPosition > 0)
                stats.LastQpcPosition100ns = qpcPosition;
        }
    }

    private static void ObserveSend(
        ProbeStats stats,
        long started,
        long done,
        bool success,
        int payloadBytes,
        SocketError? socketError)
    {
        lock (stats.Gate)
        {
            var call = Math.Max(0, done - started);
            stats.SendCalls++;
            stats.SendCallTotalTicks += call;
            stats.SendCallMaxTicks = Math.Max(stats.SendCallMaxTicks, call);

            if (success)
            {
                stats.PacketsSent++;
                stats.PayloadBytesSent += payloadBytes;
            }
            else
            {
                stats.SendErrors++;

                if (socketError == SocketError.WouldBlock)
                    stats.NonBlockingWouldBlockDrops++;
                else if (socketError == SocketError.NoBufferSpaceAvailable)
                    stats.NonBlockingNoBufferDrops++;
                else if (socketError.HasValue)
                    stats.NonBlockingOtherSocketErrors++;
            }

            if (stats.LastSendTimestamp > 0)
            {
                var delta = Math.Max(0, done - stats.LastSendTimestamp);
                stats.SendIntervalTotalTicks += delta;
                if (stats.SendIntervalMinTicks == 0 ||
                    delta < stats.SendIntervalMinTicks)
                    stats.SendIntervalMinTicks = delta;
                stats.SendIntervalMaxTicks =
                    Math.Max(stats.SendIntervalMaxTicks, delta);

                var ms = TicksToMs(delta);
                stats.SendIntervalHistogram[BucketForMilliseconds(ms)]++;
                if (ms < 2.0) stats.SendBurstsUnder2ms++;
                if (ms >= 10.0) stats.SendGapsGe10ms++;
            }

            stats.LastSendTimestamp = done;
        }
    }

    private static void WaitUntil(
        long targetTicks,
        ProbeStats stats,
        CancellationToken token)
    {
        while (!token.IsCancellationRequested)
        {
            var now = Stopwatch.GetTimestamp();
            var remaining = targetTicks - now;

            if (remaining <= 0)
            {
                var late = -remaining;

                lock (stats.Gate)
                {
                    stats.PairPacingWaits++;
                    stats.PairPacingMaxLateTicks = Math.Max(
                        stats.PairPacingMaxLateTicks,
                        late
                    );

                    if (TicksToMs(late) >= 1.0)
                        stats.PairPacingLateGe1ms++;
                }

                return;
            }

            var remainingMs = TicksToMs(remaining);

            // Sleep while comfortably away from the target, then use short
            // yields/spins only for the final fraction of a millisecond.
            if (remainingMs > 1.5)
            {
                Thread.Sleep(1);
            }
            else if (remainingMs > 0.25)
            {
                Thread.Yield();
            }
            else
            {
                Thread.SpinWait(32);
            }
        }
    }

    private static void ObserveIntraCallbackSpacing(
        ProbeStats stats,
        long previousSendDone,
        long currentSendDone)
    {
        if (previousSendDone <= 0)
            return;

        var delta = Math.Max(
            0,
            currentSendDone - previousSendDone
        );

        lock (stats.Gate)
        {
            stats.IntraCallbackSpacingCount++;
            stats.IntraCallbackSpacingTotalTicks += delta;

            if (stats.IntraCallbackSpacingMinTicks == 0 ||
                delta < stats.IntraCallbackSpacingMinTicks)
                stats.IntraCallbackSpacingMinTicks = delta;

            stats.IntraCallbackSpacingMaxTicks = Math.Max(
                stats.IntraCallbackSpacingMaxTicks,
                delta
            );

            stats.IntraCallbackSpacingHistogram[
                BucketForMilliseconds(TicksToMs(delta))
            ]++;
        }
    }

    private static void SenderLoop(
        BlockingCollection<CaptureChunk> queue,
        ProbeStats stats,
        Socket socket,
        IPEndPoint destination,
        CancellationToken token)
    {
        ushort sequence = 0;
        uint sampleTimestamp = 0;
        var accumulator = new List<byte>(8192);
        var fiveMsTicks = Math.Max(
            1L,
            (long)Math.Round(
                Stopwatch.Frequency * 0.005
            )
        );

        try
        {
            foreach (var chunk in queue.GetConsumingEnumerable(token))
            {
                lock (stats.Gate)
                    stats.ChunksConsumed++;

                accumulator.AddRange(chunk.Data);

                lock (stats.Gate)
                    stats.MaxAccumulatorBytes = Math.Max(
                        stats.MaxAccumulatorBytes,
                        accumulator.Count
                    );

                var packetsFromChunk = 0;
                var chunkOriginTicks = Stopwatch.GetTimestamp();
                var previousChunkSendDone = 0L;

                while (accumulator.Count >= PayloadBytes)
                {
                    // The WASAPI process-loopback callback is a stable 10 ms
                    // source. Network packets remain 5 ms to stay well under
                    // MTU, so pace only the second half of each callback.
                    //
                    // This deadline is local to this callback. It is never
                    // carried into the next callback, never rebased, and never
                    // used to catch up a missed wall-clock schedule.
                    if (packetsFromChunk > 0)
                    {
                        var target = chunkOriginTicks +
                            fiveMsTicks * packetsFromChunk;

                        WaitUntil(
                            target,
                            stats,
                            token
                        );

                        if (token.IsCancellationRequested)
                            break;
                    }

                    var datagram = new byte[HeaderBytes + PayloadBytes];

                    datagram[0] = (byte)'P';
                    datagram[1] = (byte)'H';
                    datagram[2] = (byte)'A';
                    datagram[3] = (byte)'1';
                    datagram[4] = 1;
                    datagram[5] = Channels;

                    BinaryPrimitives.WriteUInt16LittleEndian(
                        datagram.AsSpan(6, 2),
                        sequence
                    );
                    BinaryPrimitives.WriteUInt32LittleEndian(
                        datagram.AsSpan(8, 4),
                        sampleTimestamp
                    );
                    BinaryPrimitives.WriteUInt32LittleEndian(
                        datagram.AsSpan(12, 4),
                        FramesPerPacket
                    );

                    accumulator.CopyTo(
                        0,
                        datagram,
                        HeaderBytes,
                        PayloadBytes
                    );
                    accumulator.RemoveRange(
                        0,
                        PayloadBytes
                    );

                    var started = Stopwatch.GetTimestamp();
                    var success = true;
                    SocketError? socketError = null;

                    try
                    {
                        socket.SendTo(
                            datagram,
                            SocketFlags.None,
                            destination
                        );
                    }
                    catch (SocketException exc)
                    {
                        success = false;
                        socketError = exc.SocketErrorCode;
                    }
                    catch
                    {
                        success = false;
                    }

                    var done = Stopwatch.GetTimestamp();

                    ObserveSend(
                        stats,
                        started,
                        done,
                        success,
                        PayloadBytes,
                        socketError
                    );

                    ObserveIntraCallbackSpacing(
                        stats,
                        previousChunkSendDone,
                        done
                    );
                    previousChunkSendDone = done;

                    // Sequence/timestamp advance even when a nonblocking
                    // datagram is dropped. The Android client then sees one
                    // ordinary missing 5 ms audio packet and can conceal it
                    // instead of the host audio thread freezing.
                    sequence++;
                    sampleTimestamp += FramesPerPacket;
                    packetsFromChunk++;
                }

                lock (stats.Gate)
                    stats.MaxPacketsFromOneCallback = Math.Max(
                        stats.MaxPacketsFromOneCallback,
                        packetsFromChunk
                    );
            }
        }
        catch (OperationCanceledException)
        {
        }
        finally
        {
            lock (stats.Gate)
                stats.PartialBytesAtStop = accumulator.Count;
        }
    }

    public static async Task<int> Main(string[] args)
    {
        Dictionary<string, string> parsed;

        try
        {
            parsed = ParseArgs(args);
        }
        catch (Exception exc)
        {
            Console.Error.WriteLine(exc.Message);
            return 2;
        }

        if (!parsed.TryGetValue("pid", out var pidText) ||
            !int.TryParse(pidText, out var targetPid) ||
            targetPid <= 0 ||
            !parsed.TryGetValue("client-ip", out var clientIpText) ||
            !IPAddress.TryParse(clientIpText, out var clientAddress) ||
            clientAddress.AddressFamily != AddressFamily.InterNetwork ||
            !parsed.TryGetValue("port", out var portText) ||
            !int.TryParse(portText, out var port) ||
            port < 1024 ||
            port > 65535 ||
            !parsed.TryGetValue("log", out var logPath) ||
            !parsed.TryGetValue("status", out var statusPath))
        {
            Console.Error.WriteLine(
                "Usage: PrivyHubProcessAudio --pid PID --client-ip IPv4 " +
                "--port PORT --log PATH --status PATH"
            );
            return 2;
        }

        if (!OperatingSystem.IsWindowsVersionAtLeast(10, 0, 19041))
        {
            Console.Error.WriteLine(
                "Windows process loopback requires Windows 10 2004/build 19041 or later."
            );
            return 3;
        }

        var stats = new ProbeStats
        {
            StartedTimestamp = Stopwatch.GetTimestamp()
        };

        var cts = new CancellationTokenSource();
        var queue = new BlockingCollection<CaptureChunk>(
            new ConcurrentQueue<CaptureChunk>(),
            QueueCapacityChunks
        );

        Console.CancelKeyPress += (_, eventArgs) =>
        {
            eventArgs.Cancel = true;
            cts.Cancel();
        };

        var destination = new IPEndPoint(clientAddress, port);
        using var udp = new Socket(
            AddressFamily.InterNetwork,
            SocketType.Dgram,
            ProtocolType.Udp
        );
        udp.Blocking = false;

        WasapiRecorder? recorder = null;
        Exception? startError = null;
        var captureFormat = "";

        try
        {
            recorder = await new WasapiRecorderBuilder()
                .WithProcessLoopback(
                    (uint)targetPid,
                    ProcessLoopbackMode.IncludeTargetProcessTree
                )
                .WithFormat(new WaveFormat(SampleRate, 16, Channels))
                .WithBufferLength(10)
                .BuildAsync();

            captureFormat = recorder.WaveFormat.ToString();

            recorder.DataAvailable += (
                buffer,
                flags,
                devicePosition,
                qpcPosition
            ) =>
            {
                var frames = buffer.Length / (Channels * BytesPerSample);

                ObserveCallback(
                    stats,
                    frames,
                    buffer.Length,
                    flags,
                    devicePosition,
                    qpcPosition
                );

                var copy = buffer.ToArray();
                var chunk = new CaptureChunk(
                    Stopwatch.GetTimestamp(),
                    devicePosition,
                    qpcPosition,
                    (int)flags,
                    copy
                );

                if (!queue.TryAdd(chunk))
                {
                    lock (stats.Gate)
                    {
                        stats.QueueDroppedChunks++;
                        stats.QueueDroppedBytes += copy.Length;
                    }
                }
                else
                {
                    lock (stats.Gate)
                        stats.QueueMaxDepth = Math.Max(
                            stats.QueueMaxDepth,
                            queue.Count
                        );
                }
            };

            recorder.RecordingStopped += (_, eventArgs) =>
            {
                if (eventArgs.Exception is not null)
                {
                    lock (stats.Gate)
                        stats.RecordingStoppedError =
                            eventArgs.Exception.ToString();
                }

                cts.Cancel();
            };

            recorder.StartRecording();
        }
        catch (Exception exc)
        {
            startError = exc;
        }

        if (startError is not null || recorder is null)
        {
            var error = startError?.ToString() ?? "Recorder was not created.";
            WriteJsonAtomic(
                statusPath,
                BuildStatus(
                    stats,
                    targetPid,
                    clientIpText,
                    port,
                    logPath,
                    ready: false,
                    final: true,
                    error,
                    captureFormat
                )
            );
            WriteJsonAtomic(
                logPath,
                BuildStatus(
                    stats,
                    targetPid,
                    clientIpText,
                    port,
                    logPath,
                    ready: false,
                    final: true,
                    error,
                    captureFormat
                )
            );
            Console.Error.WriteLine(error);
            return 4;
        }

        WriteJsonAtomic(
            statusPath,
            BuildStatus(
                stats,
                targetPid,
                clientIpText,
                port,
                logPath,
                ready: true,
                final: false,
                error: null,
                captureFormat
            )
        );

        var senderTask = Task.Run(
            () => SenderLoop(
                queue,
                stats,
                udp,
                destination,
                cts.Token
            )
        );

        var statusTask = Task.Run(async () =>
        {
            while (!cts.IsCancellationRequested)
            {
                try
                {
                    await Task.Delay(
                        1000,
                        cts.Token
                    );
                }
                catch (OperationCanceledException)
                {
                    break;
                }

                try
                {
                    WriteJsonAtomic(
                        statusPath,
                        BuildStatus(
                            stats,
                            targetPid,
                            clientIpText,
                            port,
                            logPath,
                            ready: true,
                            final: false,
                            error: null,
                            captureFormat
                        )
                    );
                }
                catch
                {
                }
            }
        });

        try
        {
            while (!cts.IsCancellationRequested)
                await Task.Delay(100, cts.Token);
        }
        catch (OperationCanceledException)
        {
        }

        try
        {
            recorder.StopRecording();
            await recorder.DisposeAsync();
        }
        catch (Exception exc)
        {
            lock (stats.Gate)
                stats.StopError = exc.ToString();
        }

        queue.CompleteAdding();

        try
        {
            await senderTask;
        }
        catch
        {
        }

        try
        {
            await statusTask;
        }
        catch
        {
        }

        var finalPayload = BuildStatus(
            stats,
            targetPid,
            clientIpText,
            port,
            logPath,
            ready: false,
            final: true,
            error: null,
            captureFormat
        );

        WriteJsonAtomic(logPath, finalPayload);
        WriteJsonAtomic(statusPath, finalPayload);

        return 0;
    }
}
