import typing as t
from winkel.items import Items, ItemsContainer


Component = Items | ItemsContainer | t.Mapping | t.Set


class Plugin:

    components: t.Mapping[str, Component]

    def __init__(self, components):
        self.components = components

    def add_services(self, services):
        pass

    def merge_components(self, app):
        for name, component in self.components.items():
            trail = name.split('.')
            attr = trail[-1]
            node = app
            for stub in trail[:-1]:
                node = getattr(node, stub)
            setattr(node, attr, getattr(node, attr) | component)

    def apply(self, app):
        self.merge_components(app)
        self.add_services(app.services)
