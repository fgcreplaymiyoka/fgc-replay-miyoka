from miyoka.libs.screen_customizer import ScreenCustomizer
from miyoka.container import Container
from dependency_injector.wiring import inject, Provide
import sys


@inject
def run(
    command: str,
    screen_customizer: ScreenCustomizer = Provide[Container.screen_customizer],
):
    if command == "change":
        screen_customizer.change()
    elif command == "restore":
        screen_customizer.restore()
    else:
        print(f"Invalid command: {command}")
        exit(1)


if __name__ == "__main__":
    command = sys.argv[1]

    container = Container()
    container.wire(
        modules=[
            __name__,
        ]
    )

    run(command)
