from multiprocessing import Process
from app.logger import get_logger, setup_logger
from app.config import EyeTrackConfig, CONFIG_FILE
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from os import path
import time
import typing

# Welcome to assassin's multiprocessing hell here is your complimentary gas mask, flamethrower, fire extinguisher, and bible
# Here are some rules to follow:
# 1. Try not to share objects between processes
# 2. If you have to share objects between processes, use a manager
# 3. Do not pass a manager to a child process, it will not work
# 4. If you have to register a complex object to a manager, create a proxy
# 5. Queue's are your friend, use them
# I hope you enjoy your stay


# This is a simple wrapper around the multiprocessing.Process class
# we are using it to abstract some of the more painful parts of multiprocessing
class WorkerProcess:
    def __init__(self, name: str):
        self.__name: str = name
        self.__last_config_update = 0.0
        self.__process: Process = Process()
        self.__event_handler = FileSystemEventHandler()
        self.__observer: typing.Optional[BaseObserver] = None
        self.base_config: EyeTrackConfig = EyeTrackConfig()
        self.logger = get_logger(self.__module__)
        self.logger.debug(f"Created process `{self.__name}`")

    # TODO: we should add a event so we can gracefully shutdown the process
    def _run_process(self) -> None:
        # since we are in a child process, we need to recreate some objects that arent shared
        try:
            setup_logger()
            self.setup_watchdog()
            self.startup()
            self.run()
            self.shutdown()
        except Exception:
            self.logger.exception("Unhandled exception in child process!")

    def setup_watchdog(self) -> None:
        try:
            self.logger.debug(f"Starting config watcher thread for process `{self.__name}`")
            self.__observer = Observer()
            self.__observer.daemon = True
            self.__observer.name = f"{self.__name} Config Watcher"
            self.__event_handler.on_modified = self.on_file_modified  # type: ignore[method-assign]
            self.__observer.schedule(
                event_handler=self.__event_handler,
                path=".",
                recursive=False,
            )
            self.__observer.start()
        except Exception:
            self.logger.exception("Failed to start config watcher thread")

    def start(self) -> None:
        # don't start a process if one already exists
        if self.is_alive():
            self.logger.debug(f"Process `{self.__name}` requested to start but is already running")
            return

        self.logger.info(f"Starting Process `{self.__name}`")
        # We need to recreate the process because it is not possible to start a process that has already been stopped]
        try:
            self.__process = Process(target=self._run_process, name=f"{self.__name}")
            self.__process.daemon = True
            self.__process.start()
        except (TypeError, Exception):
            self.logger.exception(f"Failed to start process `{self.__name}`")

    def stop(self) -> None:
        # can't kill a non-existent process
        if not self.is_alive():
            self.logger.debug(f"Request to kill dead process `{self.__name}` was made!")
            return

        try:
            self.logger.info(f"Stopping process `{self.__name}`")
            self.__process.kill()
            self.__process.join()
        except (AttributeError, Exception):
            self.logger.exception(f"Failed to kill process `{self.__name}`")

    def on_file_modified(self, event: FileModifiedEvent) -> None:
        # this event is called multiple times when a file is modified
        # so we just use a one second timeout
        if time.time() - self.__last_config_update > 1:
            if event.src_path == f".{path.sep}{CONFIG_FILE}":
                self.logger.debug(f"Config updated for process `{self.__name}`")
                self.base_config.load()
                self.on_config_update(self.base_config)
                self.__last_config_update = time.time()

    def run(self) -> None:
        self.logger.critical("WorkerProcess.run() must be overridden in child class!")
        raise NotImplementedError

    def startup(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def on_config_update(self, config: EyeTrackConfig) -> None:
        pass

    def __del__(self) -> None:
        if self.is_alive():
            self.stop()

    def restart(self) -> None:
        self.stop()
        self.start()

    def process_name(self) -> str:
        return self.__name

    def is_alive(self) -> bool:
        if self.__process is None:
            return False
        else:
            return self.__process.is_alive()
