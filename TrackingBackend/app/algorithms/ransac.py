from app.processes import EyeProcessor


class Ransac:
    def __init__(self, eye_processor: EyeProcessor):
        self.ep = eye_processor
