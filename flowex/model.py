import peewee
from playhouse.sqlite_ext import JSONField

DATABASE = "flow.db"
db = peewee.SqliteDatabase(DATABASE)


class ServerTypeModel(peewee.Model):
    name = peewee.CharField(primary_key=True)
    type = peewee.CharField()

    class Meta:
        database = db


class EventModel(peewee.Model):
    date = peewee.IntegerField(primary_key=True)
    source = peewee.CharField()
    destination = peewee.CharField()
    values = JSONField()

    class Meta:
        database = db


class AlertReasonModel(peewee.Model):
    """we would keep all previous reasons for the host to have alert on"""

    host = peewee.CharField()
    reason = peewee.CharField()

    class Meta:
        primary_key = peewee.CompositeKey("host", "reason")
        database = db


def init():
    db.connect()
    db.create_tables([ServerTypeModel, EventModel, AlertReasonModel])
