"""
Unit Tests for MongoDB Document Catalog
Tests polymorphic queries, nested attributes, and array tagging.
"""

from pathlib import Path
import unittest

from src.catalog_service import ProductCatalogService


class TestProductCatalogService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = ProductCatalogService()
        seed_path = Path(__file__).parent.parent / "seed" / "products.json"
        cls.service.seed_from_file(str(seed_path))

    def test_find_by_category(self):
        electronics = self.service.find_by_category("Electronics")
        self.assertEqual(len(electronics), 2)
        names = [p["name"] for p in electronics]
        self.assertIn("UltraBook Pro 16", names)

    def test_find_by_tag_multikey(self):
        results = self.service.find_by_tag("travel")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Wireless Noise-Cancelling Headphones")

    def test_find_by_nested_attribute(self):
        results = self.service.find_by_nested_attribute("isbn", "978-1449373320")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["category"], "Books")


if __name__ == "__main__":
    unittest.main()
