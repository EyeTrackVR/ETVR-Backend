from __future__ import annotations
import uuid
import json
import os.path
import re
from pydantic import BaseModel, ValidationError, field_validator
from .logger import get_logger
from fastapi import Request, HTTPException
from app.types import Algorithms, TrackerPosition
import sys

logger = get_logger()

# TODO: we should store this in the same folder as the GUI config, we might not have write access to the executable folder
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    # remove the executable name from the path, and replace it with the config file name
    CONFIG_FILE = os.path.dirname(sys.executable) + os.path.sep + "tracker-config.json"
else:
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


class TrackerConfig(BaseModel):
    enabled: bool = False
    name: str = ""
    uuid: str = ""
    tracker_position: TrackerPosition = TrackerPosition.UNDEFINED
    algorithm: AlgorithmConfig = AlgorithmConfig()
    camera: CameraConfig = CameraConfig()

    @field_validator("uuid")
    def uuid_validator(cls, value: str) -> str:
        if value == "":
            logger.warning("No UUID found for device, generating one")
            return str(uuid.uuid4())
        return value


# FIXME: before opening any files we should check if they are locked
class EyeTrackConfig(BaseModel):
    version: int = 3
    debug: bool = True  # For future use
    osc: OSCConfig = OSCConfig()
    trackers: list[TrackerConfig] = [
        TrackerConfig(
            enabled=True,
            name="Left Eye",
            uuid=str(uuid.uuid4()),
            tracker_position=TrackerPosition.LEFT_EYE,
        ),
        TrackerConfig(
            enabled=True,
            name="Right Eye",
            uuid=str(uuid.uuid4()),
            tracker_position=TrackerPosition.RIGHT_EYE,
        ),
        TrackerConfig(
            enabled=False,
            name="Mouth",
            uuid=str(uuid.uuid4()),
            tracker_position=TrackerPosition.MOUTH,
        ),
    ]

    def save(self, file: str = CONFIG_FILE) -> None:
        try:
            with open(file, "w+", encoding="utf8") as settings_file:
                json.dump(obj=self.model_dump(), fp=settings_file, indent=4)
        except PermissionError:
            logger.error(f"Permission Denied `{file}`, assuming config has lock, Retrying...")
            self.save(file=file)

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
                os.replace(file, f"{file}.backup")
            except PermissionError:
                logger.error("Permission Denied, assuming config has lock, Retrying...")
                return self.load(file=file)

        self.save(file=file)
        return self

    def update_model(self, obj: BaseModel, data: dict) -> None:
        if isinstance(obj, BaseModel):
            for key, value in data.items():
                if hasattr(obj, key):
                    if key == "trackers":
                        logger.warning("Skiping input validation for trackers array, this may cause unexpected behaviour!")
                        logger.warning("Use the `/etvr/config/tracker` endpoints to update individual trackers")
                    current_value = getattr(obj, key)
                    if isinstance(current_value, BaseModel):
                        self.update_model(current_value, value)
                    else:
                        setattr(obj, key, value)
                else:
                    logger.debug(f"Config has no attribute `{key}`")

    def get_tracker_by_uuid(self, uuid: str) -> TrackerConfig:
        for tracker in self.trackers:
            if tracker.uuid == uuid:
                return tracker
        raise ValueError(f"No tracker found with UUID `{uuid}`")

    def get_uuid_index(self, uuid: str) -> int:
        for index, tracker in enumerate(self.trackers):
            if tracker.uuid == uuid:
                return index
        raise ValueError(f"No tracker found with UUID `{uuid}`")

    def return_config(self) -> dict:
        return self.model_dump()

    # region: FastAPI routes
    async def update(self, request: Request) -> None:
        try:
            data = await request.json()
            self.model_validate(data)
            self.update_model(self, data)
            self.save()
        except (ValidationError, Exception) as e:
            logger.error(f"Failed to update config with new values!\n{e}")
            self.__HTTPException(e)

    async def update_tracker(self, request: Request, uuid: str) -> None:
        try:
            data = await request.json()
            tracker = self.get_tracker_by_uuid(uuid)
            tracker.model_validate(data)
            self.update_model(tracker, data)
            self.save()
        except (ValidationError, ValueError, Exception) as e:
            logger.error(f"Failed to update tracker config with new values!\n{e}")
            self.__HTTPException(e)

    async def create_tracker(self, tracker: TrackerConfig) -> TrackerConfig:
        try:
            tracker = TrackerConfig.model_validate(tracker)
            self.trackers.append(tracker)
            self.save()
        except (ValidationError, Exception) as e:
            logger.error(f"Failed to create tracker!\n{e}")
            self.__HTTPException(e)
        return tracker

    async def delete_tracker(self, uuid: str) -> None:
        try:
            tracker = self.get_tracker_by_uuid(uuid)
            self.trackers.remove(tracker)
            self.save()
        except (ValueError, Exception) as e:
            logger.error(f"Failed to delete tracker!\n{e}")
            self.__HTTPException(e)

    async def get_trackers(self) -> list[TrackerConfig]:
        return self.trackers

    def __HTTPException(self, e: Exception) -> HTTPException:
        if type(e) is ValidationError:
            raise HTTPException(status_code=400, detail=e.errors(include_url=False, include_context=False))
        else:
            raise HTTPException(status_code=400, detail=str(e))

    # endregion

    # region: Model validation
    @field_validator("trackers")
    def trackers_uuid_validator(cls, value: list[TrackerConfig]) -> list[TrackerConfig]:
        uuids = []
        for tracker in value:
            if tracker.uuid in uuids:
                logger.warning(f"Duplicate UUID found for tracker {tracker.name}, generating new UUID")
                tracker.uuid = str(uuid.uuid4())
            uuids.append(tracker.uuid)
        return value

    @field_validator("trackers")
    def trackers_enabled_validator(cls, value: list[TrackerConfig]) -> list[TrackerConfig]:
        # make sure we only have one tracker per position active at one time,
        # if we have multiple we disable all occurences after the first
        enabled = []
        for tracker in value:
            if tracker.enabled:
                if tracker.tracker_position in enabled:
                    logger.warning(f"Multiple devices found with position `{tracker.tracker_position.name}`")
                    logger.warning(f"Disabling tracker `{tracker.name}`, with UUID `{tracker.uuid}`")
                    tracker.enabled = False
                else:
                    enabled.append(tracker.tracker_position)
        return value

    @field_validator("trackers")
    def trackers_position_validator(cls, value: list[TrackerConfig]) -> list[TrackerConfig]:
        # if the tracker has no position we disable it
        for tracker in value:
            if tracker.tracker_position == TrackerPosition.UNDEFINED and tracker.enabled:
                logger.warning(f"Tracker `{tracker.name}` with uuid `{tracker.uuid}` has no position, disabling it")
                tracker.enabled = False
        return value

    # endregion
