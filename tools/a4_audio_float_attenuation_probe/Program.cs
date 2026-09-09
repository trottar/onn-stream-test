using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;
using NAudio.CoreAudioApi;
using NAudio.Wave;

internal static class Program
{
    private sealed class FloatStageStats
    {
        private readonly object _gate = new();

        public long Callbacks { get; private set; }
        public long Samples { get; private set; }
        public long NonFiniteSamples { get; private set; }
        public double SumSquares { get; private set; }
        public float PeakAbsolute { get; private set; }

        public void Add(ReadOnlySpan<byte> buffer)
        {
            var samples = MemoryMarshal.Cast<byte, float>(buffer);

            lock (_gate)
            {
                Callbacks++;

                foreach (var sample in samples)
                {
                    if (!float.IsFinite(sample))
                    {
                        NonFiniteSamples++;
                        continue;
                    }

                    var absolute = Math.Abs(sample);
                    PeakAbsolute = Math.Max(PeakAbsolute, absolute);
                    SumSquares += (double)sample * sample;
                    Samples++;
                }
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
                    samples = Samples,
                    non_finite_samples = NonFiniteSamples,
                    rms_float = Math.Round(rms, 9),
                    peak_float = Math.Round(PeakAbsolute, 9),
                };
            }
        }
    }

    private sealed record SessionTarget(
        AudioSessionControl Session,
        float OriginalVolume,
        bool OriginalMute
    );

    private sealed class SessionInventory : IDisposable
    {
        public List<MMDevice> Devices { get; } = new();
        public List<SessionTarget> Targets { get; } = new();

        public void SetRelativeVolume(float factor)
        {
            foreach (var target in Targets)
            {
                target.Session.SimpleAudioVolume.Mute = false;
                target.Session.SimpleAudioVolume.Volume =
                    Math.Clamp(
                        target.OriginalVolume * factor,
                        0.0f,
                        1.0f
                    );
            }
        }

        public void Restore()
        {
            foreach (var target in Targets)
            {
                try
                {
                    target.Session.SimpleAudioVolume.Volume =
                        target.OriginalVolume;
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

    private static string ConfiguredRetroArch(
        string root)
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
        var expectedName =
            Path.GetFileNameWithoutExtension(
                configuredExecutable
            );

        var matches = new List<Process>();

        foreach (
            var process
            in Process.GetProcessesByName(
                expectedName
            )
        )
        {
            try
            {
                var actual =
                    process.MainModule?.FileName;

                if (
                    !string.IsNullOrWhiteSpace(
                        actual
                    )
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
        var inventory =
            new SessionInventory();

        using var enumerator =
            new MMDeviceEnumerator();

        using var devices =
            enumerator.EnumerateAudioEndPoints(
                DataFlow.Render,
                DeviceState.Active
            );

        for (
            var deviceIndex = 0;
            deviceIndex < devices.Count;
            deviceIndex++
        )
        {
            var device =
                devices[deviceIndex];

            inventory.Devices.Add(
                device
            );

            var sessions =
                device.AudioSessionManager.Sessions;

            for (
                var sessionIndex = 0;
                sessionIndex < sessions.Count;
                sessionIndex++
            )
            {
                AudioSessionControl? session =
                    null;

                try
                {
                    session =
                        sessions[sessionIndex];

                    if (
                        (int)session.GetProcessID
                        != pid
                    )
                    {
                        session.Dispose();
                        session = null;
                        continue;
                    }

                    var volume =
                        session.SimpleAudioVolume.Volume;

                    var mute =
                        session.SimpleAudioVolume.Mute;

                    if (mute)
                    {
                        throw new InvalidOperationException(
                            "RetroArch's audio session is already muted; restore normal local audio before running this probe."
                        );
                    }

                    if (volume <= 0.0f)
                    {
                        throw new InvalidOperationException(
                            "RetroArch's audio-session volume is zero; restore normal local audio before running this probe."
                        );
                    }

                    inventory.Targets.Add(
                        new SessionTarget(
                            session,
                            volume,
                            mute
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

    private static object StageResult(
        string label,
        double factor,
        FloatStageStats stats,
        double baselineRms)
    {
        var rms = stats.Rms();
        var observedRatio =
            baselineRms > 0.0
                ? rms / baselineRms
                : 0.0;

        var compensationFactor =
            factor > 0.0
                ? 1.0 / factor
                : 0.0;

        var compensatedRms =
            rms * compensationFactor;

        var compensatedToBaseline =
            baselineRms > 0.0
                ? compensatedRms / baselineRms
                : 0.0;

        return new
        {
            label,
            requested_relative_volume =
                factor,
            stats = stats.Snapshot(),
            observed_rms_ratio =
                Math.Round(
                    observedRatio,
                    6
                ),
            ideal_rms_ratio =
                factor,
            compensation_factor =
                compensationFactor,
            compensated_rms =
                Math.Round(
                    compensatedRms,
                    9
                ),
            compensated_to_baseline_ratio =
                Math.Round(
                    compensatedToBaseline,
                    6
                ),
        };
    }

    public static async Task<int> Main(
        string[] args)
    {
        try
        {
            var parsed = ParseArgs(args);

            if (
                !parsed.TryGetValue(
                    "root",
                    out var rootText
                )
                || string.IsNullOrWhiteSpace(
                    rootText
                )
            )
            {
                Console.Error.WriteLine(
                    "Usage: A4FloatAttenuationProbe --root PROJECT_ROOT"
                );
                return 2;
            }

            var root =
                Path.GetFullPath(rootText);

            var configuredExecutable =
                ConfiguredRetroArch(root);

            using var retroarch =
                FindRetroArch(
                    configuredExecutable
                );

            using var inventory =
                FindAudioSessions(
                    retroarch.Id
                );

            var baseline =
                new FloatStageStats();
            var tenPercent =
                new FloatStageStats();
            var onePercent =
                new FloatStageStats();
            var pointOnePercent =
                new FloatStageStats();
            var restored =
                new FloatStageStats();

            var stage = -1;

            await using var recorder =
                await new WasapiRecorderBuilder()
                    .WithProcessLoopback(
                        (uint)retroarch.Id,
                        ProcessLoopbackMode
                            .IncludeTargetProcessTree
                    )
                    .WithFormat(
                        WaveFormat
                            .CreateIeeeFloatWaveFormat(
                                48_000,
                                2
                            )
                    )
                    .WithBufferLength(10)
                    .BuildAsync();

            recorder.DataAvailable += (
                buffer,
                _,
                _,
                _
            ) =>
            {
                switch (
                    Volatile.Read(
                        ref stage
                    )
                )
                {
                    case 0:
                        baseline.Add(buffer);
                        break;
                    case 1:
                        tenPercent.Add(buffer);
                        break;
                    case 2:
                        onePercent.Add(buffer);
                        break;
                    case 3:
                        pointOnePercent.Add(buffer);
                        break;
                    case 4:
                        restored.Add(buffer);
                        break;
                }
            };

            recorder.StartRecording();

            Console.WriteLine(
                "PrivyHub A4 float attenuation/recovery probe"
            );
            Console.WriteLine(
                "Keep steady game music/audio playing for the entire test."
            );

            await Task.Delay(750);

            Console.WriteLine(
                "Stage 1/5: normal local volume baseline..."
            );
            Volatile.Write(
                ref stage,
                0
            );
            await Task.Delay(2200);

            var baselineRms =
                baseline.Rms();

            if (
                baseline.SampleCount() <= 0
                || baselineRms < 0.001
            )
            {
                throw new InvalidOperationException(
                    "Baseline process-loopback signal was too quiet. Run this during steady game music."
                );
            }

            Console.WriteLine(
                "Stage 2/5: RetroArch local volume = 10% of original..."
            );
            inventory.SetRelativeVolume(
                0.10f
            );
            Volatile.Write(
                ref stage,
                1
            );
            await Task.Delay(2200);

            Console.WriteLine(
                "Stage 3/5: RetroArch local volume = 1% of original..."
            );
            inventory.SetRelativeVolume(
                0.01f
            );
            Volatile.Write(
                ref stage,
                2
            );
            await Task.Delay(2200);

            Console.WriteLine(
                "Stage 4/5: RetroArch local volume = 0.1% of original..."
            );
            inventory.SetRelativeVolume(
                0.001f
            );
            Volatile.Write(
                ref stage,
                3
            );
            await Task.Delay(2500);

            Console.WriteLine(
                "Stage 5/5: restoring exact original volume..."
            );
            inventory.Restore();
            Volatile.Write(
                ref stage,
                4
            );
            await Task.Delay(2200);

            Volatile.Write(
                ref stage,
                -1
            );

            recorder.StopRecording();

            var tenObserved =
                tenPercent.Rms()
                / baselineRms;
            var oneObserved =
                onePercent.Rms()
                / baselineRms;
            var tinyObserved =
                pointOnePercent.Rms()
                / baselineRms;
            var restoredObserved =
                restored.Rms()
                / baselineRms;

            var tenLinearity =
                tenObserved / 0.10;
            var oneLinearity =
                oneObserved / 0.01;
            var tinyLinearity =
                tinyObserved / 0.001;

            string verdict;
            string interpretation;

            if (
                pointOnePercent.SampleCount()
                    > 0
                && tinyLinearity >= 0.65
                && tinyLinearity <= 1.35
                && restoredObserved >= 0.50
            )
            {
                verdict =
                    "FLOAT_ATTENUATION_RECOVERY_VIABLE";
                interpretation =
                    "At 0.1% local RetroArch volume, process-loopback float audio still scales closely enough to the requested attenuation that PrivyHub can restore the TV signal digitally while making local game audio effectively inaudible.";
            }
            else if (
                onePercent.SampleCount()
                    > 0
                && oneLinearity >= 0.65
                && oneLinearity <= 1.35
                && restoredObserved >= 0.50
            )
            {
                verdict =
                    "FLOAT_ATTENUATION_RECOVERY_VIABLE_AT_1_PERCENT";
                interpretation =
                    "The 1% local-volume stage remains linearly recoverable, but 0.1% does not. PrivyHub can likely suppress local game audio substantially and restore TV gain, though it may not be completely inaudible on very sensitive speakers.";
            }
            else
            {
                verdict =
                    "FLOAT_ATTENUATION_RECOVERY_NOT_VIABLE";
                interpretation =
                    "Per-session attenuation does not remain sufficiently linear at very low local volume on this host, so digital gain restoration is not a safe production solution.";
            }

            var result = new
            {
                schema =
                    "privyhub_a4_float_attenuation_recovery_probe_v1",
                verdict,
                interpretation,
                retroarch_pid =
                    retroarch.Id,
                matched_audio_sessions =
                    inventory.Targets.Count,
                original_session_volumes =
                    inventory.Targets
                        .Select(
                            target =>
                                target.OriginalVolume
                        )
                        .ToArray(),
                capture_format =
                    recorder.WaveFormat
                        .ToString(),
                baseline =
                    StageResult(
                        "baseline",
                        1.0,
                        baseline,
                        baselineRms
                    ),
                ten_percent =
                    StageResult(
                        "10_percent",
                        0.10,
                        tenPercent,
                        baselineRms
                    ),
                one_percent =
                    StageResult(
                        "1_percent",
                        0.01,
                        onePercent,
                        baselineRms
                    ),
                point_one_percent =
                    StageResult(
                        "0.1_percent",
                        0.001,
                        pointOnePercent,
                        baselineRms
                    ),
                restored =
                    StageResult(
                        "restored",
                        1.0,
                        restored,
                        baselineRms
                    ),
                linearity = new
                {
                    ten_percent =
                        Math.Round(
                            tenLinearity,
                            6
                        ),
                    one_percent =
                        Math.Round(
                            oneLinearity,
                            6
                        ),
                    point_one_percent =
                        Math.Round(
                            tinyLinearity,
                            6
                        ),
                    restored_to_baseline =
                        Math.Round(
                            restoredObserved,
                            6
                        ),
                },
                original_volume_restored =
                    true,
                privacy =
                    "No network addresses are collected.",
            };

            var outputDirectory =
                Path.Combine(
                    root,
                    "logs",
                    "games"
                );

            Directory.CreateDirectory(
                outputDirectory
            );

            var jsonOptions =
                new JsonSerializerOptions
                {
                    WriteIndented = true,
                };

            var json =
                JsonSerializer.Serialize(
                    result,
                    jsonOptions
                );

            File.WriteAllText(
                Path.Combine(
                    outputDirectory,
                    "a4_audio_float_attenuation_probe.json"
                ),
                json + Environment.NewLine
            );

            var text = string.Join(
                Environment.NewLine,
                new[]
                {
                    "PrivyHub A4 float attenuation/recovery probe",
                    "",
                    $"Verdict: {verdict}",
                    interpretation,
                    "",
                    $"Matched RetroArch audio sessions: {inventory.Targets.Count}",
                    $"Capture format: {recorder.WaveFormat}",
                    "",
                    "Linearity (1.0 = perfect scaling):",
                    $"  10%:  {Math.Round(tenLinearity, 6)}",
                    $"  1%:   {Math.Round(oneLinearity, 6)}",
                    $"  0.1%: {Math.Round(tinyLinearity, 6)}",
                    $"  restored/baseline: {Math.Round(restoredObserved, 6)}",
                    "",
                    "Baseline:",
                    JsonSerializer.Serialize(
                        baseline.Snapshot(),
                        jsonOptions
                    ),
                    "",
                    "10% local volume:",
                    JsonSerializer.Serialize(
                        tenPercent.Snapshot(),
                        jsonOptions
                    ),
                    "",
                    "1% local volume:",
                    JsonSerializer.Serialize(
                        onePercent.Snapshot(),
                        jsonOptions
                    ),
                    "",
                    "0.1% local volume:",
                    JsonSerializer.Serialize(
                        pointOnePercent.Snapshot(),
                        jsonOptions
                    ),
                    "",
                    "Restored:",
                    JsonSerializer.Serialize(
                        restored.Snapshot(),
                        jsonOptions
                    ),
                    "",
                    "No network addresses are collected.",
                    "",
                }
            );

            File.WriteAllText(
                Path.Combine(
                    outputDirectory,
                    "a4_audio_float_attenuation_probe.txt"
                ),
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
                "Saved: logs\\games\\a4_audio_float_attenuation_probe.txt"
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
