import typing as t
from inspect import _empty
from contextlib import ExitStack
from rodi import ActivationScope, Services, Dependency, Signature
from winkel.meta import Environ, WSGIEnvironWrapper


T = t.TypeVar("T")


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
        sig = Signature.from_callable(method)
        params = {
            key: Dependency(key, value.annotation)
            for key, value in sig.parameters.items()
        }
        fns = []

        for key, param in params.items():
            if param.annotation is _empty:
                fns.append(self.get(key))
            else:
                fns.append(self.get(param.annotation))

        return method(*fns)
