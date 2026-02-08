from django.core.management.base import BaseCommand
from core.ml.origin_trainer import predict_products

class Command(BaseCommand):
    help = 'Use trained origin model to predict and (optionally) apply suggested origin_country on products.'

    def add_arguments(self, parser):
        parser.add_argument('--model-dir', default='core/ml/models', help='Directory where model artifacts are stored')
        parser.add_argument('--only-missing', action='store_true', help='Only predict for products missing origin_country')
        parser.add_argument('--limit', type=int, default=0, help='Limit number of products processed (0=all)')
        parser.add_argument('--apply', action='store_true', help='Persist suggested origin to product suggested fields')
        parser.add_argument('--min-confidence', type=float, default=0.5, help='Minimum confidence to accept suggestion')

    def handle(self, *args, **options):
        try:
            summary = predict_products(model_dir=options['model_dir'], only_missing=options.get('only_missing', True), limit=options.get('limit', 0), apply=options.get('apply', False), min_confidence=options.get('min_confidence', 0.5))
            self.stdout.write(self.style.SUCCESS('Prediction complete: %s' % summary))
        except Exception as e:
            self.stderr.write('Prediction failed: %s' % e)
            raise
