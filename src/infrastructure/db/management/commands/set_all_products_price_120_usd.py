from decimal import Decimal

from django.core.management.base import BaseCommand

from src.infrastructure.db.models.catalog import Product


class Command(BaseCommand):
    help = "Set all products price to 120 USD."

    PRICE = Decimal("120.00")
    CURRENCY = Product.CurrencyChoices.USD

    def handle(self, *args, **options):
        updated = Product.objects.update(
            price=self.PRICE,
            price_new=None,
            price_old=None,
            currency=self.CURRENCY,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Updated {updated} products to price {self.PRICE} {self.CURRENCY}."
            )
        )
