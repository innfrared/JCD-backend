"""Homepage domain rules."""
from typing import List
from src.domain.catalog.entities import Product


def get_items_to_render(
    product_count: int,
    available_items: List[Product]
) -> List[Product]:
    """
    Get items to render based on product_count.
    
    Rule: items_to_render = min(productCount, available_items_count)
    """
    return available_items[:product_count]


def filter_unavailable_products(
    products: List[Product],
    include_unavailable: bool = False
) -> List[Product]:
    """
    Filter out unavailable products.
    
    Decision: Keep unavailable products but they will be marked as out of stock
    in the ProductCard. This preserves the curated order.
    """
    if include_unavailable:
        return products
    # For now, we keep all products but mark availability in ProductCard
    return products

