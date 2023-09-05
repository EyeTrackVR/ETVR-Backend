from pydantic import BaseModel, field_validator
from app.config import IP_ADDRESS_REGEX
import re


class OSCEndpoints(BaseModel):
    eyes_y: str = "/avatar/parameters/EyesY"
    left_eye_x: str = "/avatar/parameters/LeftEyeX"
    right_eye_x: str = "/avatar/parameters/RightEyeX"
    recenter: str = "/avatar/parameters/etvr_recenter"
    sync_blink: str = "/avatar/parameters/etvr_sync_blink"
    recalibrate: str = "/avatar/parameters/etvr_recalibrate"
    left_eye_blink: str = "/avatar/parameters/LeftEyeLidExpandedSqueeze"
    right_eye_blink: str = "/avatar/parameters/RightEyeLidExpandedSqueeze"


class OSCConfig(BaseModel):
    address: str = "127.0.0.1"
    mirror_eyes: bool = False
    sync_blink: bool = False
    enable_sending: bool = True
    sending_port: int = 9000
    enable_receiving: bool = False
    receiver_port: int = 9001
    vrchat_native_tracking: bool = False
    endpoints: OSCEndpoints = OSCEndpoints()

    @field_validator("address")
    def address_validator(cls, value: str) -> str:
        if re.match(IP_ADDRESS_REGEX, value) is None:
            raise ValueError("Invalid IP Address, must be localhost or a valid IPv4 address")
        return value

    @field_validator("sending_port", "receiver_port")
    def port_validator(cls, value: int) -> int:
        if value < 1 or value > 65535:
            raise ValueError("Port must be between 1 and 65535")
        return value
