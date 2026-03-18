$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Launcher = Join-Path $RootDir "scripts\run_pipeline.py"

if (-not (Test-Path $Launcher)) {
    Write-Error "Launcher not found: $Launcher"
    exit 1
}

if ($env:VIRTUAL_ENV -and (Get-Command python -ErrorAction SilentlyContinue)) {
    & python $Launcher @args
    exit $LASTEXITCODE
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $Launcher @args
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python $Launcher @args
    exit $LASTEXITCODE
}

Write-Error "Neither 'py' nor 'python' was found on PATH."
exit 1
