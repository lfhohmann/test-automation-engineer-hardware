import os

from dotenv import load_dotenv
from mongoengine import BooleanField, DateTimeField, Document, ListField, StringField, connect

load_dotenv()
connect(os.environ["DB_HOST"])


class Test(Document):
    timestamp = DateTimeField(required=True)
    passed = BooleanField(required=True)
    name = StringField(required=True)
    uuid = StringField(required=True)
    states = ListField(required=True)
    times = ListField(required=True)
    log = StringField(required=True)
