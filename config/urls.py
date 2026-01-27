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
    path('api/categories', catalog_views.CategoryListView.as_view(), name='category-list'),
    path('api/products', catalog_views.ProductListView.as_view(), name='product-list'),
    path('api/products/<int:product_id>', catalog_views.ProductDetailView.as_view(), name='product-detail'),
    path('api/home', include('interfaces.rest.homepage.urls')),
]

# Serve media files in development
if settings.DEBUG:
    from django.views.static import serve
    from django.urls import re_path
    from django.http import HttpResponse, Http404
    import os
    
    # Serve bag images from bag.import.assets folder FIRST (before default media)
    # Handle both underscore format (bag_2) from frontend and space format (bag 2) from folders
    def serve_bag_images(request, path):
        """Serve bag images, converting bag_X to bag X format."""
        # Convert bag_2/SAR_0153.jpg to bag 2/SAR_0153.jpg
        if path.startswith('bag_'):
            # Replace bag_X with bag X
            parts = path.split('/', 1)
            if len(parts) == 2:
                folder_part, file_part = parts
                folder_name = folder_part.replace('_', ' ', 1)  # Replace first underscore only
                path = f"{folder_name}/{file_part}"
        
        file_path = settings.BASE_DIR / 'bag.import.assets' / path
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return serve(request, path, document_root=str(settings.BASE_DIR / 'bag.import.assets'))
        raise Http404(f"File not found: {path}")
    
    urlpatterns += [
        re_path(r'^media/bags/(?P<path>.*)$', serve_bag_images),
    ]
    # Then serve other media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
