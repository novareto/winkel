import deform
from typing import Type
from sqlmodel import SQLModel
from func_annotator import annotation
from horseman.exceptions import HTTPError
from winkel import html, renderer
from winkel.routing import APIView
from winkel.meta import FormData


class trigger(annotation):
    name = '__form_trigger__'

    def __init__(self, name: str, title: str):
        self.annotation = {
            "name": name,
            "title": title
        }


class Form(APIView):

    model: Type[SQLModel]

    def __init__(self):
        triggers = tuple(trigger.find(self))
        self.triggers = {
            (ann['name'], '__trigger__'): func for ann, func in
            triggers
        }
        self.buttons = [
            deform.form.Button(
                value='__trigger__',
                name=ann['name'],
                title=ann['title']
            ) for ann, func in triggers
        ]

    def get_schema(self, scope, context):
        return self.model.get_schema()

    def get_form(self, scope, context):
        schema = self.get_schema(scope, context).bind(
            scope=scope,
            context=context
        )
        return deform.form.Form(schema, buttons=self.buttons)

    @html
    @renderer(template='form/default')
    def GET(self, scope, context):
        form = self.get_form(scope, context)
        return {
            "context": context,
            "rendered_form": form.render()
        }

    @html
    @renderer(template='form/default')
    def POST(self, scope, context):
        data = scope.get(FormData)
        for entry in data.form:
            if action := self.triggers.get(entry):
                try:
                    return action(scope, data.form, context)
                except deform.exception.ValidationFailure as e:
                    return {
                        "context": context,
                        "rendered_form": e.render()
                    }
        raise HTTPError(400)
