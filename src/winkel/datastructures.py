import typing as t
import bisect


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
