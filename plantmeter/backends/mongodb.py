from plantmeter.backends import BaseBackend, register, urlparse
import pymongo
import datetime

class MongoDBBackend(BaseBackend):
    """MongoDB Backend
    """
    collection = 'generation'

    def __init__(self, uri=None):
        if uri is None:
            uri = "mongodb://localhost:27017/db"
        super(MongoDBBackend, self).__init__(uri)
        self.uri = uri
        self.config = urlparse(self.uri)
        self.connection = pymongo.MongoClient(self.uri)
        self.db = self.connection[self.config['db']]
        self.db[self.collection].ensure_index(
            'name', background=True
        )

    def get(self, name, start, end, fields=None):
        filters = {
            'name': name,
            'datetime': {'$gte': start, '$lt': end}
        }
        return [x for x in self.db[self.collection].find(filters, fields)]

    def insert(self, document):
        counter = self.db['counters'].find_and_modify(
            {'_id': self.collection},
            {'$inc': {'counter': 1}}
        )
        document.update({'create_at': datetime.datetime.now()})
        return self.db[self.collection].insert(document)

    def disconnect(self):
        self.connection.disconnect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

register("mongodb", MongoDBBackend)
