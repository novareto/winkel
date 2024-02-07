import abc
import bisect
import typing as t
from functools import reduce


C = t.TypeVar('C')


class PriorityChain(t.Generic[C]):

    __slots__ = ('_chain',)

    _chain: t.List[t.Tuple[int, C]]

    def __init__(self, *components: C):
        self._chain = list(enumerate(components))

    def __iter__(self):
        return iter(self._chain)

    def add(self, component: C, order: int = 0):
        insert = (order, component)
        if not self._chain:
            self._chain = [insert]
        elif insert in self._chain:
            raise KeyError(
                'Component {component!r} already exists at #{order}.')
        else:
            bisect.insort(self._chain, insert)

    def remove(self, component: C, order: int):
        insert = (order, component)
        if insert not in self._chain:
            raise KeyError(
                'Component {component!r} doest not exist at #{order}.')
        self._chain.remove(insert)

    def clear(self):
        self._chain.clear()


Handler = t.Callable
Middleware = t.Callable[[Handler, t.Optional[t.Mapping]], Handler]


class Pipeline(PriorityChain[Middleware]):

    def wrap(self, wrapped: Handler, conf: t.Optional[t.Mapping] = None):
        if not self._chain:
            return wrapped

        return reduce(
            lambda x, y: y(x, conf),
            (m[1] for m in reversed(self._chain)),
            wrapped
        )

    def __call__(self, conf: t.Optional[t.Mapping] = None):
        def wrapper(wrapped: Handler):
            return self.wrap(wrapped, conf)
        return wrapper


class MiddlewareFactory(abc.ABC, Middleware):

    Configuration: t.ClassVar[t.Type] = None

    def __init__(self, **kwargs):
        if self.Configuration is not None:
            self.config = self.Configuration(**kwargs)
        else:
            self.config = kwargs
        self.__post_init__()

    def __post_init__(self):
        pass

    @abc.abstractmethod
    def __call__(self,
                 handler: Handler,
                 appconf: t.Optional[t.Mapping] = None) -> Handler:
        pass
