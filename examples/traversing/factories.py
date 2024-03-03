import wrapt
from sqlmodel import Session as SQLSession, select
from winkel.traversing import Application
from winkel.scope import Scope
from winkel.routing import Params
from winkel.traversing import Traverser
from models import Company, Course, Session


registry = Traverser()


@wrapt.decorator
def pass_through(wrapped, instance, args, kwargs):
    print("ran through")
    return wrapped(*args, **kwargs)


@registry.register(Application, '/company/<company_id>', pipeline=(pass_through,))
def company_factory(
        path: str, parent: Application, scope: Scope, *,
        company_id: str) -> Company:

    sqlsession = scope.get(SQLSession)
    params = scope.get(Params)
    params['company_id'] = company_id
    company = sqlsession.get(Company, company_id)
    return company


@registry.register(Company, '/courses/<course_id>')
def course_factory(
        path: str, parent: Company, scope: Scope, *,
        course_id: str) -> Course:

    sqlsession = scope.get(SQLSession)
    params = scope.get(Params)
    params['course_id'] = course_id
    query = select(Course).where(
        Course.id == course_id,
        Course.company_id == parent.id
    )
    course = sqlsession.exec(query).one_or_none()
    return course


@registry.register(Course, '/sessions/<session_id>')
def session_factory(
        path: str, parent: Course, scope: Scope, *,
        session_id: str) -> Session:

    sqlsession = scope.get(SQLSession)
    params = scope.get(Params)
    params['session_id'] = session_id
    query = select(Session).where(
        Session.id == session_id,
        Session.course_id == parent.id
    )
    session = sqlsession.exec(query).one_or_none()
    return session
