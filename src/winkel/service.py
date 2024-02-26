import inspect
from typing import Type, ClassVar, Iterable
from pydantic import BaseModel, ConfigDict
from types import MethodType
from collections import defaultdict


class Configuration(BaseModel):

    model_config = ConfigDict(
        frozen=True,
        extra='allow',
        arbitrary_types_allowed=True
    )


def marker(name: str):
    def method_tagger(method: MethodType):
        method.__marker__ = name
        return method
    return method_tagger


def get_marked_groups(instance):
    groups = defaultdict(list)
    for name in dir(instance):
        attr = getattr(instance, name, None)
        if attr and inspect.ismethod(attr) and hasattr(attr, '__marker__'):
            groups[attr.__marker__].append(attr)
    return groups


class handlers:
    on_request = marker('request')
    on_response = marker('response')
    on_error = marker('error')

    @staticmethod
    def apply(hooks, groups):
        for name in ('request', 'response', 'error'):
            if factories := groups.get(name):
                for factory in factories:
                    hooks[name].add(factory)


class factories:
    scoped = marker('scoped')
    transient = marker('transient')
    singleton = marker('singleton')

    @staticmethod
    def apply(services, groups):
        if factories := groups.get('scoped'):
            for factory in factories:
                services.add_scoped_by_factory(factory)
        if factories := groups.get('transient'):
            for factory in factories:
                services.add_transient_by_factory(factory)
        if factories := groups.get('singleton'):
            for factory in factories:
                services.add_singleton_by_factory(factory)


class Service(Configuration):

    __dependencies__: ClassVar[Iterable[Type] | None] = None
    __provides__: ClassVar[Iterable[Type] | None] = None

    def install(self, services, hooks):
        if self.__dependencies__:
            for depend in self.__dependencies__:
                if depend not in services.provider:
                    raise LookupError(
                        f'Missing dependency service: {depend}')

        groups = get_marked_groups(self)
        handlers.apply(hooks, groups)
        factories.apply(services, groups)
