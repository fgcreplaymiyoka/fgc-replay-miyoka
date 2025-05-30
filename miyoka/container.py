from dependency_injector import containers, providers
import os
from miyoka.libs.logger import setup_logger
from miyoka.libs.storages import (
    ReplayStorage,
    ReplayStreamingStorage,
    FrameStorage,
    init_storage_client,
)
from miyoka.libs.frame_splitter import FrameSplitter
from miyoka.sf6.round_analyzer import RoundAnalyzer
from miyoka.libs.bigquery import (
    FrameDataset,
    ReplayDataset,
    init_bq_client,
)
from miyoka.libs.replay_analyzer import ReplayAnalyzer
from miyoka.libs.cloud_run import CloudRun
from miyoka.libs.scene_exporter import SceneExporter
from miyoka.libs.scene_store import SceneStore
from miyoka.libs.replay_viewer_helper import ReplayViewerHelper
from unittest.mock import Mock
import importlib


def dynamic_import(game, klass_path, *args, **kwargs):
    print(f"importing miyoka.{game}.{klass_path}")
    ns, klass_name = klass_path.split(".")
    module = importlib.import_module(f"miyoka.{game}.{ns}")
    klass = getattr(module, klass_name)
    return klass(*args, **kwargs)


def _replay_streaming_storage_bucket_name(bucket_name: str) -> str:
    return f"{bucket_name}_streaming"


config_path = os.environ.get("MIYOKA_CONFIG_PATH", "./config.yaml")


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(yaml_files=[config_path])

    logger = providers.Singleton(
        setup_logger,
        name=config.log.name,
        dir_path=config.log.dir_path,
        file_name=config.log.file_name,
        file_output=config.log.file_output,
        standard_output=config.log.standard_output,
        clear_everytime=config.log.clear_everytime,
    )

    storage_client = providers.Singleton(
        init_storage_client,
        project_id=config.gcp.project_id,
    )

    bq_client = providers.Singleton(
        init_bq_client,
        project_id=config.gcp.project_id,
        location=config.gcp.region,
    )

    replay_storage = providers.Singleton(
        ReplayStorage,
        storage_client=storage_client,
        logger=logger,
        location=config.gcp.region,
        bucket_name=config.gcp.storages.replays.bucket_name,
        download_dir=config.gcp.storages.replays.download_dir,
        skip_download=config.gcp.storages.replays.skip_download,
        sa_signed_url_generator_email=config.gcp.service_accounts.signed_url_generator.email,
    )

    replay_streaming_storage_bucket_name = providers.Callable(
        _replay_streaming_storage_bucket_name, config.gcp.storages.replays.bucket_name
    )

    replay_streaming_storage = providers.Singleton(
        ReplayStreamingStorage,
        storage_client=storage_client,
        logger=logger,
        location=config.gcp.region,
        bucket_name=replay_streaming_storage_bucket_name,
    )

    frame_storage = providers.Singleton(
        FrameStorage,
        storage_client=storage_client,
        logger=logger,
        location=config.gcp.region,
        bucket_name=config.gcp.storages.frames.bucket_name,
        workers=config.gcp.storages.frames.workers,
        skip_upload=config.gcp.storages.frames.skip_upload,
    )

    replay_dataset = providers.Singleton(
        ReplayDataset,
        dataset_name=config.gcp.bigquery.dataset_name,
        table_name=config.gcp.bigquery.replay_dataset.table_name,
        bq_client=bq_client,
        logger=logger,
    )

    frame_dataset = providers.Singleton(
        FrameDataset,
        dataset_name=config.gcp.bigquery.dataset_name,
        table_name=config.gcp.bigquery.frame_dataset.table_name,
        bq_client=bq_client,
        logger=logger,
    )

    cloud_run = providers.Singleton(
        CloudRun,
        logger=logger,
        project=config.gcp.project_id,
        location=config.gcp.region,
        job_name=config.gcp.cloud_run_job.replay_analyzer.name,
    )

    frame_splitter = providers.Factory(
        FrameSplitter,
        logger=logger,
        export_dir=config.replay_analyzer.export_dir,
        batch_size=config.replay_analyzer.batch_size,
        clear_per_batch=config.replay_analyzer.clear_per_batch,
        skip_split=config.replay_analyzer.skip_split,
    )

    game_window_helper = providers.Singleton(
        dynamic_import,
        game=config.game.name,
        klass_path="game_window_helper.GameWindowHelper",
        logger=logger,
        window_name=config.game.window.name,
        extra=config.game.extra,
    )

    round_analyzer = providers.Factory(
        RoundAnalyzer,
        game_window_helper=game_window_helper,
        logger=logger,
        start_frame_at=config.replay_analyzer.start_frame_at,
        stop_frame_at=config.replay_analyzer.stop_frame_at,
        ignore_error=config.replay_analyzer.ignore_error,
        log_collapsed_inputs=config.replay_analyzer.log_collapsed_inputs,
        verify_inputs_count=config.replay_analyzer.verify_inputs_count,
    )

    replay_analyzer = providers.Factory(
        ReplayAnalyzer,
        logger=logger,
        replay_id=config.replay_analyzer.replay_id,
        upload_split_frames=config.replay_analyzer.upload_split_frames,
        upload_last_images=config.replay_analyzer.upload_last_images,
        replay_dataset=replay_dataset,
        replay_storage=replay_storage,
        frame_storage=frame_storage,
        frame_dataset=frame_dataset,
        frame_splitter=frame_splitter,
        round_analyzer_factory=round_analyzer.provider,
    )

    replay_dataset_selector = providers.Selector(
        config.replay_recorder.save_to,
        google_cloud_storage=replay_dataset,
        local_file_storage=providers.Factory(Mock),
    )

    replay_storage_selector = providers.Selector(
        config.replay_recorder.save_to,
        google_cloud_storage=replay_storage,
        local_file_storage=providers.Factory(Mock),
    )

    replay_streaming_storage_selector = providers.Selector(
        config.replay_recorder.save_to,
        google_cloud_storage=replay_streaming_storage,
        local_file_storage=providers.Factory(Mock),
    )

    replay_recorder = providers.Factory(
        dynamic_import,
        game=config.game.name,
        klass_path="replay_recorder.ReplayRecorder",
        logger=logger,
        replay_search_players=config.game.players,
        replay_search_replay_ids=config.game.replay_ids,
        analyzer_operation_mode=config.replay_recorder.analyzer_operation_mode,
        max_replays_per_run=config.replay_recorder.max_replays_per_run,
        stop_after_duplicate_replays=config.replay_recorder.stop_after_duplicate_replays,
        skip_recording=config.replay_recorder.skip_recording,
        save_to=config.replay_recorder.save_to,
        separate_round=config.replay_recorder.separate_round,
        replay_analyzer_factory=replay_analyzer.provider,
        game_window_helper=game_window_helper,
        replay_dataset=replay_dataset_selector,
        replay_storage=replay_storage_selector,
        replay_streaming_storage=replay_streaming_storage_selector,
        cloud_run=cloud_run,
        transcode_to_hls=config.replay_recorder.transcode_to_hls,
    )

    screen_customizer = providers.Factory(
        dynamic_import,
        game=config.game.name,
        klass_path="screen_customizer.ScreenCustomizer",
        logger=logger,
        game_window_helper=game_window_helper,
        exit_to_desktop=config.replay_recorder.exit_to_desktop,
    )

    replay_viewer_helper = providers.Factory(
        ReplayViewerHelper,
        logger=logger,
        password=config.replay_viewer.password,
        debug_mode=config.replay_viewer.debug_mode,
        players=config.game.players,
        time_range=config.replay_viewer.time_range,
        after_time=config.replay_viewer.after_time,
        min_mr_in_chart=config.replay_viewer.min_mr_in_chart,
        max_mr_in_chart=config.replay_viewer.max_mr_in_chart,
        default_played_after_filter=config.replay_viewer.default_played_after_filter,
    )

    scene_splitter = providers.Factory(
        dynamic_import,
        game=config.game.name,
        klass_path="scene_splitter.SceneSplitter",
    )

    scene_exporter = providers.Factory(
        SceneExporter,
    )

    scene_vectorizer = providers.Factory(
        dynamic_import,
        game=config.game.name,
        klass_path="scene_vectorizer.SceneVectorizer",
    )

    scene_store = providers.Factory(
        SceneStore,
    )
