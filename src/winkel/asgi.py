from typing import Awaitable, Callable
from winkel.scope import Scope
import typing as t
import urllib.parse
from collections.abc import Mapping
from functools import cached_property
from horseman.asgi.parsers import Data, parser
from horseman.datastructures import Cookies, ContentType, Query
from multidict import CIMultiDict
from dataclasses import dataclass, field
from rodi import Container
from horseman.types import HTTPCode

from http import HTTPStatus
from horseman.wsgi.response import Headers, Finisher, HeadersT, BodyT
from winkel.steam import Stream


class Response:

    __slots__ = ('status', 'body', 'headers', '_finishers')

    status: HTTPStatus
    body: t.Optional[BodyT]
    headers: Headers
    _finishers: t.Optional[t.Deque[Finisher]]

    def __init__(self,
                 status: HTTPCode = 200,
                 body: BodyT = None,
                 headers: t.Optional[HeadersT] = None):
        self.status = HTTPStatus(status)
        self.body = body
        self.headers = Headers(headers or ())  # idempotent.
        self._finishers = None

    @property
    def cookies(self):
        return self.headers.cookies

    async def close(self):
        """Exhaust the list of finishers. No error is handled here.
        An exception will cause the closing operation to fail during
        the finishers iteration.
        """
        if self._finishers:
            while self._finishers:
                finisher = self._finishers.popleft()
                await finisher(self)

    def add_finisher(self, task: Finisher):
        if self._finishers is None:
            self._finishers = t.Deque()
        self._finishers.append(task)

    async def __call__(self, send, receive):
        headers = list(self.headers.coalesced_items())
        await send({
            'type': 'http.response.start',
            'status': self.status.value,
            'headers': headers
        })
        await send({
            'type': 'http.response.body',
            'body': self.body
        })



class immutable_cached_property(cached_property):

    def __set__(self, instance, value):
        raise AttributeError("can't set attribute")

    def __delete__(self, instance):
        del instance.__dict__[self.attrname]


class ASGIEnvironWrapper:

    def __init__(self, environ, stream: Stream):
        if isinstance(environ, ASGIEnvironWrapper):
            raise TypeError(
                f'{self.__class__!r} cannot wrap a subclass of itself.')
        self._environ = environ
        self._headers = CIMultiDict(
            ((k.decode(), v) for k, v in environ['headers'])
        )
        self.stream = stream

    def __setitem__(self, key: str, value: t.Any):
        raise NotImplementedError(f'{self!r} is immutable')

    def __delitem__(self, key: str):
        raise NotImplementedError(f'{self!r} is immutable')

    def __getitem__(self, key: str) -> t.Any:
        return self._environ[key]

    def __iter__(self) -> t.Iterator[str]:
        return iter(self._environ)

    def __len__(self) -> int:
        return len(self._environ)

    def __eq__(self, other: t.Any) -> bool:
        if isinstance(other, self.__class__):
            return self._environ == other._environ
        if isinstance(other, Mapping):
            return self._environ == other
        raise NotImplementedError(
            f'{other!r} cannot be compared to {self!r}')

    @immutable_cached_property
    def method(self) -> str:
        return self._environ['method'].upper()

    @immutable_cached_property
    def body(self) -> t.AsyncGenerator:
        return self.stream

    async def get_data(self) -> Data:
        if self.content_type:
            await parser.parse(self.body, self.content_type)
        return Data()

    @immutable_cached_property
    def host(self):
        host_header = self._headers['host'].decode('latin1')
        return host_header

    @immutable_cached_property
    def domain(self) -> str:
        return self.host.split(':', 1)[0]

    @immutable_cached_property
    def root_path(self) -> str:
        return urllib.parse.quote(self._environ['root_path'])

    @immutable_cached_property
    def path(self) -> str:
        return self._environ['path'] or '/'

    @immutable_cached_property
    def query(self) -> Query:
        query_string = self._environ['query_string'].decode()
        return Query.from_string(query_string)

    @immutable_cached_property
    def cookies(self) -> Cookies:
        cookie = self._headers['cookie'].decode()
        return Cookies.from_string(cookie)

    @immutable_cached_property
    def content_type(self) -> ContentType:
        content_type = self._headers[b'content-type'].decode('latin1')
        return ContentType(content_type)

    @immutable_cached_property
    def application_uri(self) -> str:
        scheme = self._environ.get('scheme', 'http')
        http_host = self.host
        if ':' in http_host:
            server, port = http_host.split(':', 1)
        else:
            server = http_host
            port = '80'
        if (scheme == 'http' and port == '80') or \
           (scheme == 'https' and port == '443'):
            return f'{scheme}://{server}{self.root_path}'
        return f'{scheme}://{server}:{port}{self.root_path}'

    def uri(self, include_query: bool = True) -> str:
        path_info = urllib.parse.quote(self.path)
        if include_query:
            qs = self._environ['query_string'].decode()
            if qs:
                return f"{self.application_uri}{path_info}?{qs}"
        return f"{self.application_uri}{path_info}"


from winkel.routing.router import Router, Params
from winkel import scoped
from autorouting import MatchedRoute
from horseman.exceptions import HTTPError


@dataclass(kw_only=True)
class ASGIApp:

    services: Container = field(default_factory=Container)
    router: Router = field(default_factory=Router)

    def __post_init__(self):
        self.services.add_instance(self, self.__class__)
        self.services.add_scoped_by_factory(scoped.query)
        self.services.add_scoped_by_factory(scoped.cookies)
        self.services.add_scoped_by_factory(scoped.form_data)
        self.services.add_instance(self.router, Router)

    def finalize(self):
        # everything that needs doing before serving requests.
        self.services.build_provider()
        self.router.finalize()

    async def endpoint(self, scope: Scope) -> Response:
        route: MatchedRoute | None = self.router.get(
            scope.environ.path,
            scope.environ.method
        )
        if route is None:
            raise HTTPError(404)

        scope.register(MatchedRoute, route)
        scope.register(Params, route.params)
        return await route.routed(scope)

    async def resolve(self, environ: dict):
        scope = Scope(environ, provider=self.services.provider)
        with scope:
            with scope.stack:
                return await self.endpoint(scope)

    async def __call__(self,
                       scope: dict,
                       receive: Callable[[], Awaitable[dict]],
                       send: Callable[[dict], Awaitable[None]]):

        scope_type = scope['type']
        asgi_info = scope.get('asgi', {'version': '2.0'})

        if scope_type != 'http':
            return

        first_event = await receive()
        first_event_type = first_event['type']
        if first_event_type == 'http.disconnect':
            return

        if first_event_type != 'http.request':
            raise RuntimeError('ouch.')

        environ = ASGIEnvironWrapper(scope, Stream(receive, first_event))
        response = await self.resolve(environ)
        await response(send, receive)