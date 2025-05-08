from miyoka.libs.replay_recorder import ReplayRecorder
from miyoka.container import Container
from dependency_injector.wiring import inject, Provide


@inject
def run(
    replay_recorder: ReplayRecorder = Provide[Container.replay_recorder],
):
    replay_recorder.run()


if __name__ == "__main__":
    container = Container()
    container.wire(
        modules=[
            __name__,
        ]
    )

    run()
