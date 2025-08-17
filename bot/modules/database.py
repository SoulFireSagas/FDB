from pymongo import MongoClient
from bot.config import MongoDB

class Database:
    def __init__(self):
        self.client = MongoClient(MongoDB.URI)
        self.db = self.client[MongoDB.DB_NAME]
        self.files_collection = self.db['FILES_COLLECTION']
        self.bulk_collection = self.db['BULK_COLLECTION']

    def save_file(self, message_id, secret_code):
        self.files_collection.insert_one({
            "message_id": message_id,
            "secret_code": secret_code
        })

    def get_file(self, message_id):
        return self.files_collection.find_one({
            "message_id": message_id
        })

    def save_bulk(self, bulk_data):
        result = self.bulk_collection.insert_one(bulk_data)
        return str(result.inserted_id)

    def get_bulk(self, bulk_id):
        from bson.objectid import ObjectId
        return self.bulk_collection.find_one({"_id": ObjectId(bulk_id)})

# Initialize the database connection
db = Database()
