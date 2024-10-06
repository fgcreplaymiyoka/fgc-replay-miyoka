from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray
from typing import Optional


@dataclass
class Scene:
    id: int
    inputs: list[str]
    frame_range: range
    replay_id: str
    round_id: int
    character: str
    vector: Optional[NDArray[np.float64]] = None
    scene_video_path: Optional[str] = None

    @property
    def fullpath(self) -> str:
        return f"{self.replay_id}/{self.round_id}/{self.character}/scene-{self.id}"

    @property
    def uuid(self) -> str:
        return f"{self.replay_id}-{self.round_id}-{self.character}-scene-{self.id}"
