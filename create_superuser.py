#!/usr/bin/env python
"""Script to create a Django superuser non-interactively."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from src.infrastructure.db.models.users import User

# Change these values as needed
EMAIL = 'admin@example.com'
PASSWORD = 'admin123'  # Change this!
FIRST_NAME = 'Admin'
LAST_NAME = 'User'

if User.objects.filter(email=EMAIL).exists():
    print(f"User with email {EMAIL} already exists.")
else:
    user = User.objects.create_superuser(
        email=EMAIL,
        password=PASSWORD,
        first_name=FIRST_NAME,
        last_name=LAST_NAME
    )
    print(f"Superuser created successfully!")
    print(f"Email: {EMAIL}")
    print(f"Password: {PASSWORD}")

