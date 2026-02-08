from django.core.management.base import BaseCommand
from django.utils import timezone
from django_countries import countries
from core.models import Product
import re

COUNTRY_NAME_REGEX = re.compile(r"made in\s+([A-Za-z \-]+)", re.IGNORECASE)


def find_country_code_by_name(name):
    name = name.strip().lower()
    for code, display in countries:
        if name in display.lower() or display.lower() in name:
            return code
    return None


class Command(BaseCommand):
    help = 'Generate rule-based origin suggestions for products. Use --apply to persist suggestions.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Persist suggestions to DB (suggested fields only)')
        parser.add_argument('--limit', type=int, default=0, help='Limit number of products to process (0=all)')
        parser.add_argument('--only-missing', action='store_true', help='Only process products missing origin_country')

    def handle(self, *args, **options):
        qs = Product.objects.all().select_related('vendor')
        if options.get('only_missing'):
            qs = qs.filter(origin_country__isnull=True)
        limit = options.get('limit') or 0
        if limit > 0:
            qs = qs[:limit]

        applied = 0
        suggested_count = 0
        for p in qs:
            suggestion = None
            confidence = None
            metadata = {}

            # Heuristic 1: look for "made in X" in description
            if p.description:
                m = COUNTRY_NAME_REGEX.search(p.description)
                if m:
                    name = m.group(1)
                    code = find_country_code_by_name(name)
                    if code:
                        suggestion = code
                        confidence = 0.95
                        metadata['rule'] = 'made_in_pattern'
                        metadata['match_text'] = name

            # Heuristic 2: vendor location
            if not suggestion and getattr(p, 'vendor', None):
                v_country = getattr(p.vendor, 'location_country', None)
                if v_country:
                    # try to map to code
                    code = find_country_code_by_name(v_country) or v_country
                    suggestion = code
                    confidence = 0.6
                    metadata['rule'] = 'vendor_location'

            # Heuristic 3: keywords_for_ai contains country name
            if not suggestion and p.keywords_for_ai:
                for token in (t.strip() for t in p.keywords_for_ai.split(',')):
                    code = find_country_code_by_name(token)
                    if code:
                        suggestion = code
                        confidence = 0.7
                        metadata['rule'] = 'keywords'
                        metadata['token'] = token
                        break

            if suggestion:
                suggested_count += 1
                self.stdout.write(f'Product {p.id} suggested {suggestion} (rule={metadata.get("rule")}, conf={confidence})')
                if options.get('apply'):
                    p.suggested_origin_country = suggestion
                    p.origin_confidence = confidence
                    p.origin_inferred_by = 'rule'
                    p.origin_inference_metadata = metadata
                    p.origin_inferred_at = timezone.now()
                    p.origin_inference_status = 'suggested'
                    p.save(update_fields=['suggested_origin_country','origin_confidence','origin_inferred_by','origin_inference_metadata','origin_inferred_at','origin_inference_status'])
                    applied += 1
        self.stdout.write(self.style.SUCCESS(f'Suggested: {suggested_count}'))
        if options.get('apply'):
            self.stdout.write(self.style.SUCCESS(f'Applied: {applied}'))
