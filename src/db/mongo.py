from typing import Any

from pymongo import MongoClient


class Mongo:
    def __init__(self, uri: str, db_name: str = "ecomm"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def conversations(self):
        return self.db["conversations"]

    def logs(self):
        return self.db["retrieval_logs"]


