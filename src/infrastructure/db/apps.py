"""Django app configuration."""
from django.apps import AppConfig


class DbConfig(AppConfig):
    """Database app config."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.infrastructure.db'
    label = 'db'
    verbose_name = 'Database Models'

