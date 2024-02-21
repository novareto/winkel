import abc
import typing as t
from pydantic import BaseModel, ConfigDict
from functools import reduce
from winkel.datastructures import PriorityChain
from winkel.request import Request
from winkel.response import Response


class Configuration(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra='allow',
        arbitrary_types_allowed=True
    )


Handler = t.Callable[[Request], Response]
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
