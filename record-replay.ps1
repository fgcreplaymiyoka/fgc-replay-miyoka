Write-Host "Running replay uploader..."

# Make UTF8 default encoding in Python, otherwise multi-byte chracters in config.yaml can't be loaded in Windows.
# https://stackoverflow.com/a/50933341
$Env:PYTHONUTF8 = "1"

$obs_process_name = "obs64"
$is_obs_running = Get-Process -Name $obs_process_name -ErrorAction SilentlyContinue

if ($is_obs_running -eq $null) {
    Write-Host "OBS Studio is not running. Starting OBS Studio..."
    Start-Process "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\OBS Studio\OBS Studio (64bit).lnk" "--disable-shutdown-check"
} else {
    Write-Host "OBS Studio is already running."
}

poetry run python miyoka/customize-screen.py change

if ($LastExitCode -ne 0) {
    Write-Host "Failed to change the screen resolution. LastExitCode: $LastExitCode. Exiting..."
    exit
}

poetry run python miyoka/replay-recorder.py

if ($LastExitCode -ne 0) {
    Write-Host "Failed to record replay. LastExitCode: $LastExitCode. Exiting..."
    exit
}

poetry run python miyoka/customize-screen.py restore

if ($LastExitCode -ne 0) {
    Write-Host "Failed to restore the screen resolution. LastExitCode: $LastExitCode. Exiting..."
    exit
}

Write-Host "Stopping OBS..."
Stop-Process -Name $obs_process_name
Write-Host "OBS stopped"
