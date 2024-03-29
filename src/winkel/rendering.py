import wrapt
import functools
from typing import Sequence
from winkel.resources import Resource
from chameleon.zpt.template import PageTemplate
from winkel.resources import NeededResources
from winkel.response import Response
from winkel.scope import Scope
from winkel.services.translation import Translator, Locale
from winkel.ui import UI


def renderer(wrapped=None, *,
             template: PageTemplate | str | None = None,
             layout_name: str | None = ""):

    @wrapt.decorator
    def rendering_wrapper(wrapped, instance, args, kwargs) -> str | Response:
        content = wrapped(*args, **kwargs)

        if isinstance(content, Response):
            return content

        scope: Scope = args[0]
        ui = scope.get(UI)
        namespace = {
                'scope': scope,
                'ui': ui,
                'macros': ui.macros,
                'view': instance or wrapped,
                'context': kwargs.get('context', object()),
            }

        if template is not None:
            if not isinstance(content, dict):
                raise TypeError(
                    'Template defined but no namespace returned.')
            if isinstance(template, str):
                tpl = ui.templates[template]
            else:
                tpl = template

            namespace |= content

            translator: Translator | None = scope.get(
                Translator, default=None
            )
            locale: str | None = scope.get(
                Locale, default=None
            )
            rendered = tpl.render(
                **namespace,
                translate=translator and translator.translate or None,
                target_language=locale
            )

        elif isinstance(content, str):
            rendered = content
        else:
            raise TypeError(
                f'Unable to render type: {type(content)}.')

        if layout_name is not None:
            view = namespace['view']
            context = namespace['context']
            layout = ui.layouts.fetch(
                scope, view, context, name=layout_name
            )
            return layout(
                scope, view, context, name=layout_name, content=rendered
            )

        return rendered

    if wrapped is None:
        return functools.partial(
            renderer, template=template, layout_name=layout_name
        )

    return rendering_wrapper(wrapped)


def html(wrapped=None, *,
         resources: Sequence[Resource] | None = None):
    @wrapt.decorator
    def html_wrapper(wrapped, instance, args, kwargs) -> Response:
        content = wrapped(*args, **kwargs)

        if isinstance(content, Response):
            return content

        if not isinstance(content, str):
            raise TypeError(
                f'Unable to render type: {type(content)}.')

        scope = args[0]
        ui = scope.get(UI)
        needed_resources = scope.get(NeededResources, default=None)
        if needed_resources is None:
            print('No resource injection.')
        else:
            if ui.resources:
                needed_resources.update(ui.resources)
            if resources:
                needed_resources.update(resources)
            content = needed_resources.apply(
                content, scope.environ.application_uri
            )
        return Response.html(body=content)

    if wrapped is None:
        return functools.partial(html, resources=resources)

    return html_wrapper(wrapped)


@wrapt.decorator
def json(wrapped, instance, args, kwargs) -> Response:
    content = wrapped(*args, **kwargs)

    if isinstance(content, Response):
        return content

    if not isinstance(content, (dict, list)):
        raise TypeError(f'Unable to render type: {type(content)}.')

    return Response.to_json(body=content)
