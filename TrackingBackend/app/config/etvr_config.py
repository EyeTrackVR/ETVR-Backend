from __future__ import annotations
import json
import os.path
from fastapi import Request, HTTPException
from pydantic import BaseModel, ValidationError
from app.config import AlgorithmConfig, CameraConfig, OSCConfig, CONFIG_FILE
from app.logger import get_logger

logger = get_logger()


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
                    # If the config has invalid attributes, pydantic will replace them with default values
                    self.__dict__.update(self.model_validate_json(data))
            except (PermissionError, json.JSONDecodeError):
                logger.error("Failed to load config, file is locked, Retrying...")
                # FIXME: we need to check if the file has a lock
                return self.load(file=file)
            except ValidationError as e:
                logger.error(f"Invalid Data found in config, replacing with default values.\n{e}")

        self.save(file=file)
        return self

    async def update(self, request: Request) -> None:
        data = await request.json()
        try:
            # make sure all data is valid before we update the config
            self.model_validate(data)
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
