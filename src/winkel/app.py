import logging
from collections import defaultdict
from functools import partial
from dataclasses import dataclass, field
from rodi import Container
from horseman.exceptions import HTTPError
from horseman.mapping import Mapping, Node, RootNode
from winkel.scope import Scope
from winkel.response import Response
from winkel.service import Installable, Mountable
from winkel.datastructures import PriorityChain
from winkel.meta import Environ, ExceptionInfo
from winkel import scoped


logger = logging.getLogger(__name__)


class Mounting(Mapping):

    def add(self, app: Node, path: str):
        self[path] = app


@dataclass(kw_only=True)
class Eventful:
    events: dict = field(default_factory=partial(defaultdict, PriorityChain))

    def register_handler(self, name: str, order: int = 0):
        def handler_registration(handler):
            self.events[name].add(handler, order)
        return handler_registration

    def trigger(self, name: str, *args, **kwargs):
        if name in self.events:
            for order, handler in self.events[name]:
                response = handler(*args, **kwargs)
                if response is not None:
                    logger.debug(f'{name}: handler {handler!r} responded. Breaking early.')
                    return response

    def notify(self, name: str, *args, **kwargs):
        if name in self.events:
            for order, hook in self.events[name]:
                hook(self, *args, **kwargs)


@dataclass(kw_only=True)
class Root(RootNode, Eventful):

    name: str = ''
    services: Container = field(default_factory=Container)
    mounts: Mounting = field(default_factory=Mounting)

    def __post_init__(self):
        self.services.add_instance(self, self.__class__)
        self.services.add_scoped_by_factory(scoped.query)
        self.services.add_scoped_by_factory(scoped.cookies)
        self.services.add_scoped_by_factory(scoped.form_data)

    def finalize(self):
        # everything that needs doing before serving requests.
        self.services.build_provider()

    def use(self, *components: Installable | Mountable):
        for component in components:
            if isinstance(component, Installable):
                component.install(self.services)
            if isinstance(component, Mountable):
                component.mount(self.mounts)

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
            except HTTPError:
                pass
            else:
                return mounted.resolve(environ['PATH_INFO'], environ)

        scope = Scope(environ, provider=self.services.provider)
        with scope:
            with scope.stack:
                try:
                    response = self.trigger('scope.init', scope)
                    if response is None:
                        response = self.endpoint(scope)
                except HTTPError as err:
                    response = Response(err.status, err.body)

                scope.register(Response, response)
                self.notify('scope.response', scope, response)
                return response
