from winkel.auth import Source, User
from models import Person
from winkel.request import Scope
from winkel.response import Response
from sqlmodel import Session
from sqlmodel import SQLModel, create_engine
from sqlalchemy import select
from sqlalchemy.engine.base import Engine
from winkel.service import Service, factories
from transaction import TransactionManager
from contextlib import contextmanager


class DBSource(Source):

    def find(self, credentials: dict, scope: Scope) -> User | None:
        username = credentials.get('username')
        password = credentials.get('password')
        sqlsession = scope.get(Session)
        p = sqlsession.exec(
            select(Person).where(Person.email == username)
        ).scalar_one_or_none()
        if p is not None and p.password == password:
            return p

    def fetch(self, uid, scope) -> User | None:
        sqlsession = scope.get(Session)
        p = sqlsession.get(Person, uid)
        return p


class SQLDatabase(Service):
    url: str

    @factories.singleton
    def engine_factory(self, scope) -> Engine:
        engine = create_engine(self.url, echo=True)
        SQLModel.metadata.create_all(engine)
        return engine

    @factories.scoped
    def session_factory(self, scope) -> Session:
        return scope.stack.enter_context(self.sqlsession(scope))

    @contextmanager
    def sqlsession(self, scope):
        engine = scope.get(Engine)
        with Session(engine) as session:
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
