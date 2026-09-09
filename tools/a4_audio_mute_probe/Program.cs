using System.Buffers.Binary;
using System.Diagnostics;
using System.Text.Json;
using NAudio.CoreAudioApi;
using NAudio.Wave;

internal static class Program
{
    private sealed class StageStats
    {
        private readonly object _gate = new();

        public long Callbacks { get; private set; }
        public long Bytes { get; private set; }
        public long Samples { get; private set; }
        public long SilentFlagCallbacks { get; private set; }
        public double SumSquares { get; private set; }
        public int PeakAbsolute { get; private set; }

        public void Add(
            ReadOnlySpan<byte> buffer,
            AudioClientBufferFlags flags)
        {
            lock (_gate)
            {
                Callbacks++;
                Bytes += buffer.Length;

                if ((flags & AudioClientBufferFlags.Silent) != 0)
                    SilentFlagCallbacks++;

                for (var offset = 0; offset + 1 < buffer.Length; offset += 2)
                {
                    var sample = BinaryPrimitives.ReadInt16LittleEndian(
                        buffer.Slice(offset, 2)
                    );

                    var absolute = Math.Abs((int)sample);
                    PeakAbsolute = Math.Max(PeakAbsolute, absolute);
                    SumSquares += (double)sample * sample;
                    Samples++;
                }
            }
        }

        public object Snapshot()
        {
            lock (_gate)
            {
                var rms = Samples > 0
                    ? Math.Sqrt(SumSquares / Samples)
                    : 0.0;

                return new
                {
                    callbacks = Callbacks,
                    bytes = Bytes,
                    samples = Samples,
                    silent_flag_callbacks = SilentFlagCallbacks,
                    rms_pcm16 = Math.Round(rms, 3),
                    rms_normalized = Math.Round(rms / 32768.0, 6),
                    peak_pcm16 = PeakAbsolute,
                    peak_normalized = Math.Round(
                        PeakAbsolute / 32768.0,
                        6
                    ),
                };
            }
        }

        public double Rms()
        {
            lock (_gate)
            {
                return Samples > 0
                    ? Math.Sqrt(SumSquares / Samples)
                    : 0.0;
            }
        }

        public long SampleCount()
        {
            lock (_gate)
                return Samples;
        }
    }

    private sealed record SessionMuteTarget(
        AudioSessionControl Session,
        bool OriginalMute
    );

    private sealed class SessionInventory : IDisposable
    {
        public List<MMDevice> Devices { get; } = new();
        public List<SessionMuteTarget> Targets { get; } = new();

        public void Restore()
        {
            foreach (var target in Targets)
            {
                try
                {
                    target.Session.SimpleAudioVolume.Mute =
                        target.OriginalMute;
                }
                catch
                {
                }
            }
        }

        public void Dispose()
        {
            Restore();

            foreach (var target in Targets)
            {
                try
                {
                    target.Session.Dispose();
                }
                catch
                {
                }
            }

            foreach (var device in Devices)
            {
                try
                {
                    device.Dispose();
                }
                catch
                {
                }
            }
        }
    }

    private static string ConfiguredRetroArch(string root)
    {
        var path = Path.Combine(
            root,
            "companion",
            "games",
            "config",
            "emulators.json"
        );

        using var document = JsonDocument.Parse(
            File.ReadAllText(path)
        );

        var relative = document.RootElement
            .GetProperty("retroarch")
            .GetProperty("executable")
            .GetString();

        if (string.IsNullOrWhiteSpace(relative))
            throw new InvalidOperationException(
                "RetroArch executable is not configured."
            );

        return Path.GetFullPath(
            Path.Combine(root, relative)
        );
    }

    private static Process FindRetroArch(
        string configuredExecutable)
    {
        var expectedName = Path.GetFileNameWithoutExtension(
            configuredExecutable
        );

        var matches = new List<Process>();

        foreach (var process in Process.GetProcessesByName(expectedName))
        {
            try
            {
                var actual = process.MainModule?.FileName;

                if (
                    !string.IsNullOrWhiteSpace(actual)
                    && string.Equals(
                        Path.GetFullPath(actual),
                        configuredExecutable,
                        StringComparison.OrdinalIgnoreCase
                    )
                )
                {
                    matches.Add(process);
                }
                else
                {
                    process.Dispose();
                }
            }
            catch
            {
                process.Dispose();
            }
        }

        if (matches.Count != 1)
        {
            foreach (var process in matches)
                process.Dispose();

            throw new InvalidOperationException(
                $"Expected exactly one running project-managed RetroArch process; found {matches.Count}."
            );
        }

        return matches[0];
    }

    private static SessionInventory FindAudioSessions(
        int pid)
    {
        var inventory = new SessionInventory();
        using var enumerator = new MMDeviceEnumerator();
        using var devices = enumerator.EnumerateAudioEndPoints(
            DataFlow.Render,
            DeviceState.Active
        );

        for (var deviceIndex = 0;
             deviceIndex < devices.Count;
             deviceIndex++)
        {
            var device = devices[deviceIndex];
            inventory.Devices.Add(device);

            var sessions =
                device.AudioSessionManager.Sessions;

            for (var sessionIndex = 0;
                 sessionIndex < sessions.Count;
                 sessionIndex++)
            {
                AudioSessionControl? session = null;

                try
                {
                    session = sessions[sessionIndex];

                    if ((int)session.GetProcessID != pid)
                    {
                        session.Dispose();
                        session = null;
                        continue;
                    }

                    inventory.Targets.Add(
                        new SessionMuteTarget(
                            session,
                            session.SimpleAudioVolume.Mute
                        )
                    );

                    session = null;
                }
                finally
                {
                    session?.Dispose();
                }
            }
        }

        if (inventory.Targets.Count == 0)
        {
            inventory.Dispose();

            throw new InvalidOperationException(
                "No active Windows render audio session owned by RetroArch was found."
            );
        }

        return inventory;
    }

    private static async Task DelayStage(
        int milliseconds)
    {
        await Task.Delay(milliseconds);
    }

    private static Dictionary<string, string> ParseArgs(
        string[] args)
    {
        var parsed = new Dictionary<string, string>(
            StringComparer.OrdinalIgnoreCase
        );

        for (var index = 0; index < args.Length; index++)
        {
            var key = args[index];

            if (!key.StartsWith("--", StringComparison.Ordinal))
                throw new ArgumentException(
                    $"Unexpected argument: {key}"
                );

            if (index + 1 >= args.Length)
                throw new ArgumentException(
                    $"Missing value for {key}"
                );

            parsed[key[2..]] = args[++index];
        }

        return parsed;
    }

    public static async Task<int> Main(string[] args)
    {
        try
        {
            var parsed = ParseArgs(args);

            if (
                !parsed.TryGetValue("root", out var rootText)
                || string.IsNullOrWhiteSpace(rootText)
            )
            {
                Console.Error.WriteLine(
                    "Usage: A4AudioMuteProbe --root PROJECT_ROOT"
                );
                return 2;
            }

            var root = Path.GetFullPath(rootText);
            var output = Path.Combine(
                root,
                "logs",
                "games",
                "a4_audio_local_mute_probe.json"
            );
            var outputText = Path.Combine(
                root,
                "logs",
                "games",
                "a4_audio_local_mute_probe.txt"
            );

            var configuredExecutable =
                ConfiguredRetroArch(root);

            using var retroarch =
                FindRetroArch(configuredExecutable);

            using var inventory =
                FindAudioSessions(retroarch.Id);

            var baseline = new StageStats();
            var muted = new StageStats();
            var restored = new StageStats();

            var stage = -1;

            await using var recorder =
                await new WasapiRecorderBuilder()
                    .WithProcessLoopback(
                        (uint)retroarch.Id,
                        ProcessLoopbackMode
                            .IncludeTargetProcessTree
                    )
                    .WithFormat(
                        new WaveFormat(
                            48_000,
                            16,
                            2
                        )
                    )
                    .WithBufferLength(10)
                    .BuildAsync();

            recorder.DataAvailable += (
                buffer,
                flags,
                _,
                _
            ) =>
            {
                switch (Volatile.Read(ref stage))
                {
                    case 0:
                        baseline.Add(buffer, flags);
                        break;

                    case 1:
                        muted.Add(buffer, flags);
                        break;

                    case 2:
                        restored.Add(buffer, flags);
                        break;
                }
            };

            recorder.StartRecording();

            Console.WriteLine(
                "A4 local-audio mute probe"
            );
            Console.WriteLine(
                "Keep the game producing continuous audio during this test."
            );

            // Warm-up so process-loopback activation does not pollute
            // the baseline.
            await DelayStage(750);

            Console.WriteLine(
                "Stage 1/3: baseline process-loopback audio..."
            );
            Volatile.Write(ref stage, 0);
            await DelayStage(2500);

            if (
                baseline.SampleCount() <= 0
                || baseline.Rms() < 32.0
            )
            {
                throw new InvalidOperationException(
                    "Baseline audio was effectively silent. Run the probe while the game has continuous music/audio."
                );
            }

            Console.WriteLine(
                "Stage 2/3: muting only RetroArch's Windows audio session..."
            );

            foreach (var target in inventory.Targets)
            {
                target.Session.SimpleAudioVolume.Mute =
                    true;
            }

            Volatile.Write(ref stage, 1);
            await DelayStage(3000);

            Console.WriteLine(
                "Stage 3/3: restoring RetroArch's original local mute state..."
            );

            inventory.Restore();

            Volatile.Write(ref stage, 2);
            await DelayStage(2500);

            Volatile.Write(ref stage, -1);

            recorder.StopRecording();

            var baselineRms = baseline.Rms();
            var mutedRms = muted.Rms();
            var restoredRms = restored.Rms();

            var mutedRatio =
                mutedRms / Math.Max(1.0, baselineRms);

            var restoredRatio =
                restoredRms / Math.Max(1.0, baselineRms);

            string verdict;
            string interpretation;

            if (
                muted.SampleCount() <= 0
                || mutedRatio <= 0.10
            )
            {
                verdict =
                    "LOCAL_MUTE_ALSO_MUTES_PROCESS_LOOPBACK";
                interpretation =
                    "Muting RetroArch locally also removed nearly all audio from process-loopback capture. Per-session mute is not suitable for production streaming on this host.";
            }
            else if (
                mutedRatio >= 0.60
                && restoredRatio >= 0.35
            )
            {
                verdict =
                    "LOCAL_MUTE_PRESERVES_PROCESS_LOOPBACK";
                interpretation =
                    "RetroArch's local Windows audio session can be muted while process-loopback still receives substantial game audio. This is suitable for the A4 production design.";
            }
            else
            {
                verdict =
                    "LOCAL_MUTE_RESULT_AMBIGUOUS";
                interpretation =
                    "Process-loopback remained active, but signal level changed enough that this run is not decisive. Repeat during steady in-game music.";
            }

            var result = new
            {
                schema =
                    "privyhub_a4_local_audio_mute_probe_v1",
                verdict,
                interpretation,
                retroarch_pid = retroarch.Id,
                matched_audio_sessions =
                    inventory.Targets.Count,
                session_original_mute_states =
                    inventory.Targets
                        .Select(
                            target =>
                                target.OriginalMute
                        )
                        .ToArray(),
                baseline = baseline.Snapshot(),
                local_muted = muted.Snapshot(),
                restored = restored.Snapshot(),
                muted_to_baseline_rms_ratio =
                    Math.Round(mutedRatio, 4),
                restored_to_baseline_rms_ratio =
                    Math.Round(restoredRatio, 4),
                original_session_mute_restored = true,
                privacy =
                    "No network addresses are collected.",
            };

            Directory.CreateDirectory(
                Path.GetDirectoryName(output)!
            );

            var json = JsonSerializer.Serialize(
                result,
                new JsonSerializerOptions
                {
                    WriteIndented = true,
                }
            );

            File.WriteAllText(
                output,
                json + Environment.NewLine
            );

            var text = string.Join(
                Environment.NewLine,
                new[]
                {
                    "PrivyHub A4 local-audio mute probe",
                    "",
                    $"Verdict: {verdict}",
                    interpretation,
                    "",
                    $"Matched RetroArch audio sessions: {inventory.Targets.Count}",
                    $"Muted/baseline RMS ratio: {Math.Round(mutedRatio, 4)}",
                    $"Restored/baseline RMS ratio: {Math.Round(restoredRatio, 4)}",
                    "",
                    "Baseline:",
                    JsonSerializer.Serialize(
                        baseline.Snapshot(),
                        new JsonSerializerOptions
                        {
                            WriteIndented = true,
                        }
                    ),
                    "",
                    "RetroArch locally muted:",
                    JsonSerializer.Serialize(
                        muted.Snapshot(),
                        new JsonSerializerOptions
                        {
                            WriteIndented = true,
                        }
                    ),
                    "",
                    "Original mute state restored:",
                    JsonSerializer.Serialize(
                        restored.Snapshot(),
                        new JsonSerializerOptions
                        {
                            WriteIndented = true,
                        }
                    ),
                    "",
                    "No network addresses are collected.",
                    "",
                }
            );

            File.WriteAllText(
                outputText,
                text
            );

            Console.WriteLine();
            Console.WriteLine(
                $"Verdict: {verdict}"
            );
            Console.WriteLine(
                interpretation
            );
            Console.WriteLine();
            Console.WriteLine(
                "Saved: logs\\games\\a4_audio_local_mute_probe.txt"
            );

            return 0;
        }
        catch (Exception exc)
        {
            Console.Error.WriteLine(
                $"ERROR: {exc.Message}"
            );
            return 1;
        }
    }
}
