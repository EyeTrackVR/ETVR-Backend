from __future__ import annotations
import json
import os.path
import re
from pydantic import BaseModel, ValidationError, validate_model, validator
from .logger import get_logger
from fastapi import Request

logger = get_logger()

CONFIG_FILE = "tracker-config.json"


class BlobConfig(BaseModel):
    threshold: int = 65
    minsize: int = 10
    maxsize: int = 25


class AlgorithmConfig(BaseModel):
    blob: BlobConfig = BlobConfig()


class OSCConfigEndpoints(BaseModel):
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
    endpoints: OSCConfigEndpoints = OSCConfigEndpoints()

    @validator("address")
    def address_validator(cls, value: str) -> str:
        if re.match(r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$", value) is None:
            raise ValueError(f"Invalid IP Address")
        return value

    @validator("sending_port", "receiver_port")
    def port_validator(cls, value: int) -> int:
        if value < 1 or value > 65535:
            raise ValueError("Port must be between 1 and 65535")
        return value


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

    @validator("roi_x", "roi_y", "roi_w", "roi_h")
    def roi_validator(cls, value: int) -> int:
        if value < 0:
            raise ValueError("ROI values must be greater than 0")
        return value


class EyeTrackConfig(BaseModel):
    version: int = 2
    debug: bool = True  # For future use
    osc: OSCConfig = OSCConfig()
    left_eye: CameraConfig = CameraConfig()
    right_eye: CameraConfig = CameraConfig()
    algorithm: AlgorithmConfig = AlgorithmConfig()

    def save(self, file: str = CONFIG_FILE) -> None:
        with open(file, "w+", encoding="utf8") as settings_file:
            json.dump(obj=self.dict(), fp=settings_file, indent=4)

    def load(self, file: str = CONFIG_FILE) -> EyeTrackConfig:
        if not os.path.exists(file):
            logger.info("No config file found, using base settings")
        else:
            try:
                # since we are loading a full config we assume it is valid
                self.__dict__.update(self.parse_file(file))
                self.validate(self)
            except (PermissionError, json.JSONDecodeError):
                logger.error("Failed to load config, file is locked, Retrying...")
                # FIXME: we need to check if the file has a lock
                return self.load()
            except ValidationError as e:
                logger.error(f"Invalid Data found in config, replacing with default values.\n{e}")

        self.save()
        return self

    async def update(self, request: Request) -> None:
        data = await request.json()
        try:
            _, _, error = validate_model(self.__class__, data)
            if error:
                raise error
            self.direct_update(data)
            self.save()
        except (ValidationError, Exception):
            logger.exception("Failed to update config with new values!")

    def direct_update(self, data: dict, parents: list[str] = []) -> None:
        for name in data.keys():
            # if the value is a dict it means we need to are updating a nested config
            # so we need to recursively update all the values in the subconfig individually
            # if we don't do this we will overwrite the entire subconfig with default and partial values
            if type(data[name]) is dict:
                self.direct_update(data[name], parents + [name])
            else:
                obj = self
                if len(parents) > 0:
                    # build the path to the object
                    for parent in parents:
                        obj = getattr(obj, parent)
                value = data[name]
                if not getattr(obj, name) == value:
                    logger.debug(f"Setting Config{''.join(['[', *parents, ']']).replace('[]', '')}[{name}] to {value}")
                    setattr(obj, name, value)

    def return_config(self) -> dict:
        return self.dict()
