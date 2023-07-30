from app.config import IP_ADDRESS_REGEX, EyeTrackConfig
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
    # remove the test config if it exists
    if os.path.exists(".pytest_cache/test_config.json"):
        os.remove(".pytest_cache/test_config.json")

    config = EyeTrackConfig()
    config.load(".pytest_cache/test_config.json")
    assert config.return_config() == EyeTrackConfig().return_config()


def test_config_upate_attributes():
    config = EyeTrackConfig()
    
    config.update_attributes({"version": 3})
    assert config.return_config()["version"] == 3

    config.update_attributes({"osc": {"address": "localhost"}})
    assert config.return_config()["osc"]["address"] == "localhost"

    config.update_attributes({"osc": {"endpoints": {"eyes_y": "/eyes/y/pytest"}}})
    assert config.return_config()["osc"]["endpoints"]["eyes_y"] == "/eyes/y/pytest"
