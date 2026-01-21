from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import F
from core.models import Order
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Cancels orders that have been awaiting bank transfer for more than 48 hours and restores stock.'

    def handle(self, *args, **options):
        # Define the threshold (48 hours ago)
        threshold = timezone.now() - timedelta(hours=48)
        
        # Find orders that are still awaiting bank transfer and were created before the threshold
        orders_to_cancel = Order.objects.filter(
            status='AWAITING_BANK_TRANSFER',
            created_at__lt=threshold
        )
        
        count = 0
        if not orders_to_cancel.exists():
            self.stdout.write(self.style.SUCCESS('No expired orders found.'))
            return

        for order in orders_to_cancel:
            try:
                # Restore stock for physical products
                for item in order.items.all():
                    if item.product and item.product.product_type == 'physical':
                        # Use F expression to avoid race conditions
                        item.product.stock = F('stock') + item.quantity
                        item.product.save(update_fields=['stock'])
                
                order.status = 'CANCELLED'
                order.save(update_fields=['status'])
                
                logger.info(f"Auto-cancelled expired bank transfer order #{order.order_id}")
                count += 1
            except Exception as e:
                logger.error(f"Error cancelling order {order.order_id}: {e}")
                self.stderr.write(self.style.ERROR(f"Error cancelling order {order.order_id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f'Successfully cancelled {count} expired orders.'))
