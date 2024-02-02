from pathlib import Path
from winkel.components import VersionStore
from winkel.components.utils import get_schemas


versions1 = VersionStore()
for schema in get_schemas(Path("./schemas/mub")):
    versions1.add('OZG', schema.name, schema)

versions2 = VersionStore()
for schema in get_schemas(Path("./schemas/rul")):
    versions2.add('OZG', schema.name, schema)

versions3 = VersionStore()
for schema in get_schemas(Path("./schemas/uaz")):
    versions3.add('Reha', schema.name, schema)


test = versions1 | versions2 | versions3