"""Homepage Django models."""
from django.db import models


class HomeSection(models.Model):
    """Home section model."""
    key = models.SlugField(unique=True, max_length=100, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    main_image = models.URLField(blank=True, null=True)
    category_name = models.CharField(max_length=200, blank=True, null=True)
    product_count = models.IntegerField(default=10)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'home_sections'
        verbose_name = 'Home Section'
        verbose_name_plural = 'Home Sections'
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.key})"


class HomeSectionItem(models.Model):
    """Home section item model (curated product reference)."""
    section = models.ForeignKey(
        HomeSection,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='home_sections'
    )
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'home_section_items'
        verbose_name = 'Home Section Item'
        verbose_name_plural = 'Home Section Items'
        unique_together = [['section', 'product']]
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['section', 'sort_order']),
        ]
    
    def __str__(self):
        return f"{self.section.title} - {self.product.name}"

