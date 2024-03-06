import fnmatch
from functools import wraps
from winkel.scope import Scope


class wildstr(str):

    def __eq__(self, other):
        return fnmatch.fnmatch(other, str(self))


def ondemand(func):
    @wraps(func)
    def dispatch(scope: Scope, *args, **kwargs):
        return scope.exec(func)
    return dispatch
