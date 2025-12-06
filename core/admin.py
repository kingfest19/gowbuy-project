# c:\Users\Hp\Desktop\Nexus\core\admin.py
from django.db.models import Sum, F, Value
from django.contrib import admin, messages
from django.utils.html import format_html # For user_link helper
from django.utils.translation import gettext_lazy as _
from django.urls import reverse # For user_link helper
from django.conf import settings # To access PAYSTACK_SECRET_KEY
import requests # For Paystack API calls
import uuid # For generating idempotency keys or unique references
from django.db import transaction as db_transaction # For atomic transactions in admin actions
from decimal import Decimal, ROUND_HALF_UP # For amount calculations
# Import your user model (adjust path if needed)
from authapp.models import CustomUser

# Import ALL your core models correctly from .models
# Import ProductImage as well
from .models import (
    Category, Vendor, Product, Address, Order, OrderItem, Transaction,
    WishlistItem, ProductReview, VendorReview, ProductImage, logger, PortfolioItem, # <<< Added logger and PortfolioItem
    ProductVideo, ServiceCategory, Service, ServiceReview, ServiceImage, ServiceVideo, PayoutRequest, PricingPlan, 
    ServicePackage, DeliveryTask, ServiceProviderProfile, RiderProfile,
    RiderApplication, BoostPackage, ActiveRiderBoost, FraudReport # <<< Import RiderApplication, BoostPackage, and ActiveRiderBoost
)

# Import custom forms
from .forms import VendorProductForm


# --- CustomUser Admin (Keep as is, or move to authapp/admin.py) ---
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'bio', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active')
    ordering = ('username',)
# Ensure CustomUser is only registered once (here or in authapp/admin.py)
# Avoid registering it in both places. Assuming it's okay here for now.
# Check if CustomUser is already registered before registering again
# This avoids potential conflicts if it's also registered in authapp/admin.py
if not admin.site.is_registered(CustomUser):
    admin.site.register(CustomUser, CustomUserAdmin)


# --- Register Core Models ---

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'is_active') # Restored parent
    list_filter = ('is_active', 'parent') # Restored
    search_fields = ('name', 'description') # Restored
    prepopulated_fields = {'slug': ('name',)} # Restored
    ordering = ('name',) # Restored

# --- UPDATED Vendor Admin ---
@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_link', 'is_approved', 'is_verified', 'has_premium_3d_generation_access', 'default_fulfillment_method', 'active_product_count', 'total_sales_display', 'view_products_link', 'view_orders_link', 'created_at')
    list_filter = ('is_approved', 'is_verified', 'has_premium_3d_generation_access', 'created_at', 'location_country')
    list_editable = ('is_approved', 'is_verified', 'has_premium_3d_generation_access')
    search_fields = ('name', 'user__username', 'contact_email', 'location_city')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('user',)
    ordering = ('name',)

    # --- Add Fieldsets for better organization ---
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'slug')
        }),
        ('Status & Verification', {
            'fields': ('is_approved', 'is_verified', 'has_premium_3d_generation_access')
        }),
        ('Profile Information', {
            'fields': ('description', 'contact_email', 'phone_number', 'logo', 'location_city', 'location_country', 'latitude', 'longitude', 'default_fulfillment_method')
        }),
        ('Payout Information', { # Added for vendor payout
            'fields': ('mobile_money_provider', 'mobile_money_number', 'paypal_email', 'bank_account_name', 'bank_account_number', 'bank_name', 'bank_branch', 'paystack_recipient_code', 'stripe_account_id', 'payoneer_email', 'wise_email', 'crypto_wallet_address', 'crypto_wallet_network')
        }),
        ('Verification Documents', {
            'fields': ('verification_method', 'verification_status', 'business_registration_document', 'tax_id_number', 'other_supporting_document', 'national_id_type', 'national_id_number', 'national_id_document')
            # 'classes': ('collapse',) # Keep it open for now, or add 'collapse' if you prefer
        }),
        ('Policies', {
            'fields': ('shipping_policy', 'return_policy'),
            'classes': ('collapse',)
        }),
        ('Timestamps', { # Restored
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'view_business_registration_document_link', 'view_national_id_document_link', 'paystack_recipient_code')
    # ------------------------------------------

    def user_link(self, obj):
        if obj.user:
            try:
                link = reverse("admin:authapp_customuser_change", args=[obj.user.id])
            except:
                try:
                    link = reverse("admin:auth_user_change", args=[obj.user.id])
                except:
                    return obj.user.username
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "N/A"
    user_link.short_description = 'User Account'

    def view_business_registration_document_link(self, obj):
        if obj.business_registration_doc:
            return format_html('<a href="{}" target="_blank">View Document</a>', obj.business_registration_doc.url)
        return "N/A"
    view_business_registration_document_link.short_description = 'Business Reg. Doc'

    def view_national_id_document_link(self, obj):
        if obj.national_id_doc:
            return format_html('<a href="{}" target="_blank">View ID</a>', obj.national_id_doc.url)
        return "N/A"
    view_national_id_document_link.short_description = 'National ID Doc'

    def active_product_count(self, obj):
        return obj.products.filter(is_active=True).count()
    active_product_count.short_description = 'Active Products'

    def total_sales_display(self, obj):
        # Calculate total sales for this vendor from completed/delivered orders
        total = OrderItem.objects.filter(
            product__vendor=obj,
            order__status__in=['COMPLETED', 'delivered'] # Adjust statuses as needed
        ).aggregate(total_sales=Sum(F('price') * F('quantity')))['total_sales']
        return f"GH₵ {total.quantize(Decimal('0.01'), ROUND_HALF_UP) if total else '0.00'}"
    total_sales_display.short_description = 'Total Sales (GH₵)'

    def view_products_link(self, obj):
        url = (
            reverse("admin:core_product_changelist")
            + f"?vendor__id__exact={obj.id}"
        )
        return format_html('<a href="{}">View Products</a>', url)
    view_products_link.short_description = 'Products'

    def view_orders_link(self, obj):
        url = (
            reverse("admin:core_order_changelist")
            + f"?items__product__vendor__id__exact={obj.id}" # Query through OrderItem
        )
        return format_html('<a href="{}">View Orders</a>', url)
    view_orders_link.short_description = 'Vendor Orders'
# --- END UPDATED Vendor Admin ---

# --- Inline Admin for Product Images ---
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text')
    readonly_fields = ('uploaded_at',)

# --- Inline Admin for Product Videos ---
class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 1
    fields = ('video', 'title', 'description')
    readonly_fields = ('uploaded_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = VendorProductForm
    list_display = ('name', 'slug', 'vendor', 'category', 'price', 'stock', 'is_active', 'is_available', 'is_featured', 'created_at') # Restored 'is_available'
    list_filter = ('is_active', 'is_featured', 'category', 'vendor', 'created_at') # Restored
    search_fields = ('name', 'description', 'slug', 'vendor__name', 'category__name') # Restored
    prepopulated_fields = {'slug': ('name',)} # Restored
    list_editable = ('price', 'stock', 'is_active', 'is_featured') # Restored
    raw_id_fields = ('vendor', 'category') # Restored
    ordering = ('-created_at',) # Restored
    inlines = [ProductImageInline, ProductVideoInline] # Restored inlines
    date_hierarchy = 'created_at' # Restored

    # Option 1: Using fieldsets for better organization
    fieldsets = (
        (None, {
            'fields': ('vendor', 'category', 'name', 'slug', 'product_type')
        }),
        ('Image Enhancement', {
            'fields': ('enhance_image', 'remove_background')
        }),('Pricing & Stock', {
            'fields': ('price', 'stock')
        }),
        ('Description & Media', {
            'fields': ('description', 'keywords_for_ai', 'three_d_model', 'digital_file')
        }),
        ('Fulfillment', {
            'fields': ('fulfillment_method', 'vendor_delivery_fee')

        }),
        ('Status & Visibility', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at') # Add any other fields you want as read-only

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'address_type', 'street_address', 'city', 'country', 'latitude', 'longitude', 'is_default')
    list_filter = ('address_type', 'is_default', 'country', 'state', 'city')
    search_fields = ('user__username', 'full_name', 'street_address', 'city', 'zip_code', 'country')
    list_select_related = ('user',)
    raw_id_fields = ('user',)
    fields = ('user', 'address_type', 'full_name', 'street_address', 'apartment_address', 'city', 'state', 'zip_code', 'country', 'phone_number', 'latitude', 'longitude', 'is_default')
    ordering = ('user__username', '-is_default', '-created_at')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ('product', 'service_package', 'product_name', 'price', 'quantity', 'fulfillment_method', 'get_total_item_price') # Added fulfillment_method
    readonly_fields = ('product_name', 'price', 'get_total_item_price')
    extra = 0
    raw_id_fields = ('product', 'service_package') # Restored service_package

    def get_total_item_price(self, obj):
        return obj.get_total_item_price()
    get_total_item_price.short_description = 'Item Total'

def mark_direct_payment_received(modeladmin, request, queryset):
    updated_count = 0
    for order in queryset:
        if order.payment_method == 'direct' and order.status == 'AWAITING_DIRECT_PAYMENT':
            order.status = 'PROCESSING'
            order.save()
            updated_count += 1
    if updated_count > 0:
        modeladmin.message_user(request, f"{updated_count} order(s) marked as 'Processing' (Direct Payment Received).")
    else:
        modeladmin.message_user(request, "No applicable orders were updated. Ensure selected orders are 'Direct Payment' and 'Awaiting Direct Payment Confirmation'.", level='WARNING')
mark_direct_payment_received.short_description = "Mark Direct Payment as Received (Set to Processing)"


def get_paystack_momo_bank_code(provider_name):
    """Helper to get Paystack bank code for MoMo providers."""
    provider_name_upper = provider_name.upper()
    if 'MTN' in provider_name_upper:
        return 'MTN'
    elif 'VODAFONE' in provider_name_upper:
        return 'VOD'
    elif 'AIRTELTIGO' in provider_name_upper or 'TIGO' in provider_name_upper or 'AIRTEL' in provider_name_upper:
        return 'ATL'
    return None

def create_paystack_transfer_recipient(provider_profile):
    """Creates a Paystack Transfer Recipient and returns the recipient_code."""
    if not (provider_profile.payout_mobile_money_number and provider_profile.payout_mobile_money_provider):
        logger.error(f"Missing MoMo details for provider {provider_profile.user.username}")
        return None, "Missing Mobile Money payout details."

    bank_code = get_paystack_momo_bank_code(provider_profile.payout_mobile_money_provider)
    if not bank_code:
        logger.error(f"Could not determine Paystack bank code for MoMo provider: {provider_profile.payout_mobile_money_provider}")
        return None, f"Unsupported MoMo provider: {provider_profile.payout_mobile_money_provider}."

    url = "https://api.paystack.co/transferrecipient"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "type": "mobile_money",
        "name": provider_profile.user.get_full_name() or provider_profile.user.username,
        "account_number": provider_profile.payout_mobile_money_number,
        "bank_code": bank_code,
        "currency": "GHS"
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get("status") and data.get("data", {}).get("recipient_code"):
            recipient_code = data["data"]["recipient_code"]
            provider_profile.paystack_recipient_code = recipient_code
            provider_profile.save(update_fields=['paystack_recipient_code'])
            logger.info(f"Successfully created Paystack recipient for {provider_profile.user.username}: {recipient_code}")
            return recipient_code, None
        else:
            error_msg = data.get("message", "Failed to create Paystack recipient.")
            logger.error(f"Paystack recipient creation failed for {provider_profile.user.username}: {error_msg}")
            return None, error_msg
    except requests.exceptions.RequestException as e:
        logger.error(f"Paystack API error during recipient creation for {provider_profile.user.username}: {e}")
        return None, f"API Error: {e}"

# --- START: New function for Vendor Recipient ---
def create_paystack_transfer_recipient_for_vendor(vendor_profile):
    """Creates a Paystack Transfer Recipient for a Vendor and returns the recipient_code."""
    if not (vendor_profile.mobile_money_number and vendor_profile.mobile_money_provider):
        logger.error(f"Missing MoMo details for vendor {vendor_profile.name}")
        return None, "Missing Mobile Money payout details for vendor."

    bank_code = get_paystack_momo_bank_code(vendor_profile.mobile_money_provider) # Re-use existing helper
    if not bank_code:
        logger.error(f"Could not determine Paystack bank code for MoMo provider: {vendor_profile.mobile_money_provider} for vendor {vendor_profile.name}")
        return None, f"Unsupported MoMo provider for vendor: {vendor_profile.mobile_money_provider}."

    url = "https://api.paystack.co/transferrecipient"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "type": "mobile_money",
        "name": vendor_profile.name, # Use vendor's public name
        "account_number": vendor_profile.mobile_money_number,
        "bank_code": bank_code,
        "currency": "GHS" # Assuming GHS
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get("status") and data.get("data", {}).get("recipient_code"):
            recipient_code = data["data"]["recipient_code"]
            vendor_profile.paystack_recipient_code = recipient_code # Save to Vendor model
            vendor_profile.save(update_fields=['paystack_recipient_code'])
            logger.info(f"Successfully created Paystack recipient for VENDOR {vendor_profile.name}: {recipient_code}")
            return recipient_code, None
        else:
            error_msg = data.get("message", "Failed to create Paystack recipient for vendor.")
            logger.error(f"Paystack recipient creation failed for VENDOR {vendor_profile.name}: {error_msg}")
            return None, error_msg
    except requests.exceptions.RequestException as e:
        logger.error(f"Paystack API error during recipient creation for VENDOR {vendor_profile.name}: {e}")
        return None, f"API Error: {e}"
# --- END: New function for Vendor Recipient ---

def process_provider_payouts(modeladmin, request, queryset):
    """
    Admin action to process payouts for selected orders.
    """
    processed_orders = 0
    failed_payouts_info = []

    for order in queryset:
        if order.status == 'PENDING_PAYOUT' and order.payment_method == 'escrow':
            # Find unique providers for this order's service items
            provider_payout_data = {} # {provider_user: amount_to_payout}

            for item in order.items.filter(service_package__isnull=False):
                if item.provider: # item.provider is the CustomUser instance (service provider)
                    item_total_value = item.price * item.quantity
                    
                    # --- Platform Commission Logic ---
                    platform_commission_earned = item_total_value * settings.PLATFORM_COMMISSION_RATE # Use from settings
                    amount_to_payout_for_item = item_total_value - platform_commission_earned
                    # --- End Platform Commission Logic ---
                    
                    if item.provider not in provider_payout_data:
                        provider_payout_data[item.provider] = Decimal('0.00')
                    provider_payout_data[item.provider] += amount_to_payout_for_item
            
            if not provider_payout_data:
                failed_payouts_info.append(f"Order {order.order_id}: No service provider found for payout.")
                continue

            all_provider_payouts_successful_for_this_order = True
            for provider_user, payout_amount_decimal in provider_payout_data.items():
                try:
                    profile = provider_user.service_provider_profile
                    if not (profile.payout_mobile_money_number and profile.payout_mobile_money_provider):
                        all_provider_payouts_successful_for_this_order = False
                        failed_payouts_info.append(f"Order {order.order_id}: Provider {provider_user.username} missing payout details.")
                        continue

                    recipient_code = profile.paystack_recipient_code
                    if not recipient_code:
                        recipient_code, error_msg = create_paystack_transfer_recipient(profile)
                        if error_msg:
                            all_provider_payouts_successful_for_this_order = False
                            failed_payouts_info.append(f"Order {order.order_id}, Provider {provider_user.username}: Failed to create recipient - {error_msg}")
                            continue
                    
                    # --- Initiate Paystack Transfer ---
                    transfer_url = "https://api.paystack.co/transfer"
                    headers = {
                        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                        "Content-Type": "application/json",
                    }
                    amount_in_kobo = int(payout_amount_decimal * 100)
                    idempotency_key = str(uuid.uuid4()) # For preventing duplicate transfers

                    transfer_payload = {
                        "source": "balance", # Assuming payout from your Paystack balance
                        "amount": amount_in_kobo,
                        "recipient": recipient_code,
                        "reason": f"Payout for Order {order.order_id} - Service by {provider_user.username}",
                        "currency": "GHS",
                    }
                    
                    logger.info(f"ADMIN ACTION: Attempting Paystack transfer of GHS {payout_amount_decimal} to {provider_user.username} for Order {order.order_id}")
                    
                    try:
                        transfer_response = requests.post(transfer_url, headers=headers, json=transfer_payload, timeout=30) # Added timeout
                        transfer_response.raise_for_status()
                        transfer_data = transfer_response.json()

                        if transfer_data.get("status") and transfer_data.get("data", {}).get("status") in ['success', 'pending']:
                            Transaction.objects.create(
                                order=order,
                                user=provider_user,
                                transaction_type='payout',
                                amount=payout_amount_decimal,
                                status='pending' if transfer_data["data"]["status"] == 'pending' else 'completed',
                                gateway_transaction_id=transfer_data["data"].get("transfer_code"),
                                description=f"Paystack Payout to {provider_user.username} for Order {order.order_id}. Status: {transfer_data['data']['status']}"
                            )
                            logger.info(f"Paystack transfer initiated for {provider_user.username}, Order {order.order_id}. Status: {transfer_data['data']['status']}")

                            Transaction.objects.create(
                                order=order,
                                transaction_type='platform_commission',
                                amount=platform_commission_earned, 
                                status='completed', 
                                description=f"Platform commission from Order {order.order_id} (Provider: {provider_user.username})"
                            )
                        else:
                            all_provider_payouts_successful_for_this_order = False
                            error_msg = transfer_data.get("message", "Paystack transfer initiation failed.")
                            failed_payouts_info.append(f"Order {order.order_id}, Provider {provider_user.username}: Transfer failed - {error_msg}")
                            logger.error(f"Paystack transfer failed for {provider_user.username}, Order {order.order_id}: {error_msg}")

                    except requests.exceptions.RequestException as transfer_e:
                        all_provider_payouts_successful_for_this_order = False
                        failed_payouts_info.append(f"Order {order.order_id}, Provider {provider_user.username}: API Error during transfer - {transfer_e}")
                        logger.error(f"Paystack API error during transfer for {provider_user.username}, Order {order.order_id}: {transfer_e}")

                except ServiceProviderProfile.DoesNotExist:
                    all_provider_payouts_successful_for_this_order = False
                    failed_payouts_info.append(f"Order {order.order_id}: ServiceProviderProfile not found for {provider_user.username}.")
                except Exception as e: 
                    all_provider_payouts_successful_for_this_order = False
                    failed_payouts_info.append(f"Order {order.order_id}, Provider {provider_user.username}: Unexpected error - {str(e)}")
                    logger.exception(f"Unexpected error processing payout for provider {provider_user.username}, Order {order.order_id}")
            
            if all_provider_payouts_successful_for_this_order:
                order.status = 'COMPLETED' 
                order.save(update_fields=['status'])
                processed_orders += 1
        else:
            failed_payouts_info.append(f"Order {order.order_id}: Not eligible for payout (Status: {order.get_status_display()}, Method: {order.get_payment_method_display()}).")

    if processed_orders > 0:
        modeladmin.message_user(request, _(f"{processed_orders} order(s) successfully processed for payout and marked as completed."))
    if failed_payouts_info:
        for info in failed_payouts_info:
            modeladmin.message_user(request, info, level='WARNING')
    if not processed_orders and not failed_payouts_info:
        modeladmin.message_user(request, _("No orders were selected or eligible for payout processing."), level='INFO')

process_provider_payouts.short_description = _("Process Payouts to Providers (Simulated)")

# --- START: New Admin Action for Vendor Payouts ---
def process_vendor_payouts(modeladmin, request, queryset):
    """
    Admin action to process payouts for product vendors for selected orders.
    """
    processed_orders_count = 0
    failed_payouts_info = []

    for order in queryset:
        if order.status == 'PENDING_PAYOUT' and order.payment_method == 'escrow':
            # Aggregate amounts per vendor for this order
            vendor_payout_data = {} # {vendor_instance: {amount_to_payout: Decimal, commission_earned: Decimal, items_info: str}}

            product_items_for_payout = order.items.filter(product__isnull=False)
            if not product_items_for_payout.exists():
                failed_payouts_info.append(f"Order {order.order_id}: No product items found for vendor payout.")
                continue

            for item in product_items_for_payout:
                if not item.product or not item.product.vendor:
                    failed_payouts_info.append(f"Order {order.order_id}, Item {item.product_name or item.id}: Missing product or vendor link.")
                    continue
                
                vendor = item.product.vendor
                item_total_value = item.price * item.quantity
                
                platform_commission_for_item = item_total_value * settings.PLATFORM_COMMISSION_RATE
                amount_to_payout_for_item = item_total_value - platform_commission_for_item
                
                if vendor not in vendor_payout_data:
                    vendor_payout_data[vendor] = {'amount_to_payout': Decimal('0.00'), 'commission_earned': Decimal('0.00'), 'items_info': []}
                
                vendor_payout_data[vendor]['amount_to_payout'] += amount_to_payout_for_item
                vendor_payout_data[vendor]['commission_earned'] += platform_commission_for_item
                vendor_payout_data[vendor]['items_info'].append(f"{item.quantity}x {item.product_name}")

            if not vendor_payout_data:
                failed_payouts_info.append(f"Order {order.order_id}: No vendors identified for product payout.")
                continue

            all_vendor_payouts_successful_for_this_order = True
            for vendor, payout_details in vendor_payout_data.items():
                payout_amount_decimal = payout_details['amount_to_payout']
                total_commission_for_vendor_items = payout_details['commission_earned']
                items_description = "; ".join(payout_details['items_info'])

                if payout_amount_decimal <= 0:
                    logger.info(f"Order {order.order_id}, Vendor {vendor.name}: Payout amount is zero or less, skipping transfer.")
                    # Still log commission if earned
                    Transaction.objects.create(
                        order=order,
                        transaction_type='platform_commission',
                        amount=total_commission_for_vendor_items,
                        status='completed',
                        description=f"Platform commission from Order {order.order_id} (Vendor: {vendor.name}, Items: {items_description})")
                    continue # Move to next vendor or mark order as processed if this was the only one

                try:
                    if not (vendor.mobile_money_number and vendor.mobile_money_provider):
                        all_vendor_payouts_successful_for_this_order = False
                        failed_payouts_info.append(f"Order {order.order_id}: Vendor {vendor.name} missing payout details.")
                        continue

                    recipient_code = vendor.paystack_recipient_code
                    if not recipient_code:
                        recipient_code, error_msg = create_paystack_transfer_recipient_for_vendor(vendor)
                        if error_msg:
                            all_vendor_payouts_successful_for_this_order = False
                            failed_payouts_info.append(f"Order {order.order_id}, Vendor {vendor.name}: Failed to create recipient - {error_msg}")
                            continue
                    
                    transfer_url = "https://api.paystack.co/transfer"
                    headers = {
                        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                        "Content-Type": "application/json",
                    }
                    amount_in_kobo = int(payout_amount_decimal * 100)
                    # idempotency_key = str(uuid.uuid4()) # Idempotency key for Paystack transfers is usually set in header if supported, or part of reference.

                    transfer_payload = {
                        "source": "balance",
                        "amount": amount_in_kobo,
                        "recipient": recipient_code,
                        "reason": f"Payout for Order {order.order_id} - Products by {vendor.name}",
                        "currency": "GHS",
                    }
                    
                    logger.info(f"ADMIN ACTION: Attempting Paystack transfer of GHS {payout_amount_decimal} to VENDOR {vendor.name} for Order {order.order_id}")
                    
                    try:
                        transfer_response = requests.post(transfer_url, headers=headers, json=transfer_payload, timeout=30)
                        transfer_response.raise_for_status()
                        transfer_data = transfer_response.json()

                        if transfer_data.get("status") and transfer_data.get("data", {}).get("status") in ['success', 'pending']:
                            Transaction.objects.create(
                                order=order,
                                user=vendor.user, # Link to the vendor's user account
                                transaction_type='payout',
                                amount=payout_amount_decimal,
                                status='pending' if transfer_data["data"]["status"] == 'pending' else 'completed',
                                gateway_transaction_id=transfer_data["data"].get("transfer_code"),
                                description=f"Paystack Payout to VENDOR {vendor.name} for Order {order.order_id}. Items: {items_description}. Status: {transfer_data['data']['status']}"
                            )
                            logger.info(f"Paystack transfer initiated for VENDOR {vendor.name}, Order {order.order_id}. Status: {transfer_data['data']['status']}")

                            Transaction.objects.create(
                                order=order,
                                transaction_type='platform_commission',
                                amount=total_commission_for_vendor_items,
                                status='completed',
                                description=f"Platform commission from Order {order.order_id} (Vendor: {vendor.name}, Items: {items_description})")
                        else:
                            all_vendor_payouts_successful_for_this_order = False
                            error_msg = transfer_data.get("message", "Paystack transfer initiation failed for vendor.")
                            failed_payouts_info.append(f"Order {order.order_id}, Vendor {vendor.name}: Transfer failed - {error_msg}")
                            logger.error(f"Paystack transfer failed for VENDOR {vendor.name}, Order {order.order_id}: {error_msg}")

                    except requests.exceptions.RequestException as transfer_e:
                        all_vendor_payouts_successful_for_this_order = False
                        failed_payouts_info.append(f"Order {order.order_id}, Vendor {vendor.name}: API Error during transfer - {transfer_e}")
                        logger.error(f"Paystack API error during transfer for VENDOR {vendor.name}, Order {order.order_id}: {transfer_e}")

                except Exception as e:
                    all_vendor_payouts_successful_for_this_order = False
                    failed_payouts_info.append(f"Order {order.order_id}, Vendor {vendor.name}: Unexpected error - {str(e)}")
                    logger.exception(f"Unexpected error processing payout for VENDOR {vendor.name}, Order {order.order_id}")
            
            if all_vendor_payouts_successful_for_this_order:
                order.status = 'COMPLETED'
                order.save(update_fields=['status'])
                processed_orders_count += 1
        else:
            failed_payouts_info.append(f"Order {order.order_id}: Not eligible for vendor payout (Status: {order.get_status_display()}, Method: {order.get_payment_method_display()}).")

    if processed_orders_count > 0:
        modeladmin.message_user(request, _(f"{processed_orders_count} order(s) successfully processed for VENDOR payout and marked as completed."))
    if failed_payouts_info:
        for info in failed_payouts_info:
            modeladmin.message_user(request, info, level='WARNING')
    if not processed_orders_count and not failed_payouts_info:
        modeladmin.message_user(request, _("No orders were selected or eligible for VENDOR payout processing."), level='INFO')

process_vendor_payouts.short_description = _("Process Payouts to Product Vendors")
# --- END: New Admin Action for Vendor Payouts ---


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user_link', 'status', 'payment_method', 'total_amount', 'created_at', 'customer_confirmed_delivery_at')
    list_filter = ('status', 'payment_method', 'created_at', 'customer_confirmed_delivery_at')
    search_fields = ('order_id', 'user__username', 'transaction_id', 'shipping_address_text', 'billing_address_text', 'paystack_ref')
    list_editable = ('status',)
    readonly_fields = (
        'order_id', 'user', 'created_at', 'updated_at',
        'total_amount', 'shipping_address_text', 'billing_address_text',
        'transaction_id', 'user_link', 'paystack_ref', 'customer_confirmed_delivery_at'
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    inlines = [OrderItemInline]
    list_select_related = ('user',)
    raw_id_fields = ('user', 'shipping_address', 'billing_address')
    fieldsets = (
        (None, {'fields': ('order_id', 'user_link', 'status', 'payment_method', 'transaction_id', 'paystack_ref')}),
        ('Amount & Timing', {'fields': ('total_amount', 'created_at', 'updated_at')}),
        ('Addresses', {'fields': ('shipping_address', 'shipping_address_text', 'billing_address', 'billing_address_text')}),
        ('Notes', {'fields': ('notes',), 'classes': ('collapse',)}),
    )
    actions = [mark_direct_payment_received, process_provider_payouts, process_vendor_payouts] # <<< Added process_vendor_payouts
    def user_link(self, obj):
        if obj.user:
            try:
                link = reverse("admin:authapp_customuser_change", args=[obj.user.id])
            except:
                try:
                    link = reverse("admin:auth_user_change", args=[obj.user.id])
                except:
                    return obj.user.username
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "Guest / Deleted User"
    user_link.short_description = 'User'
    def shipping_address_present(self, obj): return bool(obj.shipping_address or obj.shipping_address_text)
    shipping_address_present.boolean = True; shipping_address_present.short_description = 'Ship Addr'
    def billing_address_present(self, obj): return bool(obj.billing_address or obj.billing_address_text)
    billing_address_present.boolean = True; billing_address_present.short_description = 'Bill Addr'

@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_link', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'product__name', 'product__vendor__name')
    list_select_related = ('user', 'product', 'product__vendor')
    raw_id_fields = ('user', 'product')
    ordering = ('-added_at',)

    def product_link(self, obj):
        if obj.product:
            link = reverse("admin:core_product_change", args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', link, obj.product.name)
        return "N/A"
    product_link.short_description = 'Product'

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product_link', 'user_link', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__username', 'review')
    list_editable = ('is_approved',)
    list_select_related = ('product', 'user', 'product__vendor')
    raw_id_fields = ('product', 'user')
    ordering = ('-created_at',)

    def product_link(self, obj):
        if obj.product:
            link = reverse("admin:core_product_change", args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', link, obj.product.name)
        return "N/A"
    product_link.short_description = 'Product'

    def user_link(self, obj):
        if obj.user:
            try:
                link = reverse("admin:authapp_customuser_change", args=[obj.user.id])
            except:
                try:
                    link = reverse("admin:auth_user_change", args=[obj.user.id])
                except:
                    return obj.user.username
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "N/A"
    user_link.short_description = 'User'

# --- START: RiderProfile Admin ---
@admin.register(RiderProfile)
class RiderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'vehicle_type', 'is_approved', 'is_available', 'created_at')
    list_filter = ('is_approved', 'is_available', 'vehicle_type', 'created_at')
    search_fields = ('user__username', 'phone_number', 'vehicle_registration_number', 'license_number')
    list_editable = ('is_approved', 'is_available')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at', 
                       'view_current_vehicle_registration_document', 
                       'view_current_drivers_license_front', 'view_current_drivers_license_back',
                       'view_current_id_card_front', 'view_current_id_card_back',
                       'view_current_vehicle_picture')
    fieldsets = (
        (None, {'fields': ('user', 'phone_number', 'address')}),
        ('Vehicle Information', {'fields': ('vehicle_type', 'vehicle_registration_number', 'license_number')}),
        ('Status & Availability', {'fields': ('is_approved', 'is_available')}),
        ('Current Verification Documents', {
            'fields': (('current_vehicle_registration_document', 'view_current_vehicle_registration_document'), 
                       ('current_drivers_license_front', 'view_current_drivers_license_front'), ('current_drivers_license_back', 'view_current_drivers_license_back'),
                       ('current_id_card_front', 'view_current_id_card_front'), ('current_id_card_back', 'view_current_id_card_back'),
                       ('current_vehicle_picture', 'view_current_vehicle_picture'))
        }),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def _get_document_view_link(self, document_field):
        if document_field and hasattr(document_field, 'url'):
            return format_html('<a href="{}" target="_blank">View Current Document</a>', document_field.url)
        return "No document uploaded."

    def view_current_vehicle_registration_document(self, obj):
        return self._get_document_view_link(obj.current_vehicle_registration_document)
    view_current_vehicle_registration_document.short_description = 'View Reg. Doc'

    def view_current_drivers_license_front(self, obj):
        return self._get_document_view_link(obj.current_drivers_license_front)
    view_current_drivers_license_front.short_description = 'View License (Front)'

    def view_current_drivers_license_back(self, obj):
        return self._get_document_view_link(obj.current_drivers_license_back)
    view_current_drivers_license_back.short_description = 'View License (Back)'

    def view_current_id_card_front(self, obj):
        return self._get_document_view_link(obj.current_id_card_front)
    view_current_id_card_front.short_description = 'View ID (Front)'

    def view_current_id_card_back(self, obj):
        return self._get_document_view_link(obj.current_id_card_back)
    view_current_id_card_back.short_description = 'View ID (Back)'

    def view_current_vehicle_picture(self, obj):
        if obj.current_vehicle_picture and hasattr(obj.current_vehicle_picture, 'url'):
            return format_html('<a href="{}" target="_blank"><img src="{}" width="100" height="auto" /></a>', 
                               obj.current_vehicle_picture.url, obj.current_vehicle_picture.url)
        return "No picture uploaded."
    view_current_vehicle_picture.short_description = 'View Vehicle Pic'
# --- END: RiderProfile Admin ---

# --- START: DeliveryTask Admin ---
@admin.register(DeliveryTask)
class DeliveryTaskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'order_link', 'rider_link', 'status', 'delivery_fee', 'rider_earning', 'platform_commission', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'rider__user__username')
    search_fields = ('task_id', 'order__order_id', 'rider__user__username', 'pickup_address_text', 'delivery_address_text')
    list_editable = ('status',)
    raw_id_fields = ('order', 'rider')
    readonly_fields = ('task_id', 'created_at', 'updated_at', 'rider_earning', 'platform_commission', 'pickup_latitude', 'pickup_longitude', 'delivery_latitude', 'delivery_longitude')
    fieldsets = (
        (None, {'fields': ('task_id', 'order', 'rider', 'status')}),
        ('Address Information', {'fields': ('pickup_address_text', ('pickup_latitude', 'pickup_longitude'), 
                                           'delivery_address_text', ('delivery_latitude', 'delivery_longitude'))}),
        ('Financials', {'fields': ('delivery_fee', 'rider_earning', 'platform_commission')}),
        ('Timestamps & Details', {'fields': ('estimated_pickup_time', 'actual_pickup_time', 
                                           'estimated_delivery_time', 'actual_delivery_time', 
                                           'special_instructions', 'created_at', 'updated_at'), 
                                 'classes': ('collapse',)}),
    )

    def order_link(self, obj):
        link = reverse("admin:core_order_change", args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', link, obj.order.order_id)
    order_link.short_description = 'Order'

    def rider_link(self, obj):
        if obj.rider:
            link = reverse("admin:core_riderprofile_change", args=[obj.rider.id])
            return format_html('<a href="{}">{}</a>', link, obj.rider.user.username)
        return _("N/A")
    rider_link.short_description = 'Assigned Rider'

# --- START: PricingPlan Admin ---
@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'price', 'currency', 'duration_days', 'is_active', 'display_order')
    list_filter = ('is_active', 'plan_type', 'currency')
    list_editable = ('price', 'is_active', 'display_order')
    search_fields = ('name', 'description')
    ordering = ('display_order', 'price')
# --- END: PricingPlan Admin ---
# --- END: DeliveryTask Admin ---

@admin.register(RiderApplication)
class RiderApplicationAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'phone_number', 'vehicle_type', 'submitted_at', 'is_reviewed', 'is_approved')
    list_filter = ('is_reviewed', 'is_approved', 'vehicle_type', 'submitted_at')
    search_fields = ('user__username', 'phone_number', 'vehicle_registration_number', 'license_number')
    list_editable = ('is_reviewed', 'is_approved')
    raw_id_fields = ('user',)
    readonly_fields = ('submitted_at', 'view_vehicle_registration_document_link', 
                       'view_drivers_license_front_link', 'view_drivers_license_back_link', 
                       'view_id_card_front_link', 'view_id_card_back_link', 
                       'view_profile_picture_link', 'view_vehicle_picture_link')
    fieldsets = (
        (None, {'fields': ('user',)}),
        ('Contact & Vehicle', {'fields': ('phone_number', 'address', 'vehicle_type', 'vehicle_registration_number', 'license_number')}),
        ('Documents', {
            'fields': (
                ('vehicle_registration_document', 'view_vehicle_registration_document_link'),
                ('drivers_license_front', 'view_drivers_license_front_link'),
                ('drivers_license_back', 'view_drivers_license_back_link'),
                ('id_card_front', 'view_id_card_front_link'),
                ('id_card_back', 'view_id_card_back_link'),
                ('profile_picture', 'view_profile_picture_link'),
                ('vehicle_picture', 'view_vehicle_picture_link'),
            )
        }),
        ('Status', {'fields': ('agreed_to_terms', 'is_reviewed', 'is_approved')}),
        ('Timestamps', {'fields': ('submitted_at',), 'classes': ('collapse',)}),
    )

    def user_link(self, obj):
        if obj.user:
            link = reverse("admin:authapp_customuser_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return _("N/A")
    user_link.short_description = 'Applicant'

    def _get_doc_view_html(self, doc_field, is_image=False):
        if doc_field and hasattr(doc_field, 'url'):
            if is_image:
                return format_html('<a href="{0}" target="_blank"><img src="{0}" width="100" /></a><br/><a href="{0}" target="_blank">View Full</a>', doc_field.url)
            return format_html('<a href="{}" target="_blank">View Document</a>', doc_field.url)
        return _("No document")

    def view_vehicle_registration_document_link(self, obj): return self._get_doc_view_html(obj.vehicle_registration_document)
    def view_drivers_license_front_link(self, obj): return self._get_doc_view_html(obj.drivers_license_front, is_image=True)
    def view_drivers_license_back_link(self, obj): return self._get_doc_view_html(obj.drivers_license_back, is_image=True)
    def view_id_card_front_link(self, obj): return self._get_doc_view_html(obj.id_card_front, is_image=True)
    def view_id_card_back_link(self, obj): return self._get_doc_view_html(obj.id_card_back, is_image=True)
    def view_profile_picture_link(self, obj): return self._get_doc_view_html(obj.profile_picture, is_image=True)
    def view_vehicle_picture_link(self, obj): return self._get_doc_view_html(obj.vehicle_picture, is_image=True)


# --- START: BoostPackage Admin ---
@admin.register(BoostPackage)
class BoostPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'boost_type', 'duration_hours', 'price', 'is_active', 'display_order', 'created_at')
    list_filter = ('boost_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_active', 'display_order', 'duration_hours')
    ordering = ('display_order', 'name')
    fieldsets = (
        (None, {'fields': ('name', 'description', 'boost_type')}),
        ('Details', {'fields': ('duration_hours', 'price', 'icon_class')}),
        ('Status & Ordering', {'fields': ('is_active', 'display_order')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at', 'updated_at')
# --- END: BoostPackage Admin ---

# --- START: ActiveRiderBoost Admin ---
@admin.register(ActiveRiderBoost)
class ActiveRiderBoostAdmin(admin.ModelAdmin):
    list_display = ('rider_profile_link', 'boost_package_link', 'activated_at', 'expires_at', 'is_active')
    list_filter = ('is_active', 'boost_package__boost_type', 'activated_at', 'expires_at')
    search_fields = ('rider_profile__user__username', 'boost_package__name')
    raw_id_fields = ('rider_profile', 'boost_package') # Makes selection easier for ForeignKey fields
    readonly_fields = ('activated_at', 'expires_at') # expires_at is auto-calculated or set
    list_editable = ('is_active',) # Allow manual override of is_active if needed
    ordering = ('-expires_at',)

    def rider_profile_link(self, obj):
        if obj.rider_profile:
            link = reverse("admin:core_riderprofile_change", args=[obj.rider_profile.id])
            return format_html('<a href="{}">{}</a>', link, obj.rider_profile.user.username)
        return "N/A"
    rider_profile_link.short_description = 'Rider'

    def boost_package_link(self, obj):
        link = reverse("admin:core_boostpackage_change", args=[obj.boost_package.id])
        return format_html('<a href="{}">{}</a>', link, obj.boost_package.name)
    boost_package_link.short_description = 'Boost Package'
# --- END: ActiveRiderBoost Admin ---

# --- START: PayoutRequest Admin ---
@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = ('profile_link', 'amount_requested', 'status', 'requested_at', 'processed_at')
    list_filter = ('status', 'requested_at', 'processed_at')
    search_fields = ('rider_profile__user__username', 'vendor_profile__name', 'service_provider_profile__user__username', 'amount_requested')
    list_editable = ('status',) # Allow admin to change status
    raw_id_fields = ('rider_profile', 'vendor_profile', 'service_provider_profile', 'transaction')
    readonly_fields = ('requested_at', 'processed_at', 'transaction') # transaction is linked when payout is made
    actions = ['mark_as_processing', 'mark_as_completed', 'mark_as_rejected']

    fieldsets = (
        (None, {'fields': ('rider_profile', 'vendor_profile', 'service_provider_profile', 'amount_requested', 'status', 'payment_method_details')}),
        ('Processing Details', {'fields': ('admin_notes', 'transaction', 'processed_at')}),
        ('Timestamps', {'fields': ('requested_at',), 'classes': ('collapse',)}),
    )

    def profile_link(self, obj):
        if obj.rider_profile:
            link = reverse("admin:core_riderprofile_change", args=[obj.rider_profile.id])
            return format_html('Rider: <a href="{}">{}</a>', link, obj.rider_profile.user.username)
        elif obj.vendor_profile:
            link = reverse("admin:core_vendor_change", args=[obj.vendor_profile.id])
            return format_html('Vendor: <a href="{}">{}</a>', link, obj.vendor_profile.name)
        elif obj.service_provider_profile:
            link = reverse("admin:core_serviceproviderprofile_change", args=[obj.service_provider_profile.id])
            return format_html('Provider: <a href="{}">{}</a>', link, obj.service_provider_profile.user.username)
        return "N/A"
    profile_link.short_description = 'Profile'

    def get_queryset(self, request):
        # Prefetch related profiles for efficiency in profile_link
        return super().get_queryset(request).select_related(
            'rider_profile__user', 
            'vendor_profile__user', 
            'service_provider_profile__user'
        )

    def mark_as_processing(self, request, queryset):
        updated_count = queryset.update(status='processing', admin_notes=F('admin_notes') + _("\nMarked as processing by admin."))
        self.message_user(request, _(f"{updated_count} payout request(s) marked as processing."))
    mark_as_processing.short_description = _("Mark selected requests as Processing")

    def mark_as_rejected(self, request, queryset):
        # For rejections, it's often good to have a more detailed reason.
        # This basic action just updates the status. You might want a custom form action for adding detailed notes.
        updated_count = queryset.update(status='rejected', admin_notes=F('admin_notes') + _("\nRejected by admin."))
        self.message_user(request, _(f"{updated_count} payout request(s) marked as rejected."))
    mark_as_rejected.short_description = _("Mark selected requests as Rejected")

    def mark_as_completed(self, request, queryset):
        successful_payouts = 0
        failed_payouts = 0

        for payout_request in queryset.filter(status__in=['pending', 'processing']):
            try:
                with db_transaction.atomic(): # Ensure all operations succeed or fail together
                    
                    target_user = None
                    profile_name_for_desc = "Unknown"
                    if payout_request.rider_profile:
                        target_user = payout_request.rider_profile.user
                        profile_name_for_desc = f"rider {target_user.username}"
                    elif payout_request.vendor_profile:
                        target_user = payout_request.vendor_profile.user
                        profile_name_for_desc = f"vendor {payout_request.vendor_profile.name}"
                    elif payout_request.service_provider_profile:
                        target_user = payout_request.service_provider_profile.user
                        profile_name_for_desc = f"provider {target_user.username}"

                    if not target_user:
                        logger.error(f"Payout request {payout_request.id} has no associated user profile. Skipping.")
                        failed_payouts +=1
                        continue

                    # Create the payout transaction
                    payout_transaction = Transaction.objects.create(
                        user=target_user,
                        transaction_type='payout',
                        amount=payout_request.amount_requested,
                        currency="GHS", # Assuming GHS, adjust if needed
                        status='completed', # Assuming payout is immediately completed by admin action
                        description=f"Payout to {profile_name_for_desc} for request ID {payout_request.id}.",
                        # gateway_transaction_id: If you have a manual reference, add it here.
                        # For Paystack, this would be the transfer_code after initiating a transfer.
                    )

                    # Update the PayoutRequest
                    payout_request.status = 'completed'
                    payout_request.processed_at = timezone.now()
                    payout_request.transaction = payout_transaction # Link the transaction
                    payout_request.admin_notes = (payout_request.admin_notes or "") + _("\nPayout marked as completed by admin.")
                    payout_request.save()

                    # TODO: (Future) Integrate with Paystack Transfers API here to initiate actual payment
                    # For now, this action assumes the payment is handled manually or by another system,
                    # and this admin action is just to record it in Nexus.

                    successful_payouts += 1
                    logger.info(f"Payout request {payout_request.id} for {profile_name_for_desc} marked as completed. Transaction ID: {payout_transaction.id}")

            except Exception as e:
                failed_payouts += 1
                logger.error(f"Error processing payout request {payout_request.id}: {e}")
                self.message_user(request, _(f"Error processing payout for request ID {payout_request.id}: {e}"), level=messages.ERROR)

        if successful_payouts > 0:
            self.message_user(request, _(f"{successful_payouts} payout request(s) successfully marked as completed and transaction(s) created."))
        if failed_payouts > 0:
            self.message_user(request, _(f"{failed_payouts} payout request(s) failed to process or had no associated user."), level=messages.WARNING)
        if successful_payouts == 0 and failed_payouts == 0:
            self.message_user(request, _("No eligible payout requests were processed. Ensure they are in 'Pending' or 'Processing' status."), level=messages.INFO)
    mark_as_completed.short_description = _("Mark selected requests as Completed (and create transaction)")

# --- END: PayoutRequest Admin ---


@admin.register(VendorReview)
class VendorReviewAdmin(admin.ModelAdmin):
    list_display = ('vendor_link', 'user_link', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('vendor__name', 'user__username', 'comment')
    list_editable = ('is_approved',)
    list_select_related = ('vendor', 'user')
    raw_id_fields = ('vendor', 'user')
    ordering = ('-created_at',)

    def vendor_link(self, obj):
        if obj.vendor:
            link = reverse("admin:core_vendor_change", args=[obj.vendor.id])
            return format_html('<a href="{}">{}</a>', link, obj.vendor.name)
        return "N/A"
    vendor_link.short_description = 'Vendor'

    def user_link(self, obj):
        if obj.user:
            try:
                link = reverse("admin:authapp_customuser_change", args=[obj.user.id])
            except:
                try:
                    link = reverse("admin:auth_user_change", args=[obj.user.id])
                except:
                    return obj.user.username
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "N/A"
    user_link.short_description = 'User'

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    fields = ('image', 'alt_text')
    readonly_fields = ('uploaded_at',)

class ServiceVideoInline(admin.TabularInline):
    model = ServiceVideo
    extra = 1
    fields = ('video', 'title', 'description')
    readonly_fields = ('uploaded_at',)

class ServicePackageInline(admin.TabularInline):
    model = ServicePackage
    extra = 1
    fields = ('name', 'description', 'price', 'delivery_time', 'revisions', 'display_order', 'is_active')
    ordering = ('display_order', 'price')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'category', 'price', 'location', 'is_active', 'is_featured', 'created_at')
    list_filter = ('is_active', 'is_featured', 'category', 'location', 'created_at')
    search_fields = ('title', 'description', 'provider__username', 'category__name')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('provider', 'category')
    ordering = ('-created_at',)
    inlines = [ServicePackageInline, ServiceImageInline, ServiceVideoInline]
    list_editable = ('is_active', 'is_featured')

@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    list_display = ('service', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating', 'created_at')
    search_fields = ('service__title', 'user__username', 'comment')
    list_editable = ('is_approved',)
    raw_id_fields = ('service', 'user')
    ordering = ('-created_at',)

class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'service', 'price', 'delivery_time', 'revisions', 'display_order', 'is_active')
    list_filter = ('is_active', 'service__category', 'service__provider')
    search_fields = ('name', 'description', 'service__title')
    list_editable = ('price', 'delivery_time', 'revisions', 'display_order', 'is_active')

admin.site.register(ServicePackage, ServicePackageAdmin)

class PortfolioItemInline(admin.TabularInline):
    model = PortfolioItem
    extra = 1
    fields = ('title', 'description', 'image', 'link')


@admin.register(ServiceProviderProfile)
class ServiceProviderProfileAdmin(admin.ModelAdmin):
    list_display = ('user_display_name', 'business_name', 'is_approved', 'active_service_count', 'total_service_revenue_display', 'view_services_link', 'view_service_orders_link', 'view_payout_requests_link', 'created_at', 'paystack_recipient_code')
    list_filter = ('is_approved',) 
    search_fields = ('user__username', 'business_name', 'user__email')
    raw_id_fields = ('user',) 
    list_editable = ('is_approved',)
    readonly_fields = ('paystack_recipient_code', 'created_at', 'updated_at') 
    fieldsets = (
        (None, {'fields': ('user', 'business_name', 'bio', 'is_approved')}),
        ('Payout Information', {'fields': (
            'mobile_money_provider', 'mobile_money_number',
            'paypal_email',
            'bank_account_name', 'bank_account_number', 'bank_name', 'bank_branch',
            'paystack_recipient_code',
            'stripe_account_id', 'payoneer_email', 'wise_email',
            'crypto_wallet_address', 'crypto_wallet_network'
        )}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    inlines = [PortfolioItemInline]

    def user_display_name(self, obj):
        return obj.user.username
    user_display_name.short_description = 'User'
    user_display_name.admin_order_field = 'user__username'

    def active_service_count(self, obj):
        return Service.objects.filter(provider=obj.user, is_active=True).count()
    active_service_count.short_description = 'Active Services'

    def total_service_revenue_display(self, obj):
        total = OrderItem.objects.filter(
            service_package__service__provider=obj.user,
            order__status__in=['COMPLETED'] # Assuming 'COMPLETED' means service delivered and paid
        ).aggregate(total_revenue=Sum(F('price') * F('quantity')))['total_revenue']
        return f"GH₵ {total.quantize(Decimal('0.01'), ROUND_HALF_UP) if total else '0.00'}"
    total_service_revenue_display.short_description = 'Total Revenue (GH₵)'

    def view_services_link(self, obj):
        url = reverse("admin:core_service_changelist") + f"?provider__id__exact={obj.user.id}"
        return format_html('<a href="{}">View Services</a>', url)
    view_services_link.short_description = 'Services'

    def view_service_orders_link(self, obj):
        url = reverse("admin:core_order_changelist") + f"?items__service_package__service__provider__id__exact={obj.user.id}"
        return format_html('<a href="{}">View Orders</a>', url)
    view_service_orders_link.short_description = 'Service Orders'

    def view_payout_requests_link(self, obj):
        url = reverse("admin:core_payoutrequest_changelist") + f"?service_provider_profile__id__exact={obj.id}"
        return format_html('<a href="{}">View Payouts</a>', url)
    view_payout_requests_link.short_description = 'Payout Requests'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_link', 'user_link', 'transaction_type', 'amount', 'currency', 'status', 'gateway_transaction_id', 'created_at')
    list_filter = ('transaction_type', 'status', 'currency', 'created_at')
    search_fields = ('order__order_id', 'user__username', 'gateway_transaction_id', 'description')
    list_select_related = ('order', 'user')
    raw_id_fields = ('order', 'user')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    def order_link(self, obj):
        if obj.order:
            link = reverse("admin:core_order_change", args=[obj.order.id])
            return format_html('<a href="{}">{}</a>', link, obj.order.order_id)
        return "N/A"
    order_link.short_description = 'Order'

    def user_link(self, obj):
        if obj.user:
            try:
                link = reverse("admin:authapp_customuser_change", args=[obj.user.id])
            except:
                try:
                    link = reverse("admin:auth_user_change", args=[obj.user.id])
                except:
                    return obj.user.username
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "N/A"
    user_link.short_description = 'User'
@admin.register(FraudReport)
class FraudReportAdmin(admin.ModelAdmin):
    list_display = ('order_link', 'risk_score', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_id', 'reasons')
    list_editable = ('status',)
    readonly_fields = ('order_link', 'risk_score', 'reasons', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    def order_link(self, obj):
        link = reverse("admin:core_order_change", args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', link, obj.order.order_id)
    order_link.short_description = 'Order'