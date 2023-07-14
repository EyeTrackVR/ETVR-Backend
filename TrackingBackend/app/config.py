from __future__ import annotations
import json
import os.path
from pydantic import BaseModel, ValidationError, validate_model
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
    left_eyelid_squeeze: str = "/avatar/parameters/LeftEyeLidExpandedSqueeze"
    right_eyelid_squeeze: str = "/avatar/parameters/RightEyeLidExpandedSqueeze"


class OSCConfig(BaseModel):
    address: str = "127.0.0.1"
    mirror_eyes: bool = False
    sync_blink: bool = False
    enable_sending: bool = True
    sending_port: int = 9000
    enable_receiving: bool = True
    receiver_port: int = 9001
    endpoints: OSCConfigEndpoints = OSCConfigEndpoints()


class CameraConfig(BaseModel):
    enabled: bool = False
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
        # TODO: check if file has lock before loading
        if not os.path.exists(file):
            logger.info("No config file found, using base settings")
        else:
            try:
                # since we are loading a full config it is fine for us to just update the entire dict because we assume
                # that the data is valid, if there are extra or missing fields in the config by default pydantic will
                # fill them in with default values.
                # if we want to "update" parts of the config at runtime we should use `setattr` so we can retain
                # previous values and only update values that have been "requested" to be changed
                self.__dict__.update(self.parse_file(file))
                self.validate(self)
            except (ValidationError, Exception):
                logger.exception("Invalid Data found in config, replacing with default values")
        self.save()
        return self

    # FIXME: if a partial config is sent it will overwrite the entire config with the partial data
    # and reset any values that were not sent
    async def update(self, request: Request) -> None:
        data = await request.json()
        try:
            values, fields, error = validate_model(self.__class__, data)
            if error:
                raise error
            for name in fields:
                value = values[name]
                logger.debug("set object data -- %s => %s", name, value)
                setattr(self, name, value)
            # Once all new values are set save just incase we crash somewhere
            self.save()
        except (ValidationError, Exception):
            logger.exception("Failed to update config with new values!")

    def return_config(self) -> dict:
        return self.dict()
