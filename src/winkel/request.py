import urllib.parse
from winkel.meta import Query, Cookies, ContentType, FormData
from winkel.scope import Scope
from winkel.components import MatchedRoute, Params


def cookies(scope: Scope) -> Cookies:
    return scope.environ.cookies


def query(scope: Scope) -> Query:
    return scope.environ.query


def content_type(scope: Scope) -> ContentType:
    return scope.environ.content_type


def form_data(scope: Scope) -> FormData:
    return scope.environ.data


def params(scope: Scope) -> Params:
    route = scope.get(MatchedRoute)
    return route.params
