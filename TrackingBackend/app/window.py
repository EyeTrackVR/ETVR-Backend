import cv2


# simple wrapper around cv2.imshow so we can disable it easily
# TODO: implement this directly in the processes base class
class Window:
    def __init__(self, debug: bool):
        self._debug: bool = debug
        self.__active: bool = False

    def imshow(self, name, frame) -> None:
        if self._debug:
            self.__active = True
            cv2.imshow(name, frame)

    def _waitkey(self, delay: int) -> None:
        if self._debug:
            cv2.waitKey(delay)
        else:
            if self.__active:
                cv2.destroyAllWindows()
                self.__active = False
