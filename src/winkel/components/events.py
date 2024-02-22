import typing as t
from elementalist.registries import SignatureCollection


def sorter(handler):
    return handler.key, handler.metadata.get('order', 1000)


class Subscribers(SignatureCollection):

    def notify(self, *args, **kwargs):
        for handler in self.match(*args, sorter=sorter):
            handler.conditional_call(*args, **kwargs)
