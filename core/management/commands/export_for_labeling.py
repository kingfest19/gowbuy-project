from django.core.management.base import BaseCommand
import csv
from core.models import Product

class Command(BaseCommand):
    help = 'Export products for external labeling (CSV).'

    def add_arguments(self, parser):
        parser.add_argument('--output', '-o', required=True, help='Path to output CSV file')
        parser.add_argument('--only-missing', action='store_true', help='Only export products missing origin_country')
        parser.add_argument('--limit', type=int, default=0, help='Limit number of products (0=all)')

    def handle(self, *args, **options):
        qs = Product.objects.all().select_related('vendor')
        if options.get('only_missing'):
            qs = qs.filter(origin_country__isnull=True)
        limit = options.get('limit') or 0
        if limit > 0:
            qs = qs[:limit]

        path = options['output']
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['product_id','name','vendor','vendor_id','description','origin_country'])
            for p in qs:
                writer.writerow([p.id, p.name, str(p.vendor), p.vendor_id, p.description or '', p.origin_country or ''])
        self.stdout.write(self.style.SUCCESS(f'Exported {qs.count()} products to {path}'))
