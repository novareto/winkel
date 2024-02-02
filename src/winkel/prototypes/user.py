import enum
import secrets
import typing as t
from dataclasses import dataclass, field
from datetime import datetime, date
from dataclasses_jsonschema import JsonSchemaMeta
from winkel.contents import DataclassModel, Proxy


class MessagingType(enum.Enum):
    email = "email"
    webpush = "webpush"


@dataclass
class Preferences(DataclassModel):

    uid: str = field(
        metadata=JsonSchemaMeta(
            title="Personen-ID aus der Fachanwendung",
            description="Beispiele: CUSA persoid, BGStandard personenId"
        )
    )

    name: str = field(
        metadata=JsonSchemaMeta(
            title="Vorname",
            description="Vorname"
        )
    )

    surname: str = field(
        metadata=JsonSchemaMeta(
            title="Name",
            description="Name"
        )
    )

    birthdate: t.Optional[date] = field(
        default=None,
        metadata=JsonSchemaMeta(
            title="Geburtsdatum"
        )
    )

    privacy: bool = field(
        default=False,
        metadata=JsonSchemaMeta(
            title="Datenschutz",
            description=(
                "Bitte best\u00e4tigen Sie hier, dass Sie "
                "die Ausf\u00fchrungen zum Datenschutzgelesen und "
                "akzeptiert haben."
            )
        )
    )

    participation: bool = field(
        default=False,
        metadata=JsonSchemaMeta(
            title="Teilnahme",
            description=(
                "Bitte best\u00e4tigen Sie uns hier die Teilnahme "
                "am Online-Verfahren."
            )
        )
    )

    mobile: str = field(
        default="",
        metadata=JsonSchemaMeta(
            title="Telefonnummer",
            description="Telefonnummer"
        )
    )

    channels: t.List[MessagingType] = field(
        default_factory=list,
        metadata=JsonSchemaMeta(
            title="Channel"
        )
    )

    webpush_subscription: t.Optional[str] = None
    annotation: t.Optional[t.Dict] = None


@dataclass
class User(DataclassModel):
    """A user object"""

    uid: str = field(
        metadata=JsonSchemaMeta(
            title="Personen-ID aus der Fachanwendung",
            description="Beispiele: CUSA persoid, BGStandard personenId"
        )
    )

    loginname: str = field(
        metadata=JsonSchemaMeta(
            title="Anmeldename für Einladungsschreiben"
        )
    )

    password: str = field(
        metadata=JsonSchemaMeta(
            title="Passwort"
        )
    )

    salt: t.Optional[str] = None

    creation_date: t.Optional[datetime] = field(
        default=None,
        metadata=JsonSchemaMeta(
            title="Erstelldatum"
        )
    )

    state: t.Optional[str] = field(
        default=None,
        metadata=JsonSchemaMeta(
            title="Status"
        )
    )

    email: t.Optional[str] = field(
        default=None,
        metadata=JsonSchemaMeta(
            title="E-Mail"
        )
    )

    organization: str = field(
        default="",
        metadata=JsonSchemaMeta(
            title="Organization",
            description="Organization"
        )
    )

    preferences: t.Optional[Preferences] = None
    annotation: t.Optional[t.Dict] = None

    @property
    def id(self):
        return self.loginname

    def __post_init__(self):
        if self.creation_date is None:
            self.creation_date = datetime.now()
        if self.salt is None:
            self.salt = secrets.token_hex(8)

    def __repr__(self):
        return f"User({self.id}, {self.email!r})"


class UserProxy(Proxy):

    @property
    def id(self):
        return self.item.loginname

    @property
    def title(self):
        return f"{self.item.id}, {self.item.email!r}"
