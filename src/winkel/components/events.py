import typing as t
from plum import Signature
from winkel.items import ItemCollection, ItemsContainer


class Subscribers(ItemsContainer):
    store: ItemCollection

    def __init__(self, store: t.Optional[ItemCollection] = None):
        if store is None:
            store = ItemCollection()
        self.store = store

    def create(self,
               value: t.Any,
               discriminant: t.Iterable[t.Type],
               **kwargs):
        signature = Signature(*discriminant)
        return self.store.create(value, signature, **kwargs)

    def register(self, discriminant: t.Iterable[t.Type], **kwargs):
        def register_event_handler(func):
            self.create(func, discriminant, **kwargs)
            return func
        return register_event_handler

    def match_all(self, *args):
        found = []
        def sorting_key(handler):
            return handler.identifier, handler.metadata.get('order', 1000)

        found = [item for item in self.store
                 if item.identifier.match(args)]
        found.sort(key=sorting_key)
        return found

    def notify(self, *args, **kwargs):
        for handler in self.match_all(*args):
            handler(*args, **kwargs)
