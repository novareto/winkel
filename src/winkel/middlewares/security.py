import typing as t
from functools import wraps, cached_property
from horseman.exceptions import HTTPError
from pathlib import PurePosixPath
from pydantic import computed_field
from winkel.auth import anonymous, User
from winkel.pipeline import Handler, Middleware
from winkel.request import Request
from winkel.response import Response


class NoAnonymous(Middleware):
    allowed_urls: t.Iterable[str]
    login_url: str | None = None

    @computed_field
    @cached_property
    def unprotected(self) -> frozenset:
        return frozenset(
            PurePosixPath(bypass) for bypass in self.allowed_urls
        )

    def __call__(self, handler: Handler) -> Handler:

        @wraps(handler)
        def wrapper(self, request: Request):
            # we skip unecessary checks if it's not protected.
            path = PurePosixPath(request.environ.path)
            for bypass in self.unprotected:
                if path.is_relative_to(bypass):
                    return handler(request)

            user = request.get(User)
            if user is anonymous:
                if self.login_url is None:
                    raise HTTPError(403)
                return Response.redirect(
                    request.script_name + self.login_url)

            return handler(request)

        return wrapper
