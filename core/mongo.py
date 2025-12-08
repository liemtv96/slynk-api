from functools import lru_cache

from pymongo import MongoClient

from .config import settings


@lru_cache
def get_mongo_client() -> MongoClient:
    return MongoClient(settings.MONGO_URI)


def get_mongo_db():
    client = get_mongo_client()
    return client[settings.MONGO_DB]
