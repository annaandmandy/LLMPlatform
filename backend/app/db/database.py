import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

mongo_client = None
db = None

async def connect_to_mongo():
    global mongo_client, db
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGO_DB", "llm_experiment")
    if uri:
        mongo_client = AsyncIOMotorClient(uri)
        db = mongo_client[db_name]
        return db
    return None

def get_db():
    return db
