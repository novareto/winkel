import urllib.parse
import horseman.parsers
from functools import cached_property
from winkel.meta import URLTools, Query, Cookies, ContentType, FormData, Environ
from winkel.scope import Scope
from winkel.components import MatchedRoute, Params

def cookies(scope: Scope) -> Cookies:
    return Cookies.from_string(
        scope.environ.get('HTTP_COOKIE', '')
    )


def query(scope: Scope) -> Environ:
    return Query.from_string(
        scope.environ.get('QUERY_STRING', '')
    )


def params(scope: Scope) -> Params:
    route = scope.get(MatchedRoute)
    return route.params


def content_type(scope: Scope) -> ContentType:
    return ContentType(scope.environ.get('CONTENT_TYPE', ''))


def form_data(scope: Scope) -> FormData:
    content_type = scope.get(ContentType)
    if content_type:
        return horseman.parsers.parser.parse(
            scope.environ['wsgi.input'],
            content_type
        )
    return FormData()


class URLUtils(URLTools):

    def __init__(self, environ: Environ):
        self.environ = environ
        self.script_name = urllib.parse.quote(
            environ.get('SCRIPT_NAME', '')
        )
        self.method = environ.get('REQUEST_METHOD', 'GET').upper()
        self.domain = environ['HTTP_HOST'].split(':', 1)[0]
        if path := environ.get('PATH_INFO'):
            self.path = path.encode('latin-1').decode('utf-8')
        else:
            self.path = "/"

    @cached_property
    def application_uri(self):
        scheme = self.environ.get('wsgi.url_scheme', 'http')
        http_host = self.environ.get('HTTP_HOST')
        if not http_host:
            server = self.environ['SERVER_NAME']
            port = self.environ.get('SERVER_PORT', '80')
        elif ':' in http_host:
            server, port = http_host.split(':', 1)
        else:
            server = http_host
            port = '80'

        if (scheme == 'http' and port == '80') or \
           (scheme == 'https' and port == '443'):
            return f'{scheme}://{server}{self.script_name}'
        return f'{scheme}://{server}:{port}{self.script_name}'

    def uri(self, include_query=True):
        url = self.application_uri
        path_info = urllib.parse.quote(self.environ.get('PATH_INFO', ''))
        if include_query:
            qs = urllib.parse.quote(self.environ.get('QUERY_STRING', ''))
            if qs:
                return f"{url}{path_info}?{qs}"
        return f"{url}{path_info}"
