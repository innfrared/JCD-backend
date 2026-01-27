"""Django admin configuration."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models.users import User, Address
from .models.catalog import (
    Category, Subcategory, VariantGroup, Product, ProductVariant, VariantSize,
    Attribute, AttributeOption, ProductAttributeValue, ProductAttributeOption
)
from .models.homepage import HomeSection, HomeSectionItem


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """User admin configuration."""
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'is_staff', 'is_active'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Address admin configuration."""
    list_display = ('label', 'full_name', 'user', 'city', 'country', 'is_default', 'created_at')
    list_filter = ('country', 'is_default', 'created_at')
    search_fields = ('label', 'full_name', 'city', 'country', 'user__email')
    raw_id_fields = ('user',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category admin configuration."""
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    """Subcategory admin configuration."""
    list_display = ('name', 'category', 'slug', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'slug', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('category',)


class VariantSizeInline(admin.TabularInline):
    """Variant size inline admin."""
    model = VariantSize
    extra = 1


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """Product variant admin configuration."""
    list_display = ('name', 'value', 'product', 'sort_order', 'color_palette')
    list_filter = ('product__category',)
    search_fields = ('name', 'value', 'product__name')
    raw_id_fields = ('product',)
    inlines = [VariantSizeInline]


class ProductVariantInline(admin.TabularInline):
    """Product variant inline admin."""
    model = ProductVariant
    extra = 1
    show_change_link = True


@admin.register(VariantGroup)
class VariantGroupAdmin(admin.ModelAdmin):
    """Variant group admin configuration."""
    list_display = ('name', 'slug', 'default_product', 'created_at')
    search_fields = ('name', 'slug')
    raw_id_fields = ('default_product',)
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'default_product')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Product admin configuration."""
    list_display = ('name', 'brand', 'category', 'subcategory', 'variant_group', 'price', 'currency', 'availability', 'created_at')
    list_filter = ('category', 'subcategory', 'variant_group', 'availability', 'currency', 'created_at')
    search_fields = ('name', 'brand', 'category__name', 'subcategory__name')
    raw_id_fields = ('category', 'subcategory', 'variant_group')
    fieldsets = (
        (None, {
            'fields': ('name', 'brand', 'category', 'subcategory')
        }),
        ('Pricing', {
            'fields': ('price', 'price_new', 'price_old', 'currency', 'availability')
        }),
        ('Variant Group', {
            'fields': ('variant_group', 'variant_color_name', 'variant_color_palette', 'variant_image'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProductVariantInline]  # Keep for backward compatibility, but will be deprecated


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    """Attribute admin configuration."""
    list_display = ('key', 'label', 'scope_type', 'scope_id', 'data_type', 'is_filterable', 'is_required', 'sort_order')
    list_filter = ('scope_type', 'data_type', 'is_filterable', 'is_required')
    search_fields = ('key', 'label')
    ordering = ('scope_type', 'scope_id', 'sort_order')


@admin.register(AttributeOption)
class AttributeOptionAdmin(admin.ModelAdmin):
    """Attribute option admin configuration."""
    list_display = ('label', 'value', 'attribute', 'sort_order')
    list_filter = ('attribute',)
    search_fields = ('label', 'value', 'attribute__label')
    raw_id_fields = ('attribute',)


class ProductAttributeOptionInline(admin.TabularInline):
    """Product attribute option inline admin."""
    model = ProductAttributeOption
    extra = 1


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    """Product attribute value admin configuration."""
    list_display = ('product', 'attribute', 'get_value_display')
    list_filter = ('attribute', 'attribute__data_type')
    search_fields = ('product__name', 'attribute__label')
    raw_id_fields = ('product', 'attribute')
    inlines = [ProductAttributeOptionInline]
    
    def get_value_display(self, obj):
        """Display the appropriate value based on data type."""
        if obj.value_text:
            return obj.value_text
        elif obj.value_number is not None:
            return str(obj.value_number)
        elif obj.value_bool is not None:
            return str(obj.value_bool)
        elif obj.selected_options.exists():
            return ', '.join([opt.option.label for opt in obj.selected_options.all()])
        return '-'
    get_value_display.short_description = 'Value'


@admin.register(ProductAttributeOption)
class ProductAttributeOptionAdmin(admin.ModelAdmin):
    """Product attribute option admin configuration."""
    list_display = ('product_attribute_value', 'option')
    list_filter = ('option__attribute',)
    search_fields = ('product_attribute_value__product__name', 'option__label')
    raw_id_fields = ('product_attribute_value', 'option')


class HomeSectionItemInline(admin.TabularInline):
    """Home section item inline admin."""
    model = HomeSectionItem
    extra = 1
    raw_id_fields = ('product',)
    ordering = ('sort_order',)


@admin.register(HomeSection)
class HomeSectionAdmin(admin.ModelAdmin):
    """Home section admin configuration."""
    list_display = ('title', 'key', 'category_name', 'product_count', 'sort_order', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'key', 'category_name', 'description')
    ordering = ('sort_order', 'id')
    inlines = [HomeSectionItemInline]
    fieldsets = (
        (None, {
            'fields': ('key', 'title', 'description', 'is_active')
        }),
        ('Display', {
            'fields': ('main_image', 'category_name', 'product_count', 'sort_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(HomeSectionItem)
class HomeSectionItemAdmin(admin.ModelAdmin):
    """Home section item admin configuration."""
    list_display = ('section', 'product', 'sort_order', 'created_at')
    list_filter = ('section', 'created_at')
    search_fields = ('section__title', 'product__name')
    raw_id_fields = ('section', 'product')
    ordering = ('section', 'sort_order')

