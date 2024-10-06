from logging import Logger
from dependency_injector.providers import Factory
from miyoka.libs.frame_splitter import FrameSplitter
from miyoka.libs.storages import (
    FrameStorage,
    ReplayStorage,
)
from miyoka.libs.bigquery import ReplayDataset, FrameDataset
from miyoka.libs.exceptions import (
    GameOver,
)
from miyoka.libs.round_analyzer import RoundAnalyzer


class ReplayAnalyzer:
    def __init__(
        self,
        logger: Logger,
        replay_id: str,
        upload_split_frames: bool,
        upload_last_images: bool,
        replay_dataset: ReplayDataset,
        replay_storage: ReplayStorage,
        frame_storage: FrameStorage,
        frame_dataset: FrameDataset,
        frame_splitter: FrameSplitter,
        round_analyzer_factory: Factory[RoundAnalyzer],
    ):
        self.logger = logger
        self.replay_id = replay_id
        self.upload_split_frames = upload_split_frames
        self.upload_last_images = upload_last_images
        self.replay_dataset = replay_dataset
        self.replay_storage = replay_storage
        self.frame_storage = frame_storage
        self.frame_dataset = frame_dataset
        self.frame_splitter = frame_splitter
        self.round_analyzer_factory = round_analyzer_factory

    def run(
        self,
    ):
        self.logger.info(f"Analyzing replay {self.replay_id}")
        metadata = self.replay_dataset.get_metadata(self.replay_id)
        self.logger.info("Metadata", extra={"metadata": metadata})
        for round_id in self.replay_storage.iterate_rounds(self.replay_id):
            if self.frame_dataset.is_exists(self.replay_id, round_id):
                self.logger.info(
                    f"Skipping round {round_id} as it is already analyzed.",
                    extra={"replay_id": self.replay_id, "round_id": round_id},
                )
                continue

            with self.replay_storage.open(self.replay_id, round_id) as download_path:
                try:
                    self.analyze_round(
                        round_id,
                        download_path,
                        metadata,
                    )
                finally:
                    if self.upload_last_images:
                        self.frame_storage.upload_as_zip(
                            "last_images",
                            f"{self.replay_id}/{round_id}/last_images.zip",
                        )

    def analyze_round(
        self,
        round_id: int,
        download_path: str,
        metadata: dict,
    ):
        round_analyzer = self.round_analyzer_factory(
            replay_id=self.replay_id, round_id=round_id, metadata=metadata
        )

        for (
            frame_range,
            frame_dir,
            total_frame_count,
        ) in self.frame_splitter.split_in_batch(download_path):
            try:
                round_analyzer.analyze_frames(frame_range, frame_dir)
            except GameOver:
                break
            except Exception as e:
                self.logger.error(
                    str(e),
                    extra={
                        "replay_id": self.replay_id,
                        "round_id": round_id,
                        "frame_range": frame_range,
                    },
                )
                raise
            finally:
                with round_analyzer.read_frame_data() as frame_data:
                    self.frame_dataset.insert(self.replay_id, round_id, frame_data)

            if self.upload_split_frames:
                first_range = frame_range.start
                last_range = frame_range[-1]
                self.frame_storage.upload_as_zip(
                    frame_dir,
                    f"{self.replay_id}/{round_id}/frames/{first_range}-{last_range}.zip",
                )
