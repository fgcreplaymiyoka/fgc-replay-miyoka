import cv2 as cv
import shutil
from typing import Iterator, Tuple
from logging import Logger
import os


class FrameSplitter:
    def __init__(
        self,
        logger: Logger,
        export_dir: str,
        batch_size: int,
        clear_per_batch: bool,
        skip_split: bool,
    ) -> None:
        self.logger = logger
        self.export_dir = export_dir
        self.batch_size = batch_size
        self.clear_per_batch = clear_per_batch
        self.skip_split = skip_split

    def split_in_batch(
        self,
        video_path: str,
    ) -> Iterator[Tuple[range, str]]:
        if self.skip_split:
            self.logger.info(
                f"Skipping frame splitting for {video_path} as per configuration."
            )
            frame_range = range(1, 100000)
            yield (frame_range, self.export_dir, 100000)
            return

        if os.path.exists(self.export_dir):
            shutil.rmtree(self.export_dir)

        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

        self.logger.info(f"Reading frames from {video_path}")
        vidcap = cv.VideoCapture(video_path)

        fps = vidcap.get(5)
        self.logger.info(f"Frames per second : {fps} FPS")

        if fps < 60:
            raise ValueError("FPS is less than 60. Invalid video file.")

        # Get frame count
        # You can replace 7 with CAP_PROP_FRAME_COUNT as well, they are enumerations
        total_frame_count = vidcap.get(7)
        self.logger.info(f"Frame count : {total_frame_count}")

        if total_frame_count < 60:
            raise ValueError("Frame count is less than 60. Invalid video file.")

        frame_id = prev_frame_id = 0

        self.logger.info(
            f"Splitted frames will be exported to {self.export_dir} directory with batch size {self.batch_size}."
        )
        while True:
            success, image = vidcap.read()

            if not success:
                break

            cv.imwrite(f"{self.export_dir}/{frame_id}.jpeg", image)

            frame_id += 1

            if (frame_id - prev_frame_id) >= self.batch_size:
                frame_range = range(prev_frame_id, frame_id)

                self.logger.info(
                    f"Prepared batch of frames {frame_range} from {video_path} to {self.export_dir} directory."
                )
                yield (frame_range, self.export_dir, total_frame_count)

                if self.clear_per_batch:
                    shutil.rmtree(self.export_dir)
                    os.makedirs(self.export_dir)

                    self.logger.info(
                        f"Cleared {self.export_dir} directory after preparing batch of frames {frame_range} from {video_path}."
                    )

                prev_frame_id = frame_id

        if frame_id != prev_frame_id:
            frame_range = range(prev_frame_id, frame_id)

            self.logger.info(
                f"Prepared batch of frames {frame_range} from {video_path} to {self.export_dir}."
            )
            yield (frame_range, self.export_dir, total_frame_count)

            if self.clear_per_batch:
                shutil.rmtree(self.export_dir)
