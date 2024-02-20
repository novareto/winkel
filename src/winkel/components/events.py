import typing as t
from elementalist.registries import CollectionRegistry


class Subscribers(CollectionRegistry):

    def match(self, *args):
        found = []

        def sorting_key(handler):
            return handler.identifier, handler.metadata.get('order', 1000)

        found = [element for element in self.store
                 if element.key.match(args)]
        found.sort(key=sorting_key)
        return found

    def notify(self, *args, **kwargs):
        for handler in self.match(*args):
            if not handler.evaluate(*args, **kwargs):
                handler(*args, **kwargs)
