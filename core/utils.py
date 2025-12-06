# c:\Users\Hp\Desktop\Nexus\core\utils.py
import logging
import requests
from math import radians, sin, cos, sqrt, atan2
from django.conf import settings
from django.utils import timezone
from django.db.models import Exists, OuterRef, Q, Count
from .models import RiderProfile, ActiveRiderBoost, DeliveryTask, Cart, Address # Ensure all are imported

logger = logging.getLogger(__name__)

def send_order_confirmation_email(order):
    """
    Placeholder for sending an order confirmation email.
    """
    logger.info(f"Placeholder: Sending order confirmation email for order {order.order_id}")
    pass

def generate_invoice_pdf(order):
    """
    Placeholder for generating a PDF invoice for an order.
    """
    logger.info(f"Placeholder: Generating invoice PDF for order {order.order_id}")
    return None # Or a dummy PDF content

def calculate_shipping_cost(cart: Cart, shipping_address: Address, nexus_fulfilled_only: bool = True):
    """
    Calculates the shipping cost for items in a given cart and shipping address.
    If nexus_fulfilled_only is True, it only considers items to be fulfilled by Nexus.
    This is a basic implementation. Real-world scenarios would be more complex.

    Args:
        cart (Cart): The user's cart object.
        shipping_address (Address): The user's shipping address object.
        nexus_fulfilled_only (bool): If True, only calculate for Nexus-fulfilled items.

    Returns:
        Decimal: The calculated shipping cost.
    """
    from decimal import Decimal # Ensure Decimal is imported

    items_to_consider = cart.items.all()
    if nexus_fulfilled_only:
        # Filter for items that will be fulfilled by Nexus
        # This assumes product.fulfillment_method or vendor.default_fulfillment_method logic
        # For simplicity here, let's assume we'll pass a pre-filtered list of items if needed,
        # or the cart items are already determined to be Nexus-fulfilled by the caller.
        # For now, let's assume the caller (place_order view) will handle which items are passed or how to interpret.
        # The view will pass only Nexus-fulfilled items if this function is to calculate only for them.
        # OR, we can filter here if the cart items have their fulfillment method set.
        # Let's adjust this to expect a list of CartItem objects if nexus_fulfilled_only is true.
        # For now, we'll keep it simple: if nexus_fulfilled_only, the logic applies to items that *would* be Nexus fulfilled.
        # The place_order view will be more explicit.
        pass # The filtering will happen in place_order, this function calculates based on items it's "told" are for Nexus.

    nexus_item_count = 0
    for item in items_to_consider:
        # Determine fulfillment method (product specific, then vendor default)
        product_fulfillment = item.product.fulfillment_method
        vendor_default_fulfillment = item.product.vendor.default_fulfillment_method if item.product.vendor else 'vendor'
        actual_fulfillment = product_fulfillment if product_fulfillment else vendor_default_fulfillment
        
        if actual_fulfillment == 'nexus' and item.product.product_type == 'physical':
            nexus_item_count += 1 # Count each unique Nexus-fulfilled physical product line item

    if nexus_item_count == 0:
        return Decimal('0.00') # No Nexus-fulfilled items, so no Nexus delivery fee

    base_shipping_fee = Decimal('3.00')  # Example base fee for Nexus fulfillment
    fee_per_nexus_item = Decimal('0.50') # Example additional fee per unique Nexus-fulfilled item type

    calculated_fee = base_shipping_fee + (nexus_item_count * fee_per_nexus_item)
    logger.info(f"Calculated NEXUS shipping cost for cart {cart.id} to {shipping_address.city if shipping_address else 'N/A'}: {calculated_fee}. Base: {base_shipping_fee}, Nexus Items: {nexus_item_count}, Fee/Item: {fee_per_nexus_item}")
    return calculated_fee.quantize(Decimal('0.01')) # Ensure two decimal places

def process_payment_with_gateway(order, payment_details):
    logger.info(f"Placeholder: Processing payment for order {order.order_id} with gateway.")
    return True, "Payment successful (placeholder)" # Placeholder success

def geocode_address(address_string):
    """
    Geocodes an address string using Google Geocoding API.
    Returns (latitude, longitude) or (None, None) if an error occurs.
    """
    from decimal import Decimal # Import here to avoid potential circular import if utils is imported early

    if not address_string:
        return None, None

    api_key = settings.GOOGLE_MAPS_API_KEY
    if not api_key or api_key == 'YOUR_GOOGLE_MAPS_API_KEY_HERE': # Check if key is placeholder
        logger.error("Geocoding: GOOGLE_MAPS_API_KEY is not configured or is a placeholder.")
        return None, None

    params = {
        'address': address_string,
        'key': api_key
    }
    try:
        response = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params=params, timeout=5)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        result = response.json()

        if result['status'] == 'OK' and result['results']:
            location = result['results'][0]['geometry']['location']
            latitude = Decimal(str(location['lat'])) # Convert to Decimal
            longitude = Decimal(str(location['lng'])) # Convert to Decimal
            logger.info(f"Geocoding successful for '{address_string}': Lat={latitude}, Lng={longitude}")
            return latitude, longitude
        else:
            logger.warning(f"Geocoding failed for '{address_string}'. Status: {result['status']}. Error: {result.get('error_message', 'No error message provided by API.')}")
            return None, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Geocoding API request failed for '{address_string}': {e}")
        return None, None
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"An unexpected error occurred during geocoding for '{address_string}': {e}", exc_info=True)
        return None, None

def assign_task_to_rider(delivery_task: DeliveryTask):
    """
    Finds the best available and approved rider for a given delivery task,
    prioritizing riders with an active 'search_top' boost.

    Args:
        delivery_task (DeliveryTask): The task to be assigned.

    Returns:
        RiderProfile or None: The assigned RiderProfile instance, or None if no suitable rider is found.
    """
    now = timezone.now()

    # Subquery to check for an active 'search_top' boost
    active_search_boost_subquery = ActiveRiderBoost.objects.filter(
        rider_profile=OuterRef('pk'),
        boost_package__boost_type='search_top',
        is_active=True,
        expires_at__gt=now
    )

    # Define active task statuses
    active_task_statuses = ['ACCEPTED_BY_RIDER', 'PICKED_UP', 'OUT_FOR_DELIVERY']

    available_riders = RiderProfile.objects.filter(
        is_approved=True,
        is_available=True
        # Add proximity filters here later if you have location data for riders and pickup
        # e.g., Q(current_location__distance_lte=(delivery_task.pickup_location, D(km=10)))
    ).annotate(
        has_active_search_boost=Exists(active_search_boost_subquery),
        current_active_tasks=Count('delivery_tasks', filter=Q(delivery_tasks__status__in=active_task_statuses)) # Use related_name
    ).order_by(
        '-has_active_search_boost',  # Riders with active 'search_top' boost first
        'current_active_tasks',      # Then by riders with fewer active tasks
        '?'                          # Then randomly among those (or by other criteria like last_assigned_at)
    )
    
    # For debugging:
    # for rider in available_riders:
    #     logger.debug(f"Rider: {rider.user.username}, Boosted: {rider.has_active_search_boost}, Active Tasks: {rider.current_active_tasks}")

    selected_rider = available_riders.first()

    if selected_rider:
        logger.info(f"Selected rider {selected_rider.user.username} for task {delivery_task.task_id}. Boosted: {selected_rider.has_active_search_boost}, Active Tasks: {selected_rider.current_active_tasks}")
    else:
        logger.warning(f"No available riders found for task {delivery_task.task_id}.")

    return selected_rider

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on the earth (specified in decimal degrees).
    Returns distance in kilometers.
    """
    R = 6371  # Radius of Earth in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# Add other utility functions below if needed
