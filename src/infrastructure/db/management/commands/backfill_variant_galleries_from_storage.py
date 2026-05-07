"""Backfill ProductVariantImage rows by listing images in each variant folder."""
from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from src.infrastructure.db.models.catalog import ProductVariant, ProductVariantImage


class Command(BaseCommand):
    help = (
        "Build ProductVariantImage galleries from Supabase storage folders "
        "derived from ProductVariant.image_url."
    )

    IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply changes. Default is dry-run.",
        )
        parser.add_argument(
            "--variant-id",
            type=int,
            default=None,
            help="Limit to one variant id for debugging.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        variant_id = options["variant_id"]
        self.stdout.write(
            self.style.WARNING(
                "Running in APPLY mode." if apply_changes else "Running in DRY-RUN mode."
            )
        )

        s3_client = self._build_s3_client()
        if s3_client is None:
            raise CommandError(
                "Supabase S3 credentials are missing. "
                "Set SUPABASE_S3_ACCESS_KEY and SUPABASE_S3_SECRET_KEY."
            )

        variants_qs = ProductVariant.objects.exclude(image_url__isnull=True).exclude(
            image_url=""
        )
        if variant_id:
            variants_qs = variants_qs.filter(id=variant_id)

        variants = list(variants_qs.order_by("id"))
        self.stdout.write(f"Scanning variants: {len(variants)}")

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        with transaction.atomic():
            for variant in variants:
                parsed = self._parse_public_url(variant.image_url)
                if parsed is None:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"[variant={variant.id}] Could not parse URL: {variant.image_url}"
                        )
                    )
                    continue

                base_url, bucket, key = parsed
                prefix = key.rsplit("/", 1)[0] + "/" if "/" in key else ""
                image_keys = self._list_image_keys(s3_client, bucket=bucket, prefix=prefix)
                if image_keys is None:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"[variant={variant.id}] Failed listing prefix: {prefix}"
                        )
                    )
                    continue
                if not image_keys:
                    skipped_count += 1
                    continue

                created, updated = self._upsert_variant_gallery(
                    variant=variant,
                    base_public_url=base_url,
                    listed_keys=image_keys,
                    current_key=key,
                )
                created_count += created
                updated_count += updated

            if not apply_changes:
                transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                "Backfill summary: "
                f"created={created_count}, updated={updated_count}, "
                f"skipped={skipped_count}, errors={error_count}"
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
            return None

        # Project id is stable in existing catalog import tooling.
        endpoint = "https://uvfwhmvqxolxabmedsho.supabase.co/storage/v1/s3"
        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
        )

    def _parse_public_url(self, image_url: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse:
        https://<project>.supabase.co/storage/v1/object/public/<bucket>/<key>
        -> (base_public_url, bucket, key)
        """
        parsed = urlparse(image_url)
        if not parsed.scheme or not parsed.netloc:
            return None
        marker = "/storage/v1/object/public/"
        path = parsed.path
        if marker not in path:
            return None
        tail = path.split(marker, 1)[1].lstrip("/")
        if "/" not in tail:
            return None
        bucket, key = tail.split("/", 1)
        if not bucket or not key:
            return None
        base_public_url = f"{parsed.scheme}://{parsed.netloc}{marker}{bucket}/"
        return base_public_url, bucket, key

    def _list_image_keys(
        self, s3_client, *, bucket: str, prefix: str
    ) -> Optional[List[str]]:
        keys: List[str] = []
        continuation_token = None
        try:
            while True:
                kwargs: Dict[str, object] = {"Bucket": bucket, "Prefix": prefix}
                if continuation_token:
                    kwargs["ContinuationToken"] = continuation_token
                response = s3_client.list_objects_v2(**kwargs)
                for obj in response.get("Contents", []):
                    key = (obj.get("Key") or "").strip()
                    if not key or key.endswith("/"):
                        continue
                    lower = key.lower()
                    if lower.endswith(self.IMAGE_EXTENSIONS):
                        keys.append(key)
                if not response.get("IsTruncated"):
                    break
                continuation_token = response.get("NextContinuationToken")
        except (BotoCoreError, ClientError):
            return None
        return sorted(set(keys))

    def _upsert_variant_gallery(
        self,
        *,
        variant: ProductVariant,
        base_public_url: str,
        listed_keys: List[str],
        current_key: str,
    ) -> Tuple[int, int]:
        created = 0
        updated = 0
        public_urls = [f"{base_public_url}{key}" for key in listed_keys]
        primary_url = f"{base_public_url}{current_key}" if current_key in listed_keys else public_urls[0]

        existing_by_url = {
            img.image_url: img
            for img in ProductVariantImage.objects.filter(variant=variant)
        }

        for sort_order, url in enumerate(public_urls):
            is_primary = url == primary_url
            row = existing_by_url.get(url)
            if row is None:
                ProductVariantImage.objects.create(
                    variant=variant,
                    image_url=url,
                    alt="",
                    sort_order=sort_order,
                    is_primary=is_primary,
                )
                created += 1
                continue

            fields_to_update: List[str] = []
            if row.sort_order != sort_order:
                row.sort_order = sort_order
                fields_to_update.append("sort_order")
            if row.is_primary != is_primary:
                row.is_primary = is_primary
                fields_to_update.append("is_primary")
            if fields_to_update:
                row.save(update_fields=fields_to_update)
                updated += 1

        return created, updated

