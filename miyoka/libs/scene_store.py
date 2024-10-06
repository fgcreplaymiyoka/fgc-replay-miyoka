import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pickle
from miyoka.libs.scene import Scene


class SceneStore:
    SIMILARITY_THRETHOLD = 0.9
    OUTPUT_DIR = "scenes_by_similarity"
    SAVE_FILE_NAME = "scene_store.pkl"

    def __init__(self):
        self.scenes: list[Scene] = []

    def append(self, scene: Scene):
        self.scenes.append(scene)

    def iterate_similar_scenes(self, columns: list[str]):
        scene_metadata = {}
        scene_metadata["replay_id"] = []
        scene_metadata["round_id"] = []
        scene_metadata["scene_id"] = []
        scene_vectors = []

        for scene in self.scenes:
            scene_vectors.append(scene.vector)
            scene_metadata["replay_id"].append(scene.replay_id)
            scene_metadata["round_id"].append(scene.round_id)
            scene_metadata["scene_id"].append(scene.id)

        # Scene Vector DB
        left_df = pd.DataFrame(
            scene_metadata, columns=["replay_id", "round_id", "scene_id"]
        )
        right_df = pd.DataFrame(scene_vectors, columns=columns)
        scene_df = left_df.join(right_df)
        print("------------ Scene vectors")
        print(scene_df)
        print("------------ Cosine Similarity")
        cos_sim = cosine_similarity(right_df, right_df)
        print(cos_sim)

        for idx in np.argwhere(cos_sim > self.SIMILARITY_THRETHOLD):
            base_scene = self.scenes[idx[0]]
            target_scene = self.scenes[idx[1]]
            yield base_scene, target_scene

    # Replay, Scenes and Frames
    # replay_id, round_id, character , player_side, scene-0, scene-1, scene-2, ... scene-N
    # XYZ      , 1       ,   c_1   , 1          , (10, 30), (30, 60), .......
    # XYZ      , 1       ,   c_2   , 2          , (10, 30), (30, 60), .......
    # XYZ      , 2       ,   c_1   , 1          , (10, 30), (30, 60), .......
    @property
    def main_df(self) -> pd.DataFrame:
        columns = {}
        columns["replay_id"] = []
        columns["round_id"] = []
        columns["scene_id"] = []
        columns["frame_range"] = []
        columns["character"] = []

        for scene in self.scenes:
            columns["replay_id"].append(scene.replay_id)
            columns["round_id"].append(scene.round_id)
            columns["scene_id"].append(scene.id)
            frame_range_val = f"{scene.frame_range.start}-{scene.frame_range.stop}"
            columns["frame_range"].append(frame_range_val)
            columns["character"].append(scene.character)

        df = pd.DataFrame(
            columns,
            columns=["replay_id", "round_id", "scene_id", "frame_range", "character"],
        )
        return df

    # By similarity
    # base-scene ,    similar-scene
    # XYZ-1-1    ,    XYZ-1-3
    # XYZ-1-1    ,    AYZ-3-30
    @property
    def similarity_df(self) -> pd.DataFrame:
        columns = {}
        columns["replay_id"] = []
        columns["round_id"] = []
        columns["character"] = []
        columns["scene_id"] = []
        columns["similar_replay_id"] = []
        columns["similar_round_id"] = []
        columns["similar_character"] = []
        columns["similar_scene_id"] = []

        for idx in np.argwhere(self.similarity_index > self.SIMILARITY_THRETHOLD):
            if idx[0] == idx[1]:
                continue  # Skip the same one

            base_scene = self.scenes[idx[0]]
            target_scene = self.scenes[idx[1]]

            if base_scene.character != target_scene.character:
                continue  # Skip different characters

            columns["replay_id"].append(base_scene.replay_id)
            columns["round_id"].append(base_scene.round_id)
            columns["character"].append(base_scene.character)
            columns["scene_id"].append(base_scene.id)
            columns["similar_replay_id"].append(target_scene.replay_id)
            columns["similar_round_id"].append(target_scene.round_id)
            columns["similar_character"].append(target_scene.character)
            columns["similar_scene_id"].append(target_scene.id)

        df = pd.DataFrame(
            columns,
            columns=[
                "replay_id",
                "round_id",
                "character",
                "scene_id",
                "similar_replay_id",
                "similar_round_id",
                "similar_character",
                "similar_scene_id",
            ],
        )
        return df

    @property
    def similarity_index(self) -> np.ndarray:
        scene_vectors = []

        for scene in self.scenes:
            scene_vectors.append(scene.vector)

        df = pd.DataFrame(scene_vectors)
        return cosine_similarity(df, df)

    def save(self):
        with open(self.SAVE_FILE_NAME, "wb") as f:
            pickle.dump(self.scenes, f)

    def load(self):
        with open(self.SAVE_FILE_NAME, "rb") as f:
            self.scenes = pickle.load(f)


if __name__ == "__main__":
    scene_store = SceneStore()
    scene_store.load()
    print(scene_store.main_df)
    print(scene_store.similarity_df)
