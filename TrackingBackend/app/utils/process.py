from multiprocessing import Process
from app.logger import get_logger, setup_logger


# This is a simple wrapper around the multiprocessing.Process class
# we are using it to abstract some of the more painful parts of multiprocessing
class WorkerProcess:
    def __init__(self, name: str):
        self.__name: str = name
        self.__process: Process = Process()
        self.logger = get_logger(self.__module__)

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

    # This method is called before the process mainloop is run
    # should be used to set up any resources that the process will need
    # Keep in mind that this method is called in within the child process
    def pre_run(self) -> None:
        pass

    def run(self) -> None:
        assert False, "This method must be overridden in the child class!"

    def _run(self) -> None:
        # since the logger isnt a shared object we need to recreate it in the child process
        # so we can have proper formatting
        setup_logger()
        self.pre_run()
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
        # We need to recreate the process because it is not possible to start a process that has already been stopped
        self.__process = Process(target=self._run, name=f"{self.__name}")
        self.__process.daemon = True
        self.__process.start()

    def stop(self) -> None:
        # can't kill a non-existent process
        if not self.is_alive():
            self.logger.debug(f"Request to kill dead process `{self.__name} was made!")
            return

        self.logger.info(f"Stopping process `{self.__name}`")
        self.__process.kill()
        self.__process.join()
