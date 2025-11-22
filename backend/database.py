from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB database manager"""
    
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect(cls):
        """Connect to MongoDB"""
        try:
            # SSL/TLS configuration for MongoDB Atlas
            cls.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                server_api=ServerApi('1'),
                tls=True,
                tlsAllowInvalidCertificates=True  # For development - use proper certs in production
            )
            # Test connection
            await cls.client.admin.command('ping')
            logger.info("✅ Connected to MongoDB successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")
    
    @classmethod
    def get_database(cls):
        """Get the database instance"""
        if cls.client is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls.client[settings.mongodb_db_name]
    
    @classmethod
    def get_collection(cls, collection_name: str):
        """Get a collection from the database"""
        db = cls.get_database()
        return db[collection_name]

