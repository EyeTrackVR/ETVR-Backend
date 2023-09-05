from pydantic import BaseModel, field_validator
from app.types import Algorithms


class BlobConfig(BaseModel):
    threshold: int = 65
    minsize: int = 10
    maxsize: int = 25


class AlgorithmConfig(BaseModel):
    algorithm_order: list[Algorithms] = [Algorithms.BLOB, Algorithms.HSRAC, Algorithms.RANSAC, Algorithms.HSF]
    blob: BlobConfig = BlobConfig()

    @field_validator("algorithm_order")
    def algorithm_validator(cls, value: list[Algorithms]) -> list[Algorithms]:
        if len(value) == 0:
            raise ValueError("At least one algorithm must be defined")

        if len(value) != len(set(value)):
            raise ValueError("Cannot have duplicate algorithms defined in algorithm_order")
        return value
