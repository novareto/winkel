import abc
import typing as t
from winkel.contents import Model
from winkel.pipeline import MiddlewareFactory


class CRUD(abc.ABC):

    model: t.Type[Model]

    @abc.abstractmethod
    def fetch(self, id: t.Any) -> t.Optional[Model]:
        pass

    @abc.abstractmethod
    def find(self, **criterions) -> t.Iterable[Model]:
        pass

    @abc.abstractmethod
    def find_one(self, **criterions) -> t.Optional[Model]:
        pass

    @abc.abstractmethod
    def create(self, data: t.Dict) -> Model:
        pass

    @abc.abstractmethod
    def update(self, inst: Model, data: t.Dict) -> t.NoReturn:
        pass

    @abc.abstractmethod
    def add(self, item: Model) -> t.NoReturn:
        pass

    @abc.abstractmethod
    def delete(self, item: Model) -> t.NoReturn:
        pass


class Database(MiddlewareFactory):
    engine: t.Any
    mappers: t.Any

    @abc.abstractmethod
    def add_mapper(self, model: Model, **kwargs):
        pass

    @abc.abstractmethod
    def binder(self, model: Model,
               session: t.Optional[t.Any] = None) -> CRUD:
        pass

    @abc.abstractmethod
    def instanciate(self, **kwargs) -> t.NoReturn:
        pass
