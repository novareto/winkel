from winkel.service import Installable, factory
from winkel.meta import Query, Cookies, ContentType, FormData
from winkel.scope import Scope


class Request(Installable):

    __provides__ = (
        Query, Cookies, FormData, ContentType
    )

    @factory('scoped')
    def cookies(self, scope: Scope) -> Cookies:
        return scope.environ.cookies


    @factory('scoped')
    def query(self, scope: Scope) -> Query:
        return scope.environ.query


    @factory('scoped')
    def content_type(self, scope: Scope) -> ContentType:
        return scope.environ.content_type


    @factory('scoped')
    def form_data(self, scope: Scope) -> FormData:
        return scope.environ.data
