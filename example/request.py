from winkel.service import Installable
from winkel import meta, request


class Request(Installable):
    __provides__ = [
        meta.URLTools, meta.Query, meta.Cookies, meta.FormData, meta.ContentType
    ]

    def install(self, services):
        services.add_scoped_by_factory(request.query)
        services.add_scoped_by_factory(request.cookies)
        services.add_scoped_by_factory(request.form_data)
        services.add_scoped_by_factory(request.content_type)
        services.add_scoped(meta.URLTools, request.URLUtils)
