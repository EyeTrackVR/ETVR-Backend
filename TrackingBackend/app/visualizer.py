import cv2
from queue import Queue

class Visualizer:
    def __init__(self, image_queue: Queue,):
        self.image_queue: Queue = image_queue
