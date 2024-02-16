import typing as t
from enum import Enum
from plum import Signature
from chameleon.zpt import template
from winkel.items import ItemResolver, ItemsContainer
from winkel.templates import Templates


DEFAULT = ""
Default = t.Literal[DEFAULT]


class Lookup(Enum):
    ALL = 'all'


class Components(ItemsContainer):
    store: ItemResolver

    def __init__(self, store: t.Optional[ItemResolver] = None):
        if store is None:
            store = ItemResolver()
        self.store = store

    def create(self,
               value: t.Any,
               discriminant: t.Iterable[t.Type],
               name: str = DEFAULT,
               **kwargs):
        signature = Signature(
            *discriminant,
            t.Literal[name] | t.Literal[Lookup.ALL]
        )
        return self.store.create(value, signature, name=name, **kwargs)

    def get(self, *args, name: str = DEFAULT):
        return self.store.lookup(*args, name)

    def match_all(self, *args):
        actions = {}
        for action in self.store.match_all(*args, Lookup.ALL):
            if action.name not in actions:
                actions[action.name] = action
        return actions

    def register(self,
                 discriminant: t.Iterable[t.Type],
                 name: str = DEFAULT,
                 **kwargs):
        def register_event_handler(func):
            self.create(func, discriminant, name=name, **kwargs)
            return func
        return register_event_handler


class NamedComponents(ItemsContainer):

    store: ItemResolver

    def __init__(self, store: t.Optional[ItemResolver] = None):
        if store is None:
            store = ItemResolver()
        self.store = store

    def create(self,
               value: t.Any,
               discriminant: t.Iterable[t.Type],
               name: str = DEFAULT,
               **kwargs):
        signature = Signature(t.Literal[name], *discriminant)
        return self.store.create(value, signature, name=name, **kwargs)

    def get(self, *args, name: str = DEFAULT):
        return self.store.lookup(name, *args)

    def register(self,
                 name: str,
                 discriminant: t.Iterable[t.Type],
                 **kws):
        def register_component(func):
            self.create(func, discriminant, name=name, **kws)
            return func
        return register_component
