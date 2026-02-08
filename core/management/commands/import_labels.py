from django.core.management.base import BaseCommand
import csv
from core.models import Product, OriginLabel
from django.contrib.auth import get_user_model
User = get_user_model()

class Command(BaseCommand):
    help = 'Import origin labels from CSV. Columns: product_id,label_country,confidence,note,source,labeler_username'

    def add_arguments(self, parser):
        parser.add_argument('--input', '-i', required=True, help='Path to input CSV file')
        parser.add_argument('--apply', action='store_true', help='Apply labels to suggested_origin_country')

    def handle(self, *args, **options):
        path = options['input']
        applied = 0
        created = 0
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get('product_id')
                if not pid:
                    continue
                try:
                    p = Product.objects.get(pk=pid)
                except Product.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'Product {pid} not found. Skipping.'))
                    continue
                country = row.get('label_country') or None
                confidence = row.get('confidence') or None
                note = row.get('note') or ''
                source = row.get('source') or 'import'
                labeler = None
                labeler_username = row.get('labeler_username')
                if labeler_username:
                    try:
                        labeler = User.objects.get(username=labeler_username)
                    except User.DoesNotExist:
                        labeler = None
                ol = OriginLabel.objects.create(product=p, label_country=country or None, confidence=float(confidence) if confidence else None, note=note, source=source, labeler=labeler)
                created += 1
                if options.get('apply') and country:
                    p.suggested_origin_country = country
                    p.origin_confidence = float(confidence) if confidence else None
                    p.origin_inferred_by = 'manual'
                    p.origin_inference_metadata = {'source': 'import'}
                    p.origin_inferred_at = ol.created_at
                    p.origin_inference_status = 'suggested'
                    p.save()
                    applied += 1
        self.stdout.write(self.style.SUCCESS(f'Imported {created} labels. Applied: {applied}'))