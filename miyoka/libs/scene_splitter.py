from abc import ABC, abstractmethod

__all__ = ["SceneSplitter"]


class SceneSplitter(ABC):
    @abstractmethod
    def split(self): ...
