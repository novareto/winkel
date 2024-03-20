import logging
from dataclasses import dataclass, field
from rodi import Container
from horseman.exceptions import HTTPError
from horseman.mapping import Mapping, Node, RootNode
from winkel.pipeline import HandlerWrapper, wrapper
from winkel.scope import Scope
from winkel.response import Response
from winkel.service import Installable, Mountable
from winkel.meta import Environ, ExceptionInfo
from winkel import scoped


logger = logging.getLogger(__name__)


class Mounts(Mapping):

    def add(self, app: Node, path: str):
        self[path] = app


@dataclass(kw_only=True, repr=False)
class Root(RootNode):

    services: Container = field(default_factory=Container)
    middlewares: list[HandlerWrapper] = field(default_factory=list)
    mounts: Mounts = field(default_factory=Mounts)

    def __post_init__(self):
        self.services.add_instance(self, self.__class__)
        self.services.add_scoped_by_factory(scoped.query)
        self.services.add_scoped_by_factory(scoped.cookies)
        self.services.add_scoped_by_factory(scoped.form_data)

    def finalize(self):
        # everything that needs doing before serving requests.
        self.services.build_provider()
        if self.middlewares:
            self.endpoint = wrapper(self.middlewares, self.endpoint)

    def use(self, *components: Installable):
        for component in components:
            component.install(self)

    def handle_exception(self, exc_info: ExceptionInfo, environ: Environ):
        typ, err, tb = exc_info
        logging.critical(err, exc_info=True)
        return Response(500, str(err))

    def endpoint(self, scope: Scope) -> Response:
        raise NotImplementedError('Implement your own.')

    def resolve(self, path: str, environ: Environ) -> Response:
        if self.mounts:
            try:
                mounted = self.mounts.resolve(path, environ)
            except HTTPError as err:
                if err.status != 404:
                    raise err
            else:
                return mounted.resolve(environ['PATH_INFO'], environ)

        scope = Scope(environ, provider=self.services.provider)
        with scope:
            with scope.stack:
                try:
                    response = self.endpoint(scope)
                except HTTPError as err:
                    response = Response(err.status, err.body)
                scope.register(Response, response)
                return response
