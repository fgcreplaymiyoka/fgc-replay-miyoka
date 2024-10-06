from abc import ABC, abstractmethod

__all__ = ["ScreenCustomizer"]


class ScreenCustomizer(ABC):
    @abstractmethod
    def change(self): ...

    @abstractmethod
    def restore(self): ...
