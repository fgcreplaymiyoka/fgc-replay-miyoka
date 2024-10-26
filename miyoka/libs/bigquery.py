from google.cloud import bigquery
from google.cloud.bigquery import Client
from google.api_core.exceptions import Conflict
from logging import Logger
from datetime import datetime, timezone, timedelta
import os
import pandas as pd
from typing import Optional
import json


def init_bq_client(project_id: str, location: str):
    return bigquery.Client(project=project_id, location=location)


class BaseBqClient:
    def __init__(
        self, dataset_name: str, table_name: str, bq_client: Client, logger: Logger
    ):
        self.dataset_name = dataset_name
        self.table_name = table_name
        self.bq_client = bq_client
        self.logger = logger

        self.ensure_dataset()

    def ensure_dataset(self):
        dataset_id = f"{self.bq_client.project}.{self.dataset_name}"
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = self.bq_client.location

        try:
            dataset = self.bq_client.create_dataset(
                dataset, timeout=30
            )  # Make an API request.
            print(
                "Created dataset {}.{}".format(
                    self.bq_client.project, dataset.dataset_id
                )
            )
        except Conflict:
            print(
                "Dataset {}.{} already exists".format(
                    self.bq_client.project, dataset.dataset_id
                )
            )

    def ensure_table(self, schema):
        table_id = f"{self.bq_client.project}.{self.dataset_name}.{self.table_name}"
        table = bigquery.Table(table_id, schema=schema)
        table = self.bq_client.create_table(table, exists_ok=True)


class ReplayDataset(BaseBqClient):
    def __init__(
        self,
        dataset_name: str,
        table_name: str,
        bq_client: Client,
        logger: Logger,
    ):
        super().__init__(dataset_name, table_name, bq_client, logger)

        schema = [
            bigquery.SchemaField("replay_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("metadata", "JSON", mode="REQUIRED"),
            bigquery.SchemaField("recorded_at", "DATETIME", mode="REQUIRED"),
        ]

        self.ensure_table(schema)

    def is_exists(self, replay_id):
        table_id = f"{self.bq_client.project}.{self.dataset_name}.{self.table_name}"
        query = (
            f"SELECT COUNT(*) as cnt FROM {table_id} WHERE replay_id = '{replay_id}'"
        )
        query_job = self.bq_client.query(query)
        result = query_job.result()
        return list(result)[0].cnt > 0

    def insert(self, replay_id, metadata: dict):
        data = [
            {
                "replay_id": replay_id,
                "metadata": json.dumps(metadata),
                "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            }
        ]

        table_id = f"{self.bq_client.project}.{self.dataset_name}.{self.table_name}"
        self.logger.info(f"Inserting data into {table_id} data: {data}")
        errors = self.bq_client.insert_rows_json(table_id, data)

        if errors == []:
            self.logger.info("New rows have been added.")
        else:
            self.logger.info(
                "Encountered errors while inserting rows: {}".format(errors)
            )

    def get_metadata(self, replay_id) -> dict:
        table_id = f"{self.bq_client.project}.{self.dataset_name}.{self.table_name}"
        rows = self.bq_client.query(
            f"SELECT * FROM `{table_id}` WHERE replay_id = '{replay_id}' LIMIT 1"
        ).to_dataframe()
        return rows.iloc[0]["metadata"]

    def get_all_rows(self, time_range: str = "30 days"):
        table_id = f"{self.bq_client.project}.{self.dataset_name}.{self.table_name}"

        delta = pd.Timedelta(time_range).to_pytimedelta()
        min_played_at = (datetime.now(timezone.utc) - delta).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        all_rows = self.bq_client.query(
            f"""
        SELECT replay_id,
               STRING(metadata.p1.character) as p1_character,
               STRING(metadata.p1.mode) as p1_mode,
               LAX_INT64(metadata.p1.mr) as p1_mr,
               LAX_INT64(metadata.p1.lp) as p1_lp,
               STRING(metadata.p1.player_name) as p1_player_name,
               STRING(metadata.p1.rank) as p1_rank,
               STRING(metadata.p1.result) as p1_result,
               JSON_QUERY_ARRAY(metadata.p1.round_results) as p1_round_results,
               STRING(metadata.p2.character) as p2_character,
               STRING(metadata.p2.mode) as p2_mode,
               LAX_INT64(metadata.p2.mr) as p2_mr,
               LAX_INT64(metadata.p2.lp) as p2_lp,
               STRING(metadata.p2.player_name) as p2_player_name,
               STRING(metadata.p2.rank) as p2_rank,
               STRING(metadata.p2.result) as p2_result,
               JSON_QUERY_ARRAY(metadata.p2.round_results) as p2_round_results,
               metadata.played_at as played_at,
               recorded_at
        FROM `{table_id}`
        WHERE JSON_VALUE(metadata.played_at) >= "{min_played_at}"
        ORDER BY JSON_VALUE(metadata.played_at) ASC
        """
        ).to_dataframe()

        all_rows["played_at"] = pd.to_datetime(all_rows["played_at"])

        return all_rows


class FrameDataset(BaseBqClient):
    def __init__(
        self,
        dataset_name: str,
        table_name: str,
        bq_client: Client,
        logger: Logger,
    ):
        super().__init__(dataset_name, table_name, bq_client, logger)

        schema = [
            bigquery.SchemaField("replay_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("round_id", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("frame_id", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("p1_input", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("p2_input", "STRING", mode="REQUIRED"),
        ]

        self.ensure_table(schema)

    def is_exists(self, replay_id, round_id):
        table_id = f"{self.bq_client.project}.{self.dataset_name}.{self.table_name}"
        query = f"SELECT COUNT(*) as cnt FROM {table_id} WHERE replay_id = '{replay_id}' AND round_id = {round_id}"
        query_job = self.bq_client.query(query)
        result = query_job.result()
        return list(result)[0].cnt > 0

    def insert(self, replay_id, round_id, frame_data: list[dict]):
        if frame_data == []:
            self.logger.info("No rows to bigquery.")
            return

        for d in frame_data:
            d["replay_id"] = replay_id
            d["round_id"] = round_id
            d["p1_input"] = " ".join(d["p1_input"])
            d["p2_input"] = " ".join(d["p2_input"])

        table_id = f"{self.bq_client.project}.{self.dataset_name}.{self.table_name}"
        self.logger.info(f"Inserting data into {table_id}")
        errors = self.bq_client.insert_rows_json(table_id, frame_data)

        if errors == []:
            self.logger.info("New rows have been added.")
        else:
            self.logger.info(
                "Encountered errors while inserting rows: {}".format(errors)
            )

    def iterate_rounds(
        self,
        mode: str,
        use_cache: bool = False,
        min_round_frame_length: int = 1200,  # At least the round is longer than 20 sec (20 * 60 frames)
        limit: Optional[int] = None,
        character: Optional[str] = None,
    ):
        all_rows = self.get_all_rows(
            character=character,
            mode=mode,
            use_cache=use_cache,
        )
        all_rows_by_group = all_rows.groupby(["replay_id", "round_id"])

        iter_count = 0

        for (replay_id, round_id), round_rows in all_rows_by_group:
            if len(round_rows) < min_round_frame_length:
                print(
                    f"WARN: Frames for this round is too short. Skipped. replay_id: {replay_id} | round_id: {round_id}"
                )
                continue

            iter_count += 1
            if limit and iter_count > limit:
                print(f"WARN: Reached iteration limit: {limit}")
                break

            yield (replay_id, round_id, round_rows)

    def get_all_rows(
        self,
        mode: str,
        use_cache: bool = False,
        character: Optional[str] = None,
        delta=timedelta(days=30),  # last 30 days
    ):
        CACHE_FILE_NAME = "frame_dataset.pkl"

        if use_cache and os.path.isfile(CACHE_FILE_NAME):
            print(f"loading from local cache {CACHE_FILE_NAME}")
            return pd.read_pickle(CACHE_FILE_NAME)

        where_clauses = []

        if character:
            where_clauses.append(
                f"(p1_character = '{character}' OR p2_character = '{character}')"
            )

        min_recorded_at = (datetime.now(timezone.utc) - delta).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        where_clauses.append(f'recorded_at >= "{min_recorded_at}"')
        where_clauses.append(f"p1_mode = '{mode}' AND p2_mode = '{mode}'")

        table_id = f"{self.bq_client.project}.{self.dataset_name}.frames"

        print(f"loading from big query")
        all_rows = self.bq_client.query(
            f"""
        SELECT *
        FROM `{table_id}`
        WHERE {" AND ".join(where_clauses)}
        ORDER BY replay_id, round_id, frame_id
        """
        ).to_dataframe()

        if use_cache:
            all_rows.to_pickle(CACHE_FILE_NAME)

        return all_rows
