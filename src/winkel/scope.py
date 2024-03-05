import typing as t
from types import FunctionType
from functools import cache
from inspect import _empty
from contextlib import ExitStack
from rodi import ActivationScope, Services, Dependency, Signature
from winkel.meta import Environ, WSGIEnvironWrapper


T = t.TypeVar("T")


@cache
def method_dependencies(
        method: FunctionType | type) -> tuple[tuple[str, Dependency], ...]:
    sig = Signature.from_callable(method)
    return tuple(
        (key, Dependency(key, value.annotation))
        for key, value in sig.parameters.items()
    )


class Scope(ActivationScope):
    environ: WSGIEnvironWrapper

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
        return key in self.scoped_services or key in self.provider

    def exec(self, method):
        fns = []
        for key, param in method_dependencies(method):
            if param.annotation is _empty:
                fns.append(self.get(key))
            else:
                fns.append(self.get(param.annotation))
        return method(*fns)
