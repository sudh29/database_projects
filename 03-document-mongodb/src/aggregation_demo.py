"""
MongoDB Aggregation Pipeline Showcase
Demonstrates multi-stage data processing pipelines: $match, $unwind, $group, $sort, $project.
Includes native Python simulation for running without a live database.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def run_aggregation_pipeline_simulation(docs: List[Dict[str, Any]]):
    print("=== MongoDB Aggregation Pipeline Showcase ===\n")

    # Pipeline 1: Category Statistics (Average Price & Total Inventory Value)
    # MongoDB equivalent:
    # db.products.aggregate([
    #   { $match: { inStock: true } },
    #   { $group: {
    #       _id: "$category",
    #       productCount: { $sum: 1 },
    #       avgPrice: { $avg: "$price" },
    #       totalInventoryValue: { $sum: { $multiply: ["$price", "$inventory"] } }
    #   }},
    #   { $sort: { totalInventoryValue: -1 } }
    # ])
    print("--- Pipeline 1: Financial & Inventory Summary by Category ---")
    category_stats = {}
    for d in docs:
        if not d.get("inStock"):
            continue
        cat = d["category"]
        if cat not in category_stats:
            category_stats[cat] = {"count": 0, "prices": [], "inventoryValue": 0.0}
        category_stats[cat]["count"] += 1
        category_stats[cat]["prices"].append(d["price"])
        category_stats[cat]["inventoryValue"] += d["price"] * d.get("inventory", 0)

    for cat, stat in sorted(category_stats.items(), key=lambda x: x[1]["inventoryValue"], reverse=True):
        avg_p = sum(stat["prices"]) / len(stat["prices"])
        print(f"Category: {cat:12} | Items: {stat['count']} | Avg Price: ${avg_p:8.2f} | Total Value: ${stat['inventoryValue']:10.2f}")

    print()

    # Pipeline 2: Unwinding Tags ($unwind) to count tag popularity
    # MongoDB equivalent:
    # db.products.aggregate([
    #   { $unwind: "$tags" },
    #   { $group: { _id: "$tags", count: { $sum: 1 } } },
    #   { $sort: { count: -1 } }
    # ])
    print("--- Pipeline 2: Tag Popularity Matrix ($unwind + $group) ---")
    tag_counts = {}
    for d in docs:
        for tag in d.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:8]:
        print(f"Tag: #{tag:15} | Tagged Products: {count}")

    print("\n=== Aggregation demo completed. ===")


if __name__ == "__main__":
    seed_path = Path(__file__).parent.parent / "seed" / "products.json"
    with open(seed_path, "r", encoding="utf-8") as f:
        products = json.load(f)
    run_aggregation_pipeline_simulation(products)
