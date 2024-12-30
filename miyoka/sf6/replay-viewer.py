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
    st.query_params.current_round_id = 1


def prev_match():
    st.query_params.current_replay_row_idx = (
        int(st.query_params.current_replay_row_idx) - 1
    )
    st.query_params.current_round_id = 1


def next_round():
    st.query_params.current_round_id = int(st.query_params.current_round_id) + 1


def prev_round():
    st.query_params.current_round_id = int(st.query_params.current_round_id) - 1


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
    st.query_params.play_date_range_changed = True
    st.query_params.filter_changed = True


def filter_changed():
    st.query_params.filter_changed = True


def clear_query_params():
    st.query_params.clear()


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

last_replay_row_idx = len(replay_dataset) - 1

if "current_replay_row_idx" not in st.query_params:
    st.query_params.current_replay_row_idx = last_replay_row_idx

if "current_round_id" not in st.query_params:
    st.query_params.current_round_id = 1

result_list = ("all", "wins", "loses")


def result_filter_changed():
    st.query_params.current_result_filter_index = result_list.index(
        st.session_state.result_filter
    )
    st.query_params.filter_changed = True


if "current_result_filter_index" not in st.query_params:
    st.query_params.current_result_filter_index = result_list.index("all")

character_list = replay_viewer_helper.get_character_list(replay_dataset)
character_list = ("all", *character_list)


def character_filter_changed():
    st.query_params.current_character_filter_index = character_list.index(
        st.session_state.character_filter
    )
    st.query_params.filter_changed = True


if "current_character_filter_index" not in st.query_params:
    st.query_params.current_character_filter_index = character_list.index("all")

if "play_date_range_changed" not in st.query_params:
    st.query_params.play_date_range_changed = True

if "filter_changed" not in st.query_params:
    st.query_params.filter_changed = True

played_after_mapping = {
    "Last 1 day": 1,
    "Last 2 days": 2,
    "Last 7 days": 7,
    "Last 14 days": 14,
    "Last 30 days": 30,
    "All": -1,
}

played_after_mapping_keys = [key for key in played_after_mapping]

if "played_after_option_index" not in st.query_params:
    if replay_viewer_helper.default_played_after_filter:
        st.query_params.played_after_option_index = played_after_mapping_keys.index(
            replay_viewer_helper.default_played_after_filter
        )
    else:
        st.query_params.played_after_option_index = len(played_after_mapping_keys) - 1


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
    st.subheader("Chart Visualization")

    interval_option = st.selectbox(
        "Aggregation Interval",
        ("Daily", "Weekly", "Monthly", "Yearly"),
    )

    interval_mapping = {
        "Daily": "D",
        "Weekly": "W",
        "Monthly": "ME",
        "Yearly": "YE",
    }

    st.subheader("Filters")

    played_after_option = st.selectbox(
        "Played after:",
        played_after_mapping_keys,
        on_change=play_date_range_changed,
        index=int(st.query_params.played_after_option_index),
    )

    if st.query_params.play_date_range_changed == "True":
        if played_after_option == "All":
            st.query_params.current_played_after = (
                replay_dataset.iloc[0]["played_at"].to_pydatetime().timestamp()
            )
        else:
            st.query_params.current_played_after = (
                datetime.now()
                - timedelta(days=played_after_mapping[played_after_option])
            ).timestamp()

        st.query_params.play_date_range_changed = False

    played_after = st.slider(
        "Played after:",
        value=datetime.fromtimestamp(float(st.query_params.current_played_after)),
        min_value=replay_dataset.iloc[0]["played_at"],
        max_value=replay_dataset.iloc[last_replay_row_idx]["played_at"],
        format="MM/DD",
    )

    replay_dataset = replay_dataset[replay_dataset["played_at"] >= played_after]
    last_replay_row_idx = len(replay_dataset) - 1

    # Filter by character
    character_filter = st.selectbox(
        "Character",
        character_list,
        index=int(st.query_params.current_character_filter_index),
        key="character_filter",
        on_change=character_filter_changed,
    )
    replay_dataset = replay_viewer_helper.filter_replay_dataset_by_character(
        character_filter, replay_dataset, player_name
    )
    last_replay_row_idx = len(replay_dataset) - 1

    # Filter by result
    result_filter = st.selectbox(
        "Result",
        result_list,
        index=int(st.query_params.current_result_filter_index),
        key="result_filter",
        on_change=result_filter_changed,
    )
    replay_dataset = replay_viewer_helper.filter_replay_dataset_by_result(
        result_filter, replay_dataset, player_name
    )
    last_replay_row_idx = len(replay_dataset) - 1

    # Filter by match range
    min_match_range, max_match_range = st.slider(
        "Match range",
        replay_dataset.index[0],
        replay_dataset.index[last_replay_row_idx],
        (
            replay_dataset.index[0],
            replay_dataset.index[last_replay_row_idx],
        ),
        on_change=filter_changed,
    )

    replay_dataset = replay_dataset[
        (replay_dataset.index >= min_match_range)
        & (replay_dataset.index <= max_match_range)
    ]
    last_replay_row_idx = len(replay_dataset) - 1

    if st.query_params.filter_changed == "True":
        st.query_params.current_replay_row_idx = last_replay_row_idx
        st.query_params.filter_changed = False

    st.button("Reset", on_click=clear_query_params)

current_row = replay_dataset.iloc[int(st.query_params.current_replay_row_idx)]
current_row_player_side = (
    1 if re.match(player_name, current_row["p1_player_name"]) else 2
)
replay_id = current_row["replay_id"]
round_id = int(st.query_params.current_round_id)
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

if not should_redact_pii:
    col_1.markdown(
        f"<p class='big-font'>Replay ID: {current_row['replay_id']}</p>",
        unsafe_allow_html=True,
    )

col_2.markdown(
    f"<p class='big-font'>Date: {current_row['played_at']}</p>", unsafe_allow_html=True
)
col_3.markdown(
    f"<p class='big-font'>Round: {st.query_params.current_round_id}</p>",
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

tab_win_rate, tab_match_count = st.tabs(["Win rate", "Match count"])

result_dataset_total = (
    player_dataset[["played_at", "result"]]
    .groupby([pd.Grouper(key="played_at", freq=interval_mapping[interval_option])])
    .count()
)
result_dataset_wins = (
    player_dataset[["played_at", "result"]]
    .query("result == 'wins'")
    .groupby([pd.Grouper(key="played_at", freq=interval_mapping[interval_option])])
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
    opponent_dataset, interval_mapping, interval_option
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
