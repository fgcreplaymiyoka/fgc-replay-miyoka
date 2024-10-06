import cv2 as cv
from logging import Logger
import contextlib
from miyoka.libs.exceptions import GameOver
from miyoka.libs.round_analyzer import RoundAnalyzer as RoundAnalyzerBase
from miyoka.sf6.game_window_helper import GameWindowHelper


class RoundAnalyzer(RoundAnalyzerBase):
    def __init__(
        self,
        game_window_helper: GameWindowHelper,
        logger: Logger,
        replay_id: str,
        round_id: int,
        start_frame_at: int,
        stop_frame_at: int,
        ignore_error: bool,
        log_collapsed_inputs: bool,
        verify_inputs_count: bool,
        metadata: dict,
    ):
        super().__init__()

        self.p1_input_history = []
        self.p2_input_history = []
        self.p1_input_count = 1
        self.p2_input_count = 1
        self.p1_input_count_verifiable = False
        self.p2_input_count_verifiable = False
        self.replay_started = False
        self.previous_frame = None
        self.duplicate_frame_count = 0
        self.dropped_frame_count = 0
        self.previous_p1_all_rows_count = None
        self.previous_p2_all_rows_count = None
        self.init_game_window_helper_screen_size = False

        self.game_window_helper = game_window_helper
        self.logger = logger
        self.start_frame_at = start_frame_at
        self.stop_frame_at = stop_frame_at
        self.ignore_error = ignore_error
        self.log_collapsed_inputs = log_collapsed_inputs
        self.verify_inputs_count = verify_inputs_count
        self.metadata = metadata

        self.replay_id = replay_id
        self.round_id = round_id
        self.frame_data = []

    @contextlib.contextmanager
    def read_frame_data(self):
        yield self.frame_data
        self.frame_data = []

    def analyze_frames(
        self,
        frame_range: range,
        frame_dir: str,
    ):
        self.logger.info(
            f"Start analyzing frames {frame_range} from {frame_dir} for round {self.round_id}"
        )
        for frame_id in frame_range:
            if frame_id <= self.start_frame_at:
                continue

            path = f"{frame_dir}/{frame_id}.jpeg"
            frame = cv.imread(path)

            if not self.init_game_window_helper_screen_size:
                height, width, channels = frame.shape
                self.game_window_helper.current_screen_width = width
                self.game_window_helper.current_screen_height = height
                self.init_game_window_helper_screen_size = True

            self._analyze(frame, frame_id)

    def _analyze(
        self,
        frame,
        frame_id,
    ):
        if not self._is_replay_started(frame):
            return

        if self._check_duplicate(frame):
            self.logger.info("duplicate", extra={"number": frame_id})
            self.duplicate_frame_count += 1
            return

        if self._check_game_over(frame):
            self.logger.info(
                "game_over", extra={"round_id": self.round_id, "number": frame_id}
            )
            raise GameOver("Game over", frame_id=frame_id)

        self.game_window_helper.save_image(frame, "last_images/frame.jpeg")

        ret, p1_all_rows_count, p2_all_rows_count = self._check_dropped_frames(frame)

        self.logger.info(
            "check_dropped_frames",
            extra={
                "number": frame_id,
                "ret": ret,
                "p1_counts": p1_all_rows_count,
                "p2_counts": p2_all_rows_count,
            },
        )

        if frame_id == self.stop_frame_at:
            raise Exception(f"Stopped at frame {frame_id} for debugging")

        if ret == "dropped":
            self.p1_input_count_verifiable = False
            self.p2_input_count_verifiable = False

        p1_input, p2_input = self._identify_replay_input(frame)

        self.logger.info(
            "input",
            extra={
                "round_id": self.round_id,
                "number": frame_id,
                "p1": p1_input,
                "p2": p2_input,
            },
        )

        self._verify_replay_input(frame, p1_input, p2_input, frame_id)

        self.frame_data.append(
            {
                "frame_id": frame_id,
                "p1_input": p1_input,
                "p2_input": p2_input,
            }
        )

        if frame_id == self.stop_frame_at:
            raise Exception(f"Stopped at frame {frame_id} for debugging")

        if ret == "dropped":
            self.p1_input_count_verifiable = False
            self.p2_input_count_verifiable = False

    def _is_replay_started(
        self,
        image,
    ):
        if self.replay_started:
            return True

        return self.game_window_helper.is_replay_started(image)

    def _check_duplicate(self, frame):
        ret = False
        if self.previous_frame is not None:
            ret = self.game_window_helper.mse(frame, self.previous_frame) < 5

        self.previous_frame = frame
        return ret

    def _compare_rows_count(self, all_rows_count, previous_all_rows_count, max_rows):
        ret = ""

        if (
            all_rows_count[0] == (previous_all_rows_count[0] + 1)
            and all_rows_count[1:max_rows] == previous_all_rows_count[1:max_rows]
        ):
            ret = "ok"
        elif (
            all_rows_count[0] == 1
            and all_rows_count[1:max_rows] == previous_all_rows_count[0 : max_rows - 1]
        ):
            ret = "ok"
        elif (
            all_rows_count[0] == 99
            and all_rows_count[1:max_rows] == previous_all_rows_count[1:max_rows]
        ):
            ret = "ok"
        return ret

    def _eval_all_rows_count(
        self,
        max_rows,
        p1_all_rows_count,
        p2_all_rows_count,
        previous_p1_all_rows_count,
        previous_p2_all_rows_count,
    ):
        if not previous_p1_all_rows_count and not previous_p2_all_rows_count:
            return ("ok", p1_all_rows_count, p2_all_rows_count)

        p1_ret = self._compare_rows_count(
            p1_all_rows_count, previous_p1_all_rows_count, max_rows
        )
        p2_ret = self._compare_rows_count(
            p2_all_rows_count, previous_p2_all_rows_count, max_rows
        )

        if p1_ret == "ok" and p2_ret == "ok":
            return ("ok", p1_all_rows_count, p2_all_rows_count)

        self.dropped_frame_count += 1
        return ("dropped", p1_all_rows_count, p2_all_rows_count)

    def _check_game_over(self, frame):
        # # Submit the tasks to the executor
        # p1_future = self.executor.submit(
        #     opencv.identify_replay_input_count, frame, "p1", row=0
        # )
        # p2_future = self.executor.submit(
        #     opencv.identify_replay_input_count, frame, "p2", row=0
        # )
        # p1_count = p1_future.result()
        # p2_count = p2_future.result()

        p1_count = self.game_window_helper.identify_replay_input_count(
            frame, "p1", row=0
        )
        p2_count = self.game_window_helper.identify_replay_input_count(
            frame, "p2", row=0
        )

        return p1_count == 0 or p2_count == 0

    def _check_dropped_frames(self, frame):
        max_rows = 3

        # p1_future = self.executor.submit(
        #     opencv.get_all_rows_count, frame, max_rows, "p1"
        # )
        # p2_future = self.executor.submit(
        #     opencv.get_all_rows_count, frame, max_rows, "p2"
        # )
        # p1_all_rows_count = p1_future.result()
        # p2_all_rows_count = p2_future.result()

        p1_all_rows_count = self.game_window_helper.get_all_rows_count(
            frame, max_rows, "p1"
        )
        p2_all_rows_count = self.game_window_helper.get_all_rows_count(
            frame, max_rows, "p2"
        )

        ret = self._eval_all_rows_count(
            max_rows,
            p1_all_rows_count,
            p2_all_rows_count,
            self.previous_p1_all_rows_count,
            self.previous_p2_all_rows_count,
        )

        self.previous_p1_all_rows_count = p1_all_rows_count
        self.previous_p2_all_rows_count = p2_all_rows_count

        return ret

    def _identify_replay_input(self, frame):
        # p1_future = self.executor.submit(
        #     opencv.identify_replay_input,
        #     frame,
        #     "p1",
        #     self.metadata["p1"]["mode"],
        # )
        # p2_future = self.executor.submit(
        #     opencv.identify_replay_input,
        #     frame,
        #     "p2",
        #     self.metadata["p2"]["mode"],
        # )
        # p1_input = p1_future.result()
        # p2_input = p2_future.result()
        p1_input = self.game_window_helper.identify_replay_input(
            frame, "p1", self.metadata["p1"]["mode"]
        )
        p2_input = self.game_window_helper.identify_replay_input(
            frame, "p2", self.metadata["p2"]["mode"]
        )

        return (p1_input, p2_input)

    def _verify_replay_input(self, frame, p1_input, p2_input, frame_id):
        self.p1_input_count, self.p1_input_count_verifiable = (
            self._verify_player_replay_input(
                "p1",
                frame,
                p1_input,
                self.p1_input_history,
                current_input_count=self.p1_input_count,
                input_count_verifiable=self.p1_input_count_verifiable,
                frame_id=frame_id,
            )
        )

        self.p2_input_count, self.p2_input_count_verifiable = (
            self._verify_player_replay_input(
                "p2",
                frame,
                p2_input,
                self.p2_input_history,
                current_input_count=self.p2_input_count,
                input_count_verifiable=self.p2_input_count_verifiable,
                frame_id=frame_id,
            )
        )

    def _verify_player_replay_input(
        self,
        player,
        frame,
        input,
        input_history,
        current_input_count,
        input_count_verifiable,
        frame_id,
    ):
        if "undef" in input:
            raise Exception(f"{player} input is empty!!!!!")

        # Calc collapsed inputs
        if input_history and input_history[-1] == input:
            current_input_count += 1
        elif input_history and input_history[-1] != input:
            if self.log_collapsed_inputs:
                self.logger.info(
                    "collapsed",
                    extra={
                        "player": player,
                        "count": current_input_count,
                        "input": input_history[-1],
                    },
                )

            if self.verify_inputs_count and input_count_verifiable:
                expected_input_count = (
                    self.game_window_helper.identify_replay_input_count(frame, player)
                )

                if (
                    current_input_count < 100
                    and expected_input_count != current_input_count
                ):
                    self.game_window_helper.save_image(
                        frame, f"last_images/{player}_input_verification_error.jpeg"
                    )

                    raise Exception(
                        f"Expected {player} input count was {expected_input_count}, but {current_input_count}. Last input: {input}. raw: {frame_id}"
                    )

            input_count_verifiable = True
            current_input_count = 1

        input_history.append(input)

        return current_input_count, input_count_verifiable
