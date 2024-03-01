from typing import Type, ClassVar, Iterable
from pydantic import BaseModel, ConfigDict
from func_annotator import annotation


class factory(annotation):
    name = '__scope_factory__'

    def __init__(self, factory_type: str):
        self.annotation = factory_type


class Installable:
    __dependencies__: ClassVar[Iterable[Type | str] | None] = None
    __provides__: ClassVar[Iterable[Type] | None] = None

    def install(self, services):
        if self.__dependencies__:
            for depend in self.__dependencies__:
                if depend not in services.provider:
                    raise LookupError(
                        f'Missing dependency service: {depend}')

        for name, func in factory.find(self):
            if name == 'scoped':
                services.add_scoped_by_factory(func)
            elif name == "transient":
                services.add_transient_by_factory(func)
            elif name == "singleton":
                services.add_singleton_by_factory(func)


class Configuration(BaseModel):

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True
    )


class Service(Installable, Configuration):
    pass
