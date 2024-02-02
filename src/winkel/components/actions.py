import typing as t
from enum import Enum
from plum import Signature
from winkel.items import ItemResolver, ItemsContainer


class Lookup(Enum):
    ALL = 'all'


class Actions(ItemsContainer):
    store: ItemResolver

    def __init__(self, store: t.Optional[ItemResolver] = None):
        if store is None:
            store = ItemResolver()
        self.store = store

    def create(self,
               value: t.Any,
               discriminant: t.Iterable[t.Type],
               name="",
               **kwargs):
        signature = Signature(
            *discriminant,
            t.Literal[name] | t.Literal[Lookup.ALL]
        )
        return self.store.create(value, signature, name=name, **kwargs)

    def get(self, *args, name=""):
        return self.store.lookup(*args, name)

    def match_all(self, *args):
        actions = {}
        for action in self.store.match_all(*args, Lookup.ALL):
            if action.name not in actions:
                actions[action.name] = action
        return actions

    def register(self, discriminant: t.Iterable[t.Type], name: str="", **kwargs):
        def register_event_handler(func):
            self.create(func, discriminant, name=name, **kwargs)
            return func
        return register_event_handler

    def __or__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Unsupported merge between {self.__class__!r} "
                f"and {other.__class__!r}"
            )
        return self.__class__(self.store | other.store)
