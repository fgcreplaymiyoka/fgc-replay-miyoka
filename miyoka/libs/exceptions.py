class GameOver(Exception):
    def __init__(self, message, frame_id: int):
        super().__init__(message)
        self.frame_id = frame_id
