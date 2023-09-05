from pydantic import BaseModel, field_validator
from app.config import IP_ADDRESS_REGEX
import re


class CameraConfig(BaseModel):
    enabled: bool = True
    capture_source: str = ""
    threshold: int = 50
    focal_length: int = 30
    rotation_angle: int = 0
    flip_x_axis: bool = False
    flip_y_axis: bool = False
    roi_x: int = 0
    roi_y: int = 0
    roi_w: int = 0
    roi_h: int = 0

    @field_validator("roi_x", "roi_y", "roi_w", "roi_h")
    def roi_validator(cls, value: int) -> int:
        if value < 0:
            raise ValueError("ROI values must be greater than 0")
        return value

    @field_validator("capture_source")
    def capture_source_validator(cls, value: str) -> str:
        if not value == "":
            if re.match(IP_ADDRESS_REGEX, value) is None:
                raise ValueError("Invalid IP Address, must be localhost or a valid IPv4 address")
        return value
