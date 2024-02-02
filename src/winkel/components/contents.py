import typing as t
from winkel.items import ItemMapping
from winkel.contents import Model


class Contents(ItemMapping[str, t.Type[Model]]):

    def create(self, value: t.Type[Model], *args, **kwargs):
        schema = value.json_schema()
        return super().create(value, *args, schema=schema, **kwargs)
