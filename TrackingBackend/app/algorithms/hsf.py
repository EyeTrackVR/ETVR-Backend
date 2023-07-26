from app.processes import EyeProcessor
from app.utils import BaseAlgorithm


class HSF(BaseAlgorithm):
    def __init__(self, eye_processor: EyeProcessor):
        self.ep = eye_processor
