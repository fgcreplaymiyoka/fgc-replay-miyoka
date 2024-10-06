Write-Host "Setting up Miyoka..."

# Read-Host -Prompt "Press Enter to exit"

# Start-Sleep -Seconds 1.5

# Write-Host "Install python dependencies..."
# poetry lock --no-update
# poetry install --with win

Remove-Item "./config.yaml"

if (-not (Test-Path "./config.yaml")) {
    Write-Host "Creating config file..."
    Copy-Item -Path "./config.yaml.example" -Destination "./config.yaml"
}

# $game = Read-Host @"
# Select the fighting game:
# Available options:
#     - 'sf6'

# "@

# $google_cloud_platform_project_id = Read-Host "Enter your GCP project ID"
# $google_cloud_platform_region = Read-Host "Enter your GCP region"

Write-Host "Authenticating for using the gcloud CLI..."
gcloud auth application-default login
gcloud auth application-default set-quota-project $google_cloud_platform_project_id
gcloud config set project $google_cloud_platform_project_id

# Set-ExecutionPolicy Unrestricted
# gcloud auth login
# gcloud services list --available --project=$google_cloud_platform_project_id
gcloud services enable vision.googleapis.com

Write-Host @"
===========================================================================
Congrats! Setup complete!
===========================================================================

A few important notes:

- Do **NOT** share config.yaml with anyone. It contains sensitive information.
"@


