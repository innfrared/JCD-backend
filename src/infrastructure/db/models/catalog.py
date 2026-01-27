"""Catalog Django models."""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    """Category model."""
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Subcategory(models.Model):
    """Subcategory model."""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subcategories'
        verbose_name = 'Subcategory'
        verbose_name_plural = 'Subcategories'
        unique_together = [['category', 'slug']]
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.category.name} > {self.name}"


class VariantGroup(models.Model):
    """Variant group model (groups products that are variants of each other)."""
    name = models.CharField(max_length=200, blank=True, null=True)
    slug = models.SlugField(max_length=200, blank=True, null=True, unique=True)
    default_product = models.ForeignKey(
        'Product',
        on_delete=models.SET_NULL,
        related_name='default_variant_groups',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'variant_groups'
        verbose_name = 'Variant Group'
        verbose_name_plural = 'Variant Groups'
        ordering = ['name', 'id']
    
    def __str__(self):
        return self.name or f"Variant Group #{self.id}"


class Product(models.Model):
    """Product model."""
    class AvailabilityChoices(models.TextChoices):
        IN_STOCK = 'in_stock', 'In Stock'
        OUT_OF_STOCK = 'out_of_stock', 'Out of Stock'
        PRE_ORDER = 'pre_order', 'Pre-Order'
    
    class CurrencyChoices(models.TextChoices):
        USD = 'USD', 'USD'
        EUR = 'EUR', 'EUR'
        GBP = 'GBP', 'GBP'
    
    name = models.CharField(max_length=300, db_index=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    price_new = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0'))])
    price_old = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0'))])
    availability = models.CharField(max_length=20, choices=AvailabilityChoices.choices, default=AvailabilityChoices.IN_STOCK)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    subcategory = models.ForeignKey(Subcategory, on_delete=models.PROTECT, related_name='products', blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CurrencyChoices.choices, default=CurrencyChoices.USD)
    variant_group = models.ForeignKey(
        VariantGroup,
        on_delete=models.SET_NULL,
        related_name='products',
        blank=True,
        null=True
    )
    variant_color_name = models.CharField(max_length=100, blank=True, null=True)
    variant_color_palette = models.CharField(max_length=100, blank=True, null=True)
    variant_image = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'availability']),
            models.Index(fields=['subcategory', 'availability']),
        ]
    
    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    """Product variant model."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=200)
    image_url = models.URLField(blank=True, null=True)
    color_palette = models.CharField(max_length=100, blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_variants'
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'
        ordering = ['sort_order', 'id']
    
    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"


class VariantSize(models.Model):
    """Variant size model."""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='sizes')
    size = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'variant_sizes'
        verbose_name = 'Variant Size'
        verbose_name_plural = 'Variant Sizes'
        unique_together = [['variant', 'size']]
    
    def __str__(self):
        return f"{self.variant} - {self.size}"


class Attribute(models.Model):
    """Attribute definition model."""
    class ScopeTypeChoices(models.TextChoices):
        CATEGORY = 'category', 'Category'
        SUBCATEGORY = 'subcategory', 'Subcategory'
    
    class DataTypeChoices(models.TextChoices):
        TEXT = 'TEXT', 'Text'
        NUMBER = 'NUMBER', 'Number'
        BOOLEAN = 'BOOLEAN', 'Boolean'
        SINGLE_SELECT = 'SINGLE_SELECT', 'Single Select'
        MULTI_SELECT = 'MULTI_SELECT', 'Multi Select'
    
    scope_type = models.CharField(max_length=20, choices=ScopeTypeChoices.choices)
    scope_id = models.IntegerField()  # Category or Subcategory ID
    key = models.CharField(max_length=100, db_index=True)
    label = models.CharField(max_length=200)
    data_type = models.CharField(max_length=20, choices=DataTypeChoices.choices)
    unit = models.CharField(max_length=20, blank=True, null=True)
    is_filterable = models.BooleanField(default=False)
    is_required = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'attributes'
        verbose_name = 'Attribute'
        verbose_name_plural = 'Attributes'
        unique_together = [['scope_type', 'scope_id', 'key']]
        ordering = ['sort_order', 'key']
        indexes = [
            models.Index(fields=['scope_type', 'scope_id']),
        ]
    
    def __str__(self):
        return f"{self.label} ({self.key})"


class AttributeOption(models.Model):
    """Attribute option model."""
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='options')
    value = models.CharField(max_length=100)
    label = models.CharField(max_length=200)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'attribute_options'
        verbose_name = 'Attribute Option'
        verbose_name_plural = 'Attribute Options'
        unique_together = [['attribute', 'value']]
        ordering = ['sort_order', 'value']
    
    def __str__(self):
        return f"{self.attribute.label} - {self.label}"


class ProductAttributeValue(models.Model):
    """Product attribute value model."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attribute_values')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value_text = models.TextField(blank=True, null=True)
    value_number = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    value_bool = models.BooleanField(blank=True, null=True)
    
    class Meta:
        db_table = 'product_attribute_values'
        verbose_name = 'Product Attribute Value'
        verbose_name_plural = 'Product Attribute Values'
        unique_together = [['product', 'attribute']]
    
    def __str__(self):
        return f"{self.product.name} - {self.attribute.label}"


class ProductAttributeOption(models.Model):
    """Product attribute option (for SELECT types)."""
    product_attribute_value = models.ForeignKey(
        ProductAttributeValue,
        on_delete=models.CASCADE,
        related_name='selected_options'
    )
    option = models.ForeignKey(AttributeOption, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'product_attribute_options'
        verbose_name = 'Product Attribute Option'
        verbose_name_plural = 'Product Attribute Options'
        unique_together = [['product_attribute_value', 'option']]
    
    def __str__(self):
        return f"{self.product_attribute_value} - {self.option.label}"

