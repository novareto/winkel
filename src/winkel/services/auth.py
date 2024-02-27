import typing as t
from functools import cached_property
from horseman.exceptions import HTTPError
from pathlib import PurePosixPath
from pydantic import computed_field
from winkel.auth import anonymous, User
from winkel.service import Service, handlers
from winkel.response import Response


class NoAnonymous(Service):
    allowed_urls: t.Set[str] = set()
    login_url: str | None = None

    @computed_field
    @cached_property
    def unprotected(self) -> frozenset:
        allowed = set((PurePosixPath(url) for url in self.allowed_urls))
        if self.login_url is not None:
            allowed.add(PurePosixPath(self.login_url))
        return frozenset(allowed)

    @handlers.before_route
    def check_access(self, app, scope) -> Response | None:
        # we skip unnecessary checks if it's not protected.
        path = PurePosixPath(scope.request.path)
        for bypass in self.unprotected:
            if path.is_relative_to(bypass):
                return None

        user = scope.get(User)
        if user is anonymous:
            if self.login_url is None:
                raise HTTPError(403)
            return Response.redirect(
                scope.request.script_name + self.login_url)
