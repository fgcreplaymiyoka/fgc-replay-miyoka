import cv2 as cv
import numpy as np
from miyoka.libs.game_window_helper import GameWindowHelper as GameWindowHelperBase
from datetime import datetime
import urllib.parse


class GameWindowHelper(GameWindowHelperBase):
    def templates_dir(self, dir):
        return f"miyoka/sf6/templates/{self.normalized_screen_width}x{self.normalized_screen_height}/{self.screen_language}/{dir}"

    def switch_to_original_language(self):
        self.change_language(self.extra["original_language"])

    def get_original_quality(self):
        return self.extra["original_quality"]

    def get_original_display_mode(self):
        return self.extra["original_display_mode"]

    def get_original_language(self):
        return self.extra["original_language"]

    def identify_screen(self, image):
        self.save_image(image, f"last_images/identify_screen/screen.jpeg")

        screen, _ = self.identify_in_screen(
            image, self.templates_dir("screens"), threthold=0.85
        )

        return screen

    def is_replay_options_exist(self, image):
        roi = (326, 704, 635, 100)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(
            cropped_image, f"last_images/is_replay_options_exist/image.jpeg"
        )

        option, _ = self.identify_in_screen(
            cropped_image, self.templates_dir("replay_options")
        )

        print(f"option: {option}")
        return option != ""

    def is_replay_options_in_round_exist(self, image):
        roi = (326, 704, 635, 100)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(
            cropped_image, f"last_images/is_replay_options_in_round_exist/image.jpeg"
        )

        option, _ = self.identify_in_screen(
            cropped_image, self.templates_dir("replay_options_in_round"), threthold=0.85
        )

        print(f"option: {option}")
        return option != ""

    def is_replay_started(self, image):
        roi = (605, 174, 76, 57)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/is_paused/image.jpeg")

        tmp, _ = self.identify_in_screen(
            cropped_image, self.templates_dir("replay_center"), threthold=0.7
        )

        return tmp == "play"

    def identify_in_screen(self, image, template_dir, threthold=0.75):
        if not isinstance(image, list):
            image = [image]

        detected = ""
        highest = 0
        roi = None

        for img in image:
            img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

            for template_file in self.all_templates(template_dir):
                template = cv.imread(
                    template_dir + "/" + template_file, cv.IMREAD_GRAYSCALE
                )
                name = template_file.replace(".jpeg", "").split("_")[0]
                score, roi = self.detect(img_gray, template)

                if (score > threthold) and (score > highest):
                    highest = score
                    detected = name
                    roi = roi

        return detected, roi

    def identify_replay_input_modern(self, image):
        modern_input, roi = self.identify_in_screen(
            image, self.templates_dir("replay_inputs_modern"), threthold=0.69
        )

        if not modern_input:
            return None

        if modern_input in ["sp", "dp", "auto", "di", "grab"]:
            return modern_input

        (x, y, width, height) = roi

        white_pix_threadhold = 96  # 1/3 of the icon size (17 * 17) = 289 / 3 = 96

        # https://imagecolorpicker.com/
        pk_color_ranges = {
            "h": [
                np.array([60, 39, 101]),  # HP/HK rgba(179,39,60,255)
                np.array([124, 116, 188]),  # HP/HK rgb(166,116,124)
            ],
            "m": [
                np.array([44, 108, 100]),  # MP/MK rgb(100,108,44)
                np.array([114, 196, 188]),  # MP/MK rgb(188,196,114)
            ],
            "l": [
                np.array([135, 119, 40]),  # LP/LK rgb(40,119,135)
                np.array([200, 198, 164]),  # LP/LK rgb(164,198,200)
            ],
        }

        ####### Color
        icon_image = image[y : y + height, x : x + width]

        highest = 0
        detected_strength = ""
        for strength, range in pk_color_ranges.items():
            mask = cv.inRange(icon_image, range[0], range[1])
            n_white_pix = np.sum(mask == 255)

            if (n_white_pix > white_pix_threadhold) and (n_white_pix > highest):
                highest = n_white_pix
                detected_strength = strength

        if not detected_strength:
            return None

        return detected_strength + modern_input

    def identify_replay_input_classic(self, image):
        classic_input, roi = self.identify_in_screen(
            image, self.templates_dir("replay_inputs_classic"), threthold=0.69
        )

        if not classic_input:
            return None

        (x, y, width, height) = roi

        white_pix_threadhold = 96  # 1/3 of the icon size (17 * 17) = 289 / 3 = 96

        # https://imagecolorpicker.com/
        pk_color_ranges = {
            "h": [
                np.array([58, 51, 133]),  # HP/HK rgba(133,51,58,255)
                np.array([164, 155, 255]),  # HP/HK rgba(245,155,164,255)
            ],
            "m": [
                np.array([45, 148, 141]),  # MP/MK rgba(141,148,45,255)
                np.array([125, 255, 255]),  # MP/MK rgba(255,254,125,255)
            ],
            "l": [
                np.array([116, 106, 46]),  # LP/LK rgba(46,106,116,255)
                np.array([255, 255, 153]),  # LP/LK rgba(153,255,255,255)
            ],
        }

        ####### Color
        icon_image = image[y : y + height, x : x + width]

        highest = 0
        detected_strength = ""
        for strength, range in pk_color_ranges.items():
            mask = cv.inRange(icon_image, range[0], range[1])
            n_white_pix = np.sum(mask == 255)

            if (n_white_pix > white_pix_threadhold) and (n_white_pix > highest):
                highest = n_white_pix
                detected_strength = strength

        if not detected_strength:
            return None

        return detected_strength + classic_input

    def identify_replay_id(self, image):
        roi = (273, 123, 90, 23)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/identify_replay_id/image.jpeg")

        name = self.detect_text(f"last_images/identify_replay_id/image.jpeg")

        return urllib.parse.quote_plus(name)

    def identify_played_at(self, image):
        roi = (858, 108, 120, 20)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/identify_played_at/image.jpeg")

        detected_played_at = self.detect_text(
            f"last_images/identify_played_at/image.jpeg"
        )

        try:
            played_at = detected_played_at.replace("-", "").strip()
            played_at = datetime.strptime(played_at, "%m/%d/%Y %H:%M")
        except Exception as e:
            self.logger.error(
                f"failed to identify played_at. detected_played_at: {detected_played_at}"
            )
            played_at = None

        return played_at

    def identify_result(self, image, player):
        p1_roi = (458, 315, 82, 29)

        if player == "p1":
            roi = p1_roi
        elif player == "p2":
            roi = self.mirror_p2_roi_from(p1_roi)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/summary_results/{player}.jpeg")

        tmp, _ = self.identify_in_screen(
            cropped_image, self.templates_dir("summary_results"), threthold=0.7
        )

        if not tmp:
            self.logger.error(f"failed to identify results for {player}")
            raise ValueError()

        return tmp

    def identify_mode(self, image, player):
        if player == "p1":
            roi = (200, 200, 30, 30)
        elif player == "p2":
            roi = (933, 200, 30, 30)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/summary_modes/{player}.jpeg")

        mode, _ = self.identify_in_screen(
            cropped_image, self.templates_dir("summary_modes"), threthold=0.70
        )

        if not mode:
            self.logger.error(f"failed to identify mode for {player}")
            raise ValueError()

        return mode

    def identify_rank(self, image, player):
        p1_roi = (250, 182, 72, 45)

        if player == "p1":
            roi = p1_roi
        elif player == "p2":
            roi = self.mirror_p2_roi_from(p1_roi)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/summary_ranks/{player}.jpeg")

        rank, _ = self.identify_in_screen(
            cropped_image, self.templates_dir("summary_ranks"), threthold=0.8
        )

        return rank

    def identify_player_name(self, image, player):
        if player == "p1":
            roi = (189, 241, 211, 23)
        elif player == "p2":
            roi = (921, 241, 211, 23)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(
            cropped_image, f"last_images/summary_player_names/{player}.jpeg"
        )
        player_name = self.detect_text(
            f"last_images/summary_player_names/{player}.jpeg"
        )
        return player_name

    def identify_mr(self, image, player):
        if player == "p1":
            roi = (325, 202, 65, 20)
        elif player == "p2":
            roi = (1062, 202, 65, 20)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/summary_mrs/{player}.jpeg")

        mr_str = self.detect_text(f"last_images/summary_mrs/{player}.jpeg")
        mr_str = mr_str.replace("MR", "").strip()

        if not mr_str.isdecimal():
            return None

        return int(mr_str)

    def identify_lp(self, image, player):
        if player == "p1":
            roi = (325, 205, 65, 21)
        elif player == "p2":
            roi = (1062, 205, 65, 21)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]

        self.save_image(cropped_image, f"last_images/summary_lps/{player}.jpeg")

        lp_str = self.detect_text(f"last_images/summary_lps/{player}.jpeg")
        lp_str = lp_str.replace("LP", "").strip()

        if not lp_str.isdecimal():
            return None

        return int(lp_str)

    def identify_character(self, image, player):
        p1_roi = (430, 175, 135, 140)

        if player == "p1":
            roi = p1_roi
        elif player == "p2":
            roi = self.mirror_p2_roi_from(p1_roi)

        (x, y, width, height) = roi
        cropped_image = image[y : y + height, x : x + width]
        cropped_image_mirror = cv.flip(cropped_image, 1)

        self.save_image(cropped_image, f"last_images/summary_characters/{player}.jpeg")

        character, _ = self.identify_in_screen(
            [cropped_image, cropped_image_mirror],
            self.templates_dir("summary_characters"),
            threthold=0.7,
        )

        if not character:
            self.logger.error(f"failed to identify character for {player}")
            return "unknown"

        return character

    def identify_round_results(self, image, player):
        p1_rois = [
            (590, 201, 40, 25),  # r1
            (590, 223, 40, 25),  # r2
            (590, 253, 40, 25),  # r3
        ]

        if player == "p1":
            rois = p1_rois
        elif player == "p2":
            rois = [self.mirror_p2_roi_from(p1_roi) for p1_roi in p1_rois]

        ret = []

        for i, roi in enumerate(rois):
            (x, y, width, height) = roi
            cropped_image = image[y : y + height, x : x + width]
            cropped_image_mirror = cv.flip(cropped_image, 1)

            self.save_image(
                cropped_image, f"last_images/summary_round_wins/{player}-r{i}.jpeg"
            )

            round_win, _ = self.identify_in_screen(
                [cropped_image, cropped_image_mirror],
                self.templates_dir("summary_round_wins"),
                threthold=0.7,
            )

            if not round_win:
                self.logger.error(f"failed to identify round_win for {player}")
                raise ValueError()

            ret.append(round_win)

        return ret

    def identify_replay_input(self, image, player, mode):
        diameter = 18
        radius = int(diameter / 2)
        p1_rois = [
            (
                72 - radius,
                163 - radius,
                diameter,
                diameter,
            ),  # arrow 115 x 245 at center . 30 x 30
            (92 - radius, 163 - radius, diameter, diameter),  # input 1
            (112 - radius, 163 - radius, diameter, diameter),  # input 2
            (132 - radius, 163 - radius, diameter, diameter),  # input 3
            (152 - radius, 163 - radius, diameter, diameter),  # input 4
            (172 - radius, 163 - radius, diameter, diameter),  # input 5
            (192 - radius, 163 - radius, diameter, diameter),  # input 6
        ]
        if mode == "classic":
            candidates = ["lp", "mp", "hp", "lk", "mk", "hk"]
        elif mode == "modern":
            candidates = ["la", "sp", "dp", "ma", "ha", "auto", "di", "grab"]

        if player == "p1":
            rois = p1_rois
        elif player == "p2":
            rois = [self.mirror_p2_roi_from(p1_roi) for p1_roi in p1_rois]
            candidates.reverse()

        inputs = []
        arrow = ""
        input = ""

        for x, y, width, height in rois:
            # print(f"player: {player} x: {x} y: {y} width: {width} height: {height}")
            cropped_image = image[y : y + height, x : x + width]
            self.save_image(
                cropped_image,
                f"last_images/identify_replay_input/{player}_{x}_{y}.jpeg",
            )

            if not arrow:
                arrow, _ = self.identify_in_screen(
                    cropped_image,
                    self.templates_dir("replay_inputs_arrows"),
                    threthold=0.67,
                )

                if not arrow:
                    arrow = "undef"
                    break

                continue

            if mode == "classic":
                input = self.identify_replay_input_classic(cropped_image)
            elif mode == "modern":
                input = self.identify_replay_input_modern(cropped_image)

            # print(f"player: {player} input: {input}")
            if input and len(candidates) > 0:
                index = candidates.index(input)
                del candidates[0 : index + 1 : 1]
                inputs.append(input)
            else:
                break

        if player == "p2":
            inputs.reverse()

        results = [arrow] + inputs
        return results

    def _detect_number(self, image, roi, player):
        (x, y, width, height) = roi
        image = image[y : y + height, x : x + width]
        image_gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        dir = self.templates_dir("replay_inputs_count")
        threthold = 0.68

        detected = None
        highest = 0

        self.save_image(
            image, f"last_images/identify_replay_input_count/{player}_{x}_{y}.jpeg"
        )

        for template_file in self.all_templates(dir):
            template = cv.imread(dir + "/" + template_file, cv.IMREAD_GRAYSCALE)
            number = int(template_file.replace(".jpeg", "")[0])
            score, _ = self.detect(image_gray, template)
            # print(f"name: {name} score: {score}")

            if (score > threthold) and (score > highest):
                # print(f"renew highest: {highest}")
                highest = score
                detected = number

        if not detected:
            detected = 0

        return detected

    def identify_replay_input_count(self, image, player, row=1):
        if row == 0:
            p1_first_digit = (35, 155, 11, 15)  # 66 +- 15 =
            p1_second_digit = (44, 155, 11, 15)  # ?
        elif row == 1:
            p1_first_digit = (35, 179, 11, 15)  # 66 +- 15 =
            p1_second_digit = (44, 179, 11, 15)  # ?
        elif row == 2:
            p1_first_digit = (35, 201, 11, 15)  # 66 +- 15 =
            p1_second_digit = (44, 201, 11, 15)  # ?
        elif row == 3:
            p1_first_digit = (35, 223, 11, 15)  # 66 +- 15 =
            p1_second_digit = (44, 223, 11, 15)  # ?
        elif row == 4:
            p1_first_digit = (35, 246, 11, 15)  # 66 +- 15 =
            p1_second_digit = (44, 246, 11, 15)  # ?
        elif row == 19:
            p1_first_digit = (35, 563, 11, 15)  # 66 +- 15 =
            p1_second_digit = (44, 563, 11, 15)  # ?

        if player == "p1":
            first_digit = p1_first_digit
            second_digit = p1_second_digit
        elif player == "p2":
            first_digit = self.mirror_p2_roi_from(p1_second_digit)
            second_digit = self.mirror_p2_roi_from(p1_first_digit)

        number_10 = self._detect_number(image, first_digit, player)
        number_1 = self._detect_number(image, second_digit, player)

        return (number_10 * 10) + number_1

    def get_all_rows_count(self, frame, max_rows, player):
        all_rows_count = [
            self.identify_replay_input_count(frame, player, row=i)
            for i in range(0, max_rows)
        ]

        return all_rows_count
