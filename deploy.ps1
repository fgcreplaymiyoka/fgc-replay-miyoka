Write-Host "Deploying Replay Viewer..."

poetry run python miyoka/export-config-to-dotenv.py

get-content .\.env | foreach {
    $name, $value = $_.split('=')
    set-content env:\$name $value
}

$google_cloud_platform_project_id = $Env:MIYOKA_GCP_PROJECT_ID
$google_cloud_platform_region = $Env:MIYOKA_GCP_REGION
$gcp_replay_viewer_service_account = $Env:MIYOKA_GCP_SERVICE_ACCOUNTS_REPLAY_VIEWER_EMAIL
$secret_id = $Env:MIYOKA_GCP_SECRETS_CONFIG_ID
$service_name = $Env:MIYOKA_GCP_CLOUD_RUN_SERVICE_REPLAY_VIEWER_NAME
$image = $Env:MIYOKA_GCP_CLOUD_RUN_SERVICE_REPLAY_VIEWER_IMAGE
$config_path = Join-Path $PSScriptRoot "config.yaml"

gcloud --quiet secrets delete $secret_id `
    --project ${google_cloud_platform_project_id}

gcloud secrets create $secret_id `
    --project ${google_cloud_platform_project_id} `
    --replication-policy="automatic" `
    --data-file=$config_path

gcloud secrets add-iam-policy-binding $secret_id `
    --project ${google_cloud_platform_project_id} `
    --member="serviceAccount:${gcp_replay_viewer_service_account}" `
    --role="roles/secretmanager.secretAccessor"

# Timeout is set to 30 minutes because streamlit uses websocket and Cloud Run sees it as a long-running HTTP requests.
# Otherwise, the page is reloaded every 5 minutes by default, which restarts a replay randomly.
# See https://cloud.google.com/run/docs/triggering/websockets for more information
gcloud run deploy ${service_name} `
    --project ${google_cloud_platform_project_id} `
    --region ${google_cloud_platform_region} `
    --service-account=${gcp_replay_viewer_service_account} `
    --allow-unauthenticated `
    --memory=1Gi `
    --set-secrets="/etc/secrets/config.yaml=${secret_id}:latest" `
    --set-env-vars="MIYOKA_CONFIG_PATH=/etc/secrets/config.yaml" `
    --image="${image}" `
    --timeout=30m

