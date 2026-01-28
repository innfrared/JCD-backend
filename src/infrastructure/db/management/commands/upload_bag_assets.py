import os
import re
from pathlib import Path
from urllib.parse import quote

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand

from src.infrastructure.db.models.catalog import Product, ProductVariant
from src.infrastructure.db.models.homepage import HomeSection


class Command(BaseCommand):
    help = "Upload bag.import.assets images to Supabase Storage and update URLs"

    def handle(self, *args, **options):
        if not settings.USE_SUPABASE_S3_MEDIA:
            self.stderr.write(
                self.style.ERROR(
                    "USE_SUPABASE_S3_MEDIA is False. Enable it to upload."
                )
            )
            return

        required = [
            "AWS_S3_ENDPOINT_URL",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_STORAGE_BUCKET_NAME",
            "MEDIA_URL",
        ]
        missing = [key for key in required if not getattr(settings, key, None)]
        if missing:
            self.stderr.write(
                self.style.ERROR(
                    f"Missing required settings: {', '.join(missing)}"
                )
            )
            return

        assets_dir = Path(settings.BASE_DIR) / "bag.import.assets"
        if not assets_dir.exists():
            self.stderr.write(
                self.style.ERROR(f"Assets directory not found: {assets_dir}")
            )
            return

        s3_client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

        uploaded = 0
        for file_path in assets_dir.rglob("*.jpg"):
            rel_path = file_path.relative_to(assets_dir)
            key = self._to_supabase_key(rel_path)
            s3_client.upload_file(
                str(file_path),
                settings.AWS_STORAGE_BUCKET_NAME,
                key,
                ExtraArgs={"ContentType": "image/jpeg"},
            )
            uploaded += 1

        self.stdout.write(self.style.SUCCESS(f"Uploaded {uploaded} images."))

        updated = 0

        updated += self._update_url_field(
            Product,
            "variant_image",
        )
        updated += self._update_url_field(
            ProductVariant,
            "image_url",
        )
        updated += self._update_url_field(
            HomeSection,
            "main_image",
        )

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} URLs."))

    @staticmethod
    def _to_supabase_key(rel_path: Path) -> str:
        path = str(rel_path).replace(os.sep, "/")
        normalized = Command._normalize_bag_path(path)
        return normalized.lstrip("/")

    @staticmethod
    def _normalize_bag_path(path: str) -> str:
        clean = path.lstrip("/")
        if clean.startswith("bags/"):
            clean = clean[len("bags/") :]
        match = re.match(r"^bag[\s_]?(\d+)/(.*)$", clean)
        if match:
            number, rest = match.groups()
            return f"bag{number}/{rest}"
        return clean

    def _update_url_field(self, model, field_name: str) -> int:
        updated = 0
        for obj in model.objects.all():
            value = getattr(obj, field_name)
            if not value:
                continue
            if value.startswith(settings.MEDIA_URL):
                continue
            local_part = None
            if value.startswith("/media/"):
                local_part = value.replace("/media/", "", 1).lstrip("/")
            elif "/media/" in value:
                local_part = value.split("/media/", 1)[1].lstrip("/")
            if not local_part:
                continue
            key = self._to_supabase_key(Path(local_part))
            public_url = settings.MEDIA_URL + quote(key, safe="/")
            if public_url != value:
                setattr(obj, field_name, public_url)
                obj.save(update_fields=[field_name])
                updated += 1
        return updated
