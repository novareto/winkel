from winkel.traversing import Application
from winkel.meta import Query, Cookies
from sqlmodel import Session as SQLSession, select
from winkel import Response, User, html, json, renderer
from winkel.response import Response
from winkel.traversing.traverser import ViewRegistry
from winkel.traversing.utils import url_for
from models import Folder


views = ViewRegistry()


@views.register(Application, '/', name="view")
@html
@renderer(template='views/index')
def root_index(scope, application):
    sqlsession = scope.get(SQLSession)
    query = select(Folder)
    folders = sqlsession.exec(query).all()
    return {
        'context': application,
        'folders': folders,
        'url_for': url_for(scope, application)
    }
