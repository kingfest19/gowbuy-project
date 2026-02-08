from django.core.management.base import BaseCommand
from django.conf import settings
import logging
from core.ml.origin_trainer import train_model

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Train an origin inference LightGBM model using labeled OriginLabel data.'

    def add_arguments(self, parser):
        parser.add_argument('--output-dir', default='core/ml/models', help='Directory to save model artifacts')
        parser.add_argument('--min-samples', type=int, default=5, help='Minimum samples per class to include')
        parser.add_argument('--test-size', type=float, default=0.2, help='Test split size')

    def handle(self, *args, **options):
        out = options['output_dir']
        try:
            summary = train_model(output_dir=out, min_samples_per_class=options['min_samples'], test_size=options['test_size'])
            self.stdout.write(self.style.SUCCESS('Training completed. Artifacts saved to %s' % out))
            # Print simple per-class metrics
            for cls, stats in summary.get('report', {}).items():
                if isinstance(stats, dict) and 'f1-score' in stats:
                    self.stdout.write(f"{cls}: precision={stats['precision']:.3f}, recall={stats['recall']:.3f}, f1={stats['f1-score']:.3f}")
        except Exception as e:
            logger.exception('Training failed')
            self.stderr.write('Training failed: %s' % e)
            raise
