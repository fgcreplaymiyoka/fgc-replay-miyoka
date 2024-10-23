from pandas import DataFrame
import numpy as np
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
from miyoka.libs.scene import Scene
from miyoka.libs.scene_splitter import SceneSplitter as SceneSplitterBase
from miyoka.sf6.constants import (
    ARROWS,
    NON_ACTION_LABEL,
    ACTION_LABEL,
    invert_arrow,
)


class SceneSplitter(SceneSplitterBase):
    # If action frames are close enough, they are concatenated as one scene i.e. `eps=30` of DBSCAN.
    CLUSTERING_DISTANCE = 30
    CLUSTERING_MIN_SAMPLES = 2
    PREFIX_FRAME_SIZE = 10
    SUFFIX_FRAME_SIZE = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def split(
        self,
        round_rows: DataFrame,
        is_display_clustering: bool = False,
    ):
        last_frame_id = round_rows.loc[round_rows["frame_id"].idxmax()]["frame_id"]
        print(f"last_frame_id: {last_frame_id}")
        replay_id = round_rows["replay_id"].values[0]
        round_id = round_rows["round_id"].values[0]

        for p in ["p1", "p2"]:
            character = round_rows[f"{p}_character"].values[0]
            print(f"p: {p} character: {character}")

            input_mask = {arrow: None for arrow in ARROWS}

            action_pos = np.array(
                [
                    [
                        row["frame_id"],
                        (
                            NON_ACTION_LABEL
                            if row[f"{p}_input"] in input_mask
                            else ACTION_LABEL
                        ),
                    ]
                    for _, row in round_rows.iterrows()
                ]
            )

            clustering = DBSCAN(
                eps=self.CLUSTERING_DISTANCE,
                min_samples=self.CLUSTERING_MIN_SAMPLES,
            ).fit(action_pos)
            labels = clustering.labels_  # labels of frames
            print(f"labels: {labels}")
            print(f"clustering: {clustering}")

            n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise_ = list(labels).count(-1)

            print("Estimated number of clusters: %d" % n_clusters_)
            print("Estimated number of noise points: %d" % n_noise_)

            unique_labels = set(labels)  # labels of clusters
            core_samples_mask = np.zeros_like(labels, dtype=bool)
            core_samples_mask[clustering.core_sample_indices_] = True

            if is_display_clustering:
                self.display_clustering(
                    labels, unique_labels, action_pos, core_samples_mask, n_clusters_
                )

            # Show scenes
            # Iterating clusters. k = a cluster
            scene_id = 0
            for label in unique_labels:
                if label == -1:
                    # Ignore noise
                    continue

                class_member_mask = labels == label

                xy = action_pos[class_member_mask & core_samples_mask]

                if set(xy[:, 1]) == {NON_ACTION_LABEL}:
                    # Ignore non-action frames
                    continue

                frame_ids = xy[:, 0]

                if len(frame_ids) == 0:
                    print(f"WARN: frame_idx is empty")
                    continue

                # print(f"frame_idx: {frame_idx}")
                min_frame_id = max(min(frame_ids) - self.PREFIX_FRAME_SIZE, 0)
                max_frame_id = min(
                    (max(frame_ids) + self.SUFFIX_FRAME_SIZE),
                    last_frame_id,
                )

                frame_range = range(min_frame_id, max_frame_id)

                print("-----------------------------------")
                print(
                    f"replay_id: {replay_id} | round_id: {round_id} | scene_id: {scene_id} | frame range: {frame_range}"
                )
                # self.create_video(replay_id, round_id, scene_id, frame_range)

                ranged_rows = round_rows.query(
                    f"frame_id >= {min_frame_id} & frame_id <= {max_frame_id}"
                )
                if p == "p1":
                    scene_inputs = [
                        row[f"{p}_input"] for _, row in ranged_rows.iterrows()
                    ]
                elif p == "p2":
                    scene_inputs = [
                        invert_arrow(row[f"{p}_input"])
                        for _, row in ranged_rows.iterrows()
                    ]
                print(f"scene_inputs: {scene_inputs}")

                scene = Scene(
                    id=scene_id,
                    inputs=scene_inputs,
                    frame_range=frame_range,
                    replay_id=replay_id,
                    round_id=round_id,
                    character=character,
                )

                scene_id += 1

                yield scene

    def display_clustering(
        self, labels, unique_labels, action_pos, core_samples_mask, n_clusters_
    ):
        color_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]
        # color_cycle = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']

        # colors = [plt.cm.Spectral(each) for each in np.linspace(0, 1, len(unique_labels))]
        colors = [color_cycle[i % len(color_cycle)] for i in range(len(unique_labels))]
        # print(colors)
        # plt.figure(figsize=(200,60))
        # Iterating clusters. k = a cluster
        for k, col in zip(unique_labels, colors):
            if k == -1:
                # Black used for noise.
                col = tuple([0, 0, 0, 1])

            class_member_mask = labels == k

            xy = action_pos[class_member_mask & core_samples_mask]
            plt.plot(
                xy[:, 0],
                xy[:, 1],
                "o",
                markerfacecolor=col,
                markeredgecolor="k",
                markersize=14,
            )

            xy = action_pos[class_member_mask & ~core_samples_mask]
            plt.plot(
                xy[:, 0],
                xy[:, 1],
                "o",
                markerfacecolor=col,
                markeredgecolor="k",
                markersize=6,
            )

        plt.title(f"Estimated number of clusters: {n_clusters_}")
        plt.show()
