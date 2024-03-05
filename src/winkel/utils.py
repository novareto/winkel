from functools import wraps
from winkel.scope import Scope


def ondemand(func):
    @wraps(func)
    def dispatch(scope: Scope, *args, **kwargs):
        return scope.exec(func)
    return dispatch
