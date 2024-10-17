Write-Host "Deploying Replay Viewer..."

$google_cloud_platform_project_id = "<todo>"
$google_cloud_platform_region = "<todo>"
$gcp_replay_viewer_service_account_name = "<todo>"
$gcp_replay_viewer_service_account = "${gcp_replay_viewer_service_account_name}@${google_cloud_platform_project_id}.iam.gserviceaccount.com"
$secret_id = "<todo>"
$image = "fgcreplaymiyoka/replay-viewer:latest"
$config_path = Join-Path $PSScriptRoot "config.yaml"

gcloud --quiet secrets delete $secret_id

gcloud secrets create $secret_id `
    --replication-policy="automatic" `
    --data-file=$config_path

gcloud secrets add-iam-policy-binding $secret_id `
    --member="serviceAccount:${gcp_replay_viewer_service_account}" `
    --role="roles/secretmanager.secretAccessor"

gcloud run deploy miyoka-viewer `
    --region ${google_cloud_platform_region} `
    --service-account=${gcp_replay_viewer_service_account} `
    --allow-unauthenticated `
    --memory=2Gi `
    --set-secrets="/etc/secrets/config.yaml=${secret_id}:latest" `
    --set-env-vars="MIYOKA_CONFIG_PATH=/etc/secrets/config.yaml" `
    --image="${image}"

