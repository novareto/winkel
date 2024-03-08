# this whole module will be moved to a dedicated  package
# as it has heavy dependencies, like deform/colander.

import deform
import colander
from typing import Type
from func_annotator import annotation
from horseman.exceptions import HTTPError
from winkel import html, renderer
from abc import ABC, abstractmethod
from winkel.routing import APIView
from winkel.meta import FormData
from winkel.scope import Scope


class trigger(annotation):
    name = '__form_trigger__'

    def __init__(self, name: str, title: str, order: int = 0):
        self.annotation = {
            "name": name,
            "title": title,
            "order": order
        }


class Form(APIView):

    def __init__(self):
        triggers = sorted(
            tuple(trigger.find(self)),
            key=lambda x: (x[0]['order'], x[0]['name'])
        )
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

    @abstractmethod
    def get_schema(self, scope, *, context=None) -> colander.Schema:
        pass

    def get_form(self, scope, *, context=None) -> deform.form.Form:
        schema = self.get_schema(scope, context=context).bind(
            scope=scope,
            context=context
        )
        return deform.form.Form(schema, buttons=self.buttons)

    @html
    @renderer
    def GET(self, scope, *, context=None):
        form = self.get_form(scope, context=context)
        return form.render()

    @html
    @renderer
    def POST(self, scope, *, context=None):
        data = scope.get(FormData)
        for trigger in self.triggers:
            if trigger in data.form:
                action = self.triggers[trigger]
                try:
                    return action(scope, data.form, context=context)
                except deform.exception.ValidationFailure as e:
                    return e.render()
        raise HTTPError(400)