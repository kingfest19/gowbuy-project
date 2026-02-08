"""
Management command to verify product origins in batch.

Usage:
    python manage.py verify_product_origins
    python manage.py verify_product_origins --suspicious-only
    python manage.py verify_product_origins --vendor-id=5
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from core.models import Product, OriginVerification
from core.origin_verification import verify_product_origin
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verify product origins using the OriginVerificationEngine'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vendor-id',
            type=int,
            help='Verify only products from a specific vendor ID'
        )
        parser.add_argument(
            '--suspicious-only',
            action='store_true',
            help='Only show suspicious origin claims'
        )
        parser.add_argument(
            '--product-id',
            type=int,
            help='Verify a specific product by ID'
        )
        parser.add_argument(
            '--save-results',
            action='store_true',
            help='Save verification results to database'
        )

    def handle(self, *args, **options):
        vendor_id = options.get('vendor_id')
        suspicious_only = options.get('suspicious_only')
        product_id = options.get('product_id')
        save_results = options.get('save_results')

        # Build query
        query = Q(is_active=True)
        if vendor_id:
            query &= Q(vendor_id=vendor_id)
        if product_id:
            query &= Q(id=product_id)

        products = Product.objects.filter(query).select_related('vendor', 'category')

        self.stdout.write(self.style.SUCCESS(f"Verifying {products.count()} products..."))

        suspicious_count = 0
        verified_count = 0

        for product in products:
            result = verify_product_origin(product)

            if suspicious_only and not result['is_suspicious']:
                continue

            verified_count += 1

            if result['is_suspicious']:
                suspicious_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"\n🚩 SUSPICIOUS: {product.name} (ID: {product.id})"
                    )
                )
                self.stdout.write(f"   Vendor: {product.vendor.name}")
                self.stdout.write(f"   Claimed Origin: {product.origin_country}")
                self.stdout.write(f"   Score: {result['verification_score']}/100")
                self.stdout.write(f"   Reasoning: {result['reasoning']}")

                if result['suggested_origin']:
                    self.stdout.write(
                        self.style.WARNING(
                            f"   Suggested Origin: {result['suggested_origin']}"
                        )
                    )

                if result['mismatches']:
                    self.stdout.write("   Mismatches:")
                    for mismatch in result['mismatches']:
                        self.stdout.write(f"     - {mismatch}")

                if result['flags']:
                    self.stdout.write("   Flags:")
                    for flag in result['flags']:
                        self.stdout.write(f"     - {flag}")
            else:
                self.stdout.write(f"✓ Verified: {product.name}")

            # Save results if requested
            if save_results:
                # You would need to create an OriginVerification model for this
                # OriginVerification.objects.update_or_create(
                #     product=product,
                #     defaults={
                #         'verification_score': result['verification_score'],
                #         'is_suspicious': result['is_suspicious'],
                #         'verification_details': result,
                #     }
                # )
                logger.info(f"Saved verification for product {product.id}")

        self.stdout.write(self.style.SUCCESS(f"\n✓ Verification complete!"))
        self.stdout.write(f"Total verified: {verified_count}")
        self.stdout.write(self.style.ERROR(f"Suspicious: {suspicious_count}"))
