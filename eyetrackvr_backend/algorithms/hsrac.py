from ..processes import EyeProcessor
from ..utils import BaseAlgorithm


class HSRAC(BaseAlgorithm):
    def __init__(self, eye_processor: EyeProcessor):
        self.ep = eye_processor
