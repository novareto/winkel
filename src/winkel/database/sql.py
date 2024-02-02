import copy
import functools
import orjson
import sqlalchemy
import sqlalchemy.exc
import typing as t
from sqlalchemy import Table, Column
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import registry, scoped_session, sessionmaker
from winkel.contents import Model
from winkel.pipeline import MiddlewareFactory
from winkel.plugins import Plugin
from winkel.items import ItemMapping
from .meta import CRUD


class SQLMapping(t.NamedTuple):
    tablename: str
    model: t.Any
    columns: t.Iterable[Column]
    constraints: t.Iterable[t.Any] = ()
    properties: t.Optional[t.Mapping] = None


class SQLStore(ItemMapping[str, SQLMapping]):

    def bind(self, mappers):
        for name, item in self.items():
            if mapper := getattr(item.value.model, '__mapper__', None):
                if mapper.registry is not mappers:
                    raise ValueError(
                        f'Model {item.value.model} already registered '
                        'for another registry.')
            else:
                table = Table(
                    item.value.tablename,
                    mappers.metadata,
                    *copy.deepcopy(item.value.columns),
                    *copy.deepcopy(item.value.constraints),
                )
                mappers.map_imperatively(
                    item.value.model,
                    table,
                    properties=item.value.properties
                )


class SQLCRUD(CRUD):

    def __init__(self, model: Model, session: t.Any):
        self.model = model
        self.session = session

    def fetch(self, id: t.Any) -> t.Optional[Model]:
        try:
            return self.session.query(self.model).get(id)
        except (sqlalchemy.exc.NoResultFound):
            return

    def find(self, **criterions) -> t.Optional[t.Iterable[Model]]:
        query = sqlalchemy.select(self.model)\
                          .filter_by(**criterions)
        return self.session.execute(query).scalars().all()

    def find_one(self, **criterions) -> t.Optional[Model]:
        query = sqlalchemy.select(self.model)\
                          .filter_by(**criterions)
        try:
            return self.session.execute(query).scalars().one()
        except (sqlalchemy.exc.NoResultFound,
                sqlalchemy.exc.MultipleResultsFound):
            return

    def count(self, **criterions) -> int:
        query = self.session.query(self.model).filter_by(**criterions)
        return query.count()

    def create(self, data: dict) -> Model:
        item = self.model.factory(data)
        self.session.add(item)
        return item

    def update(self, item: Model, data: dict) -> t.Dict:
        for field, value in data.items():
            setattr(item, field, value)
        self.session.add(item)
        return data

    def delete(self, item: Model) -> t.NoReturn:
        self.session.delete(item)

    def add(self, item: Model) -> t.NoReturn:
        self.session.add(item)


class Database:
    engine: Engine
    mappers: registry
    session_factory: t.Callable[[], scoped_session]
    _instanciated: bool = False

    def __init__(self,
                 url: str,
                 mappings: t.Optional[SQLStore] = None,
                 engine_args: t.Optional[t.Mapping] = None,
                 mappers: t.Optional[registry] = None):

        if mappers is None:
           mappers = registry()

        if mappings is None:
            mappings = SQLStore()

        self.mappers = mappers
        self.mappings = mappings
        self.engine = create_engine(
            url,
            json_serializer=lambda value: orjson.dumps(value).decode(),
            json_deserializer=orjson.loads,
            **(engine_args is not None and engine_args or {})
        )
        self.session_factory = scoped_session(
            sessionmaker(bind=self.engine)
        )

    def instanciate(self, create: bool = True):
        if self._instanciated:
            raise RuntimeError(f'{self!r} is already instanciated.')

        self.mappings.bind(self.mappers)
        if create:
            self.mappers.metadata.create_all(self.engine)
        self._instanciated = True

    def dispose(self, drop: bool = False):
        if not self._instanciated:
            raise RuntimeError(f'{self!r} is not instanciated.')

        self.mappers.dispose()
        if drop:
            self.mappers.metadata.drop_all(self.engine)
        self._instanciated = False

    def create_utility(self, transaction_manager=None):
        if not self._instanciated:
             raise RuntimeError(f'{self!r} is not instanciated.')

        session = self.session_factory()
        #if transaction_manager is not None:
        #    register(session, transaction_manager=transaction_manager)
        return functools.partial(SQLCRUD, session=session)

    def __call__(self, handler, appconf):
        def session_wrapper(request):
            tm = request.utilities['transaction_manager']
            request.utilities['crud'] = self.create_utility(
                transaction_manager=tm
            )
            response = handler(request)
            return response
        return session_wrapper
