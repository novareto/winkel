from winkel.plugins import Installable, install_method
from winkel.routing import Router


class Routable(Installable):
    router: Router

    @install_method(object)
    def route(self, application):
        application.router |= self.router
