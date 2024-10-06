import streamlit as st
import numpy as np
import pandas as pd
from miyoka.container import Container
from miyoka.libs.bigquery import FrameDataset
from miyoka.libs.replay_viewer_helper import ReplayViewerHelper

st.title("Chart")

cache_ttl = 3600  # 1 hour


@st.cache_resource(ttl=cache_ttl, show_spinner="Loading dataset...")
def load_frame_dataset():
    frame_dataset: FrameDataset = Container().frame_dataset()
    return frame_dataset.get_all_rows(mode="classic")


@st.cache_resource(ttl=cache_ttl, show_spinner="Loading replay viewer...")
def load_replay_viewer():
    return Container().replay_viewer()


frame_df: pd.DataFrame = load_frame_dataset()
replay_viewer: ReplayViewer = load_replay_viewer()

###############################################################################################
# View
###############################################################################################

# In production, users must enter the global password otherwise can't access the page.
if not replay_viewer.check_password():
    st.stop()

# MessageSizeError: Data of size 2934.3 MB exceeds the message size limit of 200.0 MB.
if replay_viewer.debug_mode:
    st.dataframe(frame_df)

p1_character_count_df = frame_df.groupby(
    "p1_character",
)["replay_id"].nunique()
p2_character_count_df = frame_df.groupby("p2_character")["replay_id"].nunique()
merged_df = (
    pd.concat([p1_character_count_df, p2_character_count_df]).groupby(level=0).sum()
)

st.subheader("Total replay count per character", divider=True)
merged_df = merged_df.rename_axis("character").rename("count")
st.bar_chart(merged_df, x_label="character", y_label="replay count")

st.subheader("Recorded replay count per date", divider=True)
daily_df = frame_df.groupby([frame_df["recorded_at"].dt.date])["replay_id"].nunique()
daily_df = daily_df.rename_axis("date").rename("count")
st.bar_chart(daily_df)
