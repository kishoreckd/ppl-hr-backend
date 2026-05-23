from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Configuration: MongoDB connection URI and database name
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "Orgchat")

# PostgreSQL connection settings (Aiven)
POSTGRES_URI = os.getenv("POSTGRES_URI", "")
POSTGRES_DB = os.getenv("POSTGRES_DB", "")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "")
POSTGRES_USER = os.getenv("POSTGRES_USER", "")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
PGSSLMODE = os.getenv("PGSSLMODE", "")

class Database:
    """
    MongoDB database client wrapper using Motor (async MongoDB driver).
    Provides methods to access collections and manage database setup.
    """

    def __init__(self):
        # Initialize the asynchronous MongoDB client
        print("Initializing MongoDB client...")
        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        print(f"Connected to MongoDB and selected database: {DB_NAME}")

    def get_collection(self, name: str):
        """
        Get a MongoDB collection by name.

        Args:
            name (str): Name of the collection.

        Returns:
            Collection object that can be used to perform operations.
        """
        print(f"Accessing collection: {name}")
        return self.db[name]

    async def list_collections(self):
        """
        Asynchronously list all collection names in the database.

        Returns:
            List of collection names.
        """
        print("Listing collections in the database...")
        collections = await self.db.list_collection_names()
        print(f"Collections in {DB_NAME}: {collections}")
        return collections

    async def ensure_collection(self, collection_name: str):
        """
        Ensure a collection exists by inserting a dummy document if it doesn't.

        Args:
            collection_name (str): Name of the collection to ensure.
        """
        if collection_name not in await self.list_collections():
            print(f"Creating collection: {collection_name}")
            await self.db[collection_name].insert_one({"_id": "dummy_id"})
            print(f"Collection {collection_name} created.")
        else:
            print(f"Collection {collection_name} already exists.")

# Dependency function to get the database object
def get_db():
    """
    Dependency injection helper to get the database instance.

    Returns:
        Database object that allows direct collection access.
    """
    database = Database()
    return database.db
