from abc import ABC, abstractmethod

__all__ = ["RoundAnalyzer"]


class RoundAnalyzer(ABC):
    @abstractmethod
    def analyze_frames(self, *args, **kwargs): ...

    @abstractmethod
    def read_frame_data(self, *args, **kwargs): ...
