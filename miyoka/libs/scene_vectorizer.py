from abc import ABC, abstractmethod
import numpy as np
from numpy.typing import NDArray

__all__ = ["SceneVectorizer"]


class SceneVectorizer(ABC):
    @abstractmethod
    def get_feature_names_out(self) -> list[str]: ...

    @abstractmethod
    def vectorize(self, inputs: list[str]) -> NDArray[np.float64]: ...
