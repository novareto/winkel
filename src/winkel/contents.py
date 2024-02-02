import typing as t
from abc import ABC, abstractmethod
from dataclasses import MISSING
from dataclasses_jsonschema import (
    JsonSchemaMixin, unwrap_optional, is_enum, is_optional)


JSONValue = t.Union[
    str, int, float, bool, None, t.Dict[str, t.Any], t.List[t.Any]
]
JSONType = t.Union[t.Dict[str, JSONValue], t.List[JSONValue]]


class Model(ABC):

    __metadata__: dict

    @classmethod
    def json_schema(cls) -> t.Optional[JSONType]:
        return None

    @abstractmethod
    def to_dict(self, validate: bool = False) -> t.Dict:
        pass

    @classmethod
    @abstractmethod
    def factory(cls, data: dict, validate: bool = False) -> 'Model':
        """Returns a fully fledged model from a dict of attributes values.
        Values in data that do not belong to the model should be overlooked
        or put into __metadata__.
        """


class DataclassModel(JsonSchemaMixin, Model):

    __metadata__ = None

    @classmethod
    def factory(cls, data, validate: bool = True):
        return cls.from_dict(data, validate=validate)

    @classmethod
    def json_to_data(
            cls, data: dict, fill_missing: bool = True) -> t.Tuple[dict, dict]:
        args: t.Dict[str, t.Any] = {}
        attrs: t.Dict[str, t.Any] = {}

        for f in cls._get_fields():
            values = args if f.field.init else attrs
            if f.mapped_name in data or (
                    fill_missing and (
                    f.field.default == MISSING and
                    f.field.default_factory == MISSING)):  # type: ignore
                try:
                    values[f.field.name] = cls._decode_field(
                        f.field.name, f.field.type, data.get(f.mapped_name)
                    )
                except ValueError:
                    ftype = unwrap_optional(f.field.type) \
                        if is_optional(f.field.type) else f.field.type
                    if is_enum(ftype):
                        values[f.field.name] = data.get(f.mapped_name)
                    else:
                        raise
        return args, attrs


class Proxy:

    __slots__ = ('item', 'workflow')

    def __init__(self, item: Model, workflow = None):
        self.item = item
        self.workflow = workflow

    @property
    def id(self):
        raise NotImplementedError('Override.')

    @property
    def date(self):
        return self.item.creation_date.strftime('%d.%m.%Y %H:%M')

    @property
    def title(self):
        raise NotImplementedError('Override.')

    @property
    def state(self):
        if self.workflow is None:
            return self.item.state
        return self.workflow.states[self.item.state].value
