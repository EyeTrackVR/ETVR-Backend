from app.config import IP_ADDRESS_REGEX, EyeTrackConfig, TrackerConfig, ConfigManager, CONFIG_FILE
import pytest
import json
import re
import os


def remove_test_config():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)


@pytest.mark.parametrize(
    "ip_list",
    [
        "127.0.0.1",
        "localhost",
        "openiris.local",
        "127.0.0.1:8080",
        "localhost:8080",
        "http://localhost",
        "http://10.0.0.39",
        "openiris.local:8080",
        "http://localhost:8080",
    ],
)
def test_ip_address_regex(ip_list):
    assert re.match(IP_ADDRESS_REGEX, ip_list) is not None


def test_config_save():
    remove_test_config()

    config = ConfigManager()
    config.save()
    assert os.path.exists(CONFIG_FILE)
    with open(CONFIG_FILE, "rt") as f:
        config_data = f.read()
        assert config_data == json.dumps(config.model_dump(), indent=4)


def test_config_load():
    remove_test_config()

    config = ConfigManager()
    config.load()
    assert config == EyeTrackConfig()


def test_config_load_modified():
    remove_test_config()

    original_config = ConfigManager()
    original_config.version = 3
    original_config.save()
    assert os.path.exists(CONFIG_FILE)

    config = ConfigManager()
    config.load()
    assert config == original_config


def test_config_load_invalid():
    remove_test_config()

    with open(CONFIG_FILE, "wt") as f:
        f.write("invalid json")

    config = ConfigManager()
    config.load()
    assert config == EyeTrackConfig()


def test_config_upate_attributes():
    config = ConfigManager()

    config.update_model(config, {"version": 3})
    assert config.model_dump()["version"] == 3

    config.update_model(config, {"osc": {"address": "localhost"}})
    assert config.model_dump()["osc"]["address"] == "localhost"

    config.update_model(config, {"osc": {"endpoints": {"eyes_y": "/avatar/parameters/EyesPytest"}}})
    assert config.model_dump()["osc"]["endpoints"]["eyes_y"] == "/avatar/parameters/EyesPytest"


def test_get_tracker_by_uuid():
    config = EyeTrackConfig()
    tracker = config.trackers[0]
    tracker.uuid = "test_uuid"
    tracker.name = "test_name"

    assert config.get_tracker_by_uuid("test_uuid") == tracker


def test_get_uuid_index():
    config = EyeTrackConfig()
    tracker = config.trackers[0]
    tracker.uuid = "test_uuid"

    assert config.get_uuid_index("test_uuid") == 0


# region: Endpoint tests
@pytest.mark.asyncio
async def test_config_reset():
    remove_test_config()

    config = ConfigManager()
    config.version = 100
    config.osc.address = "localhost"
    config.osc.receiver_port = 8081
    config.debug = not config.debug
    config.save()

    await config.reset()
    assert config == EyeTrackConfig()


@pytest.mark.asyncio
async def test_config_tracker_reset():
    remove_test_config()

    name = "test"
    uuid = "test_uuid"

    config = ConfigManager()
    tracker = config.trackers[0]
    tracker.name = name
    tracker.uuid = uuid
    tracker.camera.threshold = 100
    config.save()

    await config.reset_tracker(uuid)
    assert config.trackers[0].uuid == uuid
    assert config.trackers[0].name == name
    assert config.trackers[0].camera.threshold == EyeTrackConfig().trackers[0].camera.threshold


@pytest.mark.asyncio
async def test_create_tracker():
    config = ConfigManager()
    len_before = len(config.trackers)

    await config.create_tracker(TrackerConfig())
    assert len(config.trackers) == len_before + 1
    assert config.trackers[-1] == TrackerConfig()


@pytest.mark.asyncio
async def test_delete_tracker():
    config = ConfigManager()
    len_before = len(config.trackers)

    await config.delete_tracker(config.trackers[0].uuid)
    assert len(config.trackers) == len_before - 1
    assert config.trackers[0] != EyeTrackConfig().trackers[0]


# endregion
