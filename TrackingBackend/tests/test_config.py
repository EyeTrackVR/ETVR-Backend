from app.config import IP_ADDRESS_REGEX, EyeTrackConfig, TrackerConfig
import pytest
import json
import re
import os


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
    # remove the test config if it exists
    if os.path.exists(".pytest_cache/test_config.json"):
        os.remove(".pytest_cache/test_config.json")

    config = EyeTrackConfig()
    config.save(".pytest_cache/test_config.json")
    assert os.path.exists(".pytest_cache/test_config.json")
    with open(".pytest_cache/test_config.json", "r") as f:
        config_data = f.read()
        assert config_data == json.dumps(config.return_config(), indent=4)


def test_config_load():
    if os.path.exists(".pytest_cache/test_config.json"):
        os.remove(".pytest_cache/test_config.json")

    config = EyeTrackConfig()
    config.load(".pytest_cache/test_config.json")
    assert config == EyeTrackConfig()


def test_config_load_modified():
    if os.path.exists(".pytest_cache/test_config.json"):
        os.remove(".pytest_cache/test_config.json")

    original_config = EyeTrackConfig()
    original_config.version = 3
    original_config.save(".pytest_cache/test_config.json")
    assert os.path.exists(".pytest_cache/test_config.json")

    config = EyeTrackConfig()
    config.load(".pytest_cache/test_config.json")
    assert config == original_config


def test_config_load_invalid():
    if os.path.exists(".pytest_cache/test_config.json"):
        os.remove(".pytest_cache/test_config.json")

    with open(".pytest_cache/test_config.json", "w") as f:
        f.write("invalid json")

    config = EyeTrackConfig()
    config.load(".pytest_cache/test_config.json")
    assert config == EyeTrackConfig()


def test_config_upate_attributes():
    config = EyeTrackConfig()

    config.update_model(config, {"version": 3})
    assert config.return_config()["version"] == 3

    config.update_model(config, {"osc": {"address": "localhost"}})
    assert config.return_config()["osc"]["address"] == "localhost"

    config.update_model(config, {"osc": {"endpoints": {"eyes_y": "/avatar/parameters/EyesPytest"}}})
    assert config.return_config()["osc"]["endpoints"]["eyes_y"] == "/avatar/parameters/EyesPytest"


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
    if os.path.exists(".pytest_cache/test_config.json"):
        os.remove(".pytest_cache/test_config.json")

    config = EyeTrackConfig()
    config.version = 100
    config.osc.address = "localhost"
    config.osc.receiver_port = 8081
    config.debug = not config.debug
    config.save(".pytest_cache/test_config.json")

    await config.reset()
    assert config == EyeTrackConfig()


@pytest.mark.asyncio
async def test_config_tracker_reset():
    if os.path.exists(".pytest_cache/test_config.json"):
        os.remove(".pytest_cache/test_config.json")

    name = "test"
    uuid = "test_uuid"

    config = EyeTrackConfig()
    tracker = config.trackers[0]
    tracker.name = name
    tracker.uuid = uuid
    tracker.camera.threshold = 100
    config.save(".pytest_cache/test_config.json")

    await config.reset_tracker(uuid)
    assert config.trackers[0].uuid == uuid
    assert config.trackers[0].name == name
    assert config.trackers[0].camera.threshold == EyeTrackConfig().trackers[0].camera.threshold


@pytest.mark.asyncio
async def test_create_tracker():
    config = EyeTrackConfig()
    len_before = len(config.trackers)

    await config.create_tracker(TrackerConfig())
    assert len(config.trackers) == len_before + 1
    assert config.trackers[-1] == TrackerConfig()


@pytest.mark.asyncio
async def test_delete_tracker():
    config = EyeTrackConfig()
    len_before = len(config.trackers)

    await config.delete_tracker(config.trackers[0].uuid)
    assert len(config.trackers) == len_before - 1
    assert config.trackers[0] != EyeTrackConfig().trackers[0]


# endregion
