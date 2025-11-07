import os
from datetime import datetime, UTC
from typing import List, Dict, Optional
from pymongo import MongoClient
from pymongo.collection import Collection


class MongoDBManager:
    """
    Manages storing and retrieving chat conversations in MongoDB.
    Each conversation is stored as a single document with an array of messages.
    """

    def __init__(self, connection_string: str = "mongodb://localhost:27017/", database_name: str = "chai_db"):
        """
        Initializes the MongoDBManager.
        """
        # --- TODO 1: Initialize MongoDB Connection ---
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.conversations = self.db["conversations"]

        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """
        Creates indexes on the conversations collection for efficient querying.
        """
        self.conversations.create_index([("user_id", 1), ("thread_name", 1)], unique=True)
        self.conversations.create_index("user_id")

    def get_conversation(self, user_id: str, thread_name: str) -> List[Dict]:
        """
        --- TODO 2: Retrieve a conversation from MongoDB ---
        """
        document = self.conversations.find_one({"user_id": user_id, "thread_name": thread_name})
        if not document or "messages" not in document:
            return []
        return document["messages"]

    def save_conversation(self, user_id: str, thread_name: str, messages: List[Dict]) -> None:
        """
        --- TODO 3: Save a conversation to MongoDB ---
        """
        conversation_id = f"{user_id}_{thread_name}"
        timestamp = datetime.now(UTC).isoformat()

        document = {
            "_id": conversation_id,
            "user_id": user_id,
            "thread_name": thread_name,
            "messages": messages,
            "created_at": timestamp,
            "updated_at": timestamp
        }

        self.conversations.update_one(
            {"_id": conversation_id},
            {"$set": document},
            upsert=True
        )

    def append_message(self, user_id: str, thread_name: str, message: Dict) -> None:
        """
        --- TODO 4: Append a single message to a conversation ---
        """
        conversation_id = f"{user_id}_{thread_name}"
        timestamp = datetime.now(UTC).isoformat()

        update = {
            "$push": {"messages": message},
            "$set": {"updated_at": timestamp},
            "$setOnInsert": {
                "user_id": user_id,
                "thread_name": thread_name,
                "created_at": timestamp
            }
        }

        self.conversations.update_one(
            {"_id": conversation_id},
            update,
            upsert=True
        )

    def list_user_threads(self, user_id: str) -> List[str]:
        """
        --- TODO 5: List all conversation threads for a user ---
        """
        matches = list(self.conversations.find(
            {"user_id": user_id},
            {"thread_name": True, "_id": False}
        ))
        thread_names = [record["thread_name"] for record in matches]
        return thread_names

    def delete_conversation(self, user_id: str, thread_name: str) -> bool:
        """
        Deletes a conversation.
        """
        conversation_id = f"{user_id}_{thread_name}"
        result = self.conversations.delete_one({"_id": conversation_id})
        return result.deleted_count > 0

    def close(self) -> None:
        """Closes the MongoDB connection."""
        if self.client:
            self.client.close()

    def _wipe_database(self) -> None:
        """Deletes all conversations. Only for testing."""
        self.conversations.delete_many({})


# --- Test code ---
if __name__ == "__main__":
    print("Testing MongoDBManager")

    manager = MongoDBManager(connection_string="mongodb://localhost:27017/", database_name="chai_test_db")

    print("Testing MongoDBManager._ensure_indexes()")
    indexes = list(manager.conversations.list_indexes())
    print(f"Created {len(indexes)} indexes")

    print("\nTesting MongoDBManager.save_conversation()")
    messages = [
        {"role": "user", "content": "hello world"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    manager.save_conversation("test_user", "test_thread", messages)
    print("Successfully saved conversation!")

    print("\nTesting MongoDBManager.get_conversation()")
    retrieved = manager.get_conversation("test_user", "test_thread")
    if len(retrieved) == 2:
        print("Successfully retrieved conversation!")
    else:
        print(f"Failed! Expected 2 messages, got {len(retrieved)}")

    print("\nTesting MongoDBManager.append_message()")
    manager.append_message("test_user", "test_thread", {"role": "user", "content": "another message"})
    retrieved = manager.get_conversation("test_user", "test_thread")
    if len(retrieved) == 3:
        print("Successfully appended message!")
    else:
        print(f"Failed! Expected 3 messages, got {len(retrieved)}")

    print("\nTesting MongoDBManager.list_user_threads()")
    manager.save_conversation("test_user", "thread2", [{"role": "user", "content": "test"}])
    threads = manager.list_user_threads("test_user")
    if len(threads) == 2:
        print(f"Successfully listed threads: {threads}")
    else:
        print(f"Failed! Expected 2 threads, got {len(threads)}: {threads}")

    print("\nCleaning up test data...")
    manager._wipe_database()
    manager.close()
    print("All tests passed!")
