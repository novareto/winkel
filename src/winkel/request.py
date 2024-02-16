import abc
import typing as t
import urllib.parse
import horseman.parsers
import horseman.datastructures
import horseman.types
import wrapt
from functools import cached_property
from horseman.parsers import Data
from winkel.datastructures import TypeCastingDict
from rodi import ActivationScope, Services


T = t.TypeVar("T")


class Query(TypeCastingDict):

    @classmethod
    def from_value(cls, value: str):
        return cls(urllib.parse.parse_qsl(
            value, keep_blank_values=True, strict_parsing=True))

    @classmethod
    def from_environ(cls, environ: dict):
        qs = environ.get('QUERY_STRING', '')
        if qs:
            return cls.from_value(qs)
        return cls()


class User(abc.ABC):
    id: t.Union[str, int]


class Environ(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.method = self.get('REQUEST_METHOD', 'GET').upper()
        self.script_name = urllib.parse.quote(
            self.get('SCRIPT_NAME', '')
        )

    @cached_property
    def path(self) -> str:
        if path := self.get('PATH_INFO'):
            return path.encode('latin-1').decode('utf-8')
        return '/'

    @cached_property
    def query(self) -> Query:
        return Query.from_environ(self)

    @cached_property
    def cookies(self) -> horseman.datastructures.Cookies:
        return horseman.datastructures.Cookies.from_environ(self)

    @cached_property
    def content_type(self) -> horseman.datastructures.ContentType | None:
        if 'CONTENT_TYPE' in self:
            return horseman.datastructures.ContentType.from_http_header(
                self['CONTENT_TYPE']
            )

    @cached_property
    def application_uri(self):
        scheme = self.get('wsgi.url_scheme', 'http')
        http_host = self.get('HTTP_HOST')
        if not http_host:
            server = self['SERVER_NAME']
            port = self.get('SERVER_PORT', '80')
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
        path_info = urllib.parse.quote(self.get('PATH_INFO', ''))
        if include_query:
            qs = urllib.parse.quote(self.get('QUERY_STRING', ''))
            if qs:
                return f"{url}{path_info}?{qs}"
        return f"{url}{path_info}"

    def extract(self) -> horseman.parsers.Data:
        if '__EXTRACTED__' in self:
            return self['__EXTRACTED__']
        if self.content_type:
            data = horseman.parsers.parser(
                self['wsgi.input'], self.content_type)
        else:
            data = Data()
        self['__EXTRACTED__'] = data
        return data


class Request(ActivationScope):

    def __init__(self,
                 environ: horseman.types.Environ,
                 provider: Services | None = None,
                 scoped_services: t.Dict[t.Type[T] | str, T] | None = None):
        self.environ = Environ(environ)
        self.provider = provider or Services()
        if scoped_services is None:
            scoped_services = {}
        scoped_services[Request] = self
        scoped_services[Environ] = self.environ
        self.scoped_services = scoped_services


__all__ = ['Request', 'Query']
