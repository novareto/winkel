import fnmatch
from typing import Any
from functools import wraps
from winkel.scope import Scope


class wildstr:
    __slots__ = ('value',)

    def __init__(self, value: str):
        self.value: str = value

    def __eq__(self, other):
        return fnmatch.fnmatch(other, self.value)

    def match(self, other):
        return fnmatch.fnmatch(other, self.value)


class value:
    __slots__ = ('value',)

    def __init__(self, value: Any):
        self.value: Any = value

    def __eq__(self, other: Any):
        return self.value == other

    def match(self, other: str):
        return self.value == other


def ondemand(func):
    @wraps(func)
    def dispatch(scope: Scope, *args, **kwargs):
        return scope.exec(func)
    return dispatch
