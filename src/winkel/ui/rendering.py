import wrapt
import functools
from horseman.response import Response
from chameleon.zpt.template import PageTemplate
from winkel.ui import UI
from winkel.scope import Scope
from winkel.meta import URLTools


def renderer(wrapped=None, *,
             template: PageTemplate | str | None = None,
             layout_name: str = ""):

    @wrapt.decorator
    def rendering_wrapper(wrapped, instance, args, kwargs) -> str:
        content = wrapped(*args, **kwargs)

        if isinstance(content, Response):
            return content

        scope: Scope = args[0]
        ui = scope.get(UI)
        namespace = {
                'scope': scope,
                'ui': ui,
                'urltools': scope.get(URLTools),
                'macros': ui.macros,
                'view': instance or wrapped,
                'context': object()
            }

        if template is not None:
            if not isinstance(content, dict):
                raise TypeError(
                    'Template defined but no namespace returned.')
            if isinstance(template, str):
                tpl = ui.templates[template]
            else:
                tpl = template

            if instance and hasattr(instance, 'namespace'):
                namespace = instance.namespace(scope) | content | namespace
            else:
                namespace = content | namespace
            rendered = tpl.render(**namespace)

        elif isinstance(content, str):
            rendered = content
        elif not isinstance(content, str):
            raise TypeError(
                f'Unable to render type: {type(content)}.')

        if layout_name is not None:
            view = namespace['view']
            context = namespace['context']
            layout = ui.layouts.lookup(
                scope, view, context, name=layout_name
            )
            return layout.secure_call(
                scope, view, context,
                name=layout_name, content=rendered, namespace=namespace
            )

        return rendered

    if wrapped is None:
        return functools.partial(
            renderer, template=template, layout_name=layout_name
        )

    return rendering_wrapper(wrapped)


@wrapt.decorator
def html_endpoint(wrapped, instance, args, kwargs) -> Response:
    content = wrapped(*args, **kwargs)
    if isinstance(content, Response):
        return content
    if not isinstance(content, str):
        raise TypeError(
            f'Unable to render type: {type(content)}.')

    scope = args[0]
    ui = scope.get(UI)
    ui.inject_resources()

    return Response(
        200,
        body=content,
        headers={"Content-Type": "text/html; charset=utf-8"}
    )


@wrapt.decorator
def json_endpoint(wrapped, instance, args, kwargs) -> Response:
    content = wrapped(*args, **kwargs)
    if isinstance(content, Response):
        return content
    if not isinstance(content, (dict, list)):
        raise TypeError(f'Unable to render type: {type(content)}.')
    return Response.to_json(
        200,
        body=content,
        headers={"Content-Type": "application/json"}
    )
