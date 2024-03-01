from .app import Application
from .views import ViewRegistry
from wrapt import ObjectProxy
from typing import Any

class Traversed(ObjectProxy):
    __parent__: Any
    __trail__: str
    __path__: str

    def __init__(self, wrapped, *, parent: Any, path: str):
        super().__init__(wrapped)
        self.__parent__ = parent
        self.__trail__ = path
        if type(parent) is Traversed:
            self.__path__ = f"{parent.__path__}/{path}"
        else:
            self.__path__ = '/' + path