import typing as t
import urllib.parse
import horseman.parsers
import horseman.datastructures
import horseman.types
from functools import cached_property
from horseman.parsers import Data
from rodi import ActivationScope, Services


T = t.TypeVar("T")


class Environ:
    
    _environ: horseman.types.Environ

    def get(self, name, default=None):
        return self._environ.get(name, default=default) 
    
    def __init__(self, environ: horseman.types.Environ):
        self._environ = environ
        self.method = self._environ.get('REQUEST_METHOD', 'GET').upper()
        self.script_name = urllib.parse.quote(
            self._environ.get('SCRIPT_NAME', '')
        )

    @cached_property
    def path(self) -> str:
        if path := self._environ.get('PATH_INFO'):
            return path.encode('latin-1').decode('utf-8')
        return '/'

    @cached_property
    def query(self) -> horseman.datastructures.Query:
        return horseman.datastructures.Query.from_string(
            self._environ.get('QUERY_STRING', '')
        )

    @cached_property
    def cookies(self) -> horseman.datastructures.Cookies:
        return horseman.datastructures.Cookies.from_string(
            self._environ.get('HTTP_COOKIE', '')
        )

    @cached_property
    def content_type(self) -> horseman.datastructures.ContentType | None:
        if 'CONTENT_TYPE' in self:
            return horseman.datastructures.ContentType(
                self._environ.get('CONTENT_TYPE', '')
            )

    @cached_property
    def application_uri(self):
        scheme = self._environ.get('wsgi.url_scheme', 'http')
        http_host = self._environ.get('HTTP_HOST')
        if not http_host:
            server = self._environ['SERVER_NAME']
            port = self._environ.get('SERVER_PORT', '80')
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
        path_info = urllib.parse.quote(self._environ.get('PATH_INFO', ''))
        if include_query:
            qs = urllib.parse.quote(self._environ.get('QUERY_STRING', ''))
            if qs:
                return f"{url}{path_info}?{qs}"
        return f"{url}{path_info}"

    def extract(self) -> horseman.parsers.Data:
        if self.content_type:
            data = horseman.parsers.parser.parse(
                self._environ['wsgi.input'], self.content_type)
        else:
            data = Data()
        return data

from contextlib import ExitStack

class Request(ActivationScope):

    def __init__(self,
                 environ,
                 stack: ExitStack | None = None,
                 provider: Services | None = None,
                 scoped_services: t.Dict[t.Type[T] | str, T] | None = None):
        self.environ = Environ(environ)
        self.provider = provider or Services()
        if scoped_services is None:
            scoped_services = {}
        scoped_services[Environ] = self.environ
        self.scoped_services = scoped_services
        self.stack = stack or ExitStack()

    def register(self, key: t.Type[T] | str, value: T):
        self.scoped_services[key] = value

    def __contains__(self, key):
        return key in self.scoped_services or key in self.provider



__all__ = ['Environ', 'Request']
