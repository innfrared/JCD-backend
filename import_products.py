#!/usr/bin/env python
"""Import products from bag.import.assets folder with full specifications."""
import os
import django
from pathlib import Path
from decimal import Decimal
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.infrastructure.db.models.catalog import (
    Category, Subcategory, VariantGroup, Product,
    Attribute, ProductAttributeValue
)

# Variant groups configuration
VARIANT_GROUPS = [
    [2, 3, 4],      # Group 1 - Zani
    [5, 6, 7],      # Group 2 - Evelé
    [1, 8],         # Group 3 - Vion
    [9, 10, 11],    # Group 4 - Serin
    [12, 13, 14],   # Group 5 - Eterna
    [15, 16, 17],   # Group 6 - Noora
    [18, 19],       # Group 7 - Rosel
]

# Product names for each group
GROUP_NAMES = {
    1: "Zani",
    2: "Evelé",
    3: "Vion",
    4: "Serin",
    5: "Eterna",
    6: "Noora",
    7: "Rosel",
}

# Product data with descriptions and specifications
PRODUCT_DATA = {
    "Serin": {
        "description": "Serin – Soft power. Born from the idea of lightness and delicacy: gentleness, softness, and the subtle movement of a bird's wing. Made for a woman who loves freedom, inner peace, and natural beauty. The delicate handmade weave, natural tones, and distinctive design feel like a spring breeze—unseen, yet deeply felt. Serin is not just a bag; it speaks about feminine strength expressed through tenderness.",
        "spec_sets": [
            {
                "color": {"name": "Light Beige (Ivory)", "note": "Ivory is described as an ivory-toned shade symbolizing purity."},
                "material": "100% cotton",
                "cord_diameter_mm": 3,
                "cord_type": "Coreless (no inner core)",
                "properties": ["Soft to the touch and durable", "Moisture-resistant", "Hypoallergenic", "Does not accumulate dust", "Not prone to mold formation", "High elasticity/springiness: restores shape after stretching or compression", "Does not fade over time; keeps brightness with gentle washing"],
                "care": "Wash at a temperature not higher than 30°C. Do not wring. Gently roll the bag in a towel to absorb excess moisture, then let it dry naturally."
            },
            {
                "color": {"name": "Beige"},
                "material": "100% cotton",
                "cord_diameter_mm": 3,
                "cord_type": "Coreless (no inner core)",
                "properties": ["Soft to the touch and durable", "Moisture-resistant", "Hypoallergenic", "Does not accumulate dust", "Not prone to mold formation", "High elasticity/springiness: restores shape after stretching or compression", "Does not fade over time; keeps brightness with gentle washing"],
                "care": "Wash at a temperature not higher than 30°C. Do not wring. Gently roll the bag in a towel to absorb excess moisture, then let it dry naturally."
            },
            {
                "color": {"name": "Cream"},
                "material": "100% cotton",
                "cord_diameter_mm": 3,
                "cord_type": "Twisted rope (macramé-style), 4-strand",
                "properties": ["Textured, strong, and pleasant to the touch", "Fibers can separate lightly to create a beautiful fringe effect", "Natural, hypoallergenic, made from 100% biodegradable cotton fiber", "No chemical dyes or impurities", "No foreign odors"],
                "care": "Gentle washing recommended (up to 30°C). Avoid aggressive wringing; reshape carefully and dry naturally."
            }
        ]
    },
    "Zani": {
        "description": "Zani – Made to feel right. Eco-crafted for women who balance softness and strength. Inspired by nature and woven in earth and light tones, it celebrates calm, freedom, and effortless elegance. Naturally Zani. Unapologetically you.",
        "spec_sets": [
            {
                "color": {"name": "Beige"},
                "material": "100% cotton",
                "cord_diameter_mm": 3,
                "cord_type": "Coreless (no inner core)",
                "properties": ["Soft to the touch and durable", "Moisture-resistant", "Hypoallergenic", "Does not accumulate dust", "Not prone to mold formation", "High elasticity/springiness: restores shape after stretching or compression", "Does not fade over time; keeps brightness with gentle washing"],
                "care": "Wash at a temperature not higher than 30°C. Do not wring. Gently roll the bag in a towel to absorb excess moisture, then let it dry naturally."
            },
            {
                "color": {"name": "Light Beige (Ivory)", "note": "Ivory is described as an ivory-toned shade symbolizing purity."},
                "material": "100% cotton",
                "cord_diameter_mm": 3,
                "cord_type": "Coreless (no inner core)",
                "properties": ["Soft to the touch and durable", "Moisture-resistant", "Hypoallergenic", "Does not accumulate dust", "Not prone to mold formation", "High elasticity/springiness: restores shape after stretching or compression", "Does not fade over time; keeps brightness with gentle washing"],
                "care": "Wash at a temperature not higher than 30°C. Do not wring. Gently roll the bag in a towel to absorb excess moisture, then let it dry naturally."
            }
        ]
    },
    "Rosel": {
        "description": "Rosel – Naturally elegant. A symbol of love and grace. The name recalls soft rose petals where beauty and strength meet. Every knot and detail feels like a rose petal unfolding. Made for a woman who values her uniqueness and loves adding a little sparkle and romance to her days. Rosel is not just an accessory; it represents feminine delicacy, softness of soul, and blooming confidence.",
        "spec_sets": [
            {
                "color": {"name": "Beige with Gold shimmer"},
                "material": "Polyester + lurex",
                "cord_diameter_mm": 4,
                "cord_type": "Braided, elastic, metallized (coreless)",
                "composition": {"polyester_percent": 80, "lurex_percent": 20},
                "properties": ["Festive golden shimmer effect", "Strong and wear-resistant", "Stain-resistant", "Does not fade in the sun", "Washes well and dries quickly", "Pleasant to the touch, not prickly"],
                "care": "Avoid contact with an iron. Wash gently (around 30°C recommended). Dry naturally."
            },
            {
                "color": {"name": "Black"},
                "material": "Polyester",
                "cord_diameter_mm": 3,
                "cord_type": "Braided (round cross-section)",
                "properties": ["Textured, soft, pleasant to the touch with a slight sheen", "Easy care", "Holds shape well", "Quick drying"],
                "care": "Delicate wash at 30°C. Dry naturally."
            }
        ]
    },
    "Eterna": {
        "description": "Eterna – Elegance that lasts. Born where timeless forms meet pure materials. Its pattern—an endless weave without beginning or end—embodies women's strength, continuity, and the memories that live in everyday life and special moments. Made from eco-friendly materials with the intention to serve not only today, but tomorrow. Eterna is not only style, but a timeless companion.",
        "spec_sets": [
            {
                "color": {"name": "Gray"},
                "material": "Polypropylene (with a subtle noble shine)",
                "cord_diameter_mm": 4,
                "cord_type": "Round cord",
                "properties": ["Very strong and durable; keeps shape for years", "Does not absorb moisture (reliable in rain)", "Eco-friendly and safe", "Does not contain harmful substances", "Does not cause allergic reactions"],
                "care": "Easy care; clean gently as needed. Dry naturally. Suitable for damp weather."
            },
            {
                "color": {"name": "Steel / Gray"},
                "material": "Polyester",
                "cord_diameter_mm": 3,
                "cord_type": "Braided (round cross-section)",
                "properties": ["Textured, soft, pleasant to the touch with a slight sheen", "Easy care", "Holds shape well", "Quick drying"],
                "care": "Delicate wash at 30°C. Dry naturally."
            }
        ]
    },
    "Noora": {
        "description": "Noora – Crafted in the softness of light. Created as a reminder that every woman carries her own light—sometimes gentle, sometimes bright, always sincere. Every detail, from the weave to the form, reflects nature's simplicity and a graceful balance. Made for women who choose confidence and harmony; they don't chase fashion, they create their own rhythm.",
        "spec_sets": [
            {
                "color": {"name": "Milk Chocolate / Light Beige"},
                "material": "Polypropylene (100%)",
                "cord_diameter_mm": 3,
                "cord_type": "Coreless, round",
                "properties": ["Maximum strength; long-lasting", "Eco-friendly and safe for health", "Smooth, even, slightly glossy surface for a stylish look", "Does not absorb moisture"],
                "care": "Easy care. Clean gently as needed. Dry naturally."
            },
            {
                "color": {"name": "Gray"},
                "material": "100% cotton",
                "cord_diameter_mm": 3,
                "cord_type": "Twisted rope (macramé-style), 4-strand",
                "properties": ["Textured, strong, gentle, pleasant to the touch", "Fibers can separate lightly to create a fringe effect", "Natural, hypoallergenic, made from 100% biodegradable cotton fiber", "No chemical dyes or impurities", "No foreign odors"],
                "care": "Gentle washing recommended (up to 30°C). Avoid aggressive wringing; reshape carefully and dry naturally."
            },
            {
                "color": {"name": "Light Gray"},
                "material": "100% cotton",
                "cord_diameter_mm": 3,
                "cord_type": "Twisted rope (macramé-style), 4-strand",
                "properties": ["Textured, strong, gentle, pleasant to the touch", "Fibers can separate lightly to create a fringe effect", "Natural, hypoallergenic, made from 100% biodegradable cotton fiber", "No chemical dyes or impurities", "No foreign odors"],
                "care": "Gentle washing recommended (up to 30°C). Avoid aggressive wringing; reshape carefully and dry naturally."
            }
        ]
    },
    "Evelé": {
        "description": "Evelé – The Whisper of Elegance. Born in quietness, where true elegance is shaped. Made for a woman who doesn't strive to be loud—she simply has presence. Every fold and line, formed by hand, reflects balance and confidence. Evelé is not just an accessory; it is a small story—from nature to modern elegance. True luxury doesn't shout; it whispers: calm, proud, and impeccable.",
        "spec_sets": [
            {
                "color": {"name": "Pastel Brown / Cocoa"},
                "material": "Polyester (with a subtle noble shine)",
                "cord_diameter_mm": 5,
                "cord_type": "Coreless",
                "properties": ["Dense and springy yet very soft and pleasant to the touch", "Durable and moisture-resistant", "Eco-friendly feel, hypoallergenic", "Strong, high quality, holds a beautiful shape"],
                "care": "Gentle care recommended. Keep away from high heat; dry naturally."
            },
            {
                "color": {"name": "Linen tone"},
                "material": "Polyester (with a subtle noble shine)",
                "cord_diameter_mm": 5,
                "cord_type": "Coreless",
                "properties": ["Dense and springy yet very soft and pleasant to the touch", "Durable and moisture-resistant", "Eco-friendly feel, hypoallergenic", "Strong, high quality, holds a beautiful shape"],
                "care": "Gentle care recommended. Keep away from high heat; dry naturally."
            },
            {
                "color": {"name": "Gray"},
                "material": "Polypropylene",
                "cord_diameter_mm": 4,
                "cord_type": "Round cord",
                "properties": ["Very strong and durable; keeps shape for years", "Does not absorb moisture (reliable in rain)", "Eco-friendly and safe", "Does not contain harmful substances", "Does not cause allergic reactions"],
                "care": "Easy care; clean gently as needed. Dry naturally. Suitable for damp weather."
            },
            {
                "color": {"name": "Beige"},
                "material": "Polypropylene",
                "cord_diameter_mm": 4,
                "cord_type": "Round cord",
                "properties": ["Very strong and durable; keeps shape for years", "Does not absorb moisture (reliable in rain)", "Eco-friendly and safe", "Does not contain harmful substances", "Does not cause allergic reactions"],
                "care": "Easy care; clean gently as needed. Dry naturally. Suitable for damp weather."
            }
        ]
    },
    "Vion": {
        "description": "Vion – Effortless elegance. Born from the idea of simplicity, it speaks about calm, balance, and inner confidence. Every knot reflects the power of moderation—bringing peace, confidence, and stability. Created for those seeking the ideal blend of style and comfort. A companion for everyday journeys, workdays, and sincere evenings. Vion balances classic and modern, elegance and practicality—highlighting inner calm and taste. Without excess, yet always interesting.",
        "spec_sets": [
            {
                "color": {"name": "Indigo"},
                "material": "Polypropylene",
                "cord_diameter_mm": 3,
                "cord_type": "Coreless rope",
                "properties": ["Does not absorb moisture; stays dry in rain", "High strength and durability; holds shape for years", "Does not fade in the sun", "Withstands temperature changes", "Quick-drying and does not absorb moisture", "Hypoallergenic, safe, odor-free, no harmful additives"],
                "care": "Easy care. Clean gently as needed; dry naturally. Suitable for indoor and outdoor use."
            },
            {
                "color": {"name": "White-Green"},
                "material": "Polyester",
                "cord_diameter_mm": 3,
                "cord_type": "Coreless",
                "properties": ["Softness and flexibility; absence of fused joints makes the bag impeccable", "Springy fiber structure helps the изделие return to its original shape after stretching/compression", "Looks almost like natural raw material; soft and pleasant to the touch"],
                "care": "Gentle care recommended. Avoid high heat; dry naturally."
            },
            {
                "color": {"name": "Linen / Cocoa"},
                "material": "Polyester fiber",
                "cord_diameter_mm": 3,
                "cord_type": "Braided, coreless",
                "properties": ["Lightweight but structured; keeps form well", "Does not stretch, does not fray, does not fuzz", "Dense, light, and resilient"],
                "care": "Gentle care recommended. Avoid aggressive heat; dry naturally."
            }
        ]
    }
}

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / 'bag.import.assets'

# Map bag numbers to color names (based on spec_sets order)
BAG_TO_COLOR_MAP = {
    # Group 1 - Zani (bags 2, 3, 4)
    2: "Beige",
    3: "Light Beige (Ivory)",
    4: "Light Beige (Ivory)",  # Assuming third bag uses second color
    
    # Group 2 - Evelé (bags 5, 6, 7)
    5: "Pastel Brown / Cocoa",
    6: "Linen tone",
    7: "Gray",
    
    # Group 3 - Vion (bags 1, 8)
    1: "Indigo",
    8: "White-Green",
    
    # Group 4 - Serin (bags 9, 10, 11)
    9: "Light Beige (Ivory)",
    10: "Beige",
    11: "Cream",
    
    # Group 5 - Eterna (bags 12, 13, 14)
    12: "Gray",
    13: "Steel / Gray",
    14: "Steel / Gray",  # Assuming third bag uses second color
    
    # Group 6 - Noora (bags 15, 16, 17)
    15: "Milk Chocolate / Light Beige",
    16: "Gray",
    17: "Light Gray",
    
    # Group 7 - Rosel (bags 18, 19)
    18: "Beige with Gold shimmer",
    19: "Black",
}


def get_first_image(bag_number: int) -> str:
    """Get the first image path for a bag."""
    bag_dir = ASSETS_DIR / f"bag {bag_number}"
    if not bag_dir.exists():
        return ""
    
    images = sorted(bag_dir.glob("*.jpg"))
    if images:
        # Return URL path that will be served by Django
        # Use underscore format (bag_2) to match frontend expectations
        # Format: /media/bags/bag_{bag_number}/image_name.jpg
        image_name = images[0].name
        return f"/media/bags/bag_{bag_number}/{image_name}"
    return ""


def get_or_create_attribute(category, key, label, data_type, unit=None, sort_order=0):
    """Get or create an attribute for the category."""
    attribute, created = Attribute.objects.get_or_create(
        scope_type=Attribute.ScopeTypeChoices.CATEGORY,
        scope_id=category.id,
        key=key,
        defaults={
            'label': label,
            'data_type': data_type,
            'unit': unit,
            'sort_order': sort_order,
            'is_filterable': True,
        }
    )
    return attribute


def create_product_attribute_value(product, attribute, value_text=None, value_number=None):
    """Create or update a product attribute value."""
    attr_value, created = ProductAttributeValue.objects.get_or_create(
        product=product,
        attribute=attribute,
        defaults={
            'value_text': value_text,
            'value_number': value_number,
        }
    )
    if not created:
        attr_value.value_text = value_text
        attr_value.value_number = value_number
        attr_value.save()
    return attr_value


def create_or_get_category():
    """Create or get the Bags category."""
    category, created = Category.objects.get_or_create(
        slug='bags',
        defaults={
            'name': 'Bags',
        }
    )
    if created:
        print(f"Created category: {category.name}")
    return category


def create_or_get_subcategory(category):
    """Create or get the Handbags subcategory."""
    subcategory, created = Subcategory.objects.get_or_create(
        category=category,
        slug='handbags',
        defaults={
            'name': 'Handbags',
        }
    )
    if created:
        print(f"Created subcategory: {subcategory.name}")
    return subcategory


def create_variant_group(group_number: int, bag_numbers: list) -> VariantGroup:
    """Create a variant group for a set of bags."""
    product_name = GROUP_NAMES.get(group_number, f"Bag Collection {group_number}")
    group_name = f"{product_name} Collection"
    slug = f"{product_name.lower().replace('é', 'e')}-collection"
    
    # Get description from product data
    description = PRODUCT_DATA.get(product_name, {}).get('description', '')
    
    variant_group, created = VariantGroup.objects.get_or_create(
        slug=slug,
        defaults={
            'name': group_name,
        }
    )
    
    if created:
        print(f"Created variant group: {variant_group.name}")
    else:
        print(f"Using existing variant group: {variant_group.name}")
    
    return variant_group


def create_product(
    bag_number: int,
    category: Category,
    subcategory: Subcategory,
    variant_group: VariantGroup = None,
    is_default: bool = False,
    group_number: int = None
) -> Product:
    """Create a product for a bag with full specifications."""
    # Get first image
    image_path = get_first_image(bag_number)
    
    # Get product name and data
    product_name = GROUP_NAMES.get(group_number, "Jasmine Tote") if group_number else "Jasmine Tote"
    color_name = BAG_TO_COLOR_MAP.get(bag_number, f'Color {bag_number}')
    full_product_name = product_name
    
    # Find matching spec set
    product_data = PRODUCT_DATA.get(product_name, {})
    spec_sets = product_data.get('spec_sets', [])
    spec_set = None
    for spec in spec_sets:
        if spec['color']['name'] == color_name:
            spec_set = spec
            break
    
    # If no exact match, use first spec set
    if not spec_set and spec_sets:
        spec_set = spec_sets[0]
        color_name = spec_set['color']['name']
    
    # Default price
    base_price = Decimal('199.99')
    
    # Try to find existing product by variant_group and color, or by name pattern
    product = None
    if variant_group:
        # Look for existing product in this variant group with this color
        product = Product.objects.filter(
            variant_group=variant_group,
            variant_color_name=color_name
        ).first()
    
    # If not found, try to find by name pattern (handles old names with " - Color")
    if not product:
        old_name_pattern = f"{product_name} - {color_name}"
        product = Product.objects.filter(name=old_name_pattern).first()
        if product:
            # Update name to remove color suffix
            product.name = product_name
    
    # Create new product if not found
    created = False
    if not product:
        product = Product.objects.create(
            name=full_product_name,
            brand='Jasmine',
            price=base_price,
            price_new=base_price * Decimal('0.9'),  # 10% discount
            price_old=base_price,
            availability=Product.AvailabilityChoices.IN_STOCK,
            category=category,
            subcategory=subcategory,
            currency=Product.CurrencyChoices.USD,
            variant_group=variant_group,
            variant_color_name=color_name,
            variant_color_palette=None,  # Will be set from color if needed
            variant_image=image_path if image_path else None,
        )
        created = True
        print(f"  Created product: {product.name} (Bag {bag_number}, Color: {color_name})")
    else:
        print(f"  Updated product: {product.name} (Bag {bag_number}, Color: {color_name})")
        # Update name if it still has color suffix
        if product.name != full_product_name and ' - ' in product.name:
            product.name = full_product_name
        # Update variant fields
        if variant_group and product.variant_group != variant_group:
            product.variant_group = variant_group
        if not product.variant_image and image_path:
            product.variant_image = image_path
        if not product.variant_color_name:
            product.variant_color_name = color_name
        product.save()
    
    # Set as default product for variant group if specified
    if is_default and variant_group:
        variant_group.default_product = product
        variant_group.save()
        print(f"    Set as default product for variant group")
    
    # Create EAV attributes and values if spec_set exists
    if spec_set:
        # Create/get attributes
        material_attr = get_or_create_attribute(category, 'material', 'Material', Attribute.DataTypeChoices.TEXT, sort_order=1)
        cord_diameter_attr = get_or_create_attribute(category, 'cord_diameter_mm', 'Cord Diameter', Attribute.DataTypeChoices.NUMBER, unit='mm', sort_order=2)
        cord_type_attr = get_or_create_attribute(category, 'cord_type', 'Cord Type', Attribute.DataTypeChoices.TEXT, sort_order=3)
        properties_attr = get_or_create_attribute(category, 'properties', 'Properties', Attribute.DataTypeChoices.TEXT, sort_order=4)
        care_attr = get_or_create_attribute(category, 'care', 'Care Instructions', Attribute.DataTypeChoices.TEXT, sort_order=5)
        
        # Create attribute values
        create_product_attribute_value(product, material_attr, value_text=spec_set.get('material'))
        create_product_attribute_value(product, cord_diameter_attr, value_number=Decimal(str(spec_set.get('cord_diameter_mm', 0))))
        create_product_attribute_value(product, cord_type_attr, value_text=spec_set.get('cord_type'))
        create_product_attribute_value(product, properties_attr, value_text='; '.join(spec_set.get('properties', [])))
        create_product_attribute_value(product, care_attr, value_text=spec_set.get('care'))
        
        # Handle composition if exists
        if 'composition' in spec_set:
            comp = spec_set['composition']
            if 'polyester_percent' in comp:
                poly_attr = get_or_create_attribute(category, 'polyester_percent', 'Polyester %', Attribute.DataTypeChoices.NUMBER, unit='%', sort_order=6)
                create_product_attribute_value(product, poly_attr, value_number=Decimal(str(comp['polyester_percent'])))
            if 'lurex_percent' in comp:
                lurex_attr = get_or_create_attribute(category, 'lurex_percent', 'Lurex %', Attribute.DataTypeChoices.NUMBER, unit='%', sort_order=7)
                create_product_attribute_value(product, lurex_attr, value_number=Decimal(str(comp['lurex_percent'])))
        
        print(f"    Added specifications")
    
    return product


def main():
    """Main import function."""
    print("=" * 60)
    print("Product Import Script with Specifications")
    print("=" * 60)
    
    # Create category and subcategory
    category = create_or_get_category()
    subcategory = create_or_get_subcategory(category)
    
    print("\nCreating variant groups and products...")
    print("-" * 60)
    
    # Process each variant group
    for group_idx, bag_numbers in enumerate(VARIANT_GROUPS, start=1):
        print(f"\nProcessing Variant Group {group_idx}: Bags {bag_numbers} ({GROUP_NAMES.get(group_idx, 'Unknown')})")
        
        # Create variant group
        variant_group = create_variant_group(group_idx, bag_numbers)
        
        # Create products for each bag in the group
        for idx, bag_number in enumerate(bag_numbers):
            is_default = (idx == 0)  # First bag is default
            create_product(
                bag_number=bag_number,
                category=category,
                subcategory=subcategory,
                variant_group=variant_group,
                is_default=is_default,
                group_number=group_idx
            )
    
    print("\n" + "=" * 60)
    print("Import completed!")
    print("=" * 60)
    
    # Print summary
    total_products = Product.objects.count()
    total_groups = VariantGroup.objects.count()
    print(f"\nSummary:")
    print(f"  Total Products: {total_products}")
    print(f"  Total Variant Groups: {total_groups}")
    print(f"  Category: {category.name}")
    print(f"  Subcategory: {subcategory.name}")


if __name__ == '__main__':
    main()
