import wrapt
import functools
from horseman.response import Response
from chameleon.zpt.template import PageTemplate
from winkel.ui import UI


def template(template: PageTemplate | str):

    @wrapt.decorator
    def templated(wrapped, instance, args, kwargs) -> str:
        content = wrapped(*args, **kwargs)
        if isinstance(content, (Response, str)):
            return content

        if not isinstance(content, dict):
            raise TypeError(f'Do not know how to render {content!r}.')

        request = args[0]
        ui = request.get(UI)

        namespace = {
            'request': request,
            'ui': ui,
            'macros': ui.macros
        }

        if instance:
            namespace |= instance.namespace(request) | content
        else:
            namespace |= content

        if isinstance(template, str):
            tpl = ui.templates[template]
        else:
            tpl = template

        return tpl.render(**namespace)

    return templated


def ui_endpoint(wrapped=None, *, layout_name: str = ""):

    @wrapt.decorator
    def response_wrapped(wrapped, instance, args, kwargs) -> Response:
        content = wrapped(*args, **kwargs)
        if isinstance(content, Response):
            return content

        if not isinstance(content, str):
            raise TypeError('Do not know how to render.')

        request = args[0]
        ui = request.get(UI)
        ui.inject_resources()

        return Response(
            200,
            body=content,
            headers={"Content-Type": "text/html; charset=utf-8"}
        )

    @wrapt.decorator
    def ui_wrapped(wrapped, instance, args, kwargs) -> Response:
        content = wrapped(*args, **kwargs)
        if isinstance(content, Response):
            return content

        if not isinstance(content, str):
            raise TypeError('Do not know how to render.')

        request = args[0]
        ui = request.get(UI)
        ui.inject_resources()

        namespace = {
            'request': request,
            'ui': ui,
            'macros': ui.macros
        }

        if instance:
            namespace |= instance.namespace(request)

        layout = ui.layouts.lookup(request, name=layout_name).value
        content = layout.render(content=content, **namespace)

        return Response(
            200,
            body=content,
            headers={"Content-Type": "text/html; charset=utf-8"}
        )

    if wrapped is None:
        return functools.partial(ui_endpoint, layout_name=layout_name)

    if layout_name is None:
        return response_wrapped(wrapped)

    return ui_wrapped(wrapped)
