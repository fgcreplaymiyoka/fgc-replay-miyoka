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
    st.query_params.current_replay_row_idx = (
        int(st.query_params.current_replay_row_idx) + 1
    )
    reset_round()


def prev_match():
    st.query_params.current_replay_row_idx = (
        int(st.query_params.current_replay_row_idx) - 1
    )
    reset_round()


def next_round():
    st.query_params.round_id = int(st.query_params.round_id) + 1


def prev_round():
    st.query_params.round_id = int(st.query_params.round_id) - 1


def reset_round():
    st.query_params.round_id = 1


def clear_query_params():
    st.query_params.clear()


def reset_current_replay_row_idx():
    del st.query_params["current_replay_row_idx"]


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
min_mr_in_chart = replay_viewer_helper.min_mr_in_chart
max_mr_in_chart = replay_viewer_helper.max_mr_in_chart

debug_mode = replay_viewer_helper.debug_mode
if debug_mode:
    should_redact_pii = False

replay_dataset: pd.DataFrame = load_replay_dataset(time_range, after_time)
replay_storage: ReplayStorage = load_replay_storage()

last_replay_row_idx = len(replay_dataset) - 1

if "round_id" not in st.query_params:
    st.query_params.round_id = 1

result_list = ("all", "wins", "loses")


if "result_filter" not in st.query_params:
    st.query_params.result_filter = "all"

my_character_list = (
    replay_viewer_helper.get_player_dataset(replay_dataset, player_name)["character"]
    .sort_values()
    .unique()
)
my_character_list = ("all", *my_character_list)
opponent_character_list = (
    replay_viewer_helper.get_opponent_dataset(replay_dataset, player_name)["character"]
    .sort_values()
    .unique()
)
opponent_character_list = ("all", *opponent_character_list)

if "my_character_filter" not in st.query_params:
    st.query_params.my_character_filter = "all"

if "opponent_character_filter" not in st.query_params:
    st.query_params.opponent_character_filter = "all"

play_date_range_mapping = {
    "Last 1 day": 1,
    "Last 2 days": 2,
    "Last 7 days": 7,
    "Last 14 days": 14,
    "Last 30 days": 30,
    "All": -1,
}

play_date_range_mapping_keys = [key for key in play_date_range_mapping]

if "play_date_range" not in st.query_params:
    if replay_viewer_helper.default_played_after_filter:
        st.query_params.play_date_range = (
            replay_viewer_helper.default_played_after_filter
        )
    else:
        st.query_params.play_date_range = play_date_range_mapping_keys[-1]

interval_mapping = {
    "Daily": "D",
    "Weekly": "W",
    "Monthly": "ME",
    "Yearly": "YE",
}

interval_mapping_keys = [key for key in interval_mapping]

if "interval" not in st.query_params:
    st.query_params.interval = interval_mapping_keys[0]

###############################################################################################
# Callbacks
###############################################################################################


def interval_changed():
    st.query_params.interval = st.session_state.interval


def play_date_range_changed():
    st.query_params.play_date_range = st.session_state.play_date_range
    reset_current_replay_row_idx()
    reset_round()


def result_filter_changed():
    st.query_params.result_filter = st.session_state.result_filter
    reset_current_replay_row_idx()
    reset_round()


def my_character_filter_changed():
    st.query_params.my_character_filter = st.session_state.my_character_filter
    reset_current_replay_row_idx()
    reset_round()


def opponent_character_filter_changed():
    st.query_params.opponent_character_filter = (
        st.session_state.opponent_character_filter
    )
    reset_current_replay_row_idx()
    reset_round()


def current_replay_row_idx_changed():
    st.query_params.current_replay_row_idx = st.session_state.current_replay_row_idx
    reset_round()


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
    st.button("Reset", on_click=clear_query_params)

    st.subheader("Chart Visualization")

    interval = st.selectbox(
        "Aggregation Interval",
        interval_mapping_keys,
        on_change=interval_changed,
        index=interval_mapping_keys.index(st.query_params.interval),
        key="interval",
    )

    st.subheader("Filters")

    ###############
    # Played after: (Select box)
    ###############
    play_date_range = st.selectbox(
        "Played after:",
        play_date_range_mapping_keys,
        on_change=play_date_range_changed,
        index=play_date_range_mapping_keys.index(st.query_params.play_date_range),
        key="play_date_range",
    )

    if play_date_range == "All":
        current_played_after = (
            replay_dataset.iloc[0]["played_at"].to_pydatetime().timestamp()
        )
    else:
        current_played_after = (
            datetime.now() - timedelta(days=play_date_range_mapping[play_date_range])
        ).timestamp()

    ###############
    # Played after: (Slider)
    ###############
    played_after = st.slider(
        "Played after:",
        value=datetime.fromtimestamp(float(current_played_after)),
        min_value=replay_dataset.iloc[0]["played_at"],
        max_value=replay_dataset.iloc[last_replay_row_idx]["played_at"],
        format="MM/DD",
    )

    replay_dataset = replay_dataset[replay_dataset["played_at"] >= played_after]
    last_replay_row_idx = len(replay_dataset) - 1

    ###############
    # My character: (Select box)
    ###############
    my_character_filter = st.selectbox(
        "My character",
        my_character_list,
        index=my_character_list.index(st.query_params.my_character_filter),
        key="my_character_filter",
        on_change=my_character_filter_changed,
    )
    replay_dataset = replay_viewer_helper.filter_replay_dataset_by_my_character(
        my_character_filter, replay_dataset, player_name
    )
    last_replay_row_idx = len(replay_dataset) - 1

    ###############
    # Opponent character: (Select box)
    ###############
    opponent_character_filter = st.selectbox(
        "Opponent character",
        opponent_character_list,
        index=opponent_character_list.index(st.query_params.opponent_character_filter),
        key="opponent_character_filter",
        on_change=opponent_character_filter_changed,
    )
    replay_dataset = replay_viewer_helper.filter_replay_dataset_by_opponent_character(
        opponent_character_filter, replay_dataset, player_name
    )
    last_replay_row_idx = len(replay_dataset) - 1

    ###############
    # Result: (Select box)
    ###############
    result_filter = st.selectbox(
        "Result",
        result_list,
        index=result_list.index(st.query_params.result_filter),
        key="result_filter",
        on_change=result_filter_changed,
    )
    replay_dataset = replay_viewer_helper.filter_replay_dataset_by_result(
        result_filter, replay_dataset, player_name
    )
    last_replay_row_idx = len(replay_dataset) - 1

    ###############
    # Match range: (Slider)
    ###############
    min_match_range, max_match_range = st.slider(
        "Match range",
        replay_dataset.index[0],
        replay_dataset.index[last_replay_row_idx],
        (
            replay_dataset.index[0],
            replay_dataset.index[last_replay_row_idx],
        ),
    )

    replay_dataset = replay_dataset[
        (replay_dataset.index >= min_match_range)
        & (replay_dataset.index <= max_match_range)
    ]
    last_replay_row_idx = len(replay_dataset) - 1

    if (
        "current_replay_row_idx" not in st.query_params
        or int(st.query_params.current_replay_row_idx) > last_replay_row_idx
    ):
        st.query_params.current_replay_row_idx = last_replay_row_idx

player_dataset = replay_viewer_helper.get_player_dataset(replay_dataset, player_name)

if len(player_dataset) != len(replay_dataset):
    st.error(
        f"""
        Length of Replay dataset and Player dataset don't match.
        Please check that the `replay_viewer.player_name` in config.yaml is set correctly.
        replay_dataset: {len(replay_dataset)}
        player_dataset: {len(player_dataset)}
        """
    )
    st.stop()

current_row = replay_dataset.iloc[int(st.query_params.current_replay_row_idx)]
current_row_player_side = player_dataset.iloc[
    int(st.query_params.current_replay_row_idx)
]["player_side"]

replay_id = current_row["replay_id"]
round_id = int(st.query_params.round_id)
next_match_exist = int(st.query_params.current_replay_row_idx) < last_replay_row_idx
prev_match_exist = int(st.query_params.current_replay_row_idx) > 0
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

col_1.markdown(
    f"<p class='big-font'>Replay ID: {current_row['replay_id']}</p>",
    unsafe_allow_html=True,
)

col_2.markdown(
    f"<p class='big-font'>Date: {current_row['played_at']}</p>", unsafe_allow_html=True
)
col_3.markdown(
    f"<p class='big-font'>Round: {st.query_params.round_id}</p>",
    unsafe_allow_html=True,
)
col_4.markdown(
    f"<p class='big-font'><a href='{video_path}' download='replay.mp4'>Download replay</a></p>",
    unsafe_allow_html=True,
)

st.slider(
    "Match",
    min_value=0,
    max_value=last_replay_row_idx,
    value=int(st.query_params.current_replay_row_idx),
    key="current_replay_row_idx",
    on_change=current_replay_row_idx_changed,
)

# -------------------------------------------------------------------

base_tooltip = ["match", "rank", "character", "played_at", "replay_id"]

# -------------------------------------------------------------------

st.subheader("Road to Master", divider=True)

if player_dataset["lp"].isnull().all():
    st.write("No data available.")
else:
    tab_date, tab_match = st.tabs(["Date", "Match"])

    with tab_date:
        st.altair_chart(
            replay_viewer_helper.get_chart_lp_date(
                player_dataset, interval_mapping, interval
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
                player_dataset,
                interval_mapping,
                interval,
                min_mr_in_chart,
                max_mr_in_chart,
            ),
            use_container_width=True,
        )

    with tab_match:
        st.altair_chart(
            replay_viewer_helper.get_chart_mr_match(
                player_dataset,
                min_match_range,
                max_match_range,
                base_tooltip,
                min_mr_in_chart,
                max_mr_in_chart,
            ),
            use_container_width=True,
        )

# -------------------------------------------------------------------

st.subheader("Result", divider=True)

tab_win_rate, tab_match_count = st.tabs(["Win rate", "Match count"])

result_dataset_total = (
    player_dataset[["played_at", "result"]]
    .groupby([pd.Grouper(key="played_at", freq=interval_mapping[interval])])
    .count()
)
result_dataset_wins = (
    player_dataset[["played_at", "result"]]
    .query("result == 'wins'")
    .groupby([pd.Grouper(key="played_at", freq=interval_mapping[interval])])
    .count()
)

result_dataset_div = (
    result_dataset_wins.div(result_dataset_total)
    .round(2)
    .rename(columns={"result": "wins"})
    .add_suffix("_rate")
    .reset_index()
)

result_dataset_total = result_dataset_total.reset_index()
result_dataset_total.replace(0, numpy.nan, inplace=True)

with tab_win_rate:
    st.altair_chart(
        replay_viewer_helper.get_chart_result_win_rate(result_dataset_div),
        use_container_width=True,
    )
with tab_match_count:
    st.altair_chart(
        replay_viewer_helper.get_chart_result_match_count(result_dataset_total),
        use_container_width=True,
    )

# -------------------------------------------------------------------

st.subheader("Result by character", divider=True)

tab_win_rate, tab_match_count, tab_priority_score = st.tabs(
    ["Win rate", "Match count", "Priority"]
)

opponent_dataset = replay_viewer_helper.get_opponent_dataset(
    replay_dataset, player_name
)

opponent_dataset_priority = replay_viewer_helper.get_opponent_dataset_priority(
    opponent_dataset, interval_mapping, interval
)

opponent_dataset_priority = opponent_dataset_priority.reset_index()

with tab_priority_score:
    st.altair_chart(
        replay_viewer_helper.get_chart_result_by_character_priority_score(
            opponent_dataset_priority
        ),
        use_container_width=True,
    )

    """
    Priority score is calculated by the formula: count * (1 - win rate).
    The higher the score, the more you should prioritize the specific matchup.
    """

with tab_win_rate:
    st.altair_chart(
        replay_viewer_helper.get_chart_result_by_character_win_rate(
            opponent_dataset_priority
        ),
        use_container_width=True,
    )
with tab_match_count:
    st.altair_chart(
        replay_viewer_helper.get_chart_result_by_character_match_count(
            opponent_dataset_priority
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
