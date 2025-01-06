from logging import Logger
import hmac
import pandas as pd

try:
    import streamlit as st
    import altair as alt
except (ImportError, NotImplementedError) as e:
    print(
        "WARN: streamlit is not installed. You cannot run replay viewer in this environment."
    )


class ReplayViewerHelper:
    def __init__(
        self,
        logger: Logger,
        password: str,
        player_name: str,
        time_range: str,
        after_time: str,
        min_mr_in_chart: int | None,
        max_mr_in_chart: int | None,
        default_played_after_filter: str,
        debug_mode: bool,
        *args,
        **kwargs,
    ):
        self.logger = logger
        self.password = password
        self.player_name = player_name
        self.time_range = time_range
        self.after_time = after_time
        self.default_played_after_filter = default_played_after_filter
        self._debug_mode = debug_mode
        self.min_mr_in_chart = min_mr_in_chart or 1000
        self.max_mr_in_chart = max_mr_in_chart or 2000

    @property
    def debug_mode(self):
        return self._debug_mode

    def check_password(self):
        """Returns `True` if the user had the correct password."""

        def password_entered():
            """Checks whether a password entered by the user is correct."""
            if hmac.compare_digest(st.session_state["password"], self.password):
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # Don't store the password.
            else:
                st.session_state["password_correct"] = False

        # Return True if the password is validated.
        if self.password == "None" or st.session_state.get("password_correct", False):
            return True

        if not self.password:
            st.error(
                "❌ Password is not set to this Miyoka server. Ask the administrator if they correctly set it."
            )
            return False

        # Show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        if "password_correct" in st.session_state:
            st.error("😕 Password incorrect")
        return False

    @property
    def should_redact_pii(self):
        return self.password == "None"

    def get_chart_lp_rules(self):
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
                alt.Y("lp:Q", title=None),
                color=alt.value("#224455"),
                opacity=alt.value(0.3),
            )
        )

        text = (
            alt.Chart(thresholds)
            .mark_text(align="center", dy=-5)
            .encode(alt.Y("lp:Q", title=None), text="rank", opacity=alt.value(0.3))
        )

        return rules + text

    def get_chart_lp_date(self, player_dataset, interval_mapping, interval_option):
        lp_dataset = (
            player_dataset[["played_at", "lp"]]
            .groupby(
                [pd.Grouper(key="played_at", freq=interval_mapping[interval_option])]
            )
            .mean()
            .reset_index()
        )

        c = (
            alt.Chart(lp_dataset)
            .mark_bar(clip=True)
            .encode(
                x=alt.X(
                    "yearmonthdate(played_at):O",
                    title=None,
                    axis=alt.Axis(format="%b %d"),
                ),
                y=alt.Y("lp:Q", title=None, axis=alt.Axis(format=".0f")),
            )
        )
        chart = c + self.get_chart_lp_rules()
        return chart

    def get_chart_lp_match(
        self, player_dataset, base_tooltip, min_match_range, max_match_range
    ):
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
                color=alt.Color(
                    "character:N",
                    legend=alt.Legend(orient="bottom"),
                    scale=alt.Scale(scheme="set3"),
                ),
            )
        )
        chart = c + self.get_chart_lp_rules()
        return chart

    def get_chart_mr_date(
        self,
        player_dataset,
        interval_mapping,
        interval_option,
        min_mr_in_chart,
        max_mr_in_chart,
    ):
        mr_dataset = (
            player_dataset[["played_at", "mr"]]
            .groupby(
                [pd.Grouper(key="played_at", freq=interval_mapping[interval_option])]
            )
            .mean()
            .reset_index()
        )

        c = (
            alt.Chart(mr_dataset)
            .mark_bar(clip=True)
            .encode(
                x=alt.X(
                    "yearmonthdate(played_at):O",
                    title=None,
                    axis=alt.Axis(format="%b %d"),
                ),
                y=alt.Y("mr:Q", title=None, axis=alt.Axis(format=".0f")).scale(
                    domain=(min_mr_in_chart, max_mr_in_chart)
                ),
            )
        )
        return c

    def get_chart_mr_match(
        self,
        player_dataset,
        min_match_range,
        max_match_range,
        base_tooltip,
        min_mr_in_chart,
        max_mr_in_chart,
    ):
        c = (
            alt.Chart(player_dataset)
            .mark_bar(clip=True)
            .encode(
                x=alt.X(
                    "match:Q",
                    scale=alt.Scale(domain=[min_match_range, max_match_range]),
                    title=None,
                ),
                y=alt.Y("mr:Q", title=None).scale(
                    domain=(min_mr_in_chart, max_mr_in_chart)
                ),
                tooltip=["mr"] + base_tooltip,
                color=alt.Color(
                    "character:N",
                    legend=alt.Legend(orient="bottom"),
                    scale=alt.Scale(scheme="set3"),
                ),
            )
        )
        return c

    def filter_replay_dataset_by_result(
        self, result_filter, replay_dataset, player_name
    ):
        if result_filter == "all":
            return replay_dataset

        return replay_dataset[
            (
                replay_dataset["p1_player_name"].str.contains(
                    player_name, case=False, na=False
                )
                & (replay_dataset["p1_result"] == result_filter)
            )
            | (
                replay_dataset["p2_player_name"].str.contains(
                    player_name, case=False, na=False
                )
                & (replay_dataset["p2_result"] == result_filter)
            )
        ]

    def filter_replay_dataset_by_character(
        self, character_filter, replay_dataset, player_name
    ):
        if character_filter == "all":
            return replay_dataset

        return replay_dataset[
            (
                ~replay_dataset["p1_player_name"].str.contains(
                    player_name, case=False, na=False
                )
                & (replay_dataset["p1_character"] == character_filter)
            )
            | (
                ~replay_dataset["p2_player_name"].str.contains(
                    player_name, case=False, na=False
                )
                & (replay_dataset["p2_character"] == character_filter)
            )
        ]

    def get_character_list(self, replay_dataset):
        return pd.concat(
            [replay_dataset["p1_character"], replay_dataset["p2_character"]]
        ).unique()

    def get_player_dataset(self, replay_dataset, player_name):
        p1_player_dataset = replay_dataset[
            replay_dataset["p1_player_name"].str.contains(
                player_name, case=False, na=False
            )
        ]
        p2_player_dataset = replay_dataset[
            replay_dataset["p2_player_name"].str.contains(
                player_name, case=False, na=False
            )
        ]
        p1_player_dataset = p1_player_dataset[
            [
                "p1_rank",
                "p1_lp",
                "p1_mr",
                "p1_result",
                "p1_round_results",
                "p1_character",
                "replay_id",
                "played_at",
            ]
        ].rename(
            columns={
                "p1_rank": "rank",
                "p1_lp": "lp",
                "p1_mr": "mr",
                "p1_result": "result",
                "p1_round_results": "round_results",
                "p1_character": "character",
            }
        )
        p1_player_dataset["player_side"] = 1
        p2_player_dataset = p2_player_dataset[
            [
                "p2_rank",
                "p2_lp",
                "p2_mr",
                "p2_result",
                "p2_round_results",
                "p2_character",
                "replay_id",
                "played_at",
            ]
        ].rename(
            columns={
                "p2_rank": "rank",
                "p2_lp": "lp",
                "p2_mr": "mr",
                "p2_result": "result",
                "p2_round_results": "round_results",
                "p2_character": "character",
            }
        )
        p2_player_dataset["player_side"] = 2
        player_dataset = pd.concat([p1_player_dataset, p2_player_dataset], axis=0)
        player_dataset = player_dataset.reset_index().rename(columns={"index": "match"})
        player_dataset = player_dataset.sort_values(by="match")
        return player_dataset

    def get_opponent_dataset(self, replay_dataset, player_name):
        p1_opponent_dataset = replay_dataset[
            ~replay_dataset["p1_player_name"].str.contains(
                player_name, case=False, na=False
            )
        ]
        p2_opponent_dataset = replay_dataset[
            ~replay_dataset["p2_player_name"].str.contains(
                player_name, case=False, na=False
            )
        ]
        p1_opponent_dataset = p1_opponent_dataset[
            ["p1_character", "p1_result", "played_at"]
        ].rename(
            columns={
                "p1_character": "character",
                "p1_result": "result",
            }
        )
        p2_opponent_dataset = p2_opponent_dataset[
            ["p2_character", "p2_result", "played_at"]
        ].rename(
            columns={
                "p2_character": "character",
                "p2_result": "result",
            }
        )
        opponent_dataset = pd.concat([p1_opponent_dataset, p2_opponent_dataset], axis=0)
        return opponent_dataset

    def get_opponent_dataset_priority(
        self, opponent_dataset: pd.DataFrame, interval_mapping, interval_option
    ) -> pd.DataFrame:
        opponent_dataset_total = (
            opponent_dataset.groupby(
                [
                    pd.Grouper(key="played_at", freq=interval_mapping[interval_option]),
                    "character",
                ]
            )
            .count()
            .rename(columns={"result": "count"})
        )

        opponent_dataset_loses = (
            opponent_dataset.query("result == 'loses'")
            .groupby(
                [
                    pd.Grouper(key="played_at", freq=interval_mapping[interval_option]),
                    "character",
                ]
            )
            .count()
            .rename(columns={"result": "count"})
        )

        opponent_dataset_div = (
            opponent_dataset_loses.div(opponent_dataset_total)
            .round(2)
            .rename(columns={"count": "wins"})
            .add_suffix("_rate")
            .fillna(0.0)
        )

        opponent_dataset_priority = opponent_dataset_div.join(opponent_dataset_total)
        opponent_dataset_priority["priority"] = opponent_dataset_priority.apply(
            lambda row: row["count"] * (1.0 - row["wins_rate"]), axis=1
        )

        return opponent_dataset_priority

    def get_chart_result_by_character_priority_score(self, opponent_dataset_priority):
        return (
            alt.Chart(opponent_dataset_priority)
            .mark_rect()
            .encode(
                x=alt.X(
                    "yearmonthdate(played_at):O",
                    title=None,
                    axis=alt.Axis(format="%b %d"),
                ),
                y=alt.Y("character", title=None),
                color=alt.Color(
                    "priority:Q",
                    legend=alt.Legend(orient="bottom"),
                    scale=alt.Scale(scheme="reds"),
                ),
            )
        )

    def get_chart_result_by_character_win_rate(self, opponent_dataset_priority):
        return (
            alt.Chart(opponent_dataset_priority)
            .mark_rect()
            .encode(
                x=alt.X(
                    "yearmonthdate(played_at):O",
                    title=None,
                    axis=alt.Axis(format="%b %d"),
                ),
                y=alt.Y("character", title=None),
                color=alt.Color(
                    "wins_rate",
                    legend=alt.Legend(orient="bottom", format=".0%"),
                    scale=alt.Scale(
                        scheme="redyellowgreen",
                        domainMid=0.5,
                        domainMin=0.0,
                        domainMax=1.0,
                    ),
                ),
            )
        )

    def get_chart_result_by_character_match_count(self, opponent_dataset_priority):
        return (
            alt.Chart(opponent_dataset_priority)
            .mark_rect(clip=True)
            .encode(
                x=alt.X(
                    "yearmonthdate(played_at):O",
                    title=None,
                    axis=alt.Axis(format="%b %d"),
                ),
                y=alt.Y("character:N", title=None),
                color=alt.Color("count:Q", legend=alt.Legend(orient="bottom")),
            )
        )

    def get_chart_result_win_rate(self, result_dataset_div):
        rules = (
            alt.Chart(
                pd.DataFrame(
                    {"result": [0.5]},
                )
            )
            .mark_rule()
            .encode(
                alt.Y("result:Q", title=None),
                color=alt.value("#224455"),
                opacity=alt.value(0.3),
            )
        )

        c = (
            alt.Chart(result_dataset_div)
            .mark_bar(cornerRadius=5)
            .encode(
                x=alt.X(
                    "yearmonthdate(played_at):O",
                    title=None,
                    axis=alt.Axis(format="%b %d"),
                ),
                y=alt.Y(
                    "wins_rate:Q",
                    title=None,
                    axis=alt.Axis(format=".0%"),
                    scale=alt.Scale(domain=(0.0, 1.0)),
                ),
                color=alt.Color(
                    "wins_rate",
                    legend=alt.Legend(orient="bottom", format=".0%"),
                    scale=alt.Scale(
                        scheme="redyellowgreen",
                        domainMid=0.5,
                        domainMin=0.0,
                        domainMax=1.0,
                    ),
                ),
            )
        )
        return c + rules

    def get_chart_result_match_count(self, result_dataset_total):
        return (
            alt.Chart(result_dataset_total)
            .mark_rect(clip=True)
            .encode(
                x=alt.X(
                    "yearmonthdate(played_at):O",
                    title=None,
                    axis=alt.Axis(format="%b %d"),
                ),
                y=alt.Y("result:Q", title=None),
            )
        )
