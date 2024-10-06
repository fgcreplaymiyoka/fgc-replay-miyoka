from abc import ABC, abstractmethod

__all__ = ["ReplayUploader"]


class ReplayUploader(ABC):
    @abstractmethod
    def run(self): ...
