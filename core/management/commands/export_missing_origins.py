from django.core.management.base import BaseCommand
import csv
from core.models import Product


class Command(BaseCommand):
    help = 'List products missing origin_country. Use --export <path> to export CSV.'

    def add_arguments(self, parser):
        parser.add_argument('--export', '-e', type=str, help='Path to export CSV file')
        parser.add_argument('--limit', '-l', type=int, default=0, help='Limit number of products to show (0=all)')
        parser.add_argument('--preview', action='store_true', help='Show a preview (first 20) and exit')

    def handle(self, *args, **options):
        qs = Product.objects.filter(origin_country__isnull=True)
        count = qs.count()
        self.stdout.write(self.style.SUCCESS(f'Products missing origin_country: {count}'))

        if options.get('preview'):
            for p in qs[:20]:
                self.stdout.write(f'{p.id}\t{p.name}\t{p.vendor_id}\t{p.vendor}')
            return

        if options.get('export'):
            path = options['export']
            with open(path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['id', 'name', 'vendor_id', 'vendor_name', 'is_active'])
                for p in qs:
                    writer.writerow([p.id, p.name, p.vendor_id, str(p.vendor), p.is_active])
            self.stdout.write(self.style.SUCCESS(f'Exported {qs.count()} rows to {path}'))
            return

        limit = options.get('limit') or 0
        q = qs if limit == 0 else qs[:limit]
        for p in q:
            self.stdout.write(f'{p.id}\t{p.name}\t{p.vendor_id}\t{p.vendor}')
