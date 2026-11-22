<#
.SYNOPSIS
Start 3D Slicer with the ICH Triage module loaded from this repository.

.DESCRIPTION
Passes the module folder to Slicer with --additional-module-paths, so the
module does not have to be installed or added to the module paths by hand.
Edits in the repository take effect after "Reload" in the module panel or a
Slicer restart.

With -SelfTest, runs the module's self-test headless (--testing
--no-main-window) and exits with Slicer's exit code: 0 when all tests pass.

.PARAMETER SlicerExe
Path to Slicer.exe. Defaults to $env:SLICER_EXE, then to the per-user install
of the pinned Slicer version.

.PARAMETER SelfTest
Run the self-test headless instead of opening the Slicer window.

.PARAMETER SlicerArgs
Extra arguments passed to Slicer as they are.

.EXAMPLE
.\run-slicer-dev.ps1

.EXAMPLE
.\run-slicer-dev.ps1 -SelfTest

.EXAMPLE
.\run-slicer-dev.ps1 -SlicerExe 'D:\Slicer 5.12.4\Slicer.exe'
#>
[CmdletBinding()]
param(
    [string]$SlicerExe,
    [switch]$SelfTest,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$SlicerArgs = @()
)

$ErrorActionPreference = 'Stop'

# Pinned Slicer version; keep in step with the module README.
$SlicerVersion = '5.12.4'
$ModuleName = 'ICHTriage'
$ModuleDir = (Resolve-Path (Join-Path $PSScriptRoot "..\$ModuleName")).Path

function Find-SlicerExe {
    if ($SlicerExe) { return $SlicerExe }
    if ($env:SLICER_EXE) { return $env:SLICER_EXE }
    # Default per-user location of the official installer (NSIS, "NA-MIC" folder).
    return Join-Path $env:LOCALAPPDATA "NA-MIC\Slicer $SlicerVersion\Slicer.exe"
}

function Format-Argument([string]$Value) {
    # Start-Process on Windows PowerShell 5.1 joins arguments with spaces and
    # does not quote them, so quote anything with spaces or quotes here.
    if ($Value -match '[\s"]') { return '"' + ($Value -replace '"', '\"') + '"' }
    return $Value
}

$exe = Find-SlicerExe
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    $message = @"
Slicer.exe not found at: $exe
Install 3D Slicer $SlicerVersion (see services/slicer-ich-triage/README.md),
or pass -SlicerExe <path>, or set the SLICER_EXE environment variable.
"@
    $Host.UI.WriteErrorLine($message)
    exit 2
}

$arguments = @('--additional-module-paths', $ModuleDir)

if ($SelfTest) {
    # Python string literal for the module folder: forward slashes, no quotes.
    $pyPath = $ModuleDir -replace '\\', '/'
    if ($pyPath -match "['""]") {
        $Host.UI.WriteErrorLine("The module path contains a quote, which the self-test command cannot pass: $ModuleDir")
        exit 2
    }
    $pythonCode = "import slicer.testing; slicer.testing.runUnitTest(['$pyPath'], '$ModuleName')"
    $arguments = @('--no-splash', '--testing', '--no-main-window') + $arguments + @('--python-code', $pythonCode)
}
$arguments += $SlicerArgs

$argumentLine = ($arguments | ForEach-Object { Format-Argument $_ }) -join ' '
Write-Host "Slicer:  $exe"
Write-Host "Module:  $ModuleDir"

if (-not $SelfTest) {
    Start-Process -FilePath $exe -ArgumentList $argumentLine | Out-Null
    Write-Host "Slicer is starting. Open the module from the module list: ICH > ICH Triage."
    exit 0
}

# Slicer is a GUI application: wait for it explicitly and read its exit code.
$logFile = Join-Path ([System.IO.Path]::GetTempPath()) "ichtriage-selftest-$PID.log"
$errFile = "$logFile.err"
Write-Host "Running $ModuleName self-test headless..."
$process = Start-Process -FilePath $exe -ArgumentList $argumentLine -Wait -PassThru -NoNewWindow `
    -RedirectStandardOutput $logFile -RedirectStandardError $errFile
foreach ($file in @($logFile, $errFile)) {
    if (Test-Path -LiteralPath $file) {
        Get-Content -LiteralPath $file | Write-Host
        Remove-Item -LiteralPath $file -Force
    }
}
if ($process.ExitCode -eq 0) {
    Write-Host "Self-test passed."
} else {
    Write-Host "Self-test failed (Slicer exit code $($process.ExitCode))."
}
exit $process.ExitCode
