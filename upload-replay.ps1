Write-Host "Running replay uploader..."

$game_process_name = "Street Fighter 6"
$is_game_running = Get-Process -Name $game_process_name -ErrorAction SilentlyContinue

if ($is_game_running -eq $null) {
    Write-Host "Game is not running. Starting Game..."
    Start-Process -FilePath "steam://rungameid/1364780"
    Start-Sleep -Seconds 10
} else {
    Write-Host "Game is already running."
}

$obs_process_name = "obs64"
$is_obs_running = Get-Process -Name $obs_process_name -ErrorAction SilentlyContinue

if ($is_obs_running -eq $null) {
    Write-Host "OBS Studio is not running. Starting OBS Studio..."
    Start-Process -FilePath "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\OBS Studio\OBS Studio (64bit).lnk"
} else {
    Write-Host "OBS Studio is already running."
}

poetry run python miyoka/customize-screen.py change

if ($LastExitCode -ne 0) {
    Write-Host "Failed to change the screen resolution. LastExitCode: $LastExitCode. Exiting..."
    exit
}

poetry run python miyoka/replay-uploader.py

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
