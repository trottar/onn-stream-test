# PrivyHub - Browser/Desktop live source
# Desktop Duplication + VB-CABLE -> HLS
# Resolves paths from this script's location.

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LiveDir = Join-Path $ProjectRoot "media\live"

New-Item `
    -ItemType Directory `
    -Force `
    -Path $LiveDir `
    | Out-Null

$FfmpegCommand = Get-Command ffmpeg.exe -ErrorAction SilentlyContinue

if (-not $FfmpegCommand) {
    $FfmpegCommand = Get-Command ffmpeg -ErrorAction SilentlyContinue
}

if (-not $FfmpegCommand) {
    throw "FFmpeg was not found in PATH."
}

Set-Location $LiveDir

Remove-Item `
    .\stream.m3u8 `
    -ErrorAction SilentlyContinue

Remove-Item `
    .\stream*.ts `
    -ErrorAction SilentlyContinue

Write-Host "PrivyHub Browser/Desktop"
Write-Host "Project root: $ProjectRoot"
Write-Host "HLS output:   $LiveDir"
Write-Host ""

& $FfmpegCommand.Source `
    -f dshow `
    -thread_queue_size 1024 `
    -i 'audio=CABLE Output (VB-Audio Virtual Cable)' `
    -filter_complex 'ddagrab=output_idx=0:framerate=30:video_size=1920x1080,hwdownload,format=bgra[v]' `
    -map '[v]' `
    -map '0:a:0' `
    -c:v libx264 `
    -preset ultrafast `
    -tune zerolatency `
    -b:v 5M `
    -maxrate 5M `
    -bufsize 10M `
    -pix_fmt yuv420p `
    -g 30 `
    -keyint_min 30 `
    -sc_threshold 0 `
    -c:a aac `
    -b:a 192k `
    -ar 48000 `
    -ac 2 `
    -f hls `
    -hls_time 1 `
    -hls_list_size 30 `
    -hls_flags delete_segments+independent_segments+omit_endlist `
    stream.m3u8

exit $LASTEXITCODE
