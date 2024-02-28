import inspect
from typing import Type, ClassVar, Iterable
from pydantic import BaseModel, ConfigDict, computed_field
from types import MethodType
from collections import defaultdict


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


class Installable:
    __dependencies__: ClassVar[Iterable[Type | str] | None] = None
    __provides__: ClassVar[Iterable[Type] | None] = None

    def install(self, services):
        if self.__dependencies__:
            for depend in self.__dependencies__:
                if depend not in services.provider:
                    raise LookupError(
                        f'Missing dependency service: {depend}')

        groups = get_marked_groups(self)
        factories.apply(services, groups)


class Configuration(BaseModel):

    model_config = ConfigDict(
        frozen=True,
        extra='allow',
        arbitrary_types_allowed=True
    )


class Service(Installable, Configuration):
    pass
