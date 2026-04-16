"""Reset bags products and variants from curated payload."""
from __future__ import annotations

import os
import unicodedata
from decimal import Decimal
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from src.infrastructure.db.models.catalog import Category, Product, ProductVariant, Subcategory
from src.infrastructure.db.seed.bags_products_payload import (
    PRODUCTS_PAYLOAD,
    PRODUCT_SUBCATEGORY_MAP,
)


def _normalize_name(value: str) -> str:
    """Lowercase and strip accents for robust key matching."""
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower().strip()


class Command(BaseCommand):
    help = "Reset bags products/variants from payload (supports dry-run)."

    SUPABASE_PROJECT = "uvfwhmvqxolxabmedsho"
    SUPABASE_BUCKET = "jcd"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply changes. Default is dry-run.",
        )
        parser.add_argument(
            "--keep-extra-products",
            action="store_true",
            help="Do not delete extra existing bag products not in payload.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        keep_extra = options["keep_extra_products"]
        self.stdout.write(
            self.style.WARNING(
                "Running in APPLY mode." if apply_changes else "Running in DRY-RUN mode."
            )
        )

        bags_category = Category.objects.filter(slug="bags").first()
        if not bags_category:
            raise CommandError("Category with slug='bags' was not found.")

        subcategories_by_slug = {
            sub.slug: sub
            for sub in Subcategory.objects.filter(category=bags_category)
        }
        missing_subcategories = {
            slug
            for slugs in PRODUCT_SUBCATEGORY_MAP.values()
            for slug in slugs
            if slug not in subcategories_by_slug
        }
        if missing_subcategories:
            raise CommandError(
                "Missing required subcategories under bags: "
                + ", ".join(sorted(missing_subcategories))
            )

        payload_names = {item["bagName"] for item in PRODUCTS_PAYLOAD}
        existing_products = Product.objects.filter(category=bags_category)
        existing_by_name = {product.name: product for product in existing_products}
        unknown_existing = sorted(
            [product.name for product in existing_products if product.name not in payload_names]
        )

        s3_client = self._build_s3_client()
        missing_folders: List[str] = []
        missing_images: List[str] = []
        created_products = 0
        updated_products = 0
        created_variants = 0
        deleted_variants = 0
        deleted_products = 0

        with transaction.atomic():
            for item in PRODUCTS_PAYLOAD:
                bag_name = item["bagName"]
                bag_description = item.get("bagDescription")
                subcategory_slugs = PRODUCT_SUBCATEGORY_MAP.get(bag_name, [])
                subcategories = [subcategories_by_slug[slug] for slug in subcategory_slugs]

                existing = existing_by_name.get(bag_name)
                if existing:
                    product = existing
                    updated_products += 1
                else:
                    product = Product(
                        category=bags_category,
                        name=bag_name,
                        price=Decimal("199.99"),
                        availability=Product.AvailabilityChoices.IN_STOCK,
                        currency=Product.CurrencyChoices.USD,
                        brand="Jasmine",
                    )
                    created_products += 1

                product.description = bag_description
                if not product.brand:
                    product.brand = "Jasmine"
                if not product.price:
                    product.price = Decimal("199.99")
                product.save()
                product.subcategories.set(subcategories)

                old_variants_qs = ProductVariant.objects.filter(product=product)
                deleted_variants += old_variants_qs.count()
                old_variants_qs.delete()

                first_variant_image: Optional[str] = None
                sorted_variants = sorted(
                    item.get("variants", []),
                    key=lambda variant: variant.get("folder", ""),
                )
                for sort_index, variant in enumerate(sorted_variants):
                    folder = variant.get("folder")
                    image_url = self._resolve_first_image_url(s3_client, folder)
                    if image_url is None:
                        if folder:
                            missing_images.append(folder)
                        else:
                            missing_folders.append(f"{bag_name}:<empty>")
                    elif first_variant_image is None:
                        first_variant_image = image_url

                    ProductVariant.objects.create(
                        product=product,
                        folder=folder,
                        color=variant.get("color"),
                        material=variant.get("material"),
                        cord_diameter=variant.get("cordDiameter"),
                        cord_type=variant.get("cordType"),
                        description=variant.get("description"),
                        care=variant.get("care"),
                        handles=variant.get("handles"),
                        name="color",
                        value=variant.get("color") or "",
                        image_url=image_url,
                        sort_order=sort_index,
                    )
                    created_variants += 1

                product.variant_image = first_variant_image
                product.variant_color_name = (
                    sorted_variants[0].get("color") if sorted_variants else product.variant_color_name
                )
                product.save(update_fields=["variant_image", "variant_color_name", "updated_at"])

            if not keep_extra and unknown_existing:
                deleted_products += Product.objects.filter(
                    category=bags_category,
                    name__in=unknown_existing,
                ).count()
                Product.objects.filter(
                    category=bags_category,
                    name__in=unknown_existing,
                ).delete()

            if not apply_changes:
                transaction.set_rollback(True)

        summary = [
            f"created_products={created_products}",
            f"updated_products={updated_products}",
            f"deleted_products={deleted_products}",
            f"deleted_variants={deleted_variants}",
            f"created_variants={created_variants}",
        ]
        self.stdout.write(self.style.SUCCESS("Reset summary: " + ", ".join(summary)))

        if unknown_existing and keep_extra:
            self.stdout.write(
                self.style.WARNING(
                    "Existing bag products retained (--keep-extra-products): "
                    + ", ".join(unknown_existing)
                )
            )

        if missing_folders:
            self.stdout.write(
                self.style.WARNING("Variants with missing folder value: " + ", ".join(missing_folders))
            )
        if missing_images:
            self.stdout.write(
                self.style.WARNING(
                    "No image found in folders: " + ", ".join(sorted(set(missing_images)))
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Applied successfully." if apply_changes else "Dry-run complete (rolled back)."
            )
        )

    def _build_s3_client(self):
        access_key = os.environ.get("SUPABASE_S3_ACCESS_KEY")
        secret_key = os.environ.get("SUPABASE_S3_SECRET_KEY")
        if not access_key or not secret_key:
            self.stdout.write(
                self.style.WARNING(
                    "Supabase S3 credentials are missing; image resolution will be skipped."
                )
            )
            return None

        endpoint = (
            f"https://{self.SUPABASE_PROJECT}.supabase.co/storage/v1/s3"
        )
        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
        )

    def _resolve_first_image_url(self, s3_client, folder: Optional[str]) -> Optional[str]:
        if not folder or s3_client is None:
            return None

        prefix = folder.strip("/") + "/"
        try:
            response = s3_client.list_objects_v2(
                Bucket=self.SUPABASE_BUCKET,
                Prefix=prefix,
            )
        except (BotoCoreError, ClientError) as error:
            self.stdout.write(
                self.style.WARNING(f"Could not list objects for {folder}: {error}")
            )
            return None

        contents = response.get("Contents", [])
        image_keys = []
        for obj in contents:
            key = obj.get("Key") or ""
            if key.endswith("/"):
                continue
            lower = key.lower()
            if lower.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
                image_keys.append(key)

        if not image_keys:
            return None

        first_key = sorted(image_keys)[0]
        return (
            "https://"
            f"{self.SUPABASE_PROJECT}.supabase.co/storage/v1/object/public/"
            f"{self.SUPABASE_BUCKET}/{first_key}"
        )
