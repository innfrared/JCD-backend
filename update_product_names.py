#!/usr/bin/env python
"""Update product names to remove color suffix."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.infrastructure.db.models.catalog import Product

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

def main():
    """Update product names."""
    print("=" * 60)
    print("Updating Product Names")
    print("=" * 60)
    
    updated_count = 0
    
    # Get all products
    products = Product.objects.all()
    
    for product in products:
        # Check if product name contains a dash (indicating it has a color suffix)
        if ' - ' in product.name:
            # Extract base name (everything before " - ")
            base_name = product.name.split(' - ')[0]
            
            # Check if base name matches one of our group names
            if base_name in GROUP_NAMES.values():
                old_name = product.name
                product.name = base_name
                product.save()
                print(f"Updated: '{old_name}' -> '{base_name}'")
                updated_count += 1
            else:
                print(f"Skipped (unknown base name): {product.name}")
        else:
            print(f"Already updated or no dash: {product.name}")
    
    print("\n" + "=" * 60)
    print(f"Update completed! Updated {updated_count} products.")
    print("=" * 60)


if __name__ == '__main__':
    main()

