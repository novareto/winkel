from winkel.auth import Source, User
from models import Person
from winkel.request import Request
from winkel.response import Response
from sqlmodel import Session
from sqlmodel import SQLModel, create_engine
from sqlalchemy import select
from sqlalchemy.engine.base import Engine
from winkel.service import Service, factories, handlers
from transaction import TransactionManager


class DBSource(Source):

    def find(self, credentials: dict, request: Request) -> User | None:
        username = credentials.get('username')
        password = credentials.get('password')
        sqlsession = request.get(Session)
        p = sqlsession.exec(
            select(Person).where(Person.email == username)
        ).scalar_one_or_none()
        if p is not None and p.password == password:
            user = User()
            user.id = p.id
            return user

    def fetch(self, uid, request) -> User | None:
        sqlsession = request.get(Session)
        p = sqlsession.get(Person, uid)
        user = User()
        user.id = p.id
        return user


class SQLDatabase(Service):
    url: str

    @factories.singleton
    def engine_factory(self, context) -> Engine:
        engine = create_engine(self.url, echo=True)
        SQLModel.metadata.create_all(engine)
        return engine

    @factories.scoped
    def session_factory(self, context) -> Session:
        engine = context.get(Engine)
        session = Session(engine)
        session.begin()
        return session

    @handlers.on_response
    def ensure_commit(self, app, request, response) -> None:
        if Session not in request:
            return

        sqlsession = request.get(Session)
        if response.status < 400:
            if TransactionManager in request:
                tm = request.get(TransactionManager)
                if not tm.isDoomed():
                    sqlsession.commit()
                else:
                    sqlsession.rollback()
            else:
                sqlsession.commit()
        else:
            sqlsession.rollback()
        sqlsession.close()

    @handlers.on_error
    def rollback(self, app, request, error) -> None:
        if Session in request:
            sqlsession = request.get(Session)
            sqlsession.rollback()
