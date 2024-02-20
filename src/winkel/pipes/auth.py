import typing as t
from pathlib import PurePosixPath
from horseman.response import Response
from winkel.request import Request
from winkel.auth import Source, Authenticator
from winkel.pipeline import Handler, MiddlewareFactory


Filter = t.Callable[[Handler, Request], t.Optional[Response]]


class Authentication(MiddlewareFactory):

    class Configuration(t.NamedTuple):
        sources: t.Iterable[Source]
        user_key: str = 'user'
        filters: t.Optional[t.Iterable[Filter]] = None

    def __post_init__(self):
        self.authenticator = Authenticator(
            self.config.user_key,
            self.config.sources
        )

    def install(self, app, order: int):
        app.services.register(Authenticator, instance=self.authenticator)
        app.services.add_scoped_by_factory(self.authenticator.identify)
        app.pipeline.add(self, order)

    def __call__(self,
                 handler: Handler,
                 globalconf: t.Optional[t.Mapping] = None):

        def authentication_middleware(request):
            if self.config.filters:
                for filter in self.config.filters:
                    if (resp := filter(handler, request)) is not None:
                        return resp

            return handler(request)

        return authentication_middleware


def security_bypass(urls: t.List[str]) -> Filter:
    unprotected = frozenset(
        PurePosixPath(bypass) for bypass in urls
    )
    def _filter(caller, request):
        path = PurePosixPath(request.path)
        for bypass in unprotected:
            if path.is_relative_to(bypass):
                return caller(request)

    return _filter


def secured(path: str) -> Filter:

    def _filter(caller, request):
        if request.user is None:
            return Response.redirect(request.script_name + path)

    return _filter
