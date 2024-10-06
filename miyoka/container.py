from dependency_injector import containers, providers
from miyoka.libs.logger import setup_logger
from miyoka.libs.storages import (
    ReplayStorage,
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
import importlib


def dynamic_import(game, klass_path, *args, **kwargs):
    print(f"importing miyoka.{game}.{klass_path}")
    ns, klass_name = klass_path.split(".")
    module = importlib.import_module(f"miyoka.{game}.{ns}")
    klass = getattr(module, klass_name)
    return klass(*args, **kwargs)


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(yaml_files=["./config.yaml"])

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
        bucket_name=config.gcp.storages.replays.bucket_name,
        download_dir=config.gcp.storages.replays.download_dir,
        skip_download=config.gcp.storages.replays.skip_download,
        sa_signed_url_generator_email=config.gcp.service_accounts.signed_url_generator.email,
    )

    frame_storage = providers.Singleton(
        FrameStorage,
        storage_client=storage_client,
        logger=logger,
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

    replay_uploader = providers.Factory(
        dynamic_import,
        game=config.game.name,
        klass_path="replay_uploader.ReplayUploader",
        logger=logger,
        replay_search_user_code=config.replay_uploader.user_code,
        replay_search_replay_id=config.replay_uploader.replay_id,
        analyzer_operation_mode=config.replay_uploader.analyzer_operation_mode,
        max_replays_per_run=config.replay_uploader.max_replays_per_run,
        stop_after_duplicate_replays=config.replay_uploader.stop_after_duplicate_replays,
        skip_recording=config.replay_uploader.skip_recording,
        replay_analyzer_factory=replay_analyzer.provider,
        game_window_helper=game_window_helper,
        replay_dataset=replay_dataset,
        replay_storage=replay_storage,
        cloud_run=cloud_run,
    )

    screen_customizer = providers.Factory(
        dynamic_import,
        game=config.game.name,
        klass_path="screen_customizer.ScreenCustomizer",
        logger=logger,
        game_window_helper=game_window_helper,
    )

    replay_viewer_helper = providers.Factory(
        ReplayViewerHelper,
        logger=logger,
        password=config.replay_viewer.password,
        debug_mode=config.replay_viewer.debug_mode,
        player_name=config.replay_viewer.player_name,
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
