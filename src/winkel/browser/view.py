import wrapt
import typing as t
from horseman.response import Response
from chameleon.zpt import template


def ui_wrapped(layout="", template: t.Optional[template.PageTemplate | str] = None):
    @wrapt.decorator
    def ui_wrapped(wrapped, instance, args, kwargs):
        result = wrapped(*args, **kwargs)
        if isinstance(result, Response):
            return result

        request = args[0]
        ui = request.app.ui
        if instance:
            ns = instance.namespace(request)
        else:
            ns = {}

        if isinstance(result, str):
            value = ui.render(content=result, request=request, ui=ui, layout=layout, **ns)
        elif isinstance(result, dict):
            if template is None:
                raise ValueError('A namespace was returned but no template was specified.')
            if isinstance(template, str):
                tpl = ui.templates[template]
            else:
                tpl = template
            ns |= result
            value = ui.render(content=tpl, request=request, ui=ui, layout=layout, **ns)
        else:
            raise TypeError('Do not know how to render.')

        return Response(
            200,
            body=value,
            headers={"Content-Type": "text/html; charset=utf-8"}
        )

    return ui_wrapped

