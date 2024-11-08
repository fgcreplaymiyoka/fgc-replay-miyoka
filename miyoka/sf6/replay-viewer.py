import streamlit as st

st.set_page_config(layout="wide", page_title="Miyoka", page_icon="🕹️")

import pandas as pd
from miyoka.libs.storages import ReplayStorage
from miyoka.libs.bigquery import ReplayDataset
from miyoka.libs.replay_viewer_helper import ReplayViewerHelper
from miyoka.container import Container
import altair as alt
import re
import numpy

###############################################################################################
# Functions
###############################################################################################

cache_ttl = 3600  # 1 hour


@st.cache_data(ttl=cache_ttl, show_spinner="Loading replay dataset...")
def load_replay_dataset(time_range: str = None, after_time: str = None) -> pd.DataFrame:
    replay_dataset: ReplayDataset = Container().replay_dataset()
    return replay_dataset.get_all_rows(time_range=time_range, after_time=after_time)


@st.cache_resource(ttl=cache_ttl, show_spinner="Loading replay storage...")
def load_replay_storage() -> ReplayStorage:
    return Container().replay_storage()


@st.cache_resource(ttl=cache_ttl, show_spinner="Loading replay viewer...")
def load_replay_viewer_helper():
    return Container().replay_viewer_helper()


def next_match():
    st.session_state.current_replay_index += 1
    st.session_state.current_round_id = 1


def prev_match():
    st.session_state.current_replay_index -= 1
    st.session_state.current_round_id = 1


def next_round():
    st.session_state.current_round_id += 1


def prev_round():
    st.session_state.current_round_id -= 1


def render_current_row_value(key: str) -> str:
    global current_row_player_side

    player_side = 1 if key.startswith("p1") else 2
    value = current_row[key]

    if isinstance(value, numpy.ndarray):
        value = ", ".join(value)

    if current_row_player_side == player_side:
        return f"**{value}**"

    return value


def match_range_changed():
    st.session_state.match_range_changed = True


###############################################################################################
# Initialization
###############################################################################################

replay_viewer_helper: ReplayViewerHelper = load_replay_viewer_helper()

player_name = replay_viewer_helper.player_name
time_range = replay_viewer_helper.time_range
after_time = replay_viewer_helper.after_time
should_redact_pii = replay_viewer_helper.should_redact_pii

debug_mode = replay_viewer_helper.debug_mode
if debug_mode:
    should_redact_pii = False

replay_dataset: pd.DataFrame = load_replay_dataset(time_range, after_time)
replay_storage: ReplayStorage = load_replay_storage()

last_replay_index = replay_dataset.index[len(replay_dataset) - 1]

if "current_replay_index" not in st.session_state:
    st.session_state.current_replay_index = last_replay_index

if "current_played_after" not in st.session_state:
    st.session_state.current_played_after = replay_dataset.iloc[0][
        "played_at"
    ].to_pydatetime()

if "current_round_id" not in st.session_state:
    st.session_state.current_round_id = 1

if "match_range_changed" not in st.session_state:
    st.session_state.match_range_changed = True

###############################################################################################
# Login
###############################################################################################
# In production, users must enter the global password otherwise can't access the page.
if not replay_viewer_helper.check_password():
    st.stop()

###############################################################################################
# Filtering
###############################################################################################

with st.sidebar:
    played_after = st.slider(
        "Played after:",
        value=st.session_state.current_played_after,
        min_value=replay_dataset.iloc[0]["played_at"],
        max_value=replay_dataset.iloc[last_replay_index]["played_at"],
        format="MM/DD",
    )

    replay_dataset = replay_dataset[replay_dataset["played_at"] >= played_after]

    last_replay_index = len(replay_dataset) - 1

    min_match_range, max_match_range = st.slider(
        "Match range",
        replay_dataset.index[0],
        replay_dataset.index[last_replay_index],
        (
            replay_dataset.index[0],
            replay_dataset.index[last_replay_index],
        ),
        on_change=match_range_changed,
    )

    replay_dataset = replay_dataset[
        (replay_dataset.index >= min_match_range)
        & (replay_dataset.index <= max_match_range)
    ]

    last_replay_index = len(replay_dataset) - 1

    # st.write(last_replay_index)
    if st.session_state.match_range_changed:
        st.session_state.current_replay_index = replay_dataset.index[last_replay_index]
        st.session_state.match_range_changed = False

    value = st.slider(
        "Match",
        min_value=replay_dataset.index[0],
        max_value=replay_dataset.index[last_replay_index],
        value=st.session_state.current_replay_index,
    )
    st.session_state.current_replay_index = value

current_row = replay_dataset[
    replay_dataset.index == st.session_state.current_replay_index
].iloc[0]
current_row_player_side = (
    1 if re.match(player_name, current_row["p1_player_name"]) else 2
)
replay_id = current_row["replay_id"]
round_id = st.session_state.current_round_id
next_match_exist = (
    st.session_state.current_replay_index < replay_dataset.index[last_replay_index]
)
prev_match_exist = st.session_state.current_replay_index > replay_dataset.index[0]
next_round_exist = round_id < len(current_row["p1_round_results"])
prev_round_exist = round_id > 1
video_path = replay_storage.get_authenticated_url(replay_id, round_id)

###############################################################################################
# View
###############################################################################################

# -------------------------------------------------------------------
# st.subheader("Replay", divider=True)

st.markdown(
    f"""
<video controls="" type="video/mp4" width=100% height="auto" src="{video_path}#t=1" playsinline autoplay muted></video>
""",
    unsafe_allow_html=True,
)

# Workaround for the column width issue
# https://github.com/streamlit/streamlit/issues/5003#issuecomment-1276611218
st.write(
    """<style>

[data-testid="column"] {
    width: calc(25% - 1rem) !important;
    flex: 1 1 calc(25% - 1rem) !important;
    min-width: calc(25% - 1rem) !important;
}
.big-font {
    font-size:10px !important;
}
</style>""",
    unsafe_allow_html=True,
)
col_1, col_2, col_3, col_4 = st.columns(4)

if prev_match_exist:
    col_1.button("Prev match", on_click=prev_match)
if next_match_exist:
    col_2.button("Next match", on_click=next_match)
if prev_round_exist:
    col_3.button("Prev round", on_click=prev_round)
if next_round_exist:
    col_4.button("Next round", on_click=next_round)

replay_markdown = """
|info|player 1|player 2|
|---|---|---|"""

if not should_redact_pii:
    replay_markdown += f"""
|name|{render_current_row_value('p1_player_name')}|{render_current_row_value('p2_player_name')}|"""

replay_markdown += f"""
|character|{render_current_row_value('p1_character')}|{render_current_row_value('p2_character')}|
|mode|{render_current_row_value('p1_mode')}|{render_current_row_value('p2_mode')}|
|result|{render_current_row_value('p1_result')}|{render_current_row_value('p2_result')}|
|round result|{render_current_row_value('p1_round_results')}|{render_current_row_value('p2_round_results')}|
|lp|{render_current_row_value('p1_lp')}|{render_current_row_value('p2_lp')}|
|mr|{render_current_row_value('p1_mr')}|{render_current_row_value('p2_mr')}|
|rank|{render_current_row_value('p1_rank')}|{render_current_row_value('p2_rank')}|
"""

st.markdown(replay_markdown)

col_1, col_2, col_3, col_4 = st.columns(4)

if not should_redact_pii:
    col_1.markdown(
        f"<p class='big-font'>Replay ID: {current_row['replay_id']}</p>",
        unsafe_allow_html=True,
    )

col_2.markdown(
    f"<p class='big-font'>Date: {current_row['played_at']}</p>", unsafe_allow_html=True
)
col_3.markdown(
    f"<p class='big-font'>Round: {st.session_state.current_round_id}</p>",
    unsafe_allow_html=True,
)
col_4.markdown(
    f"<p class='big-font'><a href='{video_path}' download='replay.mp4'>Download replay</a></p>",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------

st.subheader("Road to Master", divider=True)
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
player_dataset = player_dataset.sort_values(by="match")

base_tooltip = ["match", "rank", "character", "played_at"]
if not should_redact_pii:
    base_tooltip.append("replay_id")

c = (
    alt.Chart(player_dataset)
    .mark_bar(clip=True)
    .encode(
        x=alt.X(
            "match:Q",
            scale=alt.Scale(domain=[min_match_range, max_match_range]),
            title=None,
        ),
        y={"field": "lp", "type": "quantitative"},
        tooltip=["lp"] + base_tooltip,
        color=alt.Color("character:N", legend=alt.Legend(orient="bottom")),
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
    .encode(
        alt.Y("lp:Q", title=None), color=alt.value("#224455"), opacity=alt.value(0.3)
    )
)

text = (
    alt.Chart(thresholds)
    .mark_text(align="center", dy=-5)
    .encode(alt.Y("lp:Q", title=None), text="rank", opacity=alt.value(0.3))
)

st.altair_chart(c + rules + text, use_container_width=True)

# -------------------------------------------------------------------

st.subheader("Master League", divider=True)

st.altair_chart(
    alt.Chart(player_dataset)
    .mark_bar(clip=True)
    .encode(
        x=alt.X(
            "match:Q",
            scale=alt.Scale(domain=[min_match_range, max_match_range]),
            title=None,
        ),
        y=alt.Y("mr:Q", title=None).scale(domain=(500, 2500)),
        tooltip=["mr"] + base_tooltip,
        color=alt.Color("character:N", legend=alt.Legend(orient="bottom")),
    ),
    use_container_width=True,
)

# -------------------------------------------------------------------

st.subheader("Daily result", divider=True)

c = (
    alt.Chart(player_dataset)
    .mark_bar()
    .encode(
        x=alt.X("utcmonthdate(played_at):O", title=None),
        y=alt.Y("result", aggregate="count", title=None),
        color=alt.Color("result", legend=alt.Legend(orient="bottom")),
    )
)
st.altair_chart(c, use_container_width=True)

# -------------------------------------------------------------------

st.subheader("Opponent characters", divider=True)

p1_opponent_dataset = replay_dataset[
    ~replay_dataset["p1_player_name"].str.contains(player_name, case=False, na=False)
]
p2_opponent_dataset = replay_dataset[
    ~replay_dataset["p2_player_name"].str.contains(player_name, case=False, na=False)
]
p1_opponent_dataset = p1_opponent_dataset[["p1_character", "played_at"]].rename(
    columns={
        "p1_character": "character",
    }
)
p2_opponent_dataset = p2_opponent_dataset[["p2_character", "played_at"]].rename(
    columns={
        "p2_character": "character",
    }
)
opponent_dataset = pd.concat([p1_opponent_dataset, p2_opponent_dataset], axis=0)
opponent_dataset = opponent_dataset.reset_index().rename(columns={"index": "match"})
opponent_dataset = opponent_dataset.sort_values(by="played_at")
opponent_dataset["match"] = [i for i in range(len(opponent_dataset))]

c = (
    alt.Chart(opponent_dataset)
    .mark_rect()
    .encode(
        x=alt.X("utcmonthdate(played_at):O", title=None),
        y=alt.Y("character", title=None),
        color=alt.Color("count():Q", legend=alt.Legend(orient="bottom")),
    )
)
st.altair_chart(c, use_container_width=True)

# -------------------------------------------------------------------

if debug_mode:
    st.subheader("Debug info", divider=True)
    "replay_dataset"
    st.dataframe(replay_dataset)
    "player_dataset"
    st.dataframe(player_dataset)
