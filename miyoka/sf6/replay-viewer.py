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
from datetime import datetime, timedelta

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


def play_date_range_changed():
    st.session_state.play_date_range_changed = True


def match_range_changed():
    st.session_state.match_range_changed = True


def highlight_cols(s):
    return "font-weight: bold"


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

if "current_round_id" not in st.session_state:
    st.session_state.current_round_id = 1

if "play_date_range_changed" not in st.session_state:
    st.session_state.play_date_range_changed = True

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
    st.subheader("Filters")

    played_after_mapping = {
        "Last 1 day": 1,
        "Last 2 days": 2,
        "Last 7 days": 7,
        "Last 14 days": 14,
        "Last 30 days": 30,
    }

    played_after_option = st.selectbox(
        "Played after:",
        (*played_after_mapping, "All"),
        on_change=play_date_range_changed,
        index=len(played_after_mapping) - 1,
    )

    if st.session_state.play_date_range_changed:
        if played_after_option == "All":
            st.session_state.current_played_after = replay_dataset.iloc[0][
                "played_at"
            ].to_pydatetime()
        else:
            st.session_state.current_played_after = datetime.now() - timedelta(
                days=played_after_mapping[played_after_option]
            )

        st.session_state.play_date_range_changed = False

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

    st.subheader("Aggregation")

    interval_option = st.selectbox(
        "Interval",
        ("Daily", "Weekly", "Monthly", "Yearly"),
    )

    interval_mapping = {
        "Daily": "D",
        "Weekly": "W",
        "Monthly": "ME",
        "Yearly": "YE",
    }

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
st.subheader("Replay", divider=True)

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

col_1.button("Prev match", on_click=prev_match, disabled=not prev_match_exist)
col_2.button("Prev round", on_click=prev_round, disabled=not prev_round_exist)
col_3.button("Next round", on_click=next_round, disabled=not next_round_exist)
col_4.button("Next match", on_click=next_match, disabled=not next_match_exist)

metadata = {"info": [], "player 1": [], "player 2": []}

if not should_redact_pii:
    metadata["info"].append("name")
    metadata["player 1"].append(current_row["p1_player_name"])
    metadata["player 2"].append(current_row["p2_player_name"])

metadata["info"].extend(["character", "mode", "result", "rounds", "lp", "mr", "rank"])
metadata["player 1"].extend(
    [
        current_row["p1_character"],
        current_row["p1_mode"],
        current_row["p1_result"],
        ",".join(current_row["p1_round_results"]),
        str(current_row["p1_lp"]),
        str(current_row["p1_mr"]),
        current_row["p1_rank"],
    ]
)
metadata["player 2"].extend(
    [
        current_row["p2_character"],
        current_row["p2_mode"],
        current_row["p2_result"],
        ",".join(current_row["p2_round_results"]),
        str(current_row["p2_lp"]),
        str(current_row["p2_mr"]),
        current_row["p2_rank"],
    ]
)

metadata_df = pd.DataFrame(data=metadata)
metadata_df = metadata_df.reset_index(drop=True).set_index(metadata_df.columns[0])

metadata_df = metadata_df.style.map(
    highlight_cols, subset=pd.IndexSlice[:, [f"player {current_row_player_side}"]]
)
st.table(metadata_df)

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

player_dataset = replay_viewer_helper.get_player_dataset(replay_dataset, player_name)
base_tooltip = ["match", "rank", "character", "played_at"]
if not should_redact_pii:
    base_tooltip.append("replay_id")

# -------------------------------------------------------------------

st.subheader("Road to Master", divider=True)

if player_dataset["lp"].isnull().all():
    st.write("No data available.")
else:
    tab_date, tab_match = st.tabs(["Date", "Match"])

    with tab_date:
        st.altair_chart(
            replay_viewer_helper.get_chart_lp_date(
                player_dataset, interval_mapping, interval_option
            ),
            use_container_width=True,
        )

    with tab_match:
        st.altair_chart(
            replay_viewer_helper.get_chart_lp_match(
                player_dataset, base_tooltip, min_match_range, max_match_range
            ),
            use_container_width=True,
        )

# -------------------------------------------------------------------

st.subheader("Master League", divider=True)

if player_dataset["mr"].isnull().all():
    st.write("No data available.")
else:
    tab_date, tab_match = st.tabs(["Date", "Match"])

    with tab_date:
        st.altair_chart(
            replay_viewer_helper.get_chart_mr_date(
                player_dataset, interval_mapping, interval_option
            ),
            use_container_width=True,
        )

    with tab_match:
        st.altair_chart(
            replay_viewer_helper.get_chart_mr_match(
                player_dataset, min_match_range, max_match_range, base_tooltip
            ),
            use_container_width=True,
        )

# -------------------------------------------------------------------

st.subheader("Result", divider=True)

st.altair_chart(
    replay_viewer_helper.get_chart_result(
        player_dataset, interval_mapping, interval_option
    ),
    use_container_width=True,
)

# -------------------------------------------------------------------

st.subheader("Result by character", divider=True)

tab_win_rate, tab_match_count = st.tabs(["Win rate", "Match count"])

opponent_dataset = replay_viewer_helper.get_opponent_dataset(
    replay_dataset, player_name
)

opponent_dataset_total = opponent_dataset.groupby(
    [pd.Grouper(key="played_at", freq=interval_mapping[interval_option]), "character"]
).count()
opponent_dataset_loses = (
    opponent_dataset.query("result == 'loses'")
    .groupby(
        [
            pd.Grouper(key="played_at", freq=interval_mapping[interval_option]),
            "character",
        ]
    )
    .count()
)

opponent_dataset_div = (
    opponent_dataset_loses.div(opponent_dataset_total)
    .round(2)
    .rename(columns={"result": "wins"})
    .add_suffix("_rate")
    .fillna(0.0)
    .reset_index()
)

opponent_dataset_total = opponent_dataset_total.reset_index()

with tab_win_rate:
    st.altair_chart(
        replay_viewer_helper.get_chart_result_by_character_win_rate(
            opponent_dataset_div
        ),
        use_container_width=True,
    )
with tab_match_count:
    st.altair_chart(
        replay_viewer_helper.get_chart_result_by_character_match_count(
            opponent_dataset_total
        ),
        use_container_width=True,
    )

# -------------------------------------------------------------------

if debug_mode:
    st.subheader("Debug info", divider=True)
    "replay_dataset"
    st.dataframe(replay_dataset)
    "player_dataset"
    st.dataframe(player_dataset)
    "opponent_dataset"
    st.dataframe(opponent_dataset)
