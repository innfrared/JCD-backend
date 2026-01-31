import re

from django.core.management.base import BaseCommand
from django.db import connection

from src.infrastructure.db.models.catalog import Category, Subcategory, Product


class Command(BaseCommand):
    help = "Normalize Bags category and assign style subcategories"

    BAGS_CATEGORY_ID = 1000

    SUBCATEGORIES = {
        1100: {
            "name": "Crossbody Bags",
            "slug": "crossbody-bags",
            "description": (
                "Long-strap bags worn across the body for hands-free, "
                "everyday comfort."
            ),
        },
        1200: {
            "name": "Shoulder Bags",
            "slug": "shoulder-bags",
            "description": (
                "Medium-size bags designed to rest on the shoulder or under "
                "the arm."
            ),
        },
        1300: {
            "name": "Handbags",
            "slug": "handbags",
            "description": (
                "Structured bags carried by hand or short handles for a "
                "polished look."
            ),
        },
        1400: {
            "name": "Clutches",
            "slug": "clutches",
            "description": (
                "Compact bags without long straps, ideal for evenings and "
                "minimal carry."
            ),
        },
    }

    BAG_SUBCATEGORY_MAP = {
        # Shoulder Bags
        1: [1200],
        2: [1200],
        3: [1200],
        4: [1200],
        8: [1200],
        12: [1200, 1100],
        13: [1200, 1100],
        14: [1200, 1100],
        # Crossbody Bags
        5: [1100, 1300],
        6: [1100, 1300],
        7: [1100, 1300],
        9: [1100],
        10: [1100],
        11: [1100],
        # Handbags
        15: [1300],
        16: [1300],
        17: [1300],
        # Clutches
        18: [1400],
        19: [1400],
    }

    def handle(self, *args, **options):
        bags_category = self._ensure_bags_category()
        subcategory_map = self._upsert_subcategories(bags_category)
        updated = self._assign_products(bags_category, subcategory_map)
        self.stdout.write(self.style.SUCCESS(
            f"Updated {updated} products with subcategories."
        ))

    def _ensure_bags_category(self) -> Category:
        existing_slug = Category.objects.filter(slug="bags").exclude(
            id=self.BAGS_CATEGORY_ID
        ).first()

        if existing_slug:
            existing_slug.slug = f"bags-old-{existing_slug.id}"
            existing_slug.save(update_fields=["slug"])

        bags_category, created = Category.objects.update_or_create(
            id=self.BAGS_CATEGORY_ID,
            defaults={
                "name": "Bags",
                "slug": "bags",
            },
        )

        if existing_slug:
            Product.objects.filter(category_id=existing_slug.id).update(
                category_id=bags_category.id
            )
            Subcategory.objects.filter(category_id=existing_slug.id).update(
                category_id=bags_category.id
            )

        if created:
            self.stdout.write(self.style.SUCCESS("Created Bags category."))
        return bags_category

    def _upsert_subcategories(self, category: Category) -> dict:
        subcategory_map = {}
        renamed_ids = []
        for subcategory_id, data in self.SUBCATEGORIES.items():
            subcategory, renamed_id = self._ensure_subcategory_id(
                category,
                subcategory_id,
                data["slug"],
            )
            if renamed_id:
                renamed_ids.append(renamed_id)
            subcategory.category = category
            subcategory.name = data["name"]
            subcategory.slug = data["slug"]
            subcategory.description = data["description"]
            subcategory.save()
            subcategory_map[subcategory_id] = subcategory
        if renamed_ids:
            Subcategory.objects.filter(id__in=renamed_ids).delete()
        return subcategory_map

    def _ensure_subcategory_id(
        self,
        category: Category,
        desired_id: int,
        slug: str,
    ) -> tuple[Subcategory, int | None]:
        existing_by_id = Subcategory.objects.filter(id=desired_id).first()
        existing_by_slug = Subcategory.objects.filter(
            category=category,
            slug=slug,
        ).exclude(id=desired_id).first()

        if existing_by_id:
            if existing_by_slug and existing_by_slug.id != existing_by_id.id:
                existing_by_slug.slug = f"{existing_by_slug.slug}-old-{existing_by_slug.id}"
                existing_by_slug.save(update_fields=["slug"])
                return existing_by_id, existing_by_slug.id
            return existing_by_id, None

        if existing_by_slug:
            existing_by_slug.slug = f"{existing_by_slug.slug}-old-{existing_by_slug.id}"
            existing_by_slug.save(update_fields=["slug"])
            new_subcategory = Subcategory.objects.create(
                id=desired_id,
                category=category,
                name=slug.replace("-", " ").title(),
                slug=slug,
            )
            self._repoint_subcategory_id(existing_by_slug.id, desired_id)
            return new_subcategory, existing_by_slug.id

        return Subcategory.objects.create(
            id=desired_id,
            category=category,
            name=slug.replace("-", " ").title(),
            slug=slug,
        ), None

    def _repoint_subcategory_id(self, old_id: int, new_id: int) -> None:
        through_table = Product.subcategories.through._meta.db_table

        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {through_table} SET subcategory_id = %s WHERE subcategory_id = %s",
                [new_id, old_id],
            )

    def _assign_products(self, category: Category, subcategory_map: dict) -> int:
        updated = 0
        products = Product.objects.exclude(variant_image__isnull=True).exclude(
            variant_image=""
        )

        for product in products.iterator():
            bag_number = self._extract_bag_number(product.variant_image)
            if not bag_number:
                continue
            subcategory_ids = self.BAG_SUBCATEGORY_MAP.get(bag_number)
            if not subcategory_ids:
                continue
            subcategories = [
                subcategory_map[sub_id]
                for sub_id in subcategory_ids
                if sub_id in subcategory_map
            ]
            if not subcategories:
                continue
            if product.category_id != category.id:
                product.category_id = category.id
            is_shoulder = 1200 in subcategory_ids
            if is_shoulder:
                product.price = 100
                product.price_new = None
                product.price_old = None
            product.save(update_fields=["category", "price", "price_new", "price_old"])
            product.subcategories.set(subcategories)
            updated += 1

        return updated

    @staticmethod
    def _extract_bag_number(url: str) -> int | None:
        match = re.search(r"bag[\\s_]?([0-9]+)", url)
        if not match:
            return None
        return int(match.group(1))
