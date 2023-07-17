from app.processes import EyeProcessor


class HSF:
    def __init__(self, eye_processor: EyeProcessor):
        self.ep = eye_processor
