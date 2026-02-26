import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import db
from app.config import settings


SAMPLE_PRODUCTS = [
    # Cricket Bats - Kashmir Willow
    {
        "sku": "BAT-KW-001",
        "name": "Kashmir Willow Cricket Bat - Beginner",
        "category": "bat",
        "subcategory": "kashmir_willow",
        "description": "Perfect starter bat for beginners. Made from Grade A Kashmir Willow with comfortable grip.",
        "price": 2500.00,
        "original_price": 3000.00,
        "stock_quantity": 25,
        "rating": 4.2,
        "review_count": 18,
        "sales_count": 45,
        "image_url": "https://placehold.co/400x400/png?text=Kashmir+Willow+Bat",
        "specifications": {
            "bat_type": "Kashmir Willow",
            "weight": "1050g",
            "size": "Short Handle",
            "suitable_for": "Beginner"
        }
    },
    {
        "sku": "BAT-KW-002",
        "name": "Kashmir Willow Cricket Bat - Intermediate",
        "category": "bat",
        "subcategory": "kashmir_willow",
        "description": "Grade A+ Kashmir Willow bat for club cricket. Well-balanced with good sweet spot.",
        "price": 4500.00,
        "stock_quantity": 18,
        "rating": 4.5,
        "review_count": 32,
        "sales_count": 67,
        "image_url": "https://placehold.co/400x400/png?text=Kashmir+Intermediate",
        "specifications": {
            "bat_type": "Kashmir Willow Grade A+",
            "weight": "1150g",
            "size": "Short Handle",
            "suitable_for": "Intermediate"
        }
    },
    # Cricket Bats - English Willow
    {
        "sku": "BAT-EW-001",
        "name": "English Willow Cricket Bat - Grade 3",
        "category": "bat",
        "subcategory": "english_willow",
        "description": "Premium English Willow bat for serious players. Excellent ping and performance.",
        "price": 8500.00,
        "stock_quantity": 12,
        "rating": 4.7,
        "review_count": 24,
        "sales_count": 38,
        "image_url": "https://placehold.co/400x400/png?text=English+Willow+G3",
        "specifications": {
            "bat_type": "English Willow Grade 3",
            "weight": "1180g",
            "size": "Short Handle",
            "suitable_for": "Professional"
        }
    },
    {
        "sku": "BAT-EW-002",
        "name": "English Willow Cricket Bat - Grade 1",
        "category": "bat",
        "subcategory": "english_willow",
        "description": "Top-tier English Willow bat used by professionals. Maximum performance and durability.",
        "price": 15000.00,
        "stock_quantity": 5,
        "rating": 4.9,
        "review_count": 15,
        "sales_count": 22,
        "image_url": "https://placehold.co/400x400/png?text=English+Willow+G1",
        "specifications": {
            "bat_type": "English Willow Grade 1",
            "weight": "1170g",
            "size": "Short Handle",
            "suitable_for": "Professional"
        }
    },
    # Cricket Balls
    {
        "sku": "BALL-LTR-001",
        "name": "Leather Cricket Ball - Red",
        "category": "ball",
        "subcategory": "leather",
        "description": "Professional grade leather cricket ball for match play. 4-piece construction.",
        "price": 1200.00,
        "stock_quantity": 50,
        "rating": 4.4,
        "review_count": 42,
        "sales_count": 120,
        "image_url": "https://placehold.co/400x400/png?text=Red+Leather+Ball",
        "specifications": {
            "ball_type": "Leather",
            "color": "Red",
            "weight": "156g",
            "suitable_for": "Match Play"
        }
    },
    {
        "sku": "BALL-TNS-001",
        "name": "Tennis Cricket Ball - Pack of 6",
        "category": "ball",
        "subcategory": "tennis",
        "description": "Durable tennis balls for practice and casual cricket. Pack of 6.",
        "price": 600.00,
        "stock_quantity": 80,
        "rating": 4.0,
        "review_count": 28,
        "sales_count": 95,
        "image_url": "https://placehold.co/400x400/png?text=Tennis+Balls",
        "specifications": {
            "ball_type": "Tennis",
            "quantity": "6 balls",
            "suitable_for": "Practice"
        }
    },
    # Cricket Gloves
    {
        "sku": "GLV-BTG-001",
        "name": "Batting Gloves - Youth",
        "category": "gloves",
        "subcategory": "batting",
        "description": "Comfortable batting gloves for young players. Good protection and grip.",
        "price": 1500.00,
        "stock_quantity": 30,
        "rating": 4.3,
        "review_count": 22,
        "sales_count": 55,
        "image_url": "https://placehold.co/400x400/png?text=Youth+Batting+Gloves",
        "specifications": {
            "glove_type": "Batting",
            "size": "Youth",
            "material": "PU Leather"
        }
    },
    {
        "sku": "GLV-BTG-002",
        "name": "Professional Batting Gloves",
        "category": "gloves",
        "subcategory": "batting",
        "description": "Premium batting gloves with superior protection. Used by professional players.",
        "price": 3500.00,
        "stock_quantity": 20,
        "rating": 4.6,
        "review_count": 31,
        "sales_count": 42,
        "image_url": "https://placehold.co/400x400/png?text=Pro+Batting+Gloves",
        "specifications": {
            "glove_type": "Batting",
            "size": "Men",
            "material": "Premium Leather"
        }
    },
    {
        "sku": "GLV-WK-001",
        "name": "Wicket Keeping Gloves",
        "category": "gloves",
        "subcategory": "wicket_keeping",
        "description": "Professional wicket keeping gloves with excellent grip and protection.",
        "price": 4000.00,
        "stock_quantity": 15,
        "rating": 4.5,
        "review_count": 19,
        "sales_count": 28,
        "image_url": "https://placehold.co/400x400/png?text=WK+Gloves",
        "specifications": {
            "glove_type": "Wicket Keeping",
            "size": "Men",
            "material": "Premium Leather"
        }
    },
    # Cricket Pads
    {
        "sku": "PAD-LEG-001",
        "name": "Batting Pads - Youth",
        "category": "pads",
        "subcategory": "batting",
        "description": "Lightweight batting pads for young cricketers. Good protection and comfort.",
        "price": 2000.00,
        "stock_quantity": 25,
        "rating": 4.2,
        "review_count": 16,
        "sales_count": 38,
        "image_url": "https://placehold.co/400x400/png?text=Youth+Pads",
        "specifications": {
            "pad_type": "Batting",
            "size": "Youth",
            "weight": "Light"
        }
    },
    {
        "sku": "PAD-LEG-002",
        "name": "Professional Batting Pads",
        "category": "pads",
        "subcategory": "batting",
        "description": "Premium batting pads with maximum protection. Lightweight and comfortable.",
        "price": 4500.00,
        "stock_quantity": 18,
        "rating": 4.7,
        "review_count": 25,
        "sales_count": 35,
        "image_url": "https://placehold.co/400x400/png?text=Pro+Pads",
        "specifications": {
            "pad_type": "Batting",
            "size": "Men",
            "weight": "Medium"
        }
    },
    # Cricket Helmets
    {
        "sku": "HLM-001",
        "name": "Cricket Helmet - Youth",
        "category": "helmet",
        "description": "Safety-certified cricket helmet for young players. Adjustable fit with face guard.",
        "price": 2500.00,
        "stock_quantity": 20,
        "rating": 4.4,
        "review_count": 14,
        "sales_count": 30,
        "image_url": "https://placehold.co/400x400/png?text=Youth+Helmet",
        "specifications": {
            "helmet_type": "Batting",
            "size": "Youth",
            "certification": "ISI Certified"
        }
    },
    {
        "sku": "HLM-002",
        "name": "Professional Cricket Helmet",
        "category": "helmet",
        "description": "Premium cricket helmet with titanium grill. Maximum safety and comfort.",
        "price": 5000.00,
        "stock_quantity": 12,
        "rating": 4.8,
        "review_count": 22,
        "sales_count": 28,
        "image_url": "https://placehold.co/400x400/png?text=Pro+Helmet",
        "specifications": {
            "helmet_type": "Batting",
            "size": "Men",
            "certification": "ICC Approved"
        }
    },
    # Cricket Shoes
    {
        "sku": "SHO-SPK-001",
        "name": "Cricket Shoes with Spikes",
        "category": "shoes",
        "subcategory": "spikes",
        "description": "Professional cricket shoes with metal spikes for turf wickets. Excellent grip.",
        "price": 3500.00,
        "stock_quantity": 22,
        "rating": 4.5,
        "review_count": 27,
        "sales_count": 44,
        "image_url": "https://placehold.co/400x400/png?text=Spike+Shoes",
        "specifications": {
            "shoe_type": "Spiked",
            "sole": "Metal Spikes",
            "suitable_for": "Turf Wicket"
        }
    },
    {
        "sku": "SHO-RBR-001",
        "name": "Cricket Shoes - Rubber Sole",
        "category": "shoes",
        "subcategory": "rubber",
        "description": "Comfortable cricket shoes with rubber sole for cement wickets and practice.",
        "price": 2500.00,
        "stock_quantity": 30,
        "rating": 4.3,
        "review_count": 35,
        "sales_count": 58,
        "image_url": "https://placehold.co/400x400/png?text=Rubber+Sole+Shoes",
        "specifications": {
            "shoe_type": "Rubber Sole",
            "sole": "Rubber",
            "suitable_for": "Cement Wicket"
        }
    },
    # Cricket Kit Bags
    {
        "sku": "BAG-KIT-001",
        "name": "Cricket Kit Bag - Medium",
        "category": "kit_bag",
        "description": "Spacious cricket kit bag with multiple compartments. Holds all your gear.",
        "price": 2000.00,
        "stock_quantity": 35,
        "rating": 4.1,
        "review_count": 18,
        "sales_count": 48,
        "image_url": "https://placehold.co/400x400/png?text=Kit+Bag+Medium",
        "specifications": {
            "bag_type": "Kit Bag",
            "size": "Medium",
            "compartments": "3"
        }
    },
    {
        "sku": "BAG-KIT-002",
        "name": "Professional Cricket Kit Bag - Large",
        "category": "kit_bag",
        "description": "Premium large kit bag with wheels. Perfect for professional players.",
        "price": 4000.00,
        "stock_quantity": 15,
        "rating": 4.6,
        "review_count": 21,
        "sales_count": 32,
        "image_url": "https://placehold.co/400x400/png?text=Kit+Bag+Large",
        "specifications": {
            "bag_type": "Kit Bag",
            "size": "Large",
            "features": "Wheels, 5 compartments"
        }
    },
]


async def seed_products():
    """Seed database with sample cricket products"""
    print("Connecting to database...")
    await db.connect()
    
    print(f"\nSeeding {len(SAMPLE_PRODUCTS)} products...")
    
    insert_query = """
    INSERT INTO products (
        sku, name, category, subcategory, description, price, original_price,
        in_stock, stock_quantity, rating, review_count, sales_count,
        image_url, specifications
    ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
    )
    ON CONFLICT (sku) DO UPDATE SET
        name = EXCLUDED.name,
        price = EXCLUDED.price,
        stock_quantity = EXCLUDED.stock_quantity,
        rating = EXCLUDED.rating,
        review_count = EXCLUDED.review_count,
        sales_count = EXCLUDED.sales_count
    """
    
    for product in SAMPLE_PRODUCTS:
        try:
            await db.execute(
                insert_query,
                product["sku"],
                product["name"],
                product["category"],
                product.get("subcategory"),
                product["description"],
                product["price"],
                product.get("original_price"),
                True,  # in_stock
                product["stock_quantity"],
                product["rating"],
                product["review_count"],
                product["sales_count"],
                product["image_url"],
                json.dumps(product["specifications"])
            )
            print(f"✓ Inserted: {product['name']}")
        except Exception as e:
            print(f"✗ Failed to insert {product['name']}: {e}")
    
    print("\n✓ Product seeding completed!")
    
    # Verify
    count_query = "SELECT COUNT(*) as count FROM products"
    result = await db.fetch_one(count_query)
    print(f"Total products in database: {result['count']}")
    
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(seed_products())
