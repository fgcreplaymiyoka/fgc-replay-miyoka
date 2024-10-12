import streamlit as st
import pandas as pd
import numpy as np
import datetime
from typing import Tuple
from miyoka.libs.scene_store import SceneStore
from miyoka.libs.storages import ReplayStorage
from miyoka.libs.bigquery import ReplayDataset, FrameDataset
from miyoka.libs.replay_viewer_helper import ReplayViewerHelper
from miyoka.container import Container
from miyoka.sf6.scene_splitter import SceneSplitter
from miyoka.sf6.scene_vectorizer import SceneVectorizer
import altair as alt

cache_ttl = 3600  # 1 hour


# # https://docs.streamlit.io/develop/concepts/architecture/caching
# @st.cache_resource(ttl=cache_ttl, show_spinner="Loading scene store...")
# def load_scene_store():
#     container = Container()
#     scene_store: SceneStore = container.scene_store()
#     frame_dataset: FrameDataset = container.frame_dataset()
#     scene_splitter: SceneSplitter = container.scene_splitter()
#     scene_vectorizer: SceneVectorizer = container.scene_vectorizer()
#     mode = "classic"

#     for replay_id, round_id, round_rows in frame_dataset.iterate_rounds(
#         mode=mode,
#     ):
#         print(f"========= replay_id: {replay_id} | round_id: {round_id} ==========")

#         for scene in scene_splitter.split(round_rows):
#             scene.vector = scene_vectorizer.vectorize(scene.inputs)
#             scene_store.append(scene)

#     return scene_store


@st.cache_resource(ttl=cache_ttl, show_spinner="Loading replay dataset...")
def load_replay_dataset():
    return Container().replay_dataset().get_all_rows(limit=1000)


@st.cache_resource(ttl=cache_ttl, show_spinner="Loading replay storage...")
def load_replay_storage():
    return Container().replay_storage()


@st.cache_resource(ttl=cache_ttl, show_spinner="Loading replay viewer...")
def load_replay_viewer_helper():
    return Container().replay_viewer_helper()


# @st.cache_data(ttl=cache_ttl, show_spinner="Loading main dataframe...")
# def load_main_df():
#     return scene_store.main_df


# @st.cache_data(ttl=cache_ttl, show_spinner="Loading similarity dataframe...")
# def load_similarity_df():
#     return scene_store.similarity_df


@st.cache_data(ttl=cache_ttl, show_spinner="Loading character list...")
def load_character_list():
    global replay_dataset

    p1_list = (
        replay_dataset.groupby("p1_character").p1_character.nunique().index.to_list()
    )
    p2_list = (
        replay_dataset.groupby("p2_character").p2_character.nunique().index.to_list()
    )

    return set(p1_list + p2_list)


# @st.cache_data(ttl=cache_ttl, show_spinner="Loading character main df...")
# def load_character_main_df(character: str):
#     global main_df
#     return main_df.query(f"character == '{character}'")


# @st.cache_data(ttl=cache_ttl, show_spinner="Loading replay character main df...")
# def load_replay_character_main_df(character: str):
#     global main_df
#     return main_df.query(f"character == '{character}'")[
#         ["replay_id", "round_id"]
#     ].drop_duplicates()


# @st.cache_data(ttl=cache_ttl, show_spinner="Loading character similarity df...")
# def load_character_similarity_df(character: str):
#     global similarity_df
#     return similarity_df.query(f"character == '{character}'")


def reset_current_replay_index(*args, **kwargs):
    del st.session_state["current_replay_index"]


# def split_frame_range(frame_range_str):
#     start_frame_str, end_frame_str = frame_range_str.split("-")
#     start_time = int(start_frame_str) // 60
#     end_time = int(end_frame_str) // 60.0
#     return start_time, end_time


# def similarity_label(similar_count):
#     label = ""
#     if similar_count > 10:
#         label = "Very popular 🔥"
#     elif similar_count > 2:
#         label = "Popular ✋"
#     return label


# def generate_scene_annotations() -> Tuple[pd.DataFrame, str]:
#     subtitles_file = "scene-subtitle.vtt"
#     scene_annotation = {}
#     scene_annotation["timestamp"] = []
#     scene_annotation["annotation"] = []

#     with open(subtitles_file, "w") as f:
#         f.write("WEBVTT\n")
#         f.write("\n")

#         for index, row in round_main_df.iterrows():
#             r_start_time, r_end_time = split_frame_range(row["frame_range"])
#             r_start = str(datetime.timedelta(seconds=r_start_time))
#             r_end = str(datetime.timedelta(seconds=r_end_time + 1))
#             r_scene_id = row["scene_id"]
#             df = round_similarity_df.query(f"scene_id == {r_scene_id}")
#             lebel = similarity_label(len(df.index))
#             if lebel:
#                 f.write(f"{r_start}.000 --> {r_end}.000\n")
#                 f.write(f"{lebel}\n")
#                 f.write("\n")

#                 scene_annotation["timestamp"].append(r_start)
#                 scene_annotation["annotation"].append(lebel)

#     return (
#         pd.DataFrame(scene_annotation, columns=["timestamp", "annotation"]),
#         subtitles_file,
#     )


# scene_store: SceneStore = load_scene_store()
replay_dataset: pd.DataFrame = load_replay_dataset()
replay_storage: ReplayStorage = load_replay_storage()
replay_viewer_helper: ReplayViewerHelper = load_replay_viewer_helper()
# main_df: pd.DataFrame = load_main_df()
# similarity_df: pd.DataFrame = load_similarity_df()
character_list: list[str] = load_character_list()
player_name = replay_viewer_helper.player_name

###############################################################################################
# View
###############################################################################################
# In production, users must enter the global password otherwise can't access the page.
if not replay_viewer_helper.check_password():
    st.stop()

# -------------------------------------------------------------------
# st.set_page_config(page_title="Miyoka", page_icon="🕹️")
st.title("Replay Miyoka")

if "current_character_list_index" not in st.session_state:
    st.session_state.current_character_list_index = np.random.randint(
        len(character_list)
    )

selected_char = st.selectbox(
    "Character",
    character_list,
    index=st.session_state.current_character_list_index,
    on_change=reset_current_replay_index,
)

# character_main_df: pd.DataFrame = load_character_main_df(selected_char)
# replay_character_main_df: pd.DataFrame = load_replay_character_main_df(selected_char)
# character_similarity_df: pd.DataFrame = load_character_similarity_df(selected_char)

if "current_replay_index" not in st.session_state:
    st.session_state.current_replay_index = np.random.randint(len(replay_dataset))

replay_id = replay_dataset.iloc[st.session_state.current_replay_index]["replay_id"]
round_id = 1
# round_id = replay_character_main_df.iloc[st.session_state.current_replay_index][
#     "round_id"
# ]

# round_main_df = character_main_df.query(
#     f"replay_id == '{replay_id}' & round_id == {round_id}"
# )

# round_similarity_df = character_similarity_df.query(
#     f"replay_id == '{replay_id}' & round_id == {round_id}"
# )

# annotated_scene_df, subtitles_file = generate_scene_annotations()
# video_path = replay_storage.get_authenticated_url(replay_id, round_id)

# st.video(
#     video_path,
#     start_time=1,
#     # end_time=end_time + 1,
#     autoplay=True,
#     muted=True,
#     # subtitles=subtitles_file,
# )


left_col, right_col = st.columns(2)
left_col.write("Scene annotations")
# left_col.dataframe(annotated_scene_df, hide_index=True)

if right_col.button("Next replay ⏭"):
    st.session_state.current_replay_index += 1
    st.session_state.current_replay_index %= len(replay_dataset)

if right_col.button("Prev replay ⏮️"):
    st.session_state.current_replay_index += 1
    st.session_state.current_replay_index %= len(replay_dataset)

# f"Replay ID: {replay_dataset.iloc[st.session_state.current_replay_index]['replay_id']} | Round ID: {replay_dataset.iloc[st.session_state.current_replay_index]['round_id']}"

# st.subheader("Match count", divider=True)
# daily_df = replay_dataset.groupby([replay_dataset["played_at"].dt.date])["replay_id"].nunique()
# daily_df = daily_df.rename_axis("date").rename("count")
# st.bar_chart(daily_df, x_label="play date", y_label="count")

# -------------------------------------------------------------------

st.subheader("Rank progress", divider=True)
p1_player_dataset = replay_dataset[
    replay_dataset["p1_player_name"].str.contains(player_name, case=False, na=False)
]
p2_player_dataset = replay_dataset[
    replay_dataset["p2_player_name"].str.contains(player_name, case=False, na=False)
]
p1_player_dataset = p1_player_dataset[
    ["p1_rank", "p1_lp", "p1_result", "p1_character", "replay_id", "played_at"]
].rename(columns={"p1_rank": "rank", "p1_lp": "lp", "p1_result": "result", "p1_character": "character"})
p2_player_dataset = p2_player_dataset[
    ["p2_rank", "p2_lp", "p2_result", "p2_character", "replay_id", "played_at"]
].rename(columns={"p2_rank": "rank", "p2_lp": "lp", "p2_result": "result", "p2_character": "character"})
player_dataset = pd.concat([p1_player_dataset, p2_player_dataset], axis=0)
player_dataset = player_dataset.sort_values(by="played_at")
player_dataset = player_dataset.reset_index().rename(columns={"index": "match"})

c = (
    alt.Chart(player_dataset)
    .mark_line()
    .encode(
        x={"field": "match", "type": "quantitative"},
        y={"field": "lp", "type": "quantitative"},
        tooltip=["lp", "rank", "character", "replay_id", "played_at"],
        color="character:N",
    )
)
st.altair_chart(c, use_container_width=True)

rank_order = [
    "master",
    "diamond5",
    "diamond4",
    "diamond3",
    "diamond2",
    "diamond1",
    "platinum5",
    "platinum4",
    "platinum3",
    "platinum2",
    "platinum1",
    "gold5",
    "gold4",
    "gold3",
    "gold2",
    "gold1",
    "silver5",
    "silver4",
    "silver3",
    "silver2",
    "silver1",
    "bronze5",
    "bronze4",
    "bronze3",
    "bronze2",
    "bronze1",
    "iron5",
    "iron4",
    "iron3",
    "iron2",
    "iron1",
    "rookie",
    "new",
]

c = (
    alt.Chart(player_dataset)
    .mark_line()
    .encode(
        x={"field": "match", "type": "quantitative"},
        y={"field": "rank", "type": "ordinal", "sort": rank_order},
        tooltip=["match", "lp", "rank", "character", "replay_id", "played_at"],
        color="character:N",
    )
)
st.altair_chart(c, use_container_width=True)

# -------------------------------------------------------------------

st.subheader("Daily result", divider=True)

c = (
    alt.Chart(player_dataset)
    .mark_bar()
    .encode(
        x={"field": "played_at", "type": "temporal", "timeUnit": "yearmonthdate"},
        y={"field": "result", "aggregate": "count"},
        color={"field": "result"}
    )
)
st.altair_chart(c, use_container_width=True)

# -------------------------------------------------------------------

st.subheader("Match count by character", divider=True)

p1_player_name_char_dataset = replay_dataset[["p1_player_name", "p1_character"]].rename(
    columns={"p1_player_name": "player_name", "p1_character": "character"}
)
p2_player_name_char_dataset = replay_dataset[["p2_player_name", "p2_character"]].rename(
    columns={"p2_player_name": "player_name", "p2_character": "character"}
)
player_name_char_dataset = pd.concat(
    [p1_player_name_char_dataset, p2_player_name_char_dataset], sort=True, axis=0
)

player_name_char_dataset = player_name_char_dataset[
    ~player_name_char_dataset["player_name"].str.contains(
        player_name, case=False, na=False
    )
]

character_count_df = player_name_char_dataset.groupby("character").size()
st.bar_chart(character_count_df, x_label="character", y_label="match count")

# -------------------------------------------------------------------

if replay_viewer_helper.debug_mode:
    st.subheader("Debug info", divider=True)
    "replay_dataset"
    st.dataframe(replay_dataset)
    "player_dataset"
    st.dataframe(player_dataset)
