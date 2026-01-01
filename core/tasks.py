"""Helper tasks for integration tests and app functionality."""
import logging
import os
from celery import shared_task
from django.core.files.base import ContentFile
from .ai_services_gemini import enhance_image_with_gemini, remove_image_background

logger = logging.getLogger(__name__)


@shared_task(name='celery.ping')
def ping():
    """Simple task that just returns 'pong'."""
    return 'pong'

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3, ignore_result=True)
def process_image_enhancement(self, image_id: int):
    """
    Background task to enhance a product image using AI.
    """
    # Import models inside task to avoid potential circular imports during app startup
    from .models import ProductImage, Notification
    
    vendor_user = None
    try:
        # Use select_related for a more efficient database query
        image_instance = ProductImage.objects.select_related('product__vendor__user').get(id=image_id)
        product = image_instance.product
        vendor_user = product.vendor.user
    except ProductImage.DoesNotExist:
        logger.error(f"Task {self.name} aborted: ProductImage with id={image_id} not found. No retry will be attempted.")
        return # Stop execution if the image doesn't exist

    try:
        logger.info(f"Starting AI enhancement for image {image_id} of product '{product.name}'.")
        
        with image_instance.image.open('rb') as f:
            image_bytes = f.read()

        enhanced_bytes = enhance_image_with_gemini(image_bytes)
        
        if enhanced_bytes:
            new_image_file = ContentFile(enhanced_bytes, name=f"enhanced_{os.path.basename(image_instance.image.name)}")
            ProductImage.objects.create(
                product=product, 
                image=new_image_file, 
                alt_text=f"Enhanced version of {image_instance.alt_text or 'product image'}"
            )
            # Notify the vendor upon completion
            Notification.objects.create(
                recipient=vendor_user,
                message=f"AI enhancement for your product '{product.name}' is complete. A new image has been added to its gallery."
            )
            logger.info(f"Successfully enhanced and saved new image for product '{product.name}'.")
        else:
            # This will be caught by the generic Exception and trigger a retry
            raise ValueError("AI enhancement failed to return image data.")

    except Exception as e:
        logger.error(f"Task {self.name} failed for image_id={image_id} (attempt {self.request.retries + 1}): {e}", exc_info=True)
        # Notify the user only on the final failure after all retries are exhausted.
        if self.request.retries >= self.max_retries:
            logger.warning(f"Task {self.name} for image_id={image_id} has reached max retries. Notifying user of failure.")
            if vendor_user:
                Notification.objects.create(
                    recipient=vendor_user,
                    message=f"AI enhancement for your product '{product.name}' failed after multiple attempts. Please try again later or contact support."
                )
        # Re-raise the exception to let Celery handle the retry.
        raise

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3, ignore_result=True)
def process_background_removal(self, image_id: int):
    """
    Background task to remove background from a product image.
    """
    from .models import ProductImage, Notification

    vendor_user = None
    try:
        image_instance = ProductImage.objects.select_related('product__vendor__user').get(id=image_id)
        product = image_instance.product
        vendor_user = product.vendor.user
    except ProductImage.DoesNotExist:
        logger.error(f"Task {self.name} aborted: ProductImage with id={image_id} not found. No retry will be attempted.")
        return

    try:
        logger.info(f"Starting background removal for image {image_id} of product '{product.name}'.")

        with image_instance.image.open('rb') as f:
            image_bytes = f.read()

        bg_removed_bytes = remove_image_background(image_bytes)

        if bg_removed_bytes:
            new_image_file = ContentFile(bg_removed_bytes, name=f"no_bg_{os.path.basename(image_instance.image.name)}")
            ProductImage.objects.create(
                product=product, 
                image=new_image_file, 
                alt_text=f"Background removed from {image_instance.alt_text or 'product image'}"
            )
            # Notify the vendor upon completion
            Notification.objects.create(
                recipient=vendor_user,
                message=f"Background removal for your product '{product.name}' is complete. A new image has been added to its gallery."
            )
            logger.info(f"Successfully removed background and saved new image for product '{product.name}'.")
        else:
            # This will trigger a retry
            raise ValueError("Background removal failed to return image data.")

    except Exception as e:
        logger.error(f"Task {self.name} failed for image_id={image_id} (attempt {self.request.retries + 1}): {e}", exc_info=True)
        # Notify the user only on the final failure.
        if self.request.retries >= self.max_retries:
            logger.warning(f"Task {self.name} for image_id={image_id} has reached max retries. Notifying user of failure.")
            if vendor_user:
                Notification.objects.create(
                    recipient=vendor_user,
                    message=f"Background removal for your product '{product.name}' failed after multiple attempts. Please try again later or contact support."
                )
        raise