# https://regex101.com/r/qlLITU/1
IP_ADDRESS_REGEX = (
    r"(\b(?:http:\/\/)?(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)"
    r"(?::\d{1,5})?\b|localhost(?::\d{1,5})?|http:\/\/localhost(?::\d{1,5})?|[\w-]+\.local(?::\d{1,5})?)"
)
CONFIG_FILE = "tracker-config.json"


# Importing after the constants are defined to avoid circular imports
from .algorithm_config import AlgorithmConfig, BlobConfig  # noqa: E402
from .osc_config import OSCConfig, OSCEndpoints  # noqa: E402
from .camera_config import CameraConfig  # noqa: E402
from .etvr_config import EyeTrackConfig  # noqa: E402
