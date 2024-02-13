# TODO: split this package into multiple files, its getting too big
from __future__ import annotations
import re
import sys
import uuid
import json
import time
import random
import os.path
import multiprocessing
from copy import deepcopy
from app.logger import get_logger
from typing import Callable, Final
from app.utils import mask_to_cpu_list
from watchdog.observers import Observer
from fastapi import Request, HTTPException
from watchdog.observers.api import BaseObserver
from app.types import Algorithms, TrackerPosition
from pydantic import BaseModel, ValidationError, field_validator
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

logger = get_logger()

# TODO: we should store this in the same folder as the GUI config, we might not have write access to the executable folder
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    CONFIG_PATH = os.path.dirname(sys.executable)
elif os.environ.get("ETVR_UNITTEST") is not None:
    CONFIG_PATH = ".pytest_cache"
else:
    CONFIG_PATH = "."
CONFIG_NAME: Final = "tracker-config.json"
CONFIG_FILE: Final = CONFIG_PATH + os.path.sep + CONFIG_NAME
# https://regex101.com/r/qlLITU/1
IP_ADDRESS_REGEX: Final = (
    r"(\b(?:http:\/\/)?(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)"
    r"(?::\d{1,5})?\b|localhost(?::\d{1,5})?|http:\/\/localhost(?::\d{1,5})?|[\w-]+\.local(?::\d{1,5})?)"
)


class BlobConfig(BaseModel):
    threshold: int = 65
    minsize: int = 10
    maxsize: int = 25


class LeapConfig(BaseModel):
    blink_threshold: float = 0.25

    @field_validator("blink_threshold")
    def blink_threshold_validator(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("Blink threshold must be between 0 and 1")
        return value


class AlgorithmConfig(BaseModel):
    algorithm_order: list[Algorithms] = [Algorithms.LEAP, Algorithms.BLOB, Algorithms.HSRAC, Algorithms.RANSAC, Algorithms.HSF]
    blob: BlobConfig = BlobConfig()
    leap: LeapConfig = LeapConfig()

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
    rotation: int = 0
    threshold: int = 50
    focal_length: int = 30
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
        if re.match(IP_ADDRESS_REGEX, value) is not None:
            return value
        elif "com" in value.lower():
            return value
        elif "/dev/" in value.lower():
            return value
        elif value == "":
            return value
        else:
            raise ValueError("Invalid capture source, must be a valid IP address or COM port")


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


# TODO: move management code into `ConfigManager` class
class EyeTrackConfig(BaseModel):
    version: int = 4
    debug: bool = True
    affinity_mask: str = ""
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

    @field_validator("affinity_mask")
    def affinity_mask_validator(cls, value: str) -> str:
        try:
            cpu_count = multiprocessing.cpu_count() - 1  # CPU indexing starts at 0
            cpus = mask_to_cpu_list(value)
            for cpu_index in cpus:
                if cpu_index > cpu_count:
                    logger.warning(f"CPU mask contains invalid CPU `{cpu_index}`, only `{cpu_count}` CPUs available")
                    raise ValueError
            return value
        except ValueError:
            logger.warning("Invalid CPU mask")

        return ""

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


class ConfigManager(EyeTrackConfig, FileSystemEventHandler):
    # callback function will a copy of the old config, the manager will have the new config
    def __init__(self, callback: Callable[[EyeTrackConfig], None] | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__callback = callback
        self.__logger = get_logger()
        # None by default because threads arent pickable
        self.__observer: BaseObserver | None = None

    # region: Config file management
    def start(self) -> ConfigManager:
        self.__logger.info("Starting config manager and watcher thread")
        self.__observer = Observer()
        self.__observer.daemon = True
        self.__observer.name = "Config Manager"
        self.__observer.schedule(
            event_handler=self,
            path=CONFIG_PATH,
            recursive=False,
        )
        self.__observer.start()

        # fire callbacks incase the config was modified while the server was offline
        self.on_modified(FileModifiedEvent(CONFIG_FILE))  # this also loads the config
        return self

    def stop(self) -> None:
        self.__logger.info("Stopping config manager and watcher thread")
        if self.__observer is not None:
            self.__observer.stop()

    def save(self) -> None:
        try:
            self.__logger.debug("Config save requested")
            with open(CONFIG_FILE, "wt", encoding="utf8") as file:
                json.dump(obj=self.model_dump(), fp=file, indent=4)
            self.__logger.info("Current config saved to disk")
        except PermissionError:
            self.__logger.error(f"`{CONFIG_FILE}` Permission Denied, assuming config has lock, Retrying...")
            self.save()

    def load(self) -> ConfigManager:
        # FIXME: hack to stop multiple processes open the config at the exact same time
        # if this ever happens on windows one of the processes will receive a empty file, WTF?
        time.sleep(random.random())

        try:
            file = open(CONFIG_FILE, "rt", encoding="utf8").read()
            self.__dict__.update(self.model_validate_json(file))
            if file != json.dumps(self.model_dump(), indent=4):
                self.__logger.warning("Config had validation errors, saving validated config")
                self.save()
        except PermissionError:
            self.__logger.error("Permission Denied, assuming config has lock, retrying...")
            self.load()
        except FileNotFoundError:
            self.__logger.error("Config file not found, using base settings")
            self.save()
        except (json.JSONDecodeError, ValidationError):
            self.__logger.exception("Failed to load config file!")
            self.__logger.critical("Creating backup and regenerating")
            os.replace(CONFIG_FILE, f"{CONFIG_FILE}.backup")
            self.save()

        return self

    def on_modified(self, event: FileModifiedEvent) -> None:
        # macos is weird, sometimes returns the absolute path instead of relative
        if event.src_path == CONFIG_FILE or event.src_path == os.path.abspath(CONFIG_FILE):
            self.__logger.debug(f"Config modified event fired `{event.src_path}`")
            # we cant deepcopy the whole class because threads contains multiple `AuthenticationString` objects
            old_config = deepcopy(self.model_dump())
            if self.load().model_dump() != old_config:
                self.__logger.info("Config update detected, calling callbacks")
                if self.__callback is not None:
                    self.__callback(EyeTrackConfig(**old_config))

    # endregion

    def update_model(self, obj: BaseModel, data: dict) -> None:  # TODO: make our own base model class
        if isinstance(obj, BaseModel):
            for key, value in data.items():
                if hasattr(obj, key):
                    if key == "trackers":
                        self.__logger.warning("Skiping input validation for trackers array, this may cause unexpected behaviour!")
                        self.__logger.warning("Use the `/etvr/config/tracker` endpoints to update individual trackers")
                    current_value = getattr(obj, key)
                    if isinstance(current_value, BaseModel):
                        self.update_model(current_value, value)
                    else:
                        setattr(obj, key, value)
                else:
                    self.__logger.debug(f"Config has no attribute `{key}`")

    # TODO: dont use request objects, use the actual dataclasses
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

    async def reset(self) -> None:
        new_config = EyeTrackConfig()
        self.__dict__.update(new_config.__dict__)
        self.save()

    async def reset_tracker(self, uuid: str) -> None:
        try:
            # we reset everything except the UUID and name
            old_tracker = self.get_tracker_by_uuid(uuid)
            uuid = old_tracker.uuid
            name = old_tracker.name

            tracker = TrackerConfig()
            tracker.uuid = uuid
            tracker.name = name
            self.trackers[self.get_uuid_index(uuid)] = tracker
        except (ValueError, Exception) as e:
            logger.error(f"Failed to reset tracker!\n{e}")
            self.__HTTPException(e)

    def __HTTPException(self, e: Exception) -> HTTPException:
        if type(e) is ValidationError:
            raise HTTPException(status_code=400, detail=e.errors(include_url=False, include_context=False))
        else:
            raise HTTPException(status_code=400, detail=str(e))

    # endregion

    def __del__(self) -> None:
        # the observer has a copy of this class, when it detects a change in the config file it will delete a reference
        # calling the destructor, but the copy class isnt *real* so to avoid log spam we check if the observer exists
        if self.__observer is not None:
            self.stop()

    # for reasons only god knows, ASGI wants this class to be hashable
    def __hash__(self) -> int:
        return hash(self.__class__)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EyeTrackConfig):
            return NotImplemented
        return self.model_dump() == other.model_dump()
