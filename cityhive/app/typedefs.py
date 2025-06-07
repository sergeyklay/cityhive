from aiohttp import web
from sqlalchemy.ext.asyncio import async_sessionmaker

from cityhive.infrastructure.config import Config

config_key = web.AppKey("config_key", Config)
db_key = web.AppKey("db_key", async_sessionmaker)
