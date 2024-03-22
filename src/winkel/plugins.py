from typing import Type, ClassVar, Iterable
from pydantic import BaseModel, ConfigDict
from func_annotator import annotation
import logging


logger = logging.getLogger(__name__)


class factory(annotation):
    name = '__scope_factory__'

    def __init__(self, factory_type: str):
        self.annotation = factory_type


class install_method(annotation):
    name = '__install_method__'

    def __init__(self, _for: type | tuple[type]):
        self.annotation = _for


class Configuration(BaseModel):

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True
    )


class Installable:

    def install(self, application):
        for restrict, func in install_method.find(self):
            if not isinstance(application, restrict):
                logger.warning(
                    f'Trying to install on {self} but method {func} '
                    f'requires an application of type {restrict}'
                )
                pass
            else:
                func(application)


class Mountable(Installable):
    path: str

    @install_method(object)
    def mount(self, application):
        application.mounts.add(self, self.path)


class ServiceManager(Installable):
    __dependencies__: ClassVar[Iterable[Type | str] | None] = None
    __provides__: ClassVar[Iterable[Type] | None] = None

    @install_method(object)
    def register_services(self, application):
        if self.__dependencies__:
            for depend in self.__dependencies__:
                if depend not in application.services.provider:
                    raise LookupError(
                        f'Missing dependency service: {depend}')

        for name, func in factory.find(self):
            if name == 'scoped':
                application.services.add_scoped_by_factory(func)
            elif name == "transient":
                application.services.add_transient_by_factory(func)
            elif name == "singleton":
                application.services.add_singleton_by_factory(func)
