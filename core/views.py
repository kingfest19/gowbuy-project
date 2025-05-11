# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, models # For atomic operations like placing orders
from django.db.models import Prefetch, Q, Avg, Sum, F, Count # For more complex queries, Import Avg, Sum, F, Count
from decimal import Decimal # For calculations
from django.urls import reverse # Added for cart item URLs
import logging
from django.views.decorators.http import require_POST # For actions like add/remove wishlist/review
import requests # Import requests library for Paystack API calls
# --- Import Forms ---#
from .forms import (
    VendorReviewForm, ProductReviewForm, VendorRegistrationForm, VendorVerificationForm, VendorProfileUpdateForm,
    VendorShippingForm, VendorPaymentForm, PromotionForm, AdCampaignForm, VendorProductForm,
    VendorAdditionalInfoForm, ServiceForm, ServiceReviewForm, ServiceSearchForm, ServicePackageFormSet, AddressForm
)
from authapp.forms import UserProfileUpdateForm # <<< Import UserProfileUpdateForm

# --- Import your actual models ---
from .models import (
    Product, Category, Order, OrderItem, Address, Vendor, Promotion, AdCampaign, ProductImage,
    WishlistItem, ProductReview, VendorReview, ProductVideo, # ProductImage was duplicated, ProductVideo added
    ServiceCategory, Service, ServiceReview, ServiceImage, ServiceVideo, ServicePackage # Service models
)
# ---------------------------------------------------------
# --- START: Imports for i18n and timezone ---
from django.utils.translation import activate, check_for_language, get_language, gettext_lazy as _
from django.utils import timezone # For setting confirmation timestamp
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect, Http404, FileResponse, HttpResponseForbidden
from django.urls import translate_url
# --- END: Added imports for update_language ---

logger = logging.getLogger(__name__)


# --- View for a single product page ---
def product_detail(request, product_slug):
    """Displays details for a single product, including vendor and reviews."""
    product_obj = get_object_or_404(
        Product.objects.select_related('vendor', 'category'),
        slug=product_slug,
        is_active=True,
        vendor__is_approved=True
    )

    product_images = product_obj.images.all()
    product_videos = product_obj.videos.all()

    related_products = Product.objects.filter(
        category=product_obj.category, is_active=True, vendor__is_approved=True
    ).exclude(id=product_obj.id).select_related('vendor')[:4]

    product_reviews = ProductReview.objects.filter(
        product=product_obj,
        is_approved=True
    ).select_related('user').order_by('-created_at')

    average_product_rating = product_reviews.aggregate(Avg('rating'))['rating__avg']

    is_in_wishlist = False
    user_has_reviewed_product = False
    review_form = ProductReviewForm()

    if request.user.is_authenticated:
        is_in_wishlist = WishlistItem.objects.filter(user=request.user, product=product_obj).exists()
        user_has_reviewed_product = ProductReview.objects.filter(user=request.user, product=product_obj).exists()

    context = {
        'product': product_obj,
        'product_images': product_images,
        'product_videos': product_videos,
        'related_products': related_products,
        'product_reviews': product_reviews,
        'average_product_rating': average_product_rating,
        'is_in_wishlist': is_in_wishlist,
        'review_form': review_form,
        'user_has_reviewed_product': user_has_reviewed_product,
    }
    return render(request, 'core/product_detail.html', context)

# --- START: REPLACED home VIEW ---
def home(request):
    """Displays the homepage with featured products, categories, and new items."""
    featured_products = Product.objects.filter(
        is_active=True,
        is_featured=True,
        vendor__is_approved=True
    ).select_related('vendor')[:8]

    categories = Category.objects.filter(is_active=True, parent=None)[:6]

    new_products = Product.objects.filter(
        is_active=True,
        vendor__is_approved=True
    ).order_by('-created_at')[:8]

    context = {
        'featured_products': featured_products,
        'categories': categories,
        'new_products': new_products,
    }
    return render(request, 'core/home.html', context)
# --- END: REPLACED home VIEW ---


# --- START: Context Processor for Menu ---
def menu(request):
    categories = Category.objects.filter(is_active=True, parent=None)
    # print(f"DEBUG: Product Categories for menu context: {list(categories)}")
    service_categories = ServiceCategory.objects.filter(is_active=True, parent=None)
    current_language = get_language()
    delivery_location = request.session.get('delivery_location', _("Select Location"))
    modal_categories = Category.objects.filter(is_active=True).order_by('name')

    context = {
        'categories': categories,
        'service_categories': service_categories,
        'modal_categories': modal_categories,
        'current_language': current_language,
        'delivery_location': delivery_location,
    }
    return context
# --- END: Context Processor for Menu ---

# --- View for a specific category page ---
def category_detail(request, category_slug):
    """Displays products belonging to a specific category."""
    category_obj = get_object_or_404(Category, slug=category_slug, is_active=True)
    products = Product.objects.filter(
        category=category_obj,
        is_active=True,
        vendor__is_approved=True
    ).order_by('name').select_related('vendor')
    context = {
        'category': category_obj,
        'products': products,
    }
    return render(request, 'core/category_detail.html', context)


# --- Vendor Views ---
def vendor_list(request):
    """Displays a list of approved vendors."""
    vendors = Vendor.objects.filter(is_approved=True).order_by('name')
    context = {'vendors': vendors}
    return render(request, 'core/vendor_list.html', context)


def vendor_detail(request, vendor_slug):
    """Displays a specific vendor's profile, products, and reviews."""
    vendor = get_object_or_404(Vendor, slug=vendor_slug, is_approved=True)
    products = Product.objects.filter(
        vendor=vendor,
        is_active=True
    ).order_by('-created_at').select_related('category')

    vendor_reviews = VendorReview.objects.filter(
        vendor=vendor,
        is_approved=True
    ).select_related('user').order_by('-created_at')

    average_vendor_rating = vendor_reviews.aggregate(Avg('rating'))['rating__avg']
    review_form = VendorReviewForm()
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = VendorReview.objects.filter(user=request.user, vendor=vendor).exists()

    context = {
        'vendor': vendor,
        'products': products,
        'vendor_reviews': vendor_reviews,
        'average_vendor_rating': average_vendor_rating,
        'review_form': review_form,
        'user_has_reviewed': user_has_reviewed,
    }
    return render(request, 'core/vendor_detail.html', context)


# --- Cart Views (Using Session) ---
def cart(request):
    """Displays the current shopping cart contents."""
    cart_session = request.session.get('cart', {})
    product_ids = cart_session.keys()
    products_in_cart = Product.objects.filter(
        id__in=product_ids,
        is_active=True,
        vendor__is_approved=True
    ).select_related('vendor')

    cart_items = []
    cart_total = Decimal('0.00')
    unavailable_items = False
    product_dict = {str(p.id): p for p in products_in_cart}
    items_to_remove = []

    for product_id, item_data in cart_session.items():
        product = product_dict.get(product_id)
        if product:
            quantity = item_data.get('quantity', 0)
            if quantity > 0:
                total_item_price = product.price * quantity
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total_item_price': total_item_price,
                })
                cart_total += total_item_price
            else:
                items_to_remove.append(product_id)
        else:
            unavailable_items = True
            items_to_remove.append(product_id)

    if items_to_remove:
        cart_modified = False
        for item_id in items_to_remove:
            if item_id in cart_session:
                del cart_session[item_id]
                cart_modified = True
        if cart_modified:
            request.session['cart'] = cart_session
            request.session.modified = True
            if unavailable_items:
                messages.warning(request, "Some items in your cart are no longer available and have been removed.")

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
    }
    return render(request, 'core/cart.html', context)

def add_to_cart(request):
    """Adds a product to the session cart."""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0:
                messages.error(request, "Quantity must be positive.")
                return redirect(request.META.get('HTTP_REFERER', reverse('core:home')))
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity specified.")
            return redirect(request.META.get('HTTP_REFERER', reverse('core:home')))

        product = get_object_or_404(Product, id=product_id, is_active=True, vendor__is_approved=True)
        cart_session = request.session.get('cart', {})
        product_key = str(product.id)
        current_quantity_in_cart = cart_session.get(product_key, {}).get('quantity', 0)
        requested_total_quantity = current_quantity_in_cart + quantity

        if product.product_type == 'physical' and product.stock < requested_total_quantity : # Check stock for physical products
            messages.warning(request, f"Sorry, only {product.stock} units of '{product.name}' available. Cannot add {quantity} to cart.")
        else:
            cart_session[product_key] = {'quantity': requested_total_quantity}
            request.session['cart'] = cart_session
            request.session.modified = True
            messages.success(request, f"Added {quantity} x '{product.name}' to your cart.")
        return redirect('cart')
    else:
        messages.warning(request, "Please use the 'Add to Cart' button on a product page.")
        return redirect('core:home')


# --- Checkout Process Views ---
@login_required
def checkout(request):
    """Prepares the checkout page with cart summary and address options."""
    cart_session = request.session.get('cart', {})
    if not cart_session:
        messages.info(request, "Your cart is empty. Please add items before checking out.")
        return redirect('cart')

    product_ids = cart_session.keys()
    products_in_cart = Product.objects.filter(
        id__in=product_ids,
        is_active=True,
        vendor__is_approved=True
    ).select_related('vendor')
    product_dict = {str(p.id): p for p in products_in_cart}

    cart_items = []
    cart_total = Decimal('0.00')
    stock_issue = False
    requires_shipping = False

    for product_id, item_data in cart_session.items():
        product = product_dict.get(product_id)
        if product:
            quantity = item_data.get('quantity', 0)
            if quantity > 0:
                if product.product_type == 'physical' and product.stock < quantity:
                    stock_issue = True
                    messages.error(request, f"Insufficient stock for '{product.name}'. Only {product.stock} available, but you have {quantity} in cart. Please update your cart.")
                if product.product_type == 'physical':
                    requires_shipping = True
                total_item_price = product.price * quantity
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total_item_price': total_item_price,
                })
                cart_total += total_item_price
        else:
             stock_issue = True
             messages.error(request, f"An item in your cart (ID: {product_id}) is no longer available. Please review your cart.")

    if stock_issue:
        return redirect('cart')

    billing_addresses = Address.objects.filter(user=request.user, address_type='billing').order_by('-is_default', '-created_at')
    shipping_addresses = None
    if requires_shipping:
        shipping_addresses = Address.objects.filter(user=request.user, address_type='shipping').order_by('-is_default', '-created_at')
    else:
        messages.info(request, "Your cart contains only digital items. No shipping address required.")

    address_form = AddressForm() # For adding new addresses

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'shipping_addresses': shipping_addresses,
        'billing_addresses': billing_addresses,
        'requires_shipping': requires_shipping,
        'address_form': address_form,
    }
    return render(request, 'core/checkout.html', context)

@login_required
@transaction.atomic
def place_order(request):
    """Handles the creation of an Order from the cart after checkout submission."""
    if request.method == 'POST':
        cart_session = request.session.get('cart', {})
        if not cart_session:
            messages.error(request, "Your cart is empty.")
            return redirect('cart')

        requires_shipping = False
        product_ids_in_cart = cart_session.keys()
        if Product.objects.filter(id__in=product_ids_in_cart, product_type='physical').exists():
            requires_shipping = True

        shipping_address_id = request.POST.get('shipping_address')
        billing_address_id = request.POST.get('billing_address')
        shipping_address = None
        billing_address = None

        try:
            if requires_shipping:
                if not shipping_address_id:
                    messages.error(request, "Shipping address is required for this order.")
                    return redirect('checkout')
                shipping_address = get_object_or_404(Address, id=shipping_address_id, user=request.user, address_type='shipping')

            if billing_address_id and billing_address_id != shipping_address_id: # Check if billing is different from shipping
                billing_address = get_object_or_404(Address, id=billing_address_id, user=request.user, address_type='billing')
            elif shipping_address: # If billing not provided, but shipping is, use shipping as billing
                billing_address = shipping_address
            elif not billing_address_id and not requires_shipping: # All digital, no shipping, but billing ID might be missing
                 messages.error(request, "Billing address is required.") # Or handle creating one
                 return redirect('checkout')
            elif not billing_address_id and requires_shipping and not shipping_address_id: # Should not happen if shipping_address_id is validated
                 messages.error(request, "Billing and Shipping addresses are required.")
                 return redirect('checkout')


        except (Address.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Invalid address selected or ID format incorrect. Please try again.")
            return redirect('checkout')
        
        if not billing_address: # Final check if billing_address is still None
            messages.error(request, "A billing address is required to place an order.")
            return redirect('checkout')


        products_in_cart_qs = Product.objects.select_for_update().filter(
            id__in=product_ids_in_cart,
            is_active=True,
            vendor__is_approved=True
        ).select_related('vendor')
        product_dict = {str(p.id): p for p in products_in_cart_qs}

        order_items_data = []
        final_order_total = Decimal('0.00')
        stock_issue = False

        for product_id, item_data in cart_session.items():
            product = product_dict.get(product_id)
            quantity = item_data.get('quantity', 0)

            if not product or quantity <= 0:
                messages.error(request, f"Item (ID: {product_id}) is invalid or has zero quantity. Please review your cart.")
                stock_issue = True; break

            if product.product_type == 'physical' and product.stock < quantity:
                messages.error(request, f"'{product.name}' stock changed. Only {product.stock} available, but you requested {quantity}. Please update your cart.")
                stock_issue = True; break

            item_total = product.price * quantity
            order_items_data.append({
                'product': product, 'quantity': quantity,
                'price': product.price, 'name': product.name,
                'product_type': product.product_type
            })
            final_order_total += item_total

        if stock_issue: return redirect('cart')

        shipping_address_text_val = None
        if shipping_address:
            shipping_address_text_val = f"{shipping_address.full_name}\n{shipping_address.street_address}\n{shipping_address.apartment_address or ''}\n{shipping_address.city}, {shipping_address.state} {shipping_address.zip_code}\n{shipping_address.country}\n{shipping_address.phone_number or ''}".strip()
        
        billing_address_text_val = None
        if billing_address: # Ensure billing_address is not None before accessing its attributes
             billing_address_text_val = f"{billing_address.full_name}\n{billing_address.street_address}\n{billing_address.apartment_address or ''}\n{billing_address.city}, {billing_address.state} {billing_address.zip_code}\n{billing_address.country}\n{billing_address.phone_number or ''}".strip()


        order = Order.objects.create(
            user=request.user, total_amount=final_order_total,
            shipping_address=shipping_address,
            billing_address=billing_address,
            shipping_address_text=shipping_address_text_val,
            billing_address_text=billing_address_text_val,
            status='PENDING', # Changed to PENDING for payment choice
            ordered=False # Keep ordered=False until payment method is chosen
        )

        order_items_to_create = []
        products_to_update_stock = []
        for item_data in order_items_data:
            product_instance = item_data['product']
            order_items_to_create.append(
                OrderItem(
                    order=order, product=product_instance,
                    product_name=item_data['name'], price=item_data['price'],
                    quantity=item_data['quantity']
                )
            )
            if item_data['product_type'] == 'physical':
                product_instance.stock -= item_data['quantity']
                products_to_update_stock.append(product_instance)

        OrderItem.objects.bulk_create(order_items_to_create)
        if products_to_update_stock:
            Product.objects.bulk_update(products_to_update_stock, ['stock'])

        del request.session['cart']
        request.session.modified = True

        messages.success(request, f"Order #{order.order_id} created. Please choose your payment method.")
        return redirect('core:process_checkout_choice') # Redirect to payment choice page

    else:
        messages.error(request, "Invalid request method.")
        return redirect('checkout')


# --- Order History & Detail Views ---
@login_required
def order_history(request):
    """Displays the logged-in user's order history."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {'orders': orders}
    return render(request, 'core/order_history.html', context)

@login_required
def order_detail(request, order_id):
    """Displays the details of a specific order for the logged-in user."""
    order = get_object_or_404(
        Order.objects.prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.select_related(
                'product__vendor',
                'service_package__service__provider',
                'provider'
                ))
        ).select_related('user'),
        order_id=order_id, user=request.user
    )
    can_confirm_completion = False
    if order.user == request.user and \
       order.payment_method in ['escrow', 'direct'] and \
       order.status in ['PROCESSING', 'IN_PROGRESS', 'AWAITING_DIRECT_PAYMENT'] and \
       order.items.filter(service_package__isnull=False).exists() and \
       order.customer_confirmed_completion_at is None:
        can_confirm_completion = True

    context = {
        'order': order,
        'can_confirm_completion': can_confirm_completion,
    }
    return render(request, 'core/order_detail.html', context)

# --- START: Digital Product Download View ---
@login_required
def download_digital_product(request, order_id, product_id):
    """Allows a logged-in user to download a digital product they purchased."""
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
        order_item = OrderItem.objects.get(order=order, product_id=product_id)
        product = order_item.product
    except (Order.DoesNotExist, OrderItem.DoesNotExist):
        raise Http404("Order or item not found.")

    if not product or product.product_type != 'digital' or not product.digital_file:
        messages.error(request, "This product is not available for download.")
        return redirect('core:order_detail', order_id=order_id)

    # Optional: Check order status
    # if order.status not in ['COMPLETED', 'DELIVERED', 'PROCESSING']: # Adjust based on your flow
    #     messages.warning(request, "Download is available once the order is fully processed.")
    #     return redirect('core:order_detail', order_id=order_id)

    response = FileResponse(product.digital_file.open('rb'), as_attachment=True, filename=product.digital_file.name.split('/')[-1])
    return response
# --- END: Digital Product Download View ---

# --- Wishlist Views ---
@login_required
def wishlist_detail(request):
    """Displays the user's wishlist."""
    wishlist_items = WishlistItem.objects.filter(user=request.user).select_related('product', 'product__vendor').order_by('-added_at')
    context = {'wishlist_items': wishlist_items}
    return render(request, 'core/wishlist_detail.html', context)

@login_required
@require_POST
def add_to_wishlist(request, product_id):
    """Adds a product to the user's wishlist."""
    product = get_object_or_404(Product, id=product_id, is_active=True, vendor__is_approved=True)
    wishlist_item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, f"'{product.name}' added to your wishlist.")
    else:
        messages.info(request, f"'{product.name}' is already in your wishlist.")
    return redirect(request.META.get('HTTP_REFERER', product.get_absolute_url()))

@login_required
@require_POST
def remove_from_wishlist(request, product_id):
    """Removes a product from the user's wishlist."""
    product = get_object_or_404(Product, id=product_id)
    deleted_count, _ = WishlistItem.objects.filter(user=request.user, product=product).delete()
    if deleted_count > 0:
        messages.success(request, f"'{product.name}' removed from your wishlist.")
    else:
        messages.info(request, f"'{product.name}' was not found in your wishlist.")
    return redirect(request.META.get('HTTP_REFERER', reverse('core:wishlist_detail')))


# --- Review Views ---
@login_required
@require_POST
def add_product_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True, vendor__is_approved=True)
    form = ProductReviewForm(request.POST, request.FILES)
    if ProductReview.objects.filter(user=request.user, product=product).exists():
        messages.warning(request, "You have already reviewed this product.")
        return redirect(product.get_absolute_url())
    if form.is_valid():
        if ProductReview.objects.filter(user=request.user, product=product).exists(): # Double check
            messages.warning(request, "You have already reviewed this product.")
            return redirect(product.get_absolute_url())
        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        review.save()
        messages.success(request, "Your review has been submitted successfully.")
    else:
        logger.error(f"Product Review Form Errors: {form.errors.as_json()}")
        messages.error(request, "There was an error submitting your review. Please check the form.")
    return redirect(product.get_absolute_url())

@login_required
@require_POST
def add_vendor_review(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id, is_approved=True)
    form = VendorReviewForm(request.POST)
    if VendorReview.objects.filter(user=request.user, vendor=vendor).exists():
        messages.warning(request, "You have already reviewed this vendor.")
        return redirect(vendor.get_absolute_url())
    if form.is_valid():
        if VendorReview.objects.filter(user=request.user, vendor=vendor).exists(): # Double check
            messages.warning(request, "You have already reviewed this vendor.")
            return redirect(vendor.get_absolute_url())
        review = form.save(commit=False)
        review.user = request.user
        review.vendor = vendor
        review.save()
        messages.success(request, "Your review has been submitted successfully.")
    else:
        logger.error(f"Vendor Review Form Errors: {form.errors.as_json()}")
        messages.error(request, "There was an error submitting your review. Please check the form.")
    return redirect(vendor.get_absolute_url())

# --- Search View ---
def search_results(request):
    """Handles product search queries."""
    query = request.GET.get('q', '').strip()
    results = Product.objects.none()
    if query:
        results = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(vendor__name__icontains=query),
            is_active=True,
            vendor__is_approved=True
        ).select_related('vendor', 'category').distinct()
    context = {'query': query, 'results': results}
    return render(request, 'core/search_results.html', context)

# --- Location Update View ---
def update_location(request):
    """Updates the delivery location stored in the session."""
    if request.method == 'POST':
        new_location = request.POST.get('location_input', '').strip()
        if new_location:
            request.session['delivery_location'] = new_location
            messages.success(request, f"Delivery location updated to {new_location}.")
        else:
            messages.warning(request, "Please enter a location.")
        return redirect(request.META.get('HTTP_REFERER', reverse('core:home')))
    return redirect(reverse('core:home'))

def daily_offers(request):
    """Displays products currently marked as featured/on offer."""
    offer_products = Product.objects.filter(
        is_featured=True,
        is_active=True,
        vendor__is_approved=True
    ).select_related('vendor', 'category').order_by('-created_at')
    context = {'offer_products': offer_products}
    return render(request, 'core/daily_offers.html', context)

def sell_on_nexus(request):
    """Displays information about selling on the platform."""
    return render(request, 'core/sell_on_nexus.html')

# --- Vendor Registration View ---
@login_required
def register_vendor(request):
    """Handles the vendor registration application."""
    if hasattr(request.user, 'vendor_profile'):
        messages.info(request, "You already have a vendor profile.")
        return redirect(reverse('core:vendor_dashboard')) # Redirect to dashboard
    if request.method == 'POST':
        form = VendorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.user = request.user
            vendor.is_approved = False
            vendor.is_verified = False
            vendor.save()
            messages.success(request, "Your vendor application has been submitted successfully! It will be reviewed by our team.")
            return redirect(reverse('core:vendor_dashboard')) # Redirect to dashboard
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = VendorRegistrationForm()
    context = {'form': form}
    return render(request, 'core/vendor_registration.html', context)

# --- Vendor Dashboard View ---
@login_required
def vendor_dashboard(request):
    """Displays the dashboard for the logged-in vendor."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.warning(request, "You do not have a vendor profile. Please apply first.")
        return redirect(reverse('core:sell_on_nexus'))

    vendor_products = Product.objects.filter(vendor=vendor)
    vendor_order_items = OrderItem.objects.filter(product__vendor=vendor)
    total_sales_data = vendor_order_items.aggregate(total=models.Sum(models.F('price') * models.F('quantity')))
    total_sales = total_sales_data['total'] or Decimal('0.00')
    vendor_orders = Order.objects.filter(items__in=vendor_order_items).distinct()
    total_orders_count = vendor_orders.count()
    recent_orders = vendor_orders.order_by('-created_at')[:5]
    total_products_count = vendor_products.count()
    active_products_count = vendor_products.filter(is_active=True).count()
    low_stock_products = vendor_products.filter(is_active=True, stock__lte=5).order_by('stock')[:5]

    shop_info_complete = all([vendor.name, vendor.description, vendor.contact_email, vendor.phone_number, vendor.logo])
    business_info_submitted = vendor.business_registration_doc or vendor.national_id_doc
    business_info_status = "PENDING"
    if vendor.is_verified:
         business_info_status = "COMPLETED"
    elif business_info_submitted:
         business_info_status = "PENDING REVIEW"
    shipping_info_complete = bool(vendor.shipping_policy)
    payment_info_complete = bool(vendor.mobile_money_provider and vendor.mobile_money_number)
    additional_info_complete = True # Placeholder
    all_sections_complete = all([shop_info_complete, vendor.is_verified, shipping_info_complete, payment_info_complete, additional_info_complete])

    context = {
        'vendor': vendor,
        'shop_info_complete': shop_info_complete,
        'business_info_status': business_info_status,
        'shipping_info_complete': shipping_info_complete,
        'payment_info_complete': payment_info_complete,
        'additional_info_complete': additional_info_complete,
        'all_sections_complete': all_sections_complete,
        'total_sales': total_sales,
        'total_orders_count': total_orders_count,
        'total_products_count': total_products_count,
        'active_products_count': active_products_count,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'core/vendor_dashboard.html', context)

# --- Vendor Verification View ---
@login_required
def vendor_verification(request):
    """Handles the submission of vendor verification documents."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You need to register as a vendor first.")
        return redirect(reverse('core:register_vendor'))
    if request.method == 'POST':
        form = VendorVerificationForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, "Verification documents submitted successfully. They will be reviewed by our team.")
            return redirect(reverse('core:vendor_dashboard'))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = VendorVerificationForm(instance=vendor)
    return render(request, 'core/vendor_verification.html', {'form': form, 'vendor': vendor})

# --- Vendor Profile Edit View ---
@login_required
def edit_vendor_profile(request):
    """Allows a vendor to edit their profile details."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect(reverse('core:home'))
    if request.method == 'POST':
        form = VendorProfileUpdateForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect(reverse('core:vendor_dashboard'))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = VendorProfileUpdateForm(instance=vendor)
    context = {'form': form, 'vendor': vendor}
    return render(request, 'core/edit_vendor_profile.html', context)

# --- Vendor Shipping Edit View ---
@login_required
def edit_vendor_shipping(request):
    """Allows a vendor to edit their shipping policy."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect(reverse('core:home'))
    if request.method == 'POST':
        form = VendorShippingForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, "Shipping information updated successfully.")
            return redirect(reverse('core:vendor_dashboard'))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = VendorShippingForm(instance=vendor)
    context = {'form': form, 'vendor': vendor}
    return render(request, 'core/edit_vendor_shipping.html', context)

# --- Vendor Payment Edit View ---
@login_required
def edit_vendor_payment(request):
    """Allows a vendor to edit their payment information."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect(reverse('core:home'))
    if request.method == 'POST':
        form = VendorPaymentForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, "Payment information updated successfully.")
            return redirect(reverse('core:vendor_dashboard'))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = VendorPaymentForm(instance=vendor)
    context = {'form': form, 'vendor': vendor}
    return render(request, 'core/edit_vendor_payment.html', context)

# --- Vendor Additional Info Edit View ---
@login_required
def edit_vendor_additional_info(request):
    """Allows a vendor to edit additional information like return policy."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect(reverse('core:home'))
    if request.method == 'POST':
        form = VendorAdditionalInfoForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, "Additional information updated successfully.")
            return redirect(reverse('core:vendor_dashboard'))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = VendorAdditionalInfoForm(instance=vendor)
    context = {'form': form, 'vendor': vendor}
    return render(request, 'core/edit_vendor_additional_info.html', context)

# --- Vendor Promotions Views ---
@login_required
def vendor_promotion_list(request):
    """Displays a list of promotions created by the vendor."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect(reverse('core:home'))
    promotions = Promotion.objects.filter(applicable_vendor=vendor).order_by('-start_date')
    context = {'promotions': promotions, 'vendor': vendor}
    return render(request, 'core/vendor_promotion_list.html', context)

@login_required
def vendor_promotion_create(request):
    """Handles creation of a new promotion by the vendor."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect(reverse('core:home'))
    if request.method == 'POST':
        form = PromotionForm(request.POST, vendor=vendor)
        if form.is_valid():
            promotion = form.save(commit=False)
            promotion.applicable_vendor = vendor
            promotion.save()
            form.save_m2m()
            messages.success(request, f"Promotion '{promotion.name}' created successfully.")
            return redirect(reverse('core:vendor_promotion_list'))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PromotionForm(vendor=vendor)
    context = {'form': form, 'vendor': vendor, 'form_title': 'Create New Promotion'}
    return render(request, 'core/vendor_promotion_form.html', context)

@login_required
def vendor_promotion_edit(request, promotion_id):
    """Handles editing of an existing promotion by the vendor."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect(reverse('core:home'))
    promotion = get_object_or_404(Promotion, id=promotion_id, applicable_vendor=vendor)
    if request.method == 'POST':
        form = PromotionForm(request.POST, instance=promotion, vendor=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Promotion '{promotion.name}' updated successfully.")
            return redirect(reverse('core:vendor_promotion_list'))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PromotionForm(instance=promotion, vendor=vendor)
    context = {'form': form, 'vendor': vendor, 'promotion': promotion, 'form_title': f'Edit Promotion: {promotion.name}'}
    return render(request, 'core/vendor_promotion_form.html', context)

# --- Vendor Ad Campaigns Views ---
@login_required
def vendor_campaign_list(request):
    """Displays a list of ad campaigns created by the vendor."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect(reverse('core:home'))
    campaigns = AdCampaign.objects.filter(vendor=vendor).order_by('-start_date')
    context = {'campaigns': campaigns, 'vendor': vendor}
    return render(request, 'core/vendor_campaign_list.html', context)

@login_required
def vendor_campaign_create(request):
    """Handles creation of a new ad campaign by the vendor."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect(reverse('core:home'))
    if request.method == 'POST':
        form = AdCampaignForm(request.POST, vendor=vendor)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.vendor = vendor
            campaign.save()
            messages.success(request, f"Ad Campaign '{campaign.name}' created successfully.")
            return redirect(reverse('core:vendor_campaign_list'))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AdCampaignForm(vendor=vendor)
    context = {'form': form, 'vendor': vendor, 'form_title': 'Create New Ad Campaign'}
    return render(request, 'core/vendor_campaign_form.html', context)

# --- Vendor Products Views ---
@login_required
def vendor_product_list(request):
    """Displays a list of products managed by the vendor."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect(reverse('core:home'))
    products = Product.objects.filter(vendor=vendor).order_by('-created_at')
    stock_status_filter = request.GET.get('stock_status')
    is_filtered = False
    if stock_status_filter == 'low':
        products = products.filter(stock__lte=5)
        is_filtered = True
    context = {'products': products, 'vendor': vendor, 'is_filtered': is_filtered, 'stock_status_filter': stock_status_filter}
    return render(request, 'core/vendor_product_list.html', context)

@login_required
def vendor_product_create(request):
    """Handles creation of a new product by the vendor."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect(reverse('core:home'))
    if request.method == 'POST':
        form = VendorProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = vendor
            product.save()
            messages.success(request, f"Product '{product.name}' created successfully.")
            return redirect(reverse('core:vendor_product_list'))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = VendorProductForm()
    context = {'form': form, 'vendor': vendor, 'form_title': 'Add New Product'}
    return render(request, 'core/vendor_product_form.html', context)

@login_required
def vendor_product_edit(request, product_id):
    """Handles editing of an existing product by the vendor."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect(reverse('core:home'))
    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    if request.method == 'POST':
        form = VendorProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated successfully.")
            return redirect(reverse('core:vendor_product_list'))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = VendorProductForm(instance=product)
    context = {'form': form, 'vendor': vendor, 'product': product, 'form_title': f'Edit Product: {product.name}'}
    return render(request, 'core/vendor_product_form.html', context)

@login_required
@require_POST
def vendor_product_delete(request, product_id):
    """Handles deletion of a product by the vendor."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect(reverse('core:home'))
    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    product_name = product.name
    product.delete()
    messages.success(request, f"Product '{product_name}' deleted successfully.")
    return redirect(reverse('core:vendor_product_list'))

# --- START: Vendor Orders View ---
@login_required
def vendor_order_list(request):
    """Displays a list of orders containing items sold by the vendor."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have an associated vendor profile.")
        return redirect(reverse('core:home'))
    vendor_order_items = OrderItem.objects.filter(product__vendor=vendor).select_related('order', 'product', 'order__user')
    orders = Order.objects.filter(items__in=vendor_order_items).distinct().order_by('-created_at')
    context = {'orders': orders, 'vendor': vendor}
    return render(request, 'core/vendor_order_list.html', context)
# --- END: Vendor Orders View ---

# --- START: Vendor Reports View ---
@login_required
def vendor_reports(request):
    """Displays various reports for the vendor."""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have an associated vendor profile.")
        return redirect(reverse('core:home'))
    vendor_products = Product.objects.filter(vendor=vendor)
    vendor_order_items = OrderItem.objects.filter(product__vendor=vendor).select_related('order')
    total_sales_data = vendor_order_items.aggregate(
        total_revenue=models.Sum(models.F('price') * models.F('quantity')),
        total_items_sold=models.Sum('quantity')
    )
    total_revenue = total_sales_data['total_revenue'] or Decimal('0.00')
    total_items_sold = total_sales_data['total_items_sold'] or 0
    vendor_orders = Order.objects.filter(items__in=vendor_order_items).distinct()
    total_orders_count = vendor_orders.count()
    order_status_counts = vendor_orders.values('status').annotate(count=models.Count('id')).order_by('status')
    total_products_count = vendor_products.count()
    active_products_count = vendor_products.filter(is_active=True).count()
    low_stock_products = vendor_products.filter(is_active=True, stock__lte=5).order_by('stock')
    context = {
        'vendor': vendor,
        'total_revenue': total_revenue,
        'total_items_sold': total_items_sold,
        'total_orders_count': total_orders_count,
        'order_status_counts': order_status_counts,
        'total_products_count': total_products_count,
        'active_products_count': active_products_count,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'core/vendor_reports.html', context)
# --- END: Vendor Reports View ---

# --- Language Update View ---
def update_language(request):
    """View to handle language change requests from the modal."""
    if request.method == 'POST':
        language_code_input = request.POST.get('language_input')
        available_langs = dict(settings.LANGUAGES)
        if language_code_input and language_code_input in available_langs:
            request.session[translation.LANGUAGE_SESSION_KEY] = language_code_input
            activate(language_code_input)
            next_url = request.POST.get('next', request.META.get('HTTP_REFERER', reverse('core:home')))
            response = HttpResponseRedirect(next_url)
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language_code_input,
                                max_age=settings.LANGUAGE_COOKIE_AGE,
                                path=settings.LANGUAGE_COOKIE_PATH,
                                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                                secure=settings.LANGUAGE_COOKIE_SECURE,
                                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                                samesite=settings.LANGUAGE_COOKIE_SAMESITE)
            language_name = available_langs.get(language_code_input, language_code_input)
            messages.success(request, _("Language updated to %(language_name)s.") % {'language_name': language_name})
            return response
        else:
             messages.warning(request, "Invalid language selected.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('core:home')))


# --- Authentication Views ---
def signin(request):
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('core:home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url and not next_url.startswith('/') and ':' not in next_url: # Basic security
                     next_url = reverse('core:home')
                return redirect(next_url or reverse('core:home'))
            else:
                 messages.error(request, "Invalid username or password.")
        else:
             messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    context = {'form': form, 'next': request.GET.get('next', '')}
    return render(request, 'core/signin.html', context)


def signout(request):
    current_user_name = request.user.username if request.user.is_authenticated else None
    logout(request)
    if current_user_name:
        messages.info(request, f"You have been successfully logged out, {current_user_name}.")
    else:
        messages.info(request, "You have been successfully logged out.")
    return redirect('signin')


# --- Static Page Views ---
def terms(request):
    return render(request, 'core/terms.html')

def privacy(request):
    return render(request, 'core/privacy.html')

def help_page(request):
    return render(request, 'core/help.html')


# --- START: Service Marketplace Views ---
def service_list(request):
    """Displays a list of available services."""
    services = Service.objects.filter(is_active=True).select_related('provider', 'category').order_by('-created_at')
    categories = ServiceCategory.objects.filter(is_active=True).order_by('name')
    query = request.GET.get('q', '').strip()
    search_form = ServiceSearchForm(request.GET or None)
    if query:
        services = services.filter(
            Q(title__icontains=query) | Q(description__icontains=query) |
            Q(provider__username__icontains=query) | Q(category__name__icontains=query) |
            Q(location__icontains=query)
        ).distinct()
    context = {'services': services, 'categories': categories, 'search_form': search_form, 'query': query}
    return render(request, 'core/service_list.html', context)

def service_category_detail(request, category_slug):
    """Displays services belonging to a specific service category."""
    category = get_object_or_404(ServiceCategory, slug=category_slug, is_active=True)
    services = Service.objects.filter(category=category, is_active=True).select_related('provider').order_by('-created_at')
    context = {'category': category, 'services': services}
    return render(request, 'core/service_category_detail.html', context)

def service_detail(request, service_slug):
    """Displays details for a single service."""
    service = get_object_or_404(Service, slug=service_slug, is_active=True)
    service_images = service.images.all()
    service_videos = service.videos.all()
    service_packages = service.packages.filter(is_active=True).order_by('display_order', 'price')
    reviews = ServiceReview.objects.filter(service=service, is_approved=True).select_related('user').order_by('-created_at')
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    review_form = ServiceReviewForm()
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = ServiceReview.objects.filter(service=service, user=request.user).exists()
    context = {
        'service': service, 'service_images': service_images, 'service_videos': service_videos,
        'service_packages': service_packages, 'reviews': reviews, 'average_rating': average_rating,
        'review_form': review_form, 'user_has_reviewed': user_has_reviewed,
    }
    return render(request, 'core/service_detail.html', context)

@login_required
@transaction.atomic
def service_create(request):
    """Allows logged-in users to create a new service listing."""
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        package_formset = ServicePackageFormSet(request.POST, prefix='packages')
        if form.is_valid() and package_formset.is_valid():
            service = form.save(commit=False)
            service.provider = request.user
            service.save()
            package_formset.instance = service
            package_formset.save()
            messages.success(request, "Your service and its packages have been listed successfully.")
            return redirect(service.get_absolute_url())
        else:
            messages.error(request, "Please correct the errors below.")
            logger.error(f"Service Form Errors: {form.errors.as_json(escape_html=True)}")
            logger.error(f"Package Formset Errors: {package_formset.errors}, Non-form: {package_formset.non_form_errors()}")
    else:
        form = ServiceForm()
        package_formset = ServicePackageFormSet(prefix='packages')
    context = {'form': form, 'package_formset': package_formset, 'form_title': 'Offer a New Service'}
    return render(request, 'core/service_form.html', context)

@login_required
@transaction.atomic
def service_edit(request, service_slug):
    """Allows the provider to edit their service listing."""
    service = get_object_or_404(Service, slug=service_slug, provider=request.user)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        package_formset = ServicePackageFormSet(request.POST, instance=service, prefix='packages')
        if form.is_valid() and package_formset.is_valid():
            form.save()
            package_formset.save()
            messages.success(request, "Service and packages updated successfully.")
            return redirect(service.get_absolute_url())
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ServiceForm(instance=service)
        package_formset = ServicePackageFormSet(instance=service, prefix='packages')
    context = {'form': form, 'package_formset': package_formset, 'service': service, 'form_title': f'Edit Service: {service.title}'}
    return render(request, 'core/service_form.html', context)

@login_required
@require_POST
def service_delete(request, service_slug):
    """Allows the provider to delete their service listing."""
    service = get_object_or_404(Service, slug=service_slug, provider=request.user)
    service_title = service.title
    service.delete()
    messages.success(request, f"Service '{service_title}' deleted successfully.")
    return redirect('core:service_list')

@login_required
@require_POST
def add_service_review(request, service_slug):
    """Handles submission of a service review."""
    service = get_object_or_404(Service, slug=service_slug, is_active=True)
    form = ServiceReviewForm(request.POST)
    if ServiceReview.objects.filter(user=request.user, service=service).exists():
        messages.warning(request, "You have already reviewed this service.")
        return redirect(service.get_absolute_url())
    if form.is_valid():
        if ServiceReview.objects.filter(user=request.user, service=service).exists(): # Double check
            messages.warning(request, "You have already reviewed this service.")
            return redirect(service.get_absolute_url())
        review = form.save(commit=False)
        review.user = request.user
        review.service = service
        review.save()
        messages.success(request, "Your review has been submitted successfully.")
    else:
        messages.error(request, "There was an error submitting your review. Please check the rating.")
    return redirect(service.get_absolute_url())

@login_required
@require_POST
def add_service_to_order(request, package_id):
    """Adds a selected service package to the user's pending order."""
    package = get_object_or_404(ServicePackage, id=package_id, is_active=True, service__is_active=True)
    order, created = Order.objects.get_or_create(
        user=request.user, status='PENDING', defaults={'status': 'PENDING'}
    )
    if order.items.filter(service_package=package).exists():
        messages.info(request, f"'{package.name}' for '{package.service.title}' is already in your order.")
    else:
        OrderItem.objects.create(
            order=order, service_package=package, price=package.price, quantity=1
        )
        messages.success(request, f"Added '{package.name}' for '{package.service.title}' to your order.")
    return redirect('core:order_summary')

# --- START: Dual Payment System Views ---
@login_required
def process_checkout_choice(request):
    """Displays payment method choices (GET) and processes selected (POST)."""
    try:
        order = Order.objects.get(user=request.user, status='PENDING')
    except Order.DoesNotExist:
        messages.error(request, _("You do not have an active order."))
        return redirect('core:home')
    except Order.MultipleObjectsReturned:
        order = Order.objects.filter(user=request.user, status='PENDING').latest('created_at')
        logger.warning(f"User {request.user.username} had multiple pending orders. Selected latest: {order.order_id}")

    if request.method == 'POST':
        payment_choice = request.POST.get('payment_method')
        if not payment_choice:
            messages.error(request, _("Please select a payment method."))
            return redirect(reverse('core:process_checkout_choice'))
        valid_methods = [choice[0] for choice in Order.PAYMENT_METHOD_CHOICES]
        if payment_choice not in valid_methods:
            messages.error(request, _("Invalid payment method selected."))
            return redirect(reverse('core:process_checkout_choice'))
        order.payment_method = payment_choice
        if payment_choice == 'escrow':
            order.status = 'AWAITING_ESCROW_PAYMENT'
            order.save()
            logger.info(f"Order {order.order_id} by {request.user.username} chose Escrow. Redirecting to Paystack.")
            messages.info(request, _("Proceeding to secure payment via Paystack."))
            return redirect(reverse('core:initiate_paystack_payment', kwargs={'order_id': order.id}))
        elif payment_choice == 'direct':
            order.status = 'AWAITING_DIRECT_PAYMENT'
            order.save()
            logger.info(f"Order {order.order_id} by {request.user.username} chose Direct Arrangement.")
            messages.success(request, _("Order confirmed for direct payment arrangement. Please contact the provider(s) to arrange payment."))
            return redirect(order.get_absolute_url())
        return redirect(reverse('core:process_checkout_choice'))

    available_payment_methods = []
    all_choices = dict(Order.PAYMENT_METHOD_CHOICES)
    if 'escrow' in all_choices:
        available_payment_methods.append(('escrow', all_choices['escrow']))
    allow_direct_payment = order.has_only_services() or order.has_negotiable_category_products()
    if allow_direct_payment and 'direct' in all_choices:
        if not any(pm[0] == 'direct' for pm in available_payment_methods):
            available_payment_methods.append(('direct', all_choices['direct']))
    context = {
        'order': order, 'available_payment_methods': available_payment_methods,
        'current_payment_method': order.payment_method
    }
    return render(request, 'core/process_checkout_choice.html', context)

@login_required
def initiate_paystack_payment(request, order_id):
    """Initiates a Paystack transaction for the given order."""
    order = get_object_or_404(Order, id=order_id, user=request.user, status='AWAITING_ESCROW_PAYMENT')
    url = "https://api.paystack.co/transaction/initialize"
    amount_in_pesewas = int(order.get_total_cost() * 100)
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}
    reference = f"NEXUS-SVC-{order.id}-{int(order.updated_at.timestamp())}"
    payload = {
        "email": request.user.email, "amount": amount_in_pesewas, "currency": "GHS",
        "reference": reference, "callback_url": settings.PAYSTACK_CALLBACK_URL,
        "metadata": {"order_id": order.id, "user_id": request.user.id}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        paystack_data = response.json()
        if paystack_data.get('status'):
            order.paystack_ref = reference
            order.save()
            return redirect(paystack_data['data']['authorization_url'])
        else:
            messages.error(request, f"Paystack initialization failed: {paystack_data.get('message', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Could not connect to payment gateway: {e}")
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {e}")
    return redirect(reverse('core:order_detail', kwargs={'order_id': order.id}))

def paystack_callback(request):
    """Handles the redirect back from Paystack after a payment attempt."""
    reference = request.GET.get('reference')
    if not reference:
        messages.error(request, _("Payment reference not found."))
        return redirect('core:order_summary')
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        verification_data = response.json()
        order = Order.objects.get(paystack_ref=reference)
        if verification_data.get('status') and verification_data['data']['status'] == 'success':
            if order.status not in ['PROCESSING', 'IN_PROGRESS', 'COMPLETED']:
                order.status = 'PROCESSING'
                order.transaction_id = verification_data['data'].get('id')
                order.save()
                if order.user: # Log in the user if they were logged out during the process
                    login(request, order.user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, _("Payment successful! Your order is being processed."))
            else:
                messages.info(request, _("Payment for this order was already confirmed."))
            return redirect(order.get_absolute_url())
        else:
            messages.error(request, _("Payment verification failed or payment was not successful. Please try again or contact support."))
            return redirect(order.get_absolute_url())
    except Order.DoesNotExist:
        messages.error(request, _("Order associated with this payment reference not found."))
        logger.critical(f"Paystack callback received for reference {reference}, but no matching order found.")
        return redirect('core:home')
    except requests.exceptions.RequestException as e:
        messages.error(request, _("Could not verify payment status. Please contact support if payment was debited. Error: {}").format(e))
        logger.error(f"Paystack Verification API Error: {e}")
        try: order = Order.objects.get(paystack_ref=reference); return redirect(order.get_absolute_url())
        except Order.DoesNotExist: return redirect('core:home')
    except Exception as e:
        messages.error(request, _("An unexpected error occurred during payment verification. Please contact support. Error: {}").format(e))
        logger.error(f"Unexpected Paystack Verification Error: {e}")
        try: order = Order.objects.get(paystack_ref=reference); return redirect(order.get_absolute_url())
        except Order.DoesNotExist: return redirect('core:home')
    # Fallback, should not be reached if order is found in exceptions
    try: order = Order.objects.get(paystack_ref=reference); return redirect(order.get_absolute_url())
    except Order.DoesNotExist: messages.error(request, _("Order for payment reference not found.")); return redirect('core:order_summary')

def placeholder_view(request, page_name="Placeholder"):
    """A simple view to render placeholder pages."""
    context = {'page_name': page_name}
    return render(request, 'core/placeholder.html', context)

@login_required
def order_summary_view(request):
    """Displays the summary of the current service order before payment choice."""
    try:
        order = Order.objects.prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.select_related(
                'service_package__service', 'provider'
            ))
        ).get(user=request.user, ordered=False, status='PENDING') # More specific query
    except Order.DoesNotExist:
        messages.warning(request, "You do not have an active order to summarize.")
        return redirect('core:home')
    except Order.MultipleObjectsReturned:
        order = Order.objects.filter(user=request.user, ordered=False, status='PENDING').latest('created_at')
        logger.warning(f"Multiple pending orders for {request.user.username}, selected latest: {order.order_id}")
    context = {'order': order}
    return render(request, 'core/order_summary.html', context)

@login_required
@require_POST
def customer_confirm_service_completion(request, order_id):
    """Allows customer to confirm service completion."""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    can_confirm = (
        order.payment_method in ['escrow', 'direct'] and
        order.status in ['PROCESSING', 'IN_PROGRESS', 'AWAITING_DIRECT_PAYMENT'] and
        order.items.filter(service_package__isnull=False).exists() and
        order.customer_confirmed_completion_at is None
    )
    if not can_confirm:
        messages.error(request, _("This order is not eligible for completion confirmation at this time."))
        return redirect(order.get_absolute_url())
    order.status = 'COMPLETED'
    order.customer_confirmed_completion_at = timezone.now()
    order.save()
    messages.success(request, _("Thank you for confirming the service completion! The order is now marked as completed."))
    return redirect(order.get_absolute_url())

@login_required
def provider_dashboard(request):
    """Displays the dashboard for a user who is a service provider."""
    user = request.user
    if not Service.objects.filter(provider=user).exists():
        messages.info(request, _("You haven't listed any services yet. Start by offering a service!"))
        return redirect(reverse('core:service_create'))
    services = Service.objects.filter(provider=user).order_by('-created_at')
    service_order_items = OrderItem.objects.filter(provider=user).select_related('order', 'service_package__service').order_by('-order__created_at')
    service_orders_qs = Order.objects.filter(items__in=service_order_items).distinct().order_by('-created_at')
    active_services_count = services.filter(is_active=True).count()
    total_services_count = services.count()
    completed_service_orders_count = service_orders_qs.filter(status='COMPLETED').count()
    in_progress_service_orders_count = service_orders_qs.filter(status__in=['PROCESSING', 'IN_PROGRESS']).count()
    recent_service_orders = service_orders_qs[:5]
    context = {
        'services': services, 'service_orders': service_orders_qs, 'recent_service_orders': recent_service_orders,
        'active_services_count': active_services_count, 'total_services_count': total_services_count,
        'completed_service_orders_count': completed_service_orders_count,
        'in_progress_service_orders_count': in_progress_service_orders_count,
    }
    return render(request, 'core/provider_dashboard.html', context)

def provider_profile_detail(request, username):
    """Displays the public profile of a service provider."""
    profile_owner = get_object_or_404(get_user_model(), username=username)
    services = Service.objects.filter(provider=profile_owner, is_active=True).select_related('category').order_by('-created_at')
    service_reviews = ServiceReview.objects.filter(service__provider=profile_owner, is_approved=True).select_related('user', 'service').order_by('-created_at')
    average_rating_data = ServiceReview.objects.filter(service__provider=profile_owner, is_approved=True).aggregate(average_rating=Avg('rating'), review_count=Count('id'))
    average_rating = average_rating_data.get('average_rating')
    review_count = average_rating_data.get('review_count', 0)
    context = {
        'profile_owner': profile_owner, 'services': services, 'service_reviews': service_reviews,
        'average_rating': average_rating, 'review_count': review_count,
    }
    return render(request, 'core/provider_profile_detail.html', context)

# --- START: User Profile View (Updated for Editing) ---
@login_required
def user_profile_view(request):
    """
    Displays and handles updates for the user's profile information.
    """
    if request.method == 'POST':
        # Pass request.FILES to handle profile picture uploads
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your profile has been updated successfully!'))
            return redirect('core:user_profile') # Redirect back to the profile page
        else:
            # If form is not valid, errors will be displayed by the template
            messages.error(request, _('Please correct the errors below.'))
    else:
        # For a GET request, display the form populated with the user's current data
        form = UserProfileUpdateForm(instance=request.user)

    context = {
        'form': form,
        'user_profile_owner': request.user, # For displaying user info alongside the form if needed
                                        # (e.g. current profile picture next to the upload field)
        'user': request.user # The template user_profile.html uses 'user.profile_picture.url'
    }
    return render(request, 'authapp/user_profile.html', context)
# --- END: User Profile View (Updated for Editing) ---
