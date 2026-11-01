# PowerShell HTTP glue client (Windows). Start localhost gateway before running.
# Usage: .\clients\Process-FlexAgX.ps1 -InputFile input.png -OutputFile output.png
param(
    [Parameter(Mandatory=$true)][string]$InputFile,
    [Parameter(Mandatory=$true)][string]$OutputFile,
    [string]$Gateway='http://127.0.0.1:8080',
    [string]$SessionId='powershell-client',
    [int]$FrameIndex=0,
    [double]$FrameTimeMs=16.667
)
$bytes=[System.IO.File]::ReadAllBytes((Resolve-Path $InputFile))
$payload=@{
    session_id=$SessionId
    frame_index=$FrameIndex
    dt_ms=$FrameTimeMs
    image_png_base64=[Convert]::ToBase64String($bytes)
    settings=@{ LocalDetail=20.0 }
} | ConvertTo-Json -Depth 6
$result=Invoke-RestMethod -Method Post -Uri ($Gateway.TrimEnd('/')+'/v1/frame') -ContentType 'application/json' -Body $payload
[System.IO.File]::WriteAllBytes($OutputFile,[Convert]::FromBase64String($result.image_png_base64))
Write-Host "Wrote $OutputFile (mode: $($result.mode))"
