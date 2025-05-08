from abc import ABC, abstractmethod

__all__ = ["ReplayRecorder"]


class ReplayRecorder(ABC):
    @abstractmethod
    def run(self): ...
