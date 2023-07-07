from multiprocessing import Process
from app.logger import get_logger, setup_logger


# TODO:
# ----------------------------------------------------------------------------------------------------------------------------
# currently the only problem here is that we arent sharing all memory between processes
# when starting the a child process, it creates a local copy of all the variables in the current process including class
# members that are not explicitly synced.
# this means that when we change the config in the main process, none of the child processes are aware of the change.
# one solution to this is to use a shared memory object to store the config and have the child processes read from it,
# we dont need to worry about writing to it because the config is only changed in the main process so we might be able
# to get away with just syncing the config object's dict.
# the current hacky work around is to restart the process when the config is changed. this is not ideal but it works for now
# ----------------------------------------------------------------------------------------------------------------------------


# This is a simple wrapper around the multiprocessing.Process class
# we are using it to abstract some of the more painful parts of multiprocessing
class WorkerProcess:
    def __init__(self, name: str):
        self.__name: str = name
        self.__process: Process = Process()
        self.logger = get_logger(self.__module__)
        self.logger.debug(f"Created process `{self.__name}`")

    def __del__(self) -> None:
        if self.is_alive():
            self.stop()

    def process_name(self) -> str:
        return self.__name

    def is_alive(self) -> bool:
        if self.__process is None:
            return False
        else:
            return self.__process.is_alive()

    def run(self) -> None:
        raise AssertionError("WorkerProcess.run() must be overridden in child class!")

    def _run(self) -> None:
        # since the logger isnt a shared object so we need to recreate it in the child process
        setup_logger()
        self.run()

    def restart(self) -> None:
        self.stop()
        self.start()

    def start(self) -> None:
        # don't start a process if one already exists
        if self.is_alive():
            self.logger.debug(f"Process `{self.__name}` requested to start but is already running")
            return

        self.logger.info(f"Starting Process `{self.__name}`")
        # We need to recreate the process because it is not possible to start a process that has already been stopped]
        try:
            self.__process = Process(target=self._run, name=f"{self.__name}")
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
