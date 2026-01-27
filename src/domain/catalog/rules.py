"""Catalog domain rules."""
from src.domain.shared.exceptions import BusinessRuleViolation


def ensure_product_has_category(product):
    """Ensure product has a category."""
    if not product.category_id:
        raise BusinessRuleViolation("Product must have a category")


def ensure_variant_belongs_to_product(variant, product_id: int):
    """Ensure variant belongs to product."""
    if variant.product_id != product_id:
        raise BusinessRuleViolation("Variant does not belong to this product")

