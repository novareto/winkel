import wrapt
from typing import Any
from sqlmodel import Session, select
from buckaroo import Registry
from winkel.traversing import Application
from winkel.scope import Scope
from winkel.routing import Params
from models import Company, Course


trail = Registry()


class Traversed(wrapt.ObjectProxy):
    __parent__: Any
    __trail__: str
    __path__: str

    def __init__(self, wrapped, *, parent: Any, path: str):
        super().__init__(wrapped)
        self.__parent__ = parent
        self.__trail__ = path
        if type(wrapped) is Traversed:
            self.__path__ = f"{wrapped.__path__}/{path}"
        else:
            self.__path__ = '/' + path


@trail.register(Application, '/company/{company_id}')
def company_factory(
        path: str, parent: Application, scope: Scope, *,
        company_id: str) -> Company:

    sqlsession = scope.get(Session)
    params = scope.get(Params)
    params['company_id'] = company_id
    company = sqlsession.get(Company, company_id)
    return Traversed(company, parent=parent, path=path)


@trail.register(Company, '/courses/{course_id}')
def course_factory(
        path: str, parent: Company, scope: Scope, *,
        course_id: str) -> Company:

    sqlsession = scope.get(Session)
    params = scope.get(Params)
    params['course_id'] = course_id
    query = select(Course).where(
        Course.id == course_id,
        Course.company_id == parent.id
    )
    course = sqlsession.exec(query).one_or_none()
    return Traversed(course, parent=parent, path=path)
