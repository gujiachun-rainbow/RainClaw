"""MongoDB connection for task-service."""
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

from app.core.config import settings


class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    def _connection_uri(cls) -> str:
        auth = ""
        if settings.mongodb_username and settings.mongodb_password:
            auth = f"{settings.mongodb_username}:{settings.mongodb_password}@"
        return f"mongodb://{auth}{settings.mongodb_host}:{settings.mongodb_port}"

    @classmethod
    async def connect(cls) -> None:
        if cls.client is None:
            uri = cls._connection_uri()
            logger.info(f"Task service connecting to MongoDB at {settings.mongodb_host}:{settings.mongodb_port}")
            cls.client = AsyncIOMotorClient(uri)
            cls.db = cls.client[settings.mongodb_db_name]
            await cls.client.admin.command("ping")
            await cls.init_indexes()
            logger.info("Task service MongoDB connected")

    @classmethod
    async def close(cls) -> None:
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("Task service MongoDB closed")

    @classmethod
    async def init_indexes(cls) -> None:
        if cls.db is None:
            return
        await cls.db.tasks.create_index("_id")
        await cls.db.tasks.create_index("status")
        await cls.db.tasks.create_index([("updated_at", -1)])
        await cls.db.task_runs.create_index("task_id")
        await cls.db.task_runs.create_index([("start_time", -1)])

    @classmethod
    def get_collection(cls, collection_name: str):
        if cls.db is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return cls.db[collection_name]


db = MongoDB
