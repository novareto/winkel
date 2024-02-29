import typing as t
import logging
from functools import cached_property
from pydantic import computed_field
from horseman.exceptions import HTTPError
from pathlib import PurePosixPath
from winkel.auth import anonymous, User
from winkel.service import Configuration
from winkel.response import Response
from winkel.scope import Scope
from winkel.cors import CORSPolicy
from horseman.response import Headers


logger = logging.getLogger(__name__)


class NoAnonymous(Configuration):
    allowed_urls: t.Set[str] = set()
    login_url: str | None = None

    @computed_field
    @cached_property
    def unprotected(self) -> frozenset:
        allowed = set((PurePosixPath(url) for url in self.allowed_urls))
        if self.login_url is not None:
            allowed.add(PurePosixPath(self.login_url))
        return frozenset(allowed)

    def check_access(self, scope: Scope) -> Response | None:
        # we skip unnecessary checks if it's not protected.
        path = PurePosixPath(scope.environ.path)
        for bypass in self.unprotected:
            if path.is_relative_to(bypass):
                return None

        user = scope.get(User)
        if user is anonymous:
            if self.login_url is None:
                raise HTTPError(403)
            return Response.redirect(
                scope.environ.script_name + self.login_url
            )


class CORS(Configuration):
    policy: CORSPolicy

    def preflight(self, scope: Scope) -> Response | None:
        if scope.environ.method == 'OPTIONS':
            # We intercept the preflight.
            # If a route was possible registered for OPTIONS,
            # this will override it.
            Logger.debug('Cors policy crafting preflight response.')
            origin = scope.environ.get(
                'ORIGIN'
            )
            acr_method = scope.environ.get(
                'ACCESS_CONTROL_REQUEST_METHOD'
            )
            acr_headers = request.environ.get(
                'ACCESS_CONTROL_REQUEST_HEADERS'
            )
            return Response(200, headers=Headers(
                self.policy.preflight(
                    origin=origin,
                    acr_method=acr_method,
                    acr_headers=acr_headers
                )
            ))
