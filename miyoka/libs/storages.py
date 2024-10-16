from pathlib import Path
import contextlib
from logging import Logger
import os
import json
import pathlib
import threading
import time
import zipfile
import datetime
from google.cloud import storage
from google.cloud.storage import Client
from google.auth import impersonated_credentials
from google.auth.credentials import TokenState
from google.cloud.exceptions import Conflict
import google.auth.transport.requests


def init_storage_client(project_id: str):
    return storage.Client(project=project_id)


class BaseStorageClient:
    def __init__(
        self,
        bucket_name: str,
        location: str,
        storage_client: storage.Client,
        logger: Logger,
    ):
        self.bucket_name = bucket_name
        self.storage_client = storage_client
        self.location = location
        self.logger = logger

        self.ensure_bucket()

    def ensure_bucket(self):
        try:
            self.storage_client.create_bucket(
                self.bucket_name,
                project=self.storage_client.project,
                location=self.location,
            )
            self.logger.info(f"Bucket {self.bucket_name} created.")
        except Conflict:
            self.logger.info(f"Bucket {self.bucket_name} already exists.")

    def upload_file(
        self,
        source_file_name,
        destination_blob_name,
        delete_original: bool,
    ):
        """Uploads a file to the bucket."""
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)

        self.logger.info(
            f"File {source_file_name} uploaded to {destination_blob_name}."
        )

        if delete_original:
            os.remove(source_file_name)


class ReplayStorage(BaseStorageClient):
    def __init__(
        self,
        download_dir: str,
        skip_download: bool,
        sa_signed_url_generator_email: str,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.download_dir = download_dir
        self.skip_download = skip_download
        self.sa_signed_url_generator_email = sa_signed_url_generator_email
        self.sa_access_cred: impersonated_credentials.Credentials = None

    def upload_metadata(self, replay_id, metadata: dict):
        current_dir = pathlib.Path().resolve()
        file_path = current_dir.joinpath("metadata.json")
        with open(file_path, "w") as f:
            f.write(json.dumps(metadata))
        self.upload_file(file_path, replay_id, "metadata.json", delete_original=True)

    def upload_file_in_background(self, *args, **kwargs):
        threading.Thread(target=self.upload_file, args=args, kwargs=kwargs).start()

    def upload_file(
        self,
        source_file_name,
        replay_id,
        file_name: str,
        delete_original: bool,
        initial_delay_sec: int = 0,
    ):
        time.sleep(initial_delay_sec)

        super().upload_file(
            source_file_name, f"{replay_id}/{file_name}", delete_original
        )

    def list_round_ids(self, replay_id: str):
        blobs = self.storage_client.list_blobs(
            self.bucket_name, prefix=f"{replay_id}/", delimiter="/"
        )
        videos = [blob for blob in blobs if blob.name.endswith(".mp4")]

        if len(videos) < 2:
            raise ValueError(
                f"Replay {replay_id} has less than 2 rounds. videos: {videos}"
            )

        return [int(video.name.split("/")[1].replace(".mp4", "")) for video in videos]

    def download(self, replay_id: str, file_name: str, to_path: str):
        bucket = self.storage_client.bucket(self.bucket_name)
        source_blob_name = f"{replay_id}/{file_name}"
        blob = bucket.blob(source_blob_name)
        blob.download_to_filename(to_path)

    def iterate_rounds(
        self,
        replay_id: str,
    ):
        round_ids = self.list_round_ids(replay_id=replay_id)

        for round_id in round_ids:
            self.logger.info(f"Iterating round {round_id} of replay {replay_id}")
            yield round_id

    def download_video(self, replay_id: str, round_id: int) -> str:
        download_path = self.get_downloaded_video_path(replay_id, round_id)

        if os.path.exists(download_path):
            self.logger.info(
                f"The video already exists at {download_path}. Skipping download."
            )
            return download_path

        os.makedirs(Path(download_path).parent, exist_ok=True)

        self.logger.info(
            f"Downloading round {round_id} of replay {replay_id} to {download_path}"
        )
        if self.skip_download:
            self.logger.info(
                f"Skipping download of round {round_id} of replay {replay_id}"
            )
        else:
            self.download(replay_id, file_name=f"{round_id}.mp4", to_path=download_path)
            self.logger.info(
                f"Downloaded round {round_id} of replay {replay_id} to {download_path}"
            )
        return download_path

    def get_downloaded_video_path(self, replay_id: str, round_id: int) -> str:
        return os.path.join(self.download_dir, f"{replay_id}/{round_id}.mp4")

    def get_authenticated_url(self, replay_id: str, round_id: int) -> str:
        bucket = self.storage_client.bucket(self.bucket_name)
        source_blob_name = f"{replay_id}/{round_id}.mp4"

        service_account_access_token = self.get_service_account_access_token()

        url = bucket.blob(source_blob_name).generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="GET",
            access_token=service_account_access_token,
            service_account_email=self.sa_signed_url_generator_email,
        )

        return url

    def get_service_account_access_token(self):
        if self.sa_access_cred and self.sa_access_cred.token_state == TokenState.FRESH:
            return self.sa_access_cred.token

        self.sa_access_cred = self._refresh_service_account_access_token()

        return self.sa_access_cred.token

    def _refresh_service_account_access_token(
        self,
    ) -> impersonated_credentials.Credentials:
        credentials, project_id = google.auth.default()
        target_credentials = impersonated_credentials.Credentials(
            source_credentials=credentials,
            target_principal=self.sa_signed_url_generator_email,
            target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
            lifetime=3600,  # 1 hour
        )
        request = google.auth.transport.requests.Request()
        target_credentials.refresh(request)
        return target_credentials

    @contextlib.contextmanager
    def open(
        self,
        replay_id: str,
        round_id: int,
    ):
        download_path = self.download_video(replay_id, round_id)

        yield download_path

        if self.skip_download:
            self.logger.info(
                f"Skipping removal of downloaded replay {replay_id} from {download_path}"
            )
            return
        else:
            os.remove(download_path)
            self.logger.info(
                f"Removed downloaded replay {replay_id} from {download_path}"
            )


class FrameStorage(BaseStorageClient):
    def __init__(self, workers: int, skip_upload: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workers = workers
        self.skip_upload = skip_upload

    def upload_as_zip(self, source_dir, dest_path):
        """Uploads a zip file to the bucket."""
        zip_path = "tmp.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, source_dir))

        self.upload_file(zip_path, dest_path, delete_original=True)

    def download_frames(self, replay_id, round_id) -> str:
        download_dir_path = f"download/{replay_id}/{round_id}/frames"

        if os.path.isdir(download_dir_path):
            return download_dir_path

        bucket = self.storage_client.bucket(self.bucket_name)

        blobs = self.storage_client.list_blobs(
            self.bucket_name, prefix=f"{replay_id}/{round_id}/frames"
        )

        print(f"blobs: {blobs}")

        paths = [blob.name for blob in blobs if blob.name.endswith(".zip")]
        print(f"paths: {paths}")

        for path in paths:
            source_blob_name = path
            destination_file_name = "tmp-frames.zip"
            blob = bucket.blob(source_blob_name)
            blob.download_to_filename(destination_file_name)

            print(
                "Downloaded storage object {} from bucket {} to local file {}.".format(
                    source_blob_name, self.bucket_name, destination_file_name
                )
            )

            print(f"Extracting zip {destination_file_name}...")
            with zipfile.ZipFile(destination_file_name, "r") as zip_ref:
                zip_ref.extractall(download_dir_path)

            os.remove(destination_file_name)

        return download_dir_path


if __name__ == "__main__":
    import sys
    from miyoka.container import Container

    replay_storage = Container().replay_storage()
    replay_id = sys.argv[0]
    round_id = sys.argv[1]
    print(replay_storage.get_authenticated_url(replay_id, round_id))
