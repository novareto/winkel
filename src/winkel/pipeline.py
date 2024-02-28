import abc
import typing as t
from functools import reduce
from winkel.datastructures import PriorityChain
from winkel.scope import Scope
from winkel.response import Response
from winkel.service import Configuration


Handler = t.Callable[[Scope], Response]
HandlerWrapper = t.Callable[[Handler], Handler]


class Pipeline(PriorityChain[HandlerWrapper]):

    def wrap(self, wrapped: Handler) -> Handler:
        if not self._chain:
            return wrapped

        return reduce(
            lambda x, y: y(x),
            (m[1] for m in reversed(self._chain)),
            wrapped
        )


class Middleware(abc.ABC, Configuration, HandlerWrapper):

    @abc.abstractmethod
    def __call__(self, handler: Handler) -> Handler:
        pass
