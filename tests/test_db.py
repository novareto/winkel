from winkel.app import Application
from winkel.pipeline import Pipeline
from winkel.database.sql import Database
from winkel.reha import sqlstore



database1 = Database(url="sqlite:///example1.db")
database2 = Database(url="sqlite:///example2.db")


app = Application(
    database=database1,
    pipeline=Pipeline(
        database1
    )
)


app.database.mappings |= sqlstore
app.database.instanciate()

try:
    database2.mappings |= sqlstore
    database2.instanciate()
except ValueError:
    print('Exception while trying to double register')


database1.dispose(drop=True)


database1 = Database(url="sqlite:///example1.db")
database2 = Database(url="sqlite:///example2.db", mappers=database1.mappers)
database1.mappings |= sqlstore
database1.instanciate()
database2.mappings |= sqlstore
database2.instanciate()


crud = database1.create_utility()
user_crud = crud(sqlstore['user'].value.model)


database1.dispose(drop=True)
database2.dispose(drop=True)
