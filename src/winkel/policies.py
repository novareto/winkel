import typing as t
from functools import cached_property
from horseman.exceptions import HTTPError
from pathlib import PurePosixPath
from winkel.auth import anonymous, User
from winkel.service import Configuration, computed_field
from winkel.response import Response
from winkel.meta import URLTools
from winkel.scope import Scope


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

    def check_access(self, app, scope: Scope) -> Response | None:
        # we skip unnecessary checks if it's not protected.
        url = scope.get(URLTools)
        path = PurePosixPath(url.path)
        for bypass in self.unprotected:
            if path.is_relative_to(bypass):
                return None

        user = scope.get(User)
        if user is anonymous:
            if self.login_url is None:
                raise HTTPError(403)
            return Response.redirect(url.script_name + self.login_url)
