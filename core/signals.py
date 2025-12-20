# c:\Users\Hp\Desktop\Nexus\core\signals.py
from django.dispatch import Signal
from django.db.models.signals import post_save, pre_save
from django.contrib.auth.signals import user_logged_in
from django.db import transaction as db_transaction
from django.urls import reverse # For generating notification links 
from django.dispatch import receiver # Ensure receiver is imported
from django.conf import settings # To get commission rate
from decimal import Decimal # For precise calculations
from .models import Order, DeliveryTask, Vendor, Notification, RiderApplication, Transaction, PayoutRequest, SecurityLog, ProductQuestion, ProductReview
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from django.contrib.auth import get_user_model # For notifying staff
from django.core.cache import cache # Import cache for invalidation
import logging, uuid

logger = logging.getLogger(__name__) # This is already present, just for context

order_placed = Signal()

# We need to store the old status before saving to check if it changed
@receiver(pre_save, sender=DeliveryTask)
def save_old_delivery_task_status(sender, instance, **kwargs):
    """
    Saves the original status of a DeliveryTask before it's saved.
    """
    if instance.pk: # Only for existing instances
        try:
            instance._original_status = DeliveryTask.objects.get(pk=instance.pk).status
        except DeliveryTask.DoesNotExist:
            instance._original_status = None # New instance or error
    else: # For new instances, there's no original status from DB
        instance._original_status = None

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Logs successful user login events.
    """
    ip_address = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    SecurityLog.objects.create(
        user=user,
        action='login_success',
        ip_address=ip_address,
        user_agent=user_agent,
        details=f"User '{user.username}' logged in successfully."
    )

@receiver(post_save, sender=Order)
def create_delivery_task_for_order(sender, instance, created, **kwargs):
    """
    Signal handler to create a DeliveryTask when an Order is ready for delivery.
    """
    order = instance
    # Conditions for creating a delivery task:
    # 1. Order has physical products.
    # 2. Order status indicates it's ready for processing/delivery (e.g., 'PROCESSING').
    # 3. A delivery task for this order doesn't already exist.
    # We now check if there are any physical items fulfilled by Nexus
    nexus_fulfilled_physical_items = order.items.filter(
        product__product_type='physical',
        fulfillment_method='nexus'
    )

    # Create a delivery task ONLY if there are Nexus-fulfilled physical items
    # AND the order status is appropriate AND a task doesn't already exist
    if nexus_fulfilled_physical_items.exists() and \
       order.status == 'PROCESSING' and \
       not DeliveryTask.objects.filter(order=order).exists(): # Check if a task exists for this order

        # Determine pickup address (simplistic: from the first vendor of a Nexus-fulfilled physical product)
        pickup_address_str = "Pickup address not found for Nexus fulfillment."
        pickup_lat, pickup_lng = None, None
        first_nexus_fulfilled_item = nexus_fulfilled_physical_items.first()
        if first_nexus_fulfilled_item and first_nexus_fulfilled_item.product and first_nexus_fulfilled_item.product.vendor:
            vendor = first_nexus_fulfilled_item.product.vendor
            # Construct a simple address string from the vendor's location
            pickup_address_str = f"{vendor.name}, {vendor.location_city or ''}, {vendor.location_country or ''}".strip(", ")
            if pickup_address_str == ",": pickup_address_str = "Vendor address details incomplete for pickup."
            pickup_lat = vendor.latitude
            pickup_lng = vendor.longitude


        # Use the platform_delivery_fee from the Order model for Nexus tasks
        task_delivery_fee = order.platform_delivery_fee if order.platform_delivery_fee is not None else Decimal('0.00')
        
        delivery_lat, delivery_lng = None, None
        if order.shipping_address:
            delivery_lat = order.shipping_address.latitude
            delivery_lng = order.shipping_address.longitude

        DeliveryTask.objects.create(
            order=order,
            pickup_address_text=pickup_address_str,
            pickup_latitude=pickup_lat,
            pickup_longitude=pickup_lng,
            delivery_address_text=order.shipping_address_text or "Delivery address not specified in order.",
            delivery_latitude=delivery_lat,
            delivery_longitude=delivery_lng,
            delivery_fee=task_delivery_fee,
            status='PENDING_ASSIGNMENT'
        )
        logger.info(f"DeliveryTask created for Order ID: {order.order_id}")

    elif order.status == 'PROCESSING' and not nexus_fulfilled_physical_items.exists() and order.has_physical_products():
        # If the order is PROCESSING but has physical items *not* fulfilled by Nexus,
        # you might want to transition its status differently, e.g., to 'READY_FOR_VENDOR_FULFILLMENT'
        logger.info(f"Order ID: {order.order_id} is PROCESSING but has only vendor-fulfilled physical items. No Nexus DeliveryTask created.")
@receiver(post_save, sender=DeliveryTask)
def notify_vendor_on_task_update(sender, instance, created, **kwargs): # Renamed function
    """
    Signal handler to notify the vendor when a DeliveryTask is assigned to a rider,
    marked as PICKED_UP, or marked as DELIVERED.
    """
    task = instance
    status_changed_to_assigned = (
        hasattr(task, '_original_status') and
        task._original_status != 'ACCEPTED_BY_RIDER' and # Ensure it wasn't already accepted
        task.status == 'ACCEPTED_BY_RIDER' and
        task.rider is not None # Ensure a rider is actually assigned
    )

    status_changed_to_picked_up = (
        hasattr(task, '_original_status') and
        task._original_status != 'PICKED_UP' and
        task.status == 'PICKED_UP' and
        task.rider is not None # Rider should be present if picked up
    )

    status_changed_to_delivered = (
        hasattr(task, '_original_status') and
        task._original_status != 'DELIVERED' and
        task.status == 'DELIVERED' and
        task.rider is not None # Rider should be present
    )

    # Determine vendors to notify (common for all relevant status changes)
    vendors_to_notify = set()
    customer_to_notify = None
    if task.order: # Ensure task has an order and thus an associated customer
        customer_to_notify = task.order.user
        for item in task.order.items.filter(product__product_type='physical'): # Assuming physical products for delivery tasks
            if item.product and item.product.vendor:
                vendors_to_notify.add(item.product.vendor)

    notification_message = None
    vendor_specific_message = None
    customer_specific_message = None
    log_message_prefix = ""

    if status_changed_to_assigned:
        rider_name = task.rider.user.get_full_name() or task.rider.user.username
        vehicle_info = f"{task.rider.get_vehicle_type_display()}"
        if task.rider.vehicle_registration_number:
            vehicle_info += f" ({task.rider.vehicle_registration_number})"
        
        # Message for Vendor
        vendor_specific_message = f"Rider {rider_name} ({vehicle_info}) has accepted the delivery task for order {task.order.order_id} (Task ID: {task.task_id})."
        # Message for Customer
        customer_specific_message = f"Good news! Rider {rider_name} ({vehicle_info}) has accepted the task for your order {task.order.order_id} and will be on their way soon."
        log_message_prefix = f"Rider assignment for task {task.task_id}"

    elif status_changed_to_picked_up:
        rider_name = task.rider.user.get_full_name() or task.rider.user.username
        vehicle_info = f"{task.rider.get_vehicle_type_display()}"
        if task.rider.vehicle_registration_number:
            vehicle_info += f" ({task.rider.vehicle_registration_number})"

        # Message for Vendor
        vendor_specific_message = f"Rider {rider_name} ({vehicle_info}) has picked up items for order {task.order.order_id} (Task ID: {task.task_id})."
        # Message for Customer
        customer_specific_message = f"Your order {task.order.order_id} (Task ID: {task.task_id}) has been picked up by rider {rider_name} ({vehicle_info}) and is on its way!"
        log_message_prefix = f"Pickup for task {task.task_id}"

    elif status_changed_to_delivered:
        rider_name = task.rider.user.get_full_name() or task.rider.user.username
        vehicle_info = f"{task.rider.get_vehicle_type_display()}"
        if task.rider.vehicle_registration_number:
            vehicle_info += f" ({task.rider.vehicle_registration_number})"
        # For vendor
        vendor_notification_message = f"Items for your order {task.order.order_id} (Task ID: {task.task_id}) have been delivered by rider {rider_name} ({vehicle_info})."
        # For customer
        customer_notification_message = f"Your order {task.order.order_id} (Task ID: {task.task_id}) has been delivered by rider {rider_name} ({vehicle_info})."
        log_message_prefix = f"Delivery for task {task.task_id}"
        # Customer notification could also include a link to review the rider or delivery experience.
        # We might also want to include the rider's profile picture URL in the notification's context if we decide to display it.
        # For now, the message includes text details.

    if status_changed_to_assigned or status_changed_to_picked_up:
        if vendor_specific_message and vendors_to_notify:
            logger.info(f"{log_message_prefix}. Notifying vendor(s).")
            for vendor in vendors_to_notify:
                Notification.objects.create(
                    recipient=vendor.user,
                    message=vendor_specific_message, # Use vendor-specific message
                    link=reverse('core:vendor_order_detail', kwargs={'pk': task.order.pk}) if task.order else None
                )
                logger.info(f"Notification created for vendor {vendor.name} (User: {vendor.user.username}) about {log_message_prefix.lower()}.")
        
        if customer_specific_message and customer_to_notify: # Notify customer as well
            logger.info(f"{log_message_prefix}. Notifying customer {customer_to_notify.username}.")
            Notification.objects.create(
                recipient=customer_to_notify,
                message=customer_specific_message, # Use customer-specific message
                link=reverse('core:order_detail', kwargs={'order_id': task.order.order_id}) if task.order else None
            )
            logger.info(f"Notification created for customer {customer_to_notify.username} about {log_message_prefix.lower()}.")

    elif status_changed_to_delivered:
        if vendor_notification_message and vendors_to_notify:
            logger.info(f"{log_message_prefix}. Notifying vendor(s).")
            for vendor in vendors_to_notify:
                Notification.objects.create(
                    recipient=vendor.user,
                    message=vendor_notification_message, # This was already correct
                    link=reverse('core:vendor_order_detail', kwargs={'pk': task.order.pk}) if task.order else None
                )
                logger.info(f"Notification created for vendor {vendor.name} (User: {vendor.user.username}) about {log_message_prefix.lower()}.")
        if customer_notification_message and customer_to_notify:
            logger.info(f"{log_message_prefix}. Notifying customer {customer_to_notify.username}.")
            Notification.objects.create(
                recipient=customer_to_notify,
                message=customer_notification_message, # This was already correct
                link=reverse('core:order_detail', kwargs={'order_id': task.order.order_id}) if task.order else None
            )
            logger.info(f"Notification created for customer {customer_to_notify.username} about {log_message_prefix.lower()}.")


# --- Rider Application Approval Signals ---
@receiver(pre_save, sender=RiderApplication)
def store_previous_rider_application_state(sender, instance, **kwargs):
    """
    Stores the original is_approved state of a RiderApplication before it's saved.
    """
    if instance.pk:
        try:
            instance._original_is_approved = RiderApplication.objects.get(pk=instance.pk).is_approved
        except RiderApplication.DoesNotExist:
            instance._original_is_approved = False 
    else:
        instance._original_is_approved = False

@receiver(post_save, sender=RiderApplication)
def create_or_update_rider_profile_on_approval(sender, instance, created, **kwargs):
    """
    When a RiderApplication is approved, create or update the RiderProfile
    and copy relevant information, including documents.
    Also handles de-approval.
    """
    application = instance
    
    was_not_approved_before = not getattr(instance, '_original_is_approved', False)
    is_now_approved = application.is_approved

    if is_now_approved and was_not_approved_before:
        if not application.is_reviewed:
            logger.warning(f"RiderApplication for {application.user.username} (ID: {application.id}) approved but not marked as reviewed. Ensure 'is_reviewed' is also set for full processing.")
            # Optionally, automatically mark as reviewed upon approval:
            # application.is_reviewed = True
            # application.save(update_fields=['is_reviewed']) # Be careful with recursive signals if you save here.

        try:
            profile, profile_created = RiderProfile.objects.get_or_create(user=application.user)
            
            profile.phone_number = application.phone_number
            profile.vehicle_type = application.vehicle_type
            profile.vehicle_registration_number = application.vehicle_registration_number
            profile.license_number = application.license_number
            profile.address = application.address
            
            if application.vehicle_registration_document: profile.current_vehicle_registration_document = application.vehicle_registration_document
            if application.drivers_license_front: profile.current_drivers_license_front = application.drivers_license_front
            if application.drivers_license_back: profile.current_drivers_license_back = application.drivers_license_back
            if application.id_card_front: profile.current_id_card_front = application.id_card_front
            if application.id_card_back: profile.current_id_card_back = application.id_card_back
            if application.vehicle_picture: profile.current_vehicle_picture = application.vehicle_picture
            
            if application.profile_picture and hasattr(application.user, 'profile_picture'): # Check if CustomUser has profile_picture
                application.user.profile_picture = application.profile_picture
                application.user.save(update_fields=['profile_picture'])

            profile.is_approved = True
            profile.save()
            
            logger.info(f"RiderProfile for {application.user.username} created/updated and approved from application {application.id}.")
            Notification.objects.create(
                recipient=application.user,
                message=f"Congratulations! Your rider application (ID: {application.id}) has been approved. You can now start accepting deliveries.",
                link=reverse('core:rider_dashboard')
            )
        except Exception as e:
            logger.error(f"Error creating/updating RiderProfile for {application.user.username} from application {application.id}: {e}", exc_info=True)
    elif not is_now_approved and getattr(instance, '_original_is_approved', False): # Was approved, now is not
        try:
            profile = RiderProfile.objects.get(user=application.user)
            if profile.is_approved:
                profile.is_approved = False
                profile.is_available = False
                profile.save(update_fields=['is_approved', 'is_available'])
                logger.info(f"RiderProfile for {application.user.username} de-approved based on application {application.id} status change.")
                Notification.objects.create(
                    recipient=application.user,
                    message=f"Your rider status has been updated. Your application (ID: {application.id}) is no longer marked as approved. Please contact support.",
                    link=reverse('core:rider_dashboard')
                )
        except RiderProfile.DoesNotExist:
            logger.warning(f"Attempted to de-approve RiderProfile for {application.user.username} (App ID: {application.id}), but profile does not exist.")
        except Exception as e:
            logger.error(f"Error de-approving RiderProfile for {application.user.username} (App ID: {application.id}): {e}", exc_info=True)
# --- END: Rider Application Approval Signals ---


# --- START: Automatic Delivery Task Assignment Signal ---
from .utils import assign_task_to_rider # We will create this utility function

@receiver(pre_save, sender=DeliveryTask)
def calculate_earnings_on_delivery(sender, instance, **kwargs):
    """
    Calculates rider earnings and platform commission when a task is marked as DELIVERED.
    Also creates corresponding financial transactions.
    """
    task = instance
    if task.pk: # Check if this is an existing instance
        try:
            previous_task = DeliveryTask.objects.get(pk=task.pk)
            # Check if status is changing to DELIVERED and was not DELIVERED before
            if task.status == 'DELIVERED' and getattr(previous_task, 'status', None) != 'DELIVERED': # Use getattr for safety if previous_task might not have status
                if task.delivery_fee is not None and task.delivery_fee > 0 and task.rider:
                    commission_rate = Decimal(str(settings.NEXUS_DELIVERY_COMMISSION_RATE)) # Ensure Decimal
                    
                    # Calculate commission and earnings
                    calculated_commission = task.delivery_fee * commission_rate
                    calculated_rider_earning = task.delivery_fee - calculated_commission
                    
                    task.platform_commission = calculated_commission.quantize(Decimal('0.01'))
                    task.rider_earning = calculated_rider_earning.quantize(Decimal('0.01'))
                    
                    logger.info(f"Task {task.task_id} DELIVERED. Delivery Fee: {task.delivery_fee}, Rider Earning: {task.rider_earning}, Platform Commission: {task.platform_commission}")

                    # Create Transaction records within an atomic block
                    with db_transaction.atomic():
                        # Platform Commission Transaction
                        Transaction.objects.create(
                            user=None, # Or a system user if you have one
                            transaction_type='platform_commission',
                            amount=task.platform_commission,
                            currency=task.order.currency if task.order else "GHS", # Get currency from order or default
                            status='completed',
                        order=task.order,
                        description=f"Platform commission for delivery task {task.task_id} (Order: {task.order.order_id if task.order else 'N/A'})."
                        )
                        # Rider Earning Transaction (represents amount owed to rider)
                        # This isn't a direct payout yet, but an accrual.
                        # Actual payout will be a separate transaction of type 'payout'.
                        # For now, we might not need a transaction for rider_earning itself,
                        # as the DeliveryTask.rider_earning field tracks it.
                        # Let's hold off on creating a 'rider_earning' transaction for now,
                        # and focus on commission. We'll handle rider balances later.

                else:
                    logger.warning(f"Task {task.task_id} marked DELIVERED but has no delivery_fee ({task.delivery_fee}) or no rider assigned. No earnings calculated.")
        except DeliveryTask.DoesNotExist:
            pass # New instance, no previous state to compare




@receiver(post_save, sender=DeliveryTask)
def auto_assign_delivery_task(sender, instance, created, **kwargs):
    """
    Automatically assigns a PENDING_ASSIGNMENT task to an available rider.
    """
    task = instance
    if task.status == 'PENDING_ASSIGNMENT' and task.rider is None:
        logger.info(f"Task {task.task_id} for order {task.order.order_id} is PENDING_ASSIGNMENT. Attempting auto-assignment.")
        assigned_rider_profile = assign_task_to_rider(task)

        if assigned_rider_profile:
            task.rider = assigned_rider_profile
            task.status = 'ACCEPTED_BY_RIDER' # Or 'ASSIGNED_TO_RIDER' if rider needs to manually accept via app
            # task.assigned_at = timezone.now() # Add this field to DeliveryTask if needed
            task.save(update_fields=['rider', 'status']) # , 'assigned_at'
            
            logger.info(f"Task {task.task_id} automatically assigned to rider {assigned_rider_profile.user.username}.")
            
            # Notify the assigned rider
            Notification.objects.create(
                recipient=assigned_rider_profile.user,
                message=f"New delivery task assigned: Order #{task.order.order_id}. Pickup from: {task.pickup_address_text or 'N/A'}.",
                notification_type='TASK_ASSIGNED',
                link=reverse('core:rider_task_detail', kwargs={'task_id': task.task_id})
            )
            
            # Optionally, notify vendor or customer
            # if task.order.vendor:
            #     Notification.objects.create(recipient=task.order.vendor.user, message=f"Rider {assigned_rider_profile.user.username} assigned to your order #{task.order.order_id}")
            # Notification.objects.create(recipient=task.order.user, message=f"Rider {assigned_rider_profile.user.username} is on the way for your order #{task.order.order_id}")

        else:
            logger.warning(f"No suitable rider found for task {task.task_id}. Task remains PENDING_ASSIGNMENT.")
            # Optionally, notify admin or queue for manual assignment
            # Notification.objects.create(
            #     recipient=User.objects.filter(is_staff=True).first(), # Example: notify first staff user
            #     message=f"Could not auto-assign delivery task {task.task_id} for order {task.order.order_id}. Manual intervention may be required.",
            #     notification_type='TASK_ASSIGNMENT_FAILED',
            #     link=reverse('admin:core_deliverytask_change', args=[task.id])
            # )

# --- END: Automatic Delivery Task Assignment Signal ---

# --- PayoutRequest Signals for Notifications ---

@receiver(pre_save, sender=PayoutRequest)
def store_previous_payout_request_status(sender, instance, **kwargs):
    """
    Stores the original status of a PayoutRequest before it's saved.
    """
    if instance.pk:
        try:
            instance._original_status = PayoutRequest.objects.get(pk=instance.pk).status
        except PayoutRequest.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None # New instance

@receiver(post_save, sender=PayoutRequest)
def notify_on_payout_request_update(sender, instance, created, **kwargs):
    """
    Sends notifications when a PayoutRequest is created or its status changes.
    """
    payout_request = instance
    original_status = getattr(instance, '_original_status', None)
    User = get_user_model()

    target_user = None
    profile_type_str = ""
    profile_name = "Unknown User"
    dashboard_link = reverse('core:home') # Default link

    if payout_request.rider_profile:
        target_user = payout_request.rider_profile.user
        profile_type_str = "Rider"
        profile_name = target_user.username
        dashboard_link = reverse('core:rider_earnings')
    elif payout_request.vendor_profile:
        target_user = payout_request.vendor_profile.user
        profile_type_str = "Vendor"
        profile_name = payout_request.vendor_profile.name
        dashboard_link = reverse('core:vendor_payout_requests')
    elif payout_request.service_provider_profile:
        target_user = payout_request.service_provider_profile.user
        profile_type_str = "Service Provider"
        profile_name = target_user.username
        dashboard_link = reverse('core:service_provider_payout_requests')

    if created and payout_request.status == 'pending':
        admin_message = f"New {profile_type_str} payout request from {profile_name} for GHS {payout_request.amount_requested}. Request ID: {payout_request.id}."
        admin_link = reverse('admin:core_payoutrequest_change', args=[payout_request.id])
        staff_users = User.objects.filter(is_staff=True, is_active=True)
        for staff_user in staff_users:
            Notification.objects.create(recipient=staff_user, message=admin_message, link=admin_link)
        logger.info(f"Admin notification sent for new payout request {payout_request.id} from {profile_name}.")

    elif not created and original_status != payout_request.status and target_user:
        user_message_map = {
            'processing': f"Your payout request (ID: {payout_request.id}) for GHS {payout_request.amount_requested} is now being processed.",
            'completed': f"Your payout request (ID: {payout_request.id}) for GHS {payout_request.amount_requested} has been completed." + (f" Transaction Ref: {payout_request.transaction.gateway_transaction_id or payout_request.transaction.id}." if payout_request.transaction else ""),
            'rejected': f"Your payout request (ID: {payout_request.id}) for GHS {payout_request.amount_requested} has been rejected." + (f" Reason: {payout_request.admin_notes.splitlines()[-1] if payout_request.admin_notes else ''}" if payout_request.admin_notes else ""),
            'failed': f"The payout for your request (ID: {payout_request.id}) of GHS {payout_request.amount_requested} failed. Please contact support."
        }
        user_message = user_message_map.get(payout_request.status)
        if user_message:
            Notification.objects.create(recipient=target_user, message=user_message, link=dashboard_link)
            logger.info(f"User notification sent to {target_user.username} for payout request {payout_request.id} status change to {payout_request.status}.")
# --- END: PayoutRequest Signals for Notifications ---

# --- PayPal IPN Signal Handler ---

@receiver(valid_ipn_received)
def paypal_payment_notification(sender, **kwargs):
    """
    Receiver function to handle successful payment notifications from PayPal.
    This is triggered when a payment is successfully processed and PayPal sends
    an Instant Payment Notification (IPN) to our server.
    """
    ipn_obj = sender
    logger.info(f"Received PayPal IPN signal for invoice: {ipn_obj.invoice}")

    # Check that the payment status is 'Completed'
    if ipn_obj.payment_status == ST_PP_COMPLETED:
        # Check that the receiver email is the one we expect.
        if ipn_obj.receiver_email != settings.PAYPAL_RECEIVER_EMAIL:
            logger.error(f"PayPal IPN Error: Receiver email mismatch. Expected {settings.PAYPAL_RECEIVER_EMAIL}, got {ipn_obj.receiver_email}.")
            return

        # Try to retrieve the order from your database using the invoice number (which is the order's pk)
        try:
            order = Order.objects.get(id=ipn_obj.invoice)
        except Order.DoesNotExist:
            logger.error(f"PayPal IPN Error: Order with ID {ipn_obj.invoice} not found.")
            return

        # Verify that the order is in a state where payment is expected.
        if order.status != 'AWAITING_ESCROW_PAYMENT':
            logger.warning(f"PayPal IPN Warning: Received payment for order {order.order_id} which is not awaiting payment. Current status: {order.status}. IPN txn_id: {ipn_obj.txn_id}")
            # This could be a duplicate IPN, so we don't process it again.
            return

        # Verify the payment amount and currency.
        if Decimal(ipn_obj.mc_gross) != order.total_amount.quantize(Decimal('0.01')):
            logger.error(f"PayPal IPN Error: Amount mismatch for order {order.order_id}. Expected {order.total_amount}, got {ipn_obj.mc_gross}.")
            return
        
        if ipn_obj.mc_currency != order.currency:
            logger.error(f"PayPal IPN Error: Currency mismatch for order {order.order_id}. Expected {order.currency}, got {ipn_obj.mc_currency}.")
            return

        # If all checks pass, update the order and create a transaction record.
        with db_transaction.atomic():
            # The Order model does not have a 'payment_status' field.
            # We just update the main status.
            order.status = 'PROCESSING' # This will trigger other signals like delivery task creation
            # The payment method should have already been set to 'paypal' when the order was placed.
            # We can re-affirm it here if we want.
            order.payment_method = 'paypal'
            order.save(update_fields=['status', 'payment_method'])

            # Create a transaction record for this payment
            Transaction.objects.create(
                user=order.user, transaction_type='payment', amount=Decimal(ipn_obj.mc_gross),
                currency=ipn_obj.mc_currency, status='completed', order=order,
                gateway_transaction_id=ipn_obj.txn_id, description=f"PayPal payment for Order #{order.order_id}."
            )

            # Notify the customer that their payment was successful
            Notification.objects.create(recipient=order.user, message=f"Your payment for order {order.order_id} was successful. Your order is now being processed.", link=reverse('core:order_detail', kwargs={'order_id': order.order_id}))
            logger.info(f"Successfully processed PayPal payment for Order {order.order_id}. Transaction ID: {ipn_obj.txn_id}")

    else:
        logger.warning(f"Received PayPal IPN with non-completed status: {ipn_obj.payment_status} for invoice {ipn_obj.invoice}")

# --- Product Q&A Notification Signal ---
@receiver(post_save, sender=ProductQuestion)
def notify_vendor_on_new_question(sender, instance, created, **kwargs):
    """
    Sends a notification to the vendor when a new question is posted on their product.
    """
    if created:
        question = instance
        product = question.product
        vendor = product.vendor
        
        if vendor and vendor.user:
            logger.info(f"New question for product '{product.name}'. Notifying vendor '{vendor.name}'.")
            Notification.objects.create(
                recipient=vendor.user,
                message=f"You have a new question on your product '{product.name}' from user {question.user.username}.",
                # Link to the product detail page where the Q&A is displayed
                link=product.get_absolute_url() + "#product-qa-section" # Add an anchor
            )

# --- START: AI Cache Invalidation Signal ---
@receiver(post_save, sender=ProductReview)
def clear_ai_summary_cache_on_review_change(sender, instance, **kwargs):
    """
    Clears the cached AI review summary for a product when one of its reviews
    is saved (created, updated, or approved/unapproved).
    """
    product = instance.product
    cache_key = f"ai_summary_prod_{product.id}"
    cache.delete(cache_key)
    logger.info(f"Cleared AI review summary cache for product {product.id} due to review update.")
# --- END: AI Cache Invalidation Signal ---

# --- START: Background Removal Signal ---
from .tasks import process_background_removal
from .models import ProductImage

@receiver(post_save, sender=ProductImage)
def schedule_background_removal(sender, instance, created, **kwargs):
    """
    When a new ProductImage is created, schedule a Celery task
    to remove its background.
    """
    # We only want to trigger this for newly created images,
    # and we check that it's not an image that was already processed by this task.
    if created and not instance.image.name.startswith('no_bg_'):
        logger.info(f"New ProductImage (ID: {instance.id}) created. Scheduling background removal.")
        # Use .delay() to call the task asynchronously
        process_background_removal.delay(instance.id)
# --- END: Background Removal Signal ---
