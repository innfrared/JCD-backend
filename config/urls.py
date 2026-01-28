"""
URL configuration for jasmine_backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from interfaces.rest.catalog import views as catalog_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('interfaces.rest.users.urls')),
    path('api/categories/', catalog_views.CategoryListView.as_view(), name='category-list'),
    path(
        'api/categories/all/',
        catalog_views.CategoryWithSubcategoriesListView.as_view(),
        name='category-list-with-subcategories',
    ),
    path(
        'api/categories/<int:category_id>/subcategories/',
        catalog_views.SubcategoryListByCategoryView.as_view(),
        name='subcategory-list-by-category',
    ),
    path('api/products/', catalog_views.ProductListView.as_view(), name='product-list'),
    path('api/products/<int:product_id>/', catalog_views.ProductDetailView.as_view(), name='product-detail'),
    path('api/home/', include('interfaces.rest.homepage.urls')),
]

# Serve media files in development
if settings.DEBUG:
    from django.views.static import serve
    from django.urls import re_path
    from django.http import HttpResponse, Http404
    import os
    
    # Serve bag images from bag.import.assets folder FIRST (before default media)
    def serve_bag_images(request, path):
        """Serve bag images from bag.import.assets.

        Supports:
        - bag 2/<file>.jpg
        - bag2/<file>.jpg
        - bags/bag_18/<file>.jpg

        Maps all of them to local assets folder structure: `bag 18/<file>.jpg`.
        """
        base_assets = settings.BASE_DIR / 'bag.import.assets'

        def try_serve(mapped_rel_path: str):
            file_path = base_assets / mapped_rel_path
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return serve(request, mapped_rel_path, document_root=str(base_assets))
            return None

        # Case A: `bags/bag_18/<rest>` -> `bag 18/<rest>`
        if path.startswith('bags/bag '):
            parts = path.split('/', 2)
            if len(parts) >= 3:
                bag_folder = parts[1]  # bag_18
                rest = parts[2]
                bag_num = bag_folder.replace('bag ', '')
                resp = try_serve(f"bag {bag_num}/{rest}")
                if resp:
                    return resp

        # Case B: `bags/bag18/<rest>` -> `bag 18/<rest>` (just in case)
        if path.startswith('bags/bag') and not path.startswith('bags/bag '):
            parts = path.split('/', 2)
            if len(parts) >= 3:
                bag_folder = parts[1]  # bag18
                rest = parts[2]
                bag_num = bag_folder.replace('bag', '')
                if bag_num.isdigit():
                    resp = try_serve(f"bag {bag_num}/{rest}")
                    if resp:
                        return resp

        # Case C: `bag2/<rest>` -> `bag 2/<rest>`
        if path.startswith('bag') and not path.startswith('bag '):
            parts = path.split('/', 1)
            if len(parts) == 2:
                bag_folder, rest = parts
                bag_num = bag_folder.replace('bag', '')
                if bag_num.isdigit():
                    resp = try_serve(f"bag {bag_num}/{rest}")
                    if resp:
                        return resp

        # Case D: already `bag 2/<rest>`
        resp = try_serve(path)
        if resp:
            return resp

        raise Http404(f"File not found: {path}")

    urlpatterns += [
        # Support: /media/bag2/...
        re_path(r'^media/(?P<path>bag\d+/.*)$', serve_bag_images),
        # Support: /media/bags/bag_2/...
        re_path(r'^media/(?P<path>bags/bag_\d+/.*)$', serve_bag_images),
        # Support: /media/bags/bag2/... (optional)
        re_path(r'^media/(?P<path>bags/bag\d+/.*)$', serve_bag_images),
    ]
    # Then serve other media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
