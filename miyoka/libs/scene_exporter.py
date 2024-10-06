import cv2
import os
import shutil
import pathlib
from miyoka.libs.scene import Scene


class SceneExporter:
    FPS = 25
    OUTPUT_DIR = "scenes"
    SIMILARITY_OUTPUT_DIR = "scenes_by_similarity"
    PREFIX_FRAME_SIZE = 0
    SUFFIX_FRAME_SIZE = 10

    def __init__(self):
        pass

    def export(self, scene: Scene, frames_dir_path: str) -> str:
        video_path = (
            f"{self.OUTPUT_DIR}/{scene.replay_id}/{scene.round_id}/scene-{scene.id}.mp4"
        )

        os.makedirs(
            f"{self.OUTPUT_DIR}/{scene.replay_id}/{scene.round_id}", exist_ok=True
        )

        images = [
            f"{frames_dir_path}/{i}.jpeg"
            for i in range(
                scene.frame_range.start - self.PREFIX_FRAME_SIZE,
                scene.frame_range.stop + self.SUFFIX_FRAME_SIZE,
            )
        ]
        images = [image for image in images if os.path.isfile(image)]
        frame = cv2.imread(images[0])
        height, width, layers = frame.shape

        video = cv2.VideoWriter(
            video_path, cv2.VideoWriter_fourcc(*"mp4v"), self.FPS, (width, height)
        )

        for image in images:
            video.write(cv2.imread(image))

        cv2.destroyAllWindows()
        video.release()

        return video_path

    def export_by_similarity(self, base_scene: Scene, target_scene: Scene):
        src_path = target_scene.scene_video_path
        dst_path = f"{self.SIMILARITY_OUTPUT_DIR}/{base_scene.fullpath}/{target_scene.uuid}.mp4"
        pathlib.Path(f"{self.SIMILARITY_OUTPUT_DIR}/{base_scene.fullpath}/").mkdir(
            parents=True, exist_ok=True
        )
        shutil.copyfile(src_path, dst_path)

    def clean_output_dir(self):
        shutil.rmtree(self.OUTPUT_DIR, ignore_errors=True)
        shutil.rmtree(self.SIMILARITY_OUTPUT_DIR, ignore_errors=True)


if __name__ == "__main__":
    import sys

    replay_id = sys.argv[0]
    round_id = 1
    scene_id = 999
    frame_range = range(100, 160)
    scene = Scene(
        id=scene_id,
        inputs=[],
        frame_range=frame_range,
        replay_id=replay_id,
        round_id=round_id,
        character="c_1",
    )
    frames_dir_path = "download/XYZ/1/frames"
    scene_exporter = SceneExporter()
    scene_exporter.export(scene, frames_dir_path)
