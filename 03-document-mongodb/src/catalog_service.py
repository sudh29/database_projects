"""
MongoDB Document Store: Product Catalog Service
Demonstrates polymorphic schema handling, nested attribute queries, and array operations.
Includes in-memory simulation mode so scripts run even without an active MongoDB container.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pymongo
except ImportError:
    pymongo = None


class ProductCatalogService:
    def __init__(self, mongo_uri: Optional[str] = None, db_name: str = "ecommerce"):
        self.client = None
        self.collection = None
        self.is_connected = False
        self._in_memory_docs: List[Dict[str, Any]] = []

        if pymongo and mongo_uri:
            try:
                self.client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
                self.client.server_info()  # Test connection
                self.db = self.client[db_name]
                self.collection = self.db["products"]
                self._setup_indexes()
                self.is_connected = True
                print(f"[MongoDB] Connected to database: {db_name}")
            except Exception as e:
                print(f"[MongoDB] Notice: Could not connect to live MongoDB ({e}). Falling back to in-memory mode.")
                self.is_connected = False

    def _setup_indexes(self):
        """Creates compound and multikey indexes for query performance."""
        if self.collection is not None:
            # Compound index for category filtering and sorting by price
            self.collection.create_index([("category", pymongo.ASCENDING), ("price", pymongo.ASCENDING)])
            # Multikey index on array field
            self.collection.create_index([("tags", pymongo.ASCENDING)])
            # Index on nested document field
            self.collection.create_index([("attributes.author", pymongo.ASCENDING)])

    def seed_from_file(self, file_path: str):
        """Loads seed products from JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Seed file not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            docs = json.load(f)

        if self.is_connected and self.collection is not None:
            for doc in docs:
                self.collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)
            print(f"[MongoDB] Seeded {len(docs)} documents into collection 'products'.")
        else:
            self._in_memory_docs = docs
            print(f"[In-Memory] Loaded {len(docs)} documents into simulation store.")

    def find_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Queries products by category."""
        if self.is_connected and self.collection is not None:
            return list(self.collection.find({"category": category}))
        return [d for d in self._in_memory_docs if d.get("category") == category]

    def find_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Queries products matching an array tag (multikey query)."""
        if self.is_connected and self.collection is not None:
            return list(self.collection.find({"tags": tag}))
        return [d for d in self._in_memory_docs if tag in d.get("tags", [])]

    def find_by_nested_attribute(self, key: str, value: Any) -> List[Dict[str, Any]]:
        """Queries products matching nested polymorphic attributes (e.g. attributes.ramGb)."""
        if self.is_connected and self.collection is not None:
            return list(self.collection.find({f"attributes.{key}": value}))
        return [d for d in self._in_memory_docs if d.get("attributes", {}).get(key) == value]


if __name__ == "__main__":
    service = ProductCatalogService()
    seed_path = Path(__file__).parent.parent / "seed" / "products.json"
    service.seed_from_file(str(seed_path))

    print("\n--- 1. Query Category 'Electronics' ---")
    electronics = service.find_by_category("Electronics")
    for item in electronics:
        print(f"  • {item['name']} - ${item['price']} (Battery: {item['attributes'].get('batteryLifeHours')}h)")

    print("\n--- 2. Multikey Array Search: Tag 'database' ---")
    db_items = service.find_by_tag("database")
    for item in db_items:
        print(f"  • {item['name']} (Author: {item['attributes'].get('author')})")

    print("\n--- 3. Nested Polymorphic Query: RAM == 32GB ---")
    ram_32 = service.find_by_nested_attribute("ramGb", 32)
    for item in ram_32:
        print(f"  • {item['name']} with {item['attributes'].get('processor')}")
