from __future__ import annotations
import json
import os.path
import re
from pydantic import BaseModel, ValidationError, field_validator
from .logger import get_logger
from fastapi import Request, HTTPException
from app.types import Algorithms

logger = get_logger()

CONFIG_FILE = "tracker-config.json"
# https://regex101.com/r/qlLITU/1
IP_ADDRESS_REGEX = (
    r"(\b(?:http:\/\/)?(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)"
    r"(?::\d{1,5})?\b|localhost(?::\d{1,5})?|http:\/\/localhost(?::\d{1,5})?|[\w-]+\.local(?::\d{1,5})?)"
)


class BlobConfig(BaseModel):
    threshold: int = 65
    minsize: int = 10
    maxsize: int = 25


class AlgorithmConfig(BaseModel):
    algorithm_order: list[Algorithms] = [Algorithms.BLOB, Algorithms.HSRAC, Algorithms.RANSAC, Algorithms.HSF]
    blob: BlobConfig = BlobConfig()

    @field_validator("algorithm_order")
    def algorithm_order_validator(cls, value: list[Algorithms]) -> list[Algorithms]:
        if len(value) < 1:
            raise ValueError("Algorithm order must contain at least 1 algorithm")
        
        for algorithm in value:
            if algorithm not in Algorithms:
                raise ValueError("Algorithm order must only contain valid algorithms")
            
        if len(set(value)) != len(value):
            raise ValueError("Algorithm order must not contain duplicate algorithms")
        return value


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


class EyeTrackConfig(BaseModel):
    version: int = 2
    debug: bool = True  # For future use
    osc: OSCConfig = OSCConfig()
    left_eye: CameraConfig = CameraConfig()
    right_eye: CameraConfig = CameraConfig()
    algorithm: AlgorithmConfig = AlgorithmConfig()

    def save(self, file: str = CONFIG_FILE) -> None:
        with open(file, "w+", encoding="utf8") as settings_file:
            json.dump(obj=self.model_dump(), fp=settings_file, indent=4)

    def load(self, file: str = CONFIG_FILE) -> EyeTrackConfig:
        if not os.path.exists(file):
            logger.info("No config file found, using base settings")
        else:
            try:
                with open(file, "r", encoding="utf8") as config:
                    data = config.read()
                    self.__dict__.update(self.model_validate_json(data))
            except (json.JSONDecodeError, ValidationError) as e:
                if type(e) is ValidationError:
                    logger.error(f"Invalid data found in config\n{e}")
                logger.critical("Config is corrupted, creating backup and regenerating")
                os.rename(file, f"{file}.backup")
            except PermissionError:
                logger.error("Permission Denied, assuming config has lock, Retrying...")
                return self.load(file=file)

        self.save(file=file)
        return self

    async def update(self, request: Request) -> None:
        data = await request.json()
        try:
            # make sure all data is valid before we update the config
            self.model_validate_json(data)
            self.update_attributes(data)
            self.save()
        except (ValidationError, Exception) as e:
            logger.error(f"Failed to update config with new values!\n{e}")
            if type(e) is ValidationError:
                raise HTTPException(status_code=400, detail=e.errors(include_url=False, include_context=False))
            else:
                raise HTTPException(status_code=400, detail=str(e))

    def update_attributes(self, data: dict, parents: list[str] = []) -> None:
        for name in data.keys():
            # if the value is a dict it means we are updating a nested config
            # so we need to recursively update all the values in the subconfig individually
            # if we don't do this we will overwrite the entire subconfig with default and partial values
            if isinstance(data[name], dict):
                self.update_attributes(data[name], parents + [name])
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
        return self.model_dump()