import typing as t
from contextlib import ExitStack
from rodi import ActivationScope, Services
from winkel.meta import Environ, WSGIEnvironWrapper


T = t.TypeVar("T")


class Scope(ActivationScope):
    environ: Environ

    def __init__(self,
                 environ: Environ,
                 stack: ExitStack | None = None,
                 provider: Services | None = None,
                 scoped_services: t.Dict[t.Type[T] | str, T] | None = None):
        self.environ = WSGIEnvironWrapper(environ)
        self.provider = provider or Services()
        if scoped_services is None:
            scoped_services = {}
        scoped_services[WSGIEnvironWrapper] = self.environ
        self.scoped_services = scoped_services
        self.stack = stack or ExitStack()

    def register(self, key: t.Type[T] | str, value: T):
        self.scoped_services[key] = value

    def __contains__(self, key):
        return key in self.scoped_services
