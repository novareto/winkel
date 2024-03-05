from winkel.meta import Query, Cookies, FormData
from winkel.scope import Scope


def cookies(scope: Scope) -> Cookies:
    return scope.environ.cookies


def query(scope: Scope) -> Query:
    return scope.environ.query


def form_data(scope: Scope) -> FormData:
    return scope.environ.data
