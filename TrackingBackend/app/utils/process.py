import time
from os import path
from copy import deepcopy
from app.window import Window
from multiprocessing import Process, Event
from watchdog.events import FileModifiedEvent
from app.logger import get_logger, setup_logger
from app.config import EyeTrackConfig, CONFIG_FILE, TrackerConfig, ConfigWatcher

# Welcome to assassin's multiprocessing realm
# To not repeat the same mistakes I made, here are some tips:
# 1. Try not to share objects between processes
# 2. If you have to share objects between processes, use a manager
# 3. Do not pass a manager to a child process, it will not work
# 4. If you have to register a complex object to a manager, create a proxy
# 5. Queue's are your friend, use them
# 6. Unless explicitly shared, all variables should be cloned
# 7. If you have share a variable, please document it


# TODO: when python 3.13 comes out, we should look into the new per interpreter GIL
# if it is faster maybe we should refactor this to use it?
class WorkerProcess:
    def __init__(self, name: str, uuid: str = ""):
        self.name = name
        self.__process = Process()
        self.__shutdown_event = Event()
        self.base_config = EyeTrackConfig().load()
        self.__config_watcher = ConfigWatcher(name, self._config_update)

        self.uuid = uuid
        self.debug = self.base_config.debug
        self.logger = get_logger(self.__module__)
        self.window = Window(self.base_config.debug)
        self.logger.debug(f"Initialized process `{self.name}`")

    # region: Child class overrides and callbacks
    def run(self) -> None:
        """run the child process main loop.
        * Should not include a while loop this parent class should handle lifecycles.
        * All children must override this method and implement their own main loop
        * Although its better to handle all errors in the child process, this parent class will take care of unhandled exceptions
        * Unless necessary, do not call cv2.waitkey(1) this parent class handle all debug windows
        """
        self.logger.critical("WorkerProcess.run() must be overridden in child class!")
        raise NotImplementedError

    def startup(self) -> None:
        """initialization code that is run inside the child process before the main loop starts."""

    def shutdown(self) -> None:
        """cleanup code that is run inside the child process right after the main loop ends."""

    def on_config_update(self, config: EyeTrackConfig) -> None:
        """callback function that is called when any part of the config is updated."""

    def on_tracker_config_update(self, tracker_config: TrackerConfig) -> None:
        """callback function that is called when the tracker with the given uuid is updated."""

    # endregion

    # region: Internal methods
    def _run(self) -> None:
        try:
            self.__config_watcher.start()
            setup_logger()
            self.startup()
            self._mainloop()
            self.shutdown()
        except Exception:
            self.logger.exception("Error occurred in child process!")

    def _mainloop(self) -> None:
        while not self.__shutdown_event.is_set():
            try:
                self.run()
                self.window._waitkey(1)
            except KeyboardInterrupt:
                self.logger.warning("Keyboard interrupt received, shutting down...")
                self.__shutdown_event.set()
                break
            except Exception:
                self.logger.exception("Unhandled exception in child process! Continuing...")
                continue

    def _config_update(self, event: FileModifiedEvent) -> None:
        if event.src_path == f".{path.sep}{CONFIG_FILE}":
            old_config = deepcopy(self.base_config)
            self.base_config.load()
            if self.base_config != old_config:
                self.logger.debug(f"Config updated for process `{self.name}`")
                self.debug = self.base_config.debug
                self.on_config_update(self.base_config)
                self.window._debug = self.base_config.debug
                for tracker in self.base_config.trackers:
                    if tracker.uuid == self.uuid:
                        old_tracker = old_config.get_tracker_by_uuid(self.uuid)
                        if tracker != old_tracker:
                            self.logger.info(f"Tracker config updated for process `{self.name}`")
                            self.on_tracker_config_update(tracker)

    # endregion

    def start(self) -> None:
        if self.is_alive():
            self.logger.debug(f"Process `{self.name}` requested to start but is already running")
            return

        try:
            self.__shutdown_event.clear()
            self.logger.info(f"Starting Process `{self.name}`")
            self.__process = Process(target=self._run, name=f"{self.name}")
            self.__process.daemon = True
            self.__process.start()
        except (TypeError, Exception):
            self.logger.exception(f"Failed to start process `{self.name}`")

    def stop(self) -> None:
        if not self.is_alive():
            self.logger.debug(f"Request to kill dead process `{self.name}` was made!")
            return

        try:
            self.__shutdown_event.set()
            self.logger.info(f"Stopping process `{self.name}`")
            self.__process.join(timeout=5)
        except (AttributeError, Exception):
            self.logger.exception(f"Failed to stop process `{self.name}`")
        finally:
            self.kill()

    def kill(self) -> None:
        if self.is_alive():
            self.__process.kill()
            self.__process.join()
            self.logger.info(f"Killed process `{self.name}`")

    def restart(self) -> None:
        self.stop()
        self.start()

    def process_name(self) -> str:
        return self.name

    def is_alive(self) -> bool:
        if self.__process is None:
            return False
        else:
            return self.__process.is_alive()

    def __del__(self) -> None:
        if self.is_alive():
            self.stop()

    def __repr__(self) -> str:
        child_class = self.__class__.__name__
        parent_class = self.__class__.__bases__[0].__name__
        return f"{parent_class}(child={child_class}, name='{self.name}' alive={self.is_alive()}, uuid='{self.uuid}')"


# Example usage:
if __name__ == "__main__":

    class ExampleWorker(WorkerProcess):
        def __init__(self):
            super().__init__("Example Worker")

        def startup(self) -> None:
            self.logger.info("This code is run in the child process before the main loop")

        def run(self) -> None:
            self.logger.info("This code is run in a loop from the child process")

        def shutdown(self) -> None:
            self.logger.info("When a shutdown is requested, this code is run in the child process")

        def on_config_update(self, config) -> None:
            self.logger.info("When the config is updated, this code is run in the child process")

    example_worker = ExampleWorker()
    example_worker.start()
    time.sleep(5)
    example_worker.stop()
