from miyoka.libs.replay_uploader import ReplayUploader
from miyoka.container import Container
from dependency_injector.wiring import inject, Provide


@inject
def run(
    replay_uploader: ReplayUploader = Provide[Container.replay_uploader],
):
    replay_uploader.run()


if __name__ == "__main__":
    container = Container()
    container.wire(
        modules=[
            __name__,
        ]
    )

    run()
