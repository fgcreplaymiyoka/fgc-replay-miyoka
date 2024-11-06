from logging import Logger
import os
import json
import time
import pydirectinput
import subprocess
import re
from dependency_injector.providers import Factory
from datetime import datetime, timezone
from miyoka.libs.screen_customizer import ScreenCustomizer as ScreenCustomizerBase
from miyoka.sf6.game_window_helper import (
    GameWindowHelper,
)
from miyoka.sf6.constants import (
    get_nth_character_combination,
    replay_select_character_position,
)

pydirectinput.FAILSAFE = False

__all__ = ["ScreenCustomizer"]


class ScreenCustomizer(ScreenCustomizerBase):
    def __init__(
        self,
        logger: Logger,
        game_window_helper: GameWindowHelper,
        exit_to_desktop: bool,
    ):
        super().__init__()

        self.logger = logger
        self.game_window_helper = game_window_helper
        self.exit_to_desktop = exit_to_desktop

    def change(self):
        self.logger.info("Changing screen.....")
        self.game_window_helper.wait_until_game_launched()
        self.game_window_helper.wait_until_game_focused()
        self.game_window_helper.update_game_window_size()
        self.game_window_helper.switch_to_original_language()
        self.game_window_helper.init_camera()

        is_quality_changed = False
        is_borderless_windowed_changed = False
        is_language_changed = False

        while True:
            frame = self.game_window_helper.grab_frame()
            screen = self.game_window_helper.identify_screen(frame)

            self.logger.info(f"screen: {screen}")

            if (
                is_quality_changed
                and is_borderless_windowed_changed
                and is_language_changed
            ):
                self.logger.info(f"Changing screen complete!")
                break

            match screen:
                case "TitleScreen":
                    pydirectinput.press("Tab")  # Press Any Button
                case "MainBh":
                    pydirectinput.press("Tab")  # Open menu
                    time.sleep(3)
                case "News":
                    pydirectinput.press("ESC")  # Exit from news
                case "MultiMenuProfile":
                    pydirectinput.press("s")  # Down
                    pydirectinput.press("a")  # Left
                    pydirectinput.press("a")  # Left
                case "MultiOptions":
                    pydirectinput.press("f")  # Enter
                case "OptionsGame":
                    pydirectinput.press("q")  # Left
                case "OptionsGraphicsQualityLowest":
                    is_quality_changed = True
                    pydirectinput.press("s")  # Down
                    self.game_window_helper.update_game_window_size()
                case "OptionsGraphicsQualityLow":
                    pydirectinput.press("a")  # Left - To Lowest
                    self.game_window_helper.update_game_window_size()
                case "OptionsGraphicsQualityNormal":
                    pydirectinput.press("d")  # Left - To Lowest
                    self.game_window_helper.update_game_window_size()
                case "OptionsGraphicsQualityHigh":
                    pydirectinput.press("d")  # Right - To Lowest
                    self.game_window_helper.update_game_window_size()
                case "OptionsGraphicsQualityHighest":
                    pydirectinput.press("d")  # Right - To Lowest
                    self.game_window_helper.update_game_window_size()
                case "OptionsGraphicsOutputDisplay":
                    pydirectinput.press("s")  # Down
                case "OptionsGraphicsResolution":
                    pydirectinput.press("s")  # Down
                case "OptionsGraphicsBasicGraphicSettings":
                    pydirectinput.press("f")  # Enter
                    pydirectinput.press("s")  # Down
                    pydirectinput.press("s")  # Down - To Display Mode
                case "OptionsGraphicsBasicGraphicSettingsDisplayModeBorderlessWindowed":
                    pydirectinput.press("d")  # Right - to Windowed
                    time.sleep(3)
                    self.game_window_helper.update_game_window_size()
                case "OptionsGraphicsBasicGraphicSettingsDisplayModeWindowed":
                    is_borderless_windowed_changed = True
                    pydirectinput.press("ESC")  # Exit
                    pydirectinput.press("q")  # Left - To Language
                case "OptionsLanguageDisplayLanguageEnglish":
                    is_language_changed = True
                    pydirectinput.press("ESC")  # Exit
                    pydirectinput.press("ESC")  # Exit
                case "ErrorCommunication" | "ErrorCommunication2":
                    pydirectinput.press("f")  # OK - Close dialog
                case "MainFg":
                    pydirectinput.press("a")  # Left
                case (
                    "ReplaySummary"
                    | "SearchResults"
                    | "KeywordSearchByPlayerName"
                    | "CfnReplays"
                    | "MultiMenuCfn"
                    | "FightingGroundPractice"
                    | "FightingGroundVersus"
                    | "KeywordSearchByUserCode"
                ):
                    pydirectinput.press("ESC")  # Exit
                case _:
                    pass

            time.sleep(1)

    def restore(self):
        self.logger.info("Restoring screen.....")

        self.game_window_helper.wait_until_game_launched()
        self.game_window_helper.wait_until_game_focused()
        self.game_window_helper.update_game_window_size()
        self.game_window_helper.init_camera()

        is_quality_changed = False
        is_borderless_windowed_changed = False
        is_language_changed = False

        while True:
            frame = self.game_window_helper.grab_frame()
            screen = self.game_window_helper.identify_screen(frame)

            self.logger.info(f"screen: {screen}")

            if (
                is_quality_changed
                and is_borderless_windowed_changed
                and is_language_changed
            ):
                self.logger.info(f"Restoring screen complete!")

                if self.exit_to_desktop:
                    self._exit_to_desktop()

                break

            match screen:
                case "TitleScreen":
                    pydirectinput.press("Tab")  # Press Any Button
                case "MainBh":
                    pydirectinput.press("Tab")  # Open menu
                    time.sleep(3)
                case "News":
                    pydirectinput.press("ESC")  # Exit from news
                case "MultiMenuProfile":
                    pydirectinput.press("s")  # Down
                    pydirectinput.press("a")  # Left
                    pydirectinput.press("a")  # Left
                case "MultiOptions":
                    pydirectinput.press("f")  # Enter
                case "OptionsGame":
                    pydirectinput.press("q")  # Left
                case "OptionsGraphicsQualityLowest":
                    if self.game_window_helper.get_original_quality() == "Lowest":
                        pydirectinput.press("s")  # Down
                        is_quality_changed = True
                    else:
                        pydirectinput.press("d")  # Right

                    self.game_window_helper.update_game_window_size()
                case "OptionsGraphicsQualityLow":
                    if self.game_window_helper.get_original_quality() == "Low":
                        pydirectinput.press("s")  # Down
                        is_quality_changed = True
                    else:
                        pydirectinput.press("d")  # Right

                    self.game_window_helper.update_game_window_size()
                case "OptionsGraphicsQualityNormal":
                    if self.game_window_helper.get_original_quality() == "Normal":
                        pydirectinput.press("s")  # Down
                        is_quality_changed = True
                    else:
                        pydirectinput.press("d")  # Right

                    self.game_window_helper.update_game_window_size()
                case "OptionsGraphicsQualityHigh":
                    if self.game_window_helper.get_original_quality() == "High":
                        pydirectinput.press("s")  # Down
                        is_quality_changed = True
                    else:
                        pydirectinput.press("d")  # Right

                    self.game_window_helper.update_game_window_size()
                case "OptionsGraphicsQualityHighest":
                    if self.game_window_helper.get_original_quality() == "Highest":
                        pydirectinput.press("s")  # Down
                        is_quality_changed = True
                    else:
                        pydirectinput.press("d")  # Right

                    self.game_window_helper.update_game_window_size()
                case "OptionsGraphicsOutputDisplay":
                    pydirectinput.press("s")  # Down
                case "OptionsGraphicsResolution":
                    pydirectinput.press("s")  # Down
                case "OptionsGraphicsBasicGraphicSettings":
                    pydirectinput.press("f")  # Enter
                    pydirectinput.press("s")  # Down
                    pydirectinput.press("s")  # Down - To Display Mode
                case "OptionsGraphicsBasicGraphicSettingsDisplayModeWindowed":
                    if (
                        self.game_window_helper.get_original_display_mode()
                        == "Windowed"
                    ):
                        pydirectinput.press("ESC")  # Exit
                        pydirectinput.press("q")  # Left - To Language
                        is_borderless_windowed_changed = True
                    else:
                        pydirectinput.press("d")  # Right

                    self.game_window_helper.update_game_window_size()
                case "OptionsGraphicsBasicGraphicSettingsDisplayModeBorderlessWindowed":
                    if (
                        self.game_window_helper.get_original_display_mode()
                        == "BorderlessWindowed"
                    ):
                        pydirectinput.press("ESC")  # Exit
                        pydirectinput.press("q")  # Left - To Language
                        is_borderless_windowed_changed = True
                    else:
                        pydirectinput.press("d")  # Right

                    self.game_window_helper.update_game_window_size()
                case "OptionsLanguageDisplayLanguageEnglish":
                    if self.game_window_helper.get_original_language() == "en":
                        time.sleep(3)
                        pydirectinput.press("ESC")  # Exit
                        pydirectinput.press("ESC")  # Exit
                        is_language_changed = True
                    else:
                        pydirectinput.press("f")  # Enter - To select Language
                case "OptionsLanguageDisplayLanguageJapanese":
                    if self.game_window_helper.get_original_language() == "jp":
                        pydirectinput.press("ESC")  # Exit
                        pydirectinput.press("ESC")  # Exit
                    else:
                        pydirectinput.press("f")  # Enter - To select Language
                case "OptionsLanguageDisplayLanguageSelectEnglish":
                    pass  # TODO:
                case (
                    "ReplaySummary"
                    | "SearchResults"
                    | "KeywordSearchByPlayerName"
                    | "CfnReplays"
                    | "MultiMenuCfn"
                    | "KeywordSearchByUserCode"
                ):
                    pydirectinput.press("ESC")  # Exit
                case _:
                    pass

            time.sleep(1)

    def _exit_to_desktop(self):
        self.logger.info("Exiting to desktop.....")

        did_exit = False

        while True:
            frame = self.game_window_helper.grab_frame()
            screen = self.game_window_helper.identify_screen(frame)

            self.logger.info(f"screen: {screen}")

            if did_exit:
                self.logger.info(f"Exit to desktop complete!")
                break

            match screen:
                case "TitleScreen":
                    pydirectinput.press("Tab")  # Press Any Button
                case "MainBh":
                    pydirectinput.press("Tab")  # Open menu
                    time.sleep(3)
                case "News":
                    pydirectinput.press("ESC")  # Exit from news
                case "MultiMenuProfile":
                    pydirectinput.press("s")  # Down
                    pydirectinput.press("s")  # Down
                case "MultiMenuExitToDesktop":
                    pydirectinput.press("f")  # Enter
                case "MultiMenuExitToDesktopConfirmation":
                    pydirectinput.press("a")  # Left
                    pydirectinput.press("f")  # Enter
                    did_exit = True
                case _:
                    pass

            time.sleep(1)
