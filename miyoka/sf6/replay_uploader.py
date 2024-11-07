from logging import Logger
import os
import json
import time
import pydirectinput
import subprocess
import re
from typing import Optional
from dependency_injector.providers import Factory
from datetime import datetime, timezone
from miyoka.libs.utils import cleanup_dir
from miyoka.libs.replay_analyzer import ReplayAnalyzer
from miyoka.libs.cloud_run import CloudRun
from miyoka.libs.storages import ReplayStorage
from miyoka.libs.bigquery import ReplayDataset
from miyoka.libs.replay_uploader import ReplayUploader as ReplayUploaderBase
from miyoka.libs.game_window_helper import WIDTH_1280, HEIGHT_720
from miyoka.sf6.game_window_helper import (
    GameWindowHelper,
)
from miyoka.sf6.constants import (
    get_nth_character_combination,
    replay_select_character_position,
)

pydirectinput.FAILSAFE = False

__all__ = ["ReplayUploader"]


class ReplayUploader(ReplayUploaderBase):
    def __init__(
        self,
        logger: Logger,
        game_window_helper: GameWindowHelper,
        replay_search_user_code: str,
        replay_search_replay_id: str,
        analyzer_operation_mode: bool,
        replay_analyzer_factory: Factory[ReplayAnalyzer],
        replay_dataset: ReplayDataset,
        replay_storage: ReplayStorage,
        cloud_run: CloudRun,
        max_replays_per_run: Optional[int] = None,
        stop_after_duplicate_replays: Optional[int] = None,
        skip_recording: Optional[bool] = None,
    ):
        super().__init__()

        self.logger = logger
        self.game_window_helper = game_window_helper
        self.replay_search_user_code = str(replay_search_user_code)
        self.replay_search_replay_id = replay_search_replay_id
        self.analyzer_operation_mode = analyzer_operation_mode
        self.replay_analyzer_factory = replay_analyzer_factory
        self.replay_dataset = replay_dataset
        self.replay_storage = replay_storage
        self.cloud_run = cloud_run
        self.max_replays_per_run = max_replays_per_run
        self.stop_after_duplicate_replays = stop_after_duplicate_replays
        self.skip_recording = skip_recording

        self.current_replay_id = None
        self.replay_rewind_count = 5
        self.in_replay = False
        self.replay_done = False
        self.round = 0
        self.recorded_replay_count = 0
        self.duplicate_replay_count = 0

        cleanup_dir("last_images")
        game_window_helper.wait_until_game_launched()
        game_window_helper.wait_until_game_focused()
        game_window_helper.ensure_obs()
        game_window_helper.update_game_window_size()
        game_window_helper.init_camera()

        if game_window_helper.normalized_screen_width != WIDTH_1280:
            raise ValueError(
                f"Window width must be {WIDTH_1280} but currently it's {game_window_helper.normalized_screen_width}. "
                "Please make sure that the Game setting and Windows Display setting have the same size."
            )

        if game_window_helper.normalized_screen_height != HEIGHT_720:
            raise ValueError(
                f"Window height must be {HEIGHT_720} but currently it's {game_window_helper.normalized_screen_height}. "
                "Please make sure that the Game setting and Windows Display setting have the same size."
            )

    def run(self):
        tab_repeat_mode = False
        g_repeat_mode = False

        while True:
            frame = self.game_window_helper.grab_frame()

            if self.in_replay:
                if (
                    tab_repeat_mode == False
                    and not self.game_window_helper.is_replay_options_exist(frame)
                ):
                    # Stop recording
                    ret = subprocess.run(
                        ["obs-cmd-windows-amd64.exe", "recording", "stop"],
                        capture_output=True,
                        text=True,
                    )
                    # Upload to GCS
                    recording_path_search = re.search(
                        'Result: Ok\("(.*)"\)', ret.stdout
                    )

                    try:
                        recording_path = recording_path_search.group(1)
                    except Exception as ex:
                        print("Recoding might not have started yet", ex)
                        continue

                    self.replay_storage.upload_file_in_background(
                        recording_path,
                        self.current_replay_id,
                        f"{self.round}.mp4",
                        delete_original=True,
                        initial_delay_sec=5,  # Wait for 5 seconds before starts uploading, becuase OBS might not have finished exporting the file.
                    )
                    tab_repeat_mode = True
                    self.round += 1

            screen = self.game_window_helper.identify_screen(frame)

            self.logger.info(f"screen: {screen}")

            match screen:
                case "TitleScreen":
                    self.in_replay = False
                    tab_repeat_mode = False
                    g_repeat_mode = False
                    pydirectinput.press("Tab")  # Press Any Button
                case "MainBh":
                    self.in_replay = False
                    tab_repeat_mode = False
                    g_repeat_mode = False
                    pydirectinput.press("Tab")  # Open menu
                    time.sleep(3)
                case "News":
                    pydirectinput.press("ESC")  # Exit from news
                case "MultiMenuProfile":
                    pydirectinput.press("d")  # Right
                case "MultiMenuCfn":
                    pydirectinput.press("f")  # Enter
                case "CfnPlayers":
                    pydirectinput.press("d")  # Right
                case "CfnClubs":
                    pydirectinput.press("d")  # Right
                case "CfnReplays":
                    pydirectinput.press("f")  # Enter
                    time.sleep(2)
                case "ReplaysRecommended":
                    pydirectinput.press("q")  # Left
                case "ReplaysConditionalSearch":
                    pydirectinput.press("c")  # Right
                case "KeywordSearchByPlayerName":
                    pydirectinput.press("s")  # Down in submenu
                case "KeywordSearchByUserCode":
                    if self.replay_search_user_code:
                        pydirectinput.press("f")  # Enter
                    else:
                        pydirectinput.press("s")  # Down in submenu
                case "DialogUserCode":
                    pydirectinput.press("f")  # Enter the text box
                    time.sleep(2)
                    self.logger.info(
                        f"Setting user code {self.replay_search_user_code}"
                    )
                    pydirectinput.write(self.replay_search_user_code)
                    pydirectinput.press("Enter")  # Exit the focus from the text box
                    pydirectinput.press("s")  # Down
                    pydirectinput.press("f")  # Enter - Start searching
                case "SearchResults":
                    if self.replay_done:
                        time.sleep(2)
                        pydirectinput.press("s")  # Down - Select the next replay
                        self.replay_done = False

                    pydirectinput.press("f")  # Enter - Enter a replay
                case "ReplaySummary":
                    if self.recorded_replay_count >= self.max_replays_per_run:
                        self.logger.info(
                            f"Recorded {self.recorded_replay_count} replays. Stopping."
                        )
                        return

                    if self.duplicate_replay_count >= self.stop_after_duplicate_replays:
                        self.logger.info(
                            f"Already recorded {self.duplicate_replay_count} replays. Stopping."
                        )
                        return

                    success = self.extract_replay_summary(frame)

                    if not success or self.skip_recording:
                        pydirectinput.press("ESC")  # Exit
                        self.replay_done = True
                        continue

                    pydirectinput.press("f")  # Enter - Start watching replay

                    # For showing reply menu and skipping opening
                    tab_repeat_mode = True
                    self.round = 1
                    self.recorded_replay_count += 1
                case "ReplayMenu":
                    tab_repeat_mode = False
                    g_repeat_mode = True
                    self.in_replay = True

                    pydirectinput.press("Tab")  # Close replay menu

                    time.sleep(1)

                    pydirectinput.press("r")  # Pause
                    for _ in range(self.replay_rewind_count):
                        pydirectinput.press(
                            "z"
                        )  # Previous Scene - Rolling back to the beginning of the game.

                    # Start recording
                    subprocess.run(["obs-cmd-windows-amd64.exe", "recording", "start"])

                    time.sleep(2)

                    pydirectinput.press("r")  # Resume
                case "ReplayEndDiaglogPlayAgain":
                    self.in_replay = False
                    g_repeat_mode = False
                    self.replay_done = True

                    if self.analyzer_operation_mode == "schedule":
                        # Analyze asynchronously so the uploading iteration is not blocked.
                        self.cloud_run.schedule_analyze_in_background(
                            self.current_replay_id,
                            initial_delay_sec=30,  # Wait for 30 seconds before scheduling job, becuase uploading the last round video might have not beend uploaded yet.
                        )
                    elif self.analyzer_operation_mode == "inline":
                        replay_analyzer: ReplayAnalyzer = self.replay_analyzer_factory(
                            replay_id=self.current_replay_id
                        )
                        replay_analyzer.run()
                    elif self.analyzer_operation_mode == "skip":
                        self.logger.info(f"screen: {screen}")
                    else:
                        raise Exception(
                            f"Unknown analyzer_operation_mode: {self.analyzer_operation_mode}"
                        )

                    pydirectinput.press("s")  # Down
                    pydirectinput.press("f")  # Confirm - End replay

                    self.game_window_helper.update_game_window_size()  # Reset the game window size after the analyze.
                case "ErrorCommunication" | "ErrorCommunication2":
                    pydirectinput.press("f")  # OK - Close dialog
                case "ErrorLogin":
                    pydirectinput.press("d")  # To Right
                    pydirectinput.press("f")  # Click No to the offline mode
                case "MainFg":
                    pydirectinput.press("a")  # Left
                case "OptionsLanguageDisplayLanguageEnglish" | "MultiOptions":
                    pydirectinput.press("ESC")  # Exit
                case _:
                    pass

            # time.sleep(0.2)

            if tab_repeat_mode:
                pydirectinput.press("Tab")
            if g_repeat_mode:
                pydirectinput.press("g")

            time.sleep(0.3)

    def extract_replay_summary(self, frame) -> bool:
        current_replay_id = self.game_window_helper.identify_replay_id(frame)

        self.current_replay_id = current_replay_id

        if self.replay_dataset.is_exists(current_replay_id):
            self.logger.warn(f"Replay {current_replay_id} already exists")
            self.duplicate_replay_count += 1
            return False

        played_at = self.game_window_helper.identify_played_at(frame)
        p1_wins = self.game_window_helper.identify_result(frame, player="p1")
        p2_wins = self.game_window_helper.identify_result(frame, player="p2")
        p1_mode = self.game_window_helper.identify_mode(frame, player="p1")
        p2_mode = self.game_window_helper.identify_mode(frame, player="p2")
        p1_player_name = self.game_window_helper.identify_player_name(
            frame, player="p1"
        )
        p2_player_name = self.game_window_helper.identify_player_name(
            frame, player="p2"
        )

        p1_rank = self.game_window_helper.identify_rank(frame, player="p1")
        p2_rank = self.game_window_helper.identify_rank(frame, player="p2")
        p1_mr, p2_mr = None, None
        p1_lp, p2_lp = None, None
        if p1_rank == "master":
            p1_mr = self.game_window_helper.identify_mr(frame, player="p1")
        else:
            p1_lp = self.game_window_helper.identify_lp(frame, player="p1")

        if p2_rank == "master":
            p2_mr = self.game_window_helper.identify_mr(frame, player="p2")
        else:
            p2_lp = self.game_window_helper.identify_lp(frame, player="p2")

        if not p1_rank:
            p1_rank = self.identify_rank_from_lp(p1_lp)
        if not p2_rank:
            p2_rank = self.identify_rank_from_lp(p2_lp)

        p1_character = self.game_window_helper.identify_character(frame, player="p1")
        p2_character = self.game_window_helper.identify_character(frame, player="p2")
        p1_round_results = self.game_window_helper.identify_round_results(
            frame, player="p1"
        )
        p2_round_results = self.game_window_helper.identify_round_results(
            frame, player="p2"
        )

        if p1_round_results[-1] == p2_round_results[-1]:
            p1_round_results.pop()
            p2_round_results.pop()

        current_metadata = {}
        current_metadata["p1"] = {}
        current_metadata["p2"] = {}
        current_metadata["p1"]["result"] = p1_wins
        current_metadata["p2"]["result"] = p2_wins
        current_metadata["p1"]["mode"] = p1_mode
        current_metadata["p2"]["mode"] = p2_mode
        current_metadata["p1"]["rank"] = p1_rank
        current_metadata["p2"]["rank"] = p2_rank
        current_metadata["p1"]["mr"] = p1_mr
        current_metadata["p2"]["mr"] = p2_mr
        current_metadata["p1"]["lp"] = p1_lp
        current_metadata["p2"]["lp"] = p2_lp
        current_metadata["p1"]["player_name"] = p1_player_name
        current_metadata["p2"]["player_name"] = p2_player_name
        current_metadata["p1"]["character"] = p1_character
        current_metadata["p2"]["character"] = p2_character
        current_metadata["p1"]["round_results"] = p1_round_results
        current_metadata["p2"]["round_results"] = p2_round_results
        current_metadata["recorded_at"] = datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        current_metadata["played_at"] = played_at.strftime("%Y-%m-%d %H:%M:%S")

        self.replay_dataset.insert(
            current_replay_id,
            metadata=current_metadata,
        )

        return True

    def identify_rank_from_lp(self, lp):
        if lp is None:
            return "new"

        if lp < 200:
            return "rookie1"
        elif lp < 400:
            return "rookie2"
        elif lp < 600:
            return "rookie3"
        elif lp < 800:
            return "rookie4"
        elif lp < 1000:
            return "rookie5"
        elif lp < 1400:
            return "iron1"
        elif lp < 1800:
            return "iron2"
        elif lp < 2200:
            return "iron3"
        elif lp < 2600:
            return "iron4"
        elif lp < 3000:
            return "iron5"
        elif lp < 3400:
            return "bronze1"
        elif lp < 3800:
            return "bronze2"
        elif lp < 4200:
            return "bronze3"
        elif lp < 4600:
            return "bronze4"
        elif lp < 5000:
            return "bronze5"
        elif lp < 5800:
            return "silver1"
        elif lp < 6600:
            return "silver2"
        elif lp < 7400:
            return "silver3"
        elif lp < 8200:
            return "silver4"
        elif lp < 9000:
            return "silver5"
        elif lp < 9800:
            return "gold1"
        elif lp < 10600:
            return "gold2"
        elif lp < 11400:
            return "gold3"
        elif lp < 12200:
            return "gold4"
        elif lp < 13000:
            return "gold5"
        elif lp < 14200:
            return "platinum1"
        elif lp < 15400:
            return "platinum2"
        elif lp < 16600:
            return "platinum3"
        elif lp < 17800:
            return "platinum4"
        elif lp < 19000:
            return "platinum5"
        elif lp < 20200:
            return "diamond1"
        elif lp < 21400:
            return "diamond2"
        elif lp < 22600:
            return "diamond3"
        elif lp < 23800:
            return "diamond4"
        elif lp < 25000:
            return "diamond5"
        else:
            return "master"
