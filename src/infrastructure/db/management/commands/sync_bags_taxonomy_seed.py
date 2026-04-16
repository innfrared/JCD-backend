"""Sync bags taxonomy from seed source of truth."""
from django.core.management.base import BaseCommand

from src.infrastructure.db.models.catalog import Category, Subcategory
from src.infrastructure.db.seed.bags_seed import BAGS_CATEGORY, BAGS_SUBCATEGORIES


class Command(BaseCommand):
    help = "Sync Bags category/subcategories from seed config."

    def handle(self, *args, **options):
        category, _ = Category.objects.update_or_create(
            slug=BAGS_CATEGORY["slug"],
            defaults={
                "name": BAGS_CATEGORY["name"],
                "image": BAGS_CATEGORY.get("image"),
            },
        )

        for sub in BAGS_SUBCATEGORIES:
            Subcategory.objects.update_or_create(
                category=category,
                slug=sub["slug"],
                defaults={
                    "name": sub["name"],
                    "description": sub.get("description"),
                    "image": sub.get("image"),
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Bags taxonomy synced from seed configuration."
            )
        )
