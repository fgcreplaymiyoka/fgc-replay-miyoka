IMAGE_NAME_ANALYZER := miyoka-replay-analyzer
IMAGE_NAME_VIEWER := miyoka-replay-viewer
DOCKER_FILE_ANALYZER := container_images/analyzer/Dockerfile
DOCKER_FILE_VIEWER := container_images/viewer/Dockerfile


# Create a config file
config:
	cp config.yaml.example config.yaml

# Build the Docker image
build-analyzer:
	docker buildx build --platform linux/amd64 -t $(IMAGE_NAME_ANALYZER) -f $(DOCKER_FILE_ANALYZER) .

build-viewer:
	docker buildx build --platform linux/amd64 -t $(IMAGE_NAME_VIEWER) -f $(DOCKER_FILE_VIEWER) .

# Clean up the Docker image
clean:
	docker rmi $(IMAGE_NAME_ANALYZER)

upload_replay:
	poetry run python miyoka/replay-uploader.py

screenshot:
	poetry run python miyoka/libs/screenshot.py

# Run frame-analyzer.py with poetry
analyze:
	poetry run python miyoka/replay-analyzer.py

# Analyze using the Docker image
analyze-in-docker:
	docker run \
		--rm \
		--name miyoka-analyzer \
		-v "$(HOME)/.config/gcloud/application_default_credentials.json":/gcp/creds.json:ro \
		--env GOOGLE_APPLICATION_CREDENTIALS=/gcp/creds.json \
		$(IMAGE_NAME_ANALYZER)

viewer-dev:
	poetry run streamlit run miyoka/sf6/replay-viewer.py

viewer:
	poetry run streamlit run miyoka/sf6/replay-viewer.py \
		--server.port=8080 \
		--server.address=0.0.0.0 \
		--server.fileWatcherType="none"

viewer-in-docker:
	docker run \
		--rm \
		--name miyoka-viewer \
		-p 8080:8080 \
		-v "$(HOME)/.config/gcloud/application_default_credentials.json":/gcp/creds.json:ro \
		--env GOOGLE_APPLICATION_CREDENTIALS=/gcp/creds.json \
		$(IMAGE_NAME_VIEWER)

group_scenes:
	poetry run python miyoka/group-scenes.py

# Push the Docker image to GCR Artifact Registry
push-analyzer:
	docker tag $(IMAGE_NAME_ANALYZER) $(REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(ARTIFACT_REGISTRY_REPO)/$(IMAGE_NAME_ANALYZER):latest
	docker push $(REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(ARTIFACT_REGISTRY_REPO)/$(IMAGE_NAME_ANALYZER)

push-viewer:
	docker tag $(IMAGE_NAME_VIEWER) $(REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(ARTIFACT_REGISTRY_REPO)/$(IMAGE_NAME_VIEWER):latest
	docker push $(REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(ARTIFACT_REGISTRY_REPO)/$(IMAGE_NAME_VIEWER)

pull-analyzer:
	docker pull $(REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(ARTIFACT_REGISTRY_REPO)/$(IMAGE_NAME_ANALYZER):latest

pull-viewer:
	docker pull $(REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(ARTIFACT_REGISTRY_REPO)/$(IMAGE_NAME_VIEWER):latest

auth-artifact-registry:
	gcloud auth configure-docker $(REGION)-docker.pkg.dev

create-job:
	gcloud run jobs create $(REPLAY_ANALYZER_JOB) \
		--region $(REGION) \
		--image="$(REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(ARTIFACT_REGISTRY_REPO)/$(IMAGE_NAME_ANALYZER):latest" \
		--cpu=1 \
		--memory=2Gi \
		--max-retries=0 \
		--task-timeout=12h \
		--set-env-vars=LOG_STANDARD_OUTPUT=true \
		--set-env-vars=LOG_FILE_OUTPUT=false \
		--set-env-vars=FRAME_SPLITTER_BATCH_SIZE=1000

# update-job:
# 	gcloud run jobs update $(REPLAY_ANALYZER_JOB) \
# 		--region $(REGION) \
# 		--image="$(REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(ARTIFACT_REGISTRY_REPO)/$(IMAGE_NAME_ANALYZER):latest" \
# 		--set-env-vars=LOG_STANDARD_OUTPUT=1 \
# 		--set-env-vars=PRINT_PROGRESS=0

delete-job:
	gcloud run jobs delete $(REPLAY_ANALYZER_JOB) --region $(REGION) --quiet

run-job:
	gcloud run jobs execute $(REPLAY_ANALYZER_JOB) \
		--async \
		--region $(REGION) \
		--update-env-vars=REPLAY_ANALYZER_REPLAY_ID=$(REPLAY_ANALYZER_REPLAY_ID)

# run-all:
# 	./run-all.sh

deploy-viewer-service:
	gcloud run deploy miyoka-viewer \
		--region $(REGION) \
		--allow-unauthenticated \
		--memory=2Gi \
		--image="$(REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(ARTIFACT_REGISTRY_REPO)/$(IMAGE_NAME_VIEWER):latest"

delete-viewer-service:
	gcloud run services delete miyoka-viewer \
		--region $(REGION)

# Deploy the Docker image
deploy-analyzer: build-analyzer push-analyzer
deploy-viewer: build-viewer push-viewer deploy-viewer-service

deploy-and-run: deploy run-job
# deploy-and-run-all: deploy run-all

lint:
	poetry run flake8 miyoka

format:
	poetry run black miyoka

# Setup service accounts and permission grants for generating signed URLs to directly stream the replay video from the GCS.
# https://cloud.google.com/storage/docs/access-control/signing-urls-with-helpers#storage-signed-url-object-python
# 
# The service account's name appears in the email address that is provisioned during creation,
# in the format SERVICE_ACCOUNT_NAME@PROJECT_ID.iam.gserviceaccount.com.
# https://cloud.google.com/iam/docs/service-accounts-create
#
# You also need to enable IAM Service Account Credentials API
# gcloud auth print-access-token --impersonate-service-account=sf6-replay-miyoka@sf6-replay-adviser.iam.gserviceaccount.com
setup-signed-url-generation:
	gcloud iam service-accounts create ${GCP_SIGNED_URL_SERVICE_ACCOUNT_NAME} \
		--description="Service account for Miyoka (e.g. generating authenticated URL to GCS blob)" \
  		--display-name="${GCP_SIGNED_URL_SERVICE_ACCOUNT_NAME}"
	
	# This is needed for letting the SA to read the replay video (mp4).
	gcloud projects add-iam-policy-binding ${GCP_PROJECT} \
		--member="serviceAccount:${GCP_SIGNED_URL_SERVICE_ACCOUNT}" \
		--role="roles/storage.objectViewer"

	# This is needed for iam.serviceAccounts.signBlob permission to let the SA to generate a signed URL.
	gcloud projects add-iam-policy-binding ${GCP_PROJECT} \
		--member="serviceAccount:${GCP_SIGNED_URL_SERVICE_ACCOUNT}" \
		--role="roles/iam.serviceAccountTokenCreator"

	# This is needed for generating an SA access token from the application default credential.
	gcloud projects add-iam-policy-binding ${GCP_PROJECT} \
		--member="serviceAccount:${GCP_DEFAULT_COMPUTE_SERVICE_ACCOUNT}" \
		--role="roles/iam.serviceAccountTokenCreator"

	# This is needed for generating an SA access token from the application default credential.
	gcloud projects add-iam-policy-binding ${GCP_PROJECT} \
		--member="user:${GCP_USER_ACCOUNT}" \
		--role="roles/iam.serviceAccountTokenCreator"
