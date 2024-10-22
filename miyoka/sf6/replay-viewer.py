import streamlit as st

st.set_page_config(layout="wide", page_title="Miyoka", page_icon="🕹️")

import pandas as pd
from miyoka.libs.storages import ReplayStorage
from miyoka.libs.bigquery import ReplayDataset
from miyoka.libs.replay_viewer_helper import ReplayViewerHelper
from miyoka.container import Container
import altair as alt

cache_ttl = 3600  # 1 hour


@st.cache_resource(ttl=cache_ttl, show_spinner="Loading replay dataset...")
def load_replay_dataset():
    replay_dataset: ReplayDataset = Container().replay_dataset()
    return replay_dataset.get_all_rows(limit=1000)


@st.cache_resource(ttl=cache_ttl, show_spinner="Loading replay storage...")
def load_replay_storage() -> ReplayStorage:
    return Container().replay_storage()


@st.cache_resource(ttl=cache_ttl, show_spinner="Loading replay viewer...")
def load_replay_viewer_helper():
    return Container().replay_viewer_helper()


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


def reset_current_replay_index(*args, **kwargs):
    del st.session_state["current_replay_index"]


replay_dataset: pd.DataFrame = load_replay_dataset()
replay_storage: ReplayStorage = load_replay_storage()
replay_viewer_helper: ReplayViewerHelper = load_replay_viewer_helper()
character_list: list[str] = load_character_list()
player_name = replay_viewer_helper.player_name

###############################################################################################
# View
###############################################################################################
# In production, users must enter the global password otherwise can't access the page.
if not replay_viewer_helper.check_password():
    st.stop()

# -------------------------------------------------------------------
st.subheader("Replay", divider=True)

last_replay_index = len(replay_dataset) - 1

if "current_replay_index" not in st.session_state:
    st.session_state.current_replay_index = last_replay_index

if "current_round_id" not in st.session_state:
    st.session_state.current_round_id = 1

current_row = replay_dataset.iloc[st.session_state.current_replay_index]
replay_id = current_row["replay_id"]
round_id = st.session_state.current_round_id
video_path = replay_storage.get_authenticated_url(replay_id, round_id)

html_string = f"""
<video controls="" width=100% height="auto" src="{video_path}#t=1" playsinline autoplay muted></video>
"""

st.markdown(html_string, unsafe_allow_html=True)

st.slider("Match", 0, last_replay_index, key="current_replay_index")

left_col, middle_col, right_col = st.columns(3)


def next_match():
    st.session_state.current_replay_index += 1
    st.session_state.current_replay_index %= len(replay_dataset)
    st.session_state.current_round_id = 1


def prev_match():
    st.session_state.current_replay_index -= 1
    st.session_state.current_replay_index %= len(replay_dataset)
    st.session_state.current_round_id = 1


def next_round():
    st.session_state.current_round_id += 1


def prev_round():
    st.session_state.current_round_id -= 1


left_col.button("Next match", on_click=next_match)
left_col.button("Prev match", on_click=prev_match)
middle_col.button("Next round", on_click=next_round)
middle_col.button("Prev round", on_click=prev_round)
right_col.dataframe(current_row)

# -------------------------------------------------------------------

st.subheader("Rank progress", divider=True)
p1_player_dataset = replay_dataset[
    replay_dataset["p1_player_name"].str.contains(player_name, case=False, na=False)
]
p2_player_dataset = replay_dataset[
    replay_dataset["p2_player_name"].str.contains(player_name, case=False, na=False)
]
p1_player_dataset = p1_player_dataset[
    ["p1_rank", "p1_lp", "p1_mr", "p1_result", "p1_character", "replay_id", "played_at"]
].rename(
    columns={
        "p1_rank": "rank",
        "p1_lp": "lp",
        "p1_mr": "mr",
        "p1_result": "result",
        "p1_character": "character",
    }
)
p2_player_dataset = p2_player_dataset[
    ["p2_rank", "p2_lp", "p2_mr", "p2_result", "p2_character", "replay_id", "played_at"]
].rename(
    columns={
        "p2_rank": "rank",
        "p2_lp": "lp",
        "p2_mr": "mr",
        "p2_result": "result",
        "p2_character": "character",
    }
)
player_dataset = pd.concat([p1_player_dataset, p2_player_dataset], axis=0)
player_dataset = player_dataset.reset_index().rename(columns={"index": "match"})
player_dataset = player_dataset.sort_values(by="played_at")
player_dataset["match"] = [i for i in range(len(player_dataset))]

c = (
    alt.Chart(player_dataset)
    .mark_bar(clip=True)
    .encode(
        x=alt.X("match:Q", scale=alt.Scale(domain=[0, last_replay_index]), title=None),
        y={"field": "lp", "type": "quantitative"},
        tooltip=["match", "lp", "rank", "character", "replay_id", "played_at"],
        color=alt.Color('character:N', legend=alt.Legend(orient='bottom')),
    )
)

thresholds = pd.DataFrame(
    [
        {"lp": 25000, "rank": "master"},
        {"lp": 19000, "rank": "diamond"},
        {"lp": 13000, "rank": "platinum"},
        {"lp": 9000, "rank": "gold"},
        {"lp": 5000, "rank": "silver"},
        {"lp": 3000, "rank": "bronze"},
        {"lp": 1000, "rank": "iron"},
        {"lp": 0, "rank": "rookie"},
    ]
)

rules = (
    alt.Chart(thresholds)
    .mark_rule()
    .encode(alt.Y("lp:Q", title=None), color=alt.value("#224455"), opacity=alt.value(0.3))
)

text = (
    alt.Chart(thresholds)
    .mark_text(align="center", dy=-5)
    .encode(alt.Y("lp:Q", title=None), text="rank", opacity=alt.value(0.3))
)

st.altair_chart(c + rules + text, use_container_width=True)

# -------------------------------------------------------------------

st.subheader("Daily result", divider=True)

c = (
    alt.Chart(player_dataset)
    .mark_bar()
    .encode(
        x={"field": "played_at", "type": "temporal", "timeUnit": "yearmonthdate"},
        y=alt.Y("result", aggregate="count", title=None),
        color=alt.Color('result', legend=alt.Legend(orient='bottom')),
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
