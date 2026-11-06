import os
import motor.motor_asyncio

def get_db():
    """Connect to MongoDB using the MONGO_URI environment variable."""
    uri = os.getenv("MONGO_URI")
    if not uri:
        raise ValueError("MONGO_URI environment variable is not set")
    
    # Create the motor client
    client = motor.motor_asyncio.AsyncIOMotorClient(uri)
    
    # Extract DB name from URI or default to 'prescription_ocr'
    db_name = "prescription_ocr"
    try:
        # Standard MongoDB connection string parser to extract db if present
        parsed_db = uri.split("/")[-1].split("?")[0]
        if parsed_db:
            db_name = parsed_db
    except Exception:
        pass
        
    return client[db_name]

def get_users_collection():
    """Retrieve the users collection."""
    return get_db()["users"]

def get_extractions_collection():
    """Retrieve the extractions collection."""
    return get_db()["extractions"]
