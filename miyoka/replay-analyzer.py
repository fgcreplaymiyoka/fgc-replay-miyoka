from miyoka.libs.replay_analyzer import ReplayAnalyzer
from miyoka.container import Container
from dependency_injector.wiring import inject, Provide


@inject
def run(
    replay_analyzer: ReplayAnalyzer = Provide[Container.replay_analyzer],
):
    replay_analyzer.run()


if __name__ == "__main__":
    container = Container()
    container.wire(
        modules=[
            __name__,
        ]
    )

    run()
