from eyetrackvr_backend.utils import clamp
import pytest


@pytest.mark.parametrize(
    "x, low, high, expected",
    [
        (0, 0, 0, 0),
        (0, 0, 1, 0),
        (0, 1, 2, 1),
        (2, 0, 1, 1),
        (2, 0, 2, 2),
        (2, 1, 2, 2),
        (2, 2, 2, 2),
    ],
)
def test_clamp(x, low, high, expected):
    assert clamp(x, low, high) == expected
