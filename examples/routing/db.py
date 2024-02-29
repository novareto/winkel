from winkel.auth import Source, User
from models import Person
from winkel.scope import Scope
from functools import cached_property
from winkel.response import Response
from pydantic import computed_field
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy import select
from sqlalchemy.engine.base import Engine
from winkel.service import Service, factory
from transaction import TransactionManager
from contextlib import contextmanager


class DBSource(Source):

    def find(self, credentials: dict, scope: Scope) -> User | None:
        username = credentials.get('username')
        password = credentials.get('password')
        sqlsession = scope.get(Session)
        p = sqlsession.exec(
            select(Person).where(
                Person.email == username,
                Person.password == password
            )
        ).scalar_one_or_none()
        return p

    def fetch(self, uid, scope) -> User | None:
        sqlsession = scope.get(Session)
        return sqlsession.get(Person, uid)


class SQLDatabase(Service):

    __provides__ = [Session]

    url: str

    @computed_field
    @cached_property
    def engine(self) -> Engine:
        engine = create_engine(self.url, echo=True)
        SQLModel.metadata.create_all(engine)
        return engine

    @factory('scoped')
    def session_factory(self, scope) -> Session:
        return scope.stack.enter_context(self.sqlsession(scope))

    @contextmanager
    def sqlsession(self, scope):
        with Session(self.engine) as session:
            try:
                yield session
            except Exception:
                # maybe log.
                raise
            else:
                response = scope.get(Response)
                if response.status >= 400:
                    session.rollback()
                    return

                if TransactionManager in scope:
                    txn = scope.get(TransactionManager)
                    if txn.isDoomed():
                        session.rollback()
                        return

                session.commit()
