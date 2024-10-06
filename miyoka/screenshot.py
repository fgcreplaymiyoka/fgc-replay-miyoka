import dxcam
from miyoka.libs.game_window_helper import GameWindowHelper
from miyoka.container import Container
from dependency_injector.wiring import inject, Provide


@inject
def screenshot(
    game_window_helper: GameWindowHelper = Provide[Container.game_window_helper],
):
    game_window_helper.wait_until_game_launched()
    game_window_helper.wait_until_game_focused()
    game_window_helper.update_game_window_size()
    game_window_helper.init_camera()

    frame = game_window_helper.grab_frame()

    game_window_helper.save_image(frame)


if __name__ == "__main__":
    container = Container()
    container.wire(
        modules=[
            __name__,
        ]
    )

    screenshot()
