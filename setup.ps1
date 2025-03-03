Write-Host "Setting up Miyoka..."

if (Test-Path "./config.yaml") {
    Remove-Item "./config.yaml"
}

Write-Host "Creating config file..."
Copy-Item -Path "./config.yaml.example" -Destination "./config.yaml"

$game_name = Read-Host "Enter your fighting game name.  Supported games: [sf6]"

if ($game_name -eq "sf6") {
    $game_window_name = "Street Fighter 6"
    $original_language = "en"
    $original_quality = "Low"
    $original_display_mode = "BorderlessWindowed"
    $game_extra = @"
original_language: $original_language
    original_quality: $original_quality
    original_display_mode: $original_display_mode
"@
}

(Get-Content ./config.yaml).Replace('<game.name>', "$game_name") | Set-Content ./config.yaml
(Get-Content ./config.yaml).Replace('<game.window.name>', "$game_window_name") | Set-Content ./config.yaml
(Get-Content ./config.yaml).Replace('<game.window.width>', "$game_window_width") | Set-Content ./config.yaml
(Get-Content ./config.yaml).Replace('<game.extra>', "$game_extra") | Set-Content ./config.yaml

$google_cloud_platform_project_id = Read-Host "Enter your [GCP project ID](https://github.com/fgcreplaymiyoka/fgc-replay-miyoka/blob/main/docs/getting_started.md)"
$google_cloud_platform_region = Read-Host "Enter your [GCP region](https://cloud.google.com/compute/docs/regions-zones). Example: asia-northeast1"
$randomString = -join ((65..90) + (97..122) | Get-Random -Count 8 | ForEach-Object {[char]$_})

(Get-Content ./config.yaml).Replace('<google_cloud_platform.project_id>', "$google_cloud_platform_project_id") | Set-Content ./config.yaml
(Get-Content ./config.yaml).Replace('<google_cloud_platform.region>', "$google_cloud_platform_region") | Set-Content ./config.yaml
(Get-Content ./config.yaml).Replace('<gcp.storages.replays.bucket_name>', "miyoka_replays_$($randomString.ToLower())") | Set-Content ./config.yaml
(Get-Content ./config.yaml).Replace('<gcp.storages.frames.bucket_name>', "miyoka_frames_$($randomString.ToLower())") | Set-Content ./config.yaml

Write-Host "Authenticating for using the gcloud CLI..."
gcloud auth application-default login
gcloud auth application-default set-quota-project $google_cloud_platform_project_id
gcloud config set project $google_cloud_platform_project_id

Write-Host "Enabling services on your GCP project..."
# Set-ExecutionPolicy Unrestricted
# gcloud auth login
# gcloud services list --available --project=$google_cloud_platform_project_id
# https://developers.google.com/apis-explorer/#p/run/v2/
gcloud services enable run.googleapis.com
gcloud services enable vision.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable iamcredentials.googleapis.com
gcloud services enable transcoder.googleapis.com

Write-Host "Creating service accounts on GCP..."
$gcp_replay_viewer_service_account_name = "miyoka-replay-viewer"
$gcp_replay_viewer_service_account = "${gcp_replay_viewer_service_account_name}@${google_cloud_platform_project_id}.iam.gserviceaccount.com"
$gcp_signed_url_service_account_name = "miyoka-signed-url"
$gcp_signed_url_service_account = "${gcp_signed_url_service_account_name}@${google_cloud_platform_project_id}.iam.gserviceaccount.com"

gcloud iam service-accounts create ${gcp_replay_viewer_service_account_name} `
    --description="Service account for Miyoka Replay Viewer" `
    --display-name="${gcp_replay_viewer_service_account_name}"

# Setup service accounts and permission grants for generating signed URLs to directly stream the replay video from the GCS.
# https://cloud.google.com/storage/docs/access-control/signing-urls-with-helpers#storage-signed-url-object-python
gcloud iam service-accounts create ${gcp_signed_url_service_account_name} `
    --description="Service account for Miyoka Signed URL Generator" `
    --display-name="${gcp_signed_url_service_account_name}"

# This is needed for basic operational resource access in the Cloud Run instance.
gcloud projects add-iam-policy-binding ${google_cloud_platform_project_id} `
    --member="serviceAccount:${gcp_replay_viewer_service_account}" `
    --role="roles/editor"

# This is needed for generating an SA access token from the replay viewer service account.
gcloud projects add-iam-policy-binding ${google_cloud_platform_project_id} `
    --member="serviceAccount:${gcp_replay_viewer_service_account}" `
    --role="roles/iam.serviceAccountTokenCreator"

# This is needed for letting the SA to read the replay video (mp4/hls).
gcloud projects add-iam-policy-binding ${google_cloud_platform_project_id} `
    --member="serviceAccount:${gcp_signed_url_service_account}" `
    --role="roles/storage.objectViewer"

# This is needed for iam.serviceAccounts.signBlob permission to let the SA to generate a signed URL.
gcloud projects add-iam-policy-binding ${google_cloud_platform_project_id} `
    --member="serviceAccount:${gcp_signed_url_service_account}" `
    --role="roles/iam.serviceAccountTokenCreator"

(Get-Content ./config.yaml).Replace('<service_accounts.replay_viewer.email>', "$gcp_replay_viewer_service_account") | Set-Content ./config.yaml
(Get-Content ./config.yaml).Replace('<service_accounts.signed_url_generator.email>', "$gcp_signed_url_service_account") | Set-Content ./config.yaml

Write-Host @"
===========================================================================
Congrats! Setup complete!
===========================================================================

A few important notes:

- Do **NOT** share config.yaml with anyone. It contains sensitive information.
"@


