# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, models # For atomic operations like placing orders
from django.db.models import Prefetch, Q, Avg, Sum, F # For more complex queries, Import Avg, Sum, F
from decimal import Decimal # For calculations
from django.urls import reverse # Added for cart item URLs
from django.views.decorators.http import require_POST # For actions like add/remove wishlist/review
# --- Import Forms ---
from .forms import VendorReviewForm, ProductReviewForm, VendorRegistrationForm, VendorVerificationForm, VendorProfileUpdateForm, VendorShippingForm, VendorPaymentForm, PromotionForm, AdCampaignForm, VendorProductForm # <<< Import new forms
# --- Import your actual models ---
# Import ALL models needed, including new ones
from .models import (
    Product, Category, Order, OrderItem, Address, Vendor, Promotion, AdCampaign, ProductImage, # <<< Import new models
    WishlistItem, ProductReview, VendorReview, ProductImage, ProductVideo # <<< Import ProductVideo
)
# ---------------------------------------------------------
# --- START: Added imports for update_language ---
from django.utils.translation import activate, check_for_language, get_language
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import translate_url
# --- END: Added imports for update_language ---


# --- View for a single product page ---
def product_detail(request, product_slug):
    """Displays details for a single product, including vendor and reviews."""
    product_obj = get_object_or_404(
        Product.objects.select_related('vendor', 'category'),
        slug=product_slug,
        is_active=True,
        vendor__is_approved=True
    )

    # Fetch all related images using the related_name 'images' from ProductImage model
    product_images = product_obj.images.all()

    # Fetch all related videos using the related_name 'videos' from ProductVideo model
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
    user_has_reviewed_product = False # Initialize review status
    review_form = ProductReviewForm() # Instantiate the form

    if request.user.is_authenticated:
        is_in_wishlist = WishlistItem.objects.filter(user=request.user, product=product_obj).exists()
        # Check if user has reviewed THIS product
        user_has_reviewed_product = ProductReview.objects.filter(user=request.user, product=product_obj).exists()

    context = {
        'product': product_obj,
        'product_images': product_images, # <<< Pass the images to the template
        'product_videos': product_videos, # <<< Pass the videos to the template
        'related_products': related_products,
        'product_reviews': product_reviews,
        'average_product_rating': average_product_rating,
        'is_in_wishlist': is_in_wishlist,
        'review_form': review_form, # Pass form to context
        'user_has_reviewed_product': user_has_reviewed_product, # Pass status to context
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

    # <<< Fetch New Products >>>
    new_products = Product.objects.filter(
        is_active=True,
        vendor__is_approved=True
    ).order_by('-created_at')[:8] # Get latest 8 active products

    context = {
        'featured_products': featured_products,
        'categories': categories,
        'new_products': new_products, # <<< Add to context
    }
    return render(request, 'core/home.html', context)
# --- END: REPLACED home VIEW ---


def menu(request):
    """Displays the main menu, typically showing categories."""
    # Fetch all active top-level categories and prefetch their active subcategories
    categories = Category.objects.filter(
        is_active=True, parent=None
    ).prefetch_related(
        Prefetch('subcategories', queryset=Category.objects.filter(is_active=True).order_by('name'))
    ).order_by('name')
    context = {'categories': categories}
    return render(request, 'core/menu.html', context)

# --- View for a specific category page ---
def category_detail(request, category_slug):
    """Displays products belonging to a specific category."""
    category_obj = get_object_or_404(Category, slug=category_slug, is_active=True)
    # Modify query for vendor approval and product activity
    products = Product.objects.filter(
        category=category_obj,
        is_active=True,
        vendor__is_approved=True # <<< Vendor Check
    ).order_by('name').select_related('vendor') # Select related vendor
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

    # Instantiate the form to pass to the template
    review_form = VendorReviewForm()
    # Check if user already reviewed THIS vendor
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = VendorReview.objects.filter(user=request.user, vendor=vendor).exists()

    context = {
        'vendor': vendor,
        'products': products,
        'vendor_reviews': vendor_reviews,
        'average_vendor_rating': average_vendor_rating,
        'review_form': review_form, # Pass form to context
        'user_has_reviewed': user_has_reviewed, # Pass review status
    }
    return render(request, 'core/vendor_detail.html', context)


# --- Cart Views (Using Session) ---
def cart(request):
    """Displays the current shopping cart contents."""
    cart_session = request.session.get('cart', {})
    product_ids = cart_session.keys()
    # Fetch only active products from approved vendors
    products_in_cart = Product.objects.filter(
        id__in=product_ids,
        is_active=True,
        vendor__is_approved=True # <<< Vendor Check
    ).select_related('vendor') # Fetch vendor info

    cart_items = []
    cart_total = Decimal('0.00')
    unavailable_items = False # Flag if any item became inactive/deleted

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

# @login_required # Decide if guests can add to cart
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

        # Ensure product is active AND vendor is approved
        product = get_object_or_404(Product, id=product_id, is_active=True, vendor__is_approved=True) # <<< Vendor Check
        cart_session = request.session.get('cart', {})
        product_key = str(product.id)

        current_quantity_in_cart = cart_session.get(product_key, {}).get('quantity', 0)
        requested_total_quantity = current_quantity_in_cart + quantity

        if product.stock < requested_total_quantity:
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

# --- TODO: Add views for updating quantity and removing items from cart ---
# def update_cart_item(request, product_id): ...
# def remove_cart_item(request, product_id): ...


# --- Checkout Process Views ---
@login_required
def checkout(request):
    """Prepares the checkout page with cart summary and address options."""
    cart_session = request.session.get('cart', {})
    if not cart_session:
        messages.info(request, "Your cart is empty. Please add items before checking out.")
        return redirect('cart')

    product_ids = cart_session.keys()
    # Ensure products are active AND vendors approved
    products_in_cart = Product.objects.filter(
        id__in=product_ids,
        is_active=True,
        vendor__is_approved=True # <<< Vendor Check
    ).select_related('vendor')
    product_dict = {str(p.id): p for p in products_in_cart}

    cart_items = []
    cart_total = Decimal('0.00')
    stock_issue = False

    for product_id, item_data in cart_session.items():
        product = product_dict.get(product_id)
        if product:
            quantity = item_data.get('quantity', 0)
            if quantity > 0:
                if product.stock < quantity:
                    stock_issue = True
                    messages.error(request, f"Insufficient stock for '{product.name}'. Only {product.stock} available, but you have {quantity} in cart. Please update your cart.")
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

    shipping_addresses = Address.objects.filter(user=request.user, address_type='shipping').order_by('-is_default', '-created_at')
    billing_addresses = Address.objects.filter(user=request.user, address_type='billing').order_by('-is_default', '-created_at')

    # TODO: Add forms for selecting/creating addresses

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'shipping_addresses': shipping_addresses,
        'billing_addresses': billing_addresses,
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

        shipping_address_id = request.POST.get('shipping_address')
        billing_address_id = request.POST.get('billing_address')

        try:
            shipping_address = get_object_or_404(Address, id=shipping_address_id, user=request.user, address_type='shipping')
            if billing_address_id and billing_address_id != shipping_address_id:
                billing_address = get_object_or_404(Address, id=billing_address_id, user=request.user, address_type='billing')
            else:
                billing_address = shipping_address
        except (Address.DoesNotExist, ValueError):
            messages.error(request, "Invalid address selected or ID format incorrect. Please try again.")
            return redirect('checkout')

        product_ids = cart_session.keys()
        # Lock products, ensure active and vendor approved
        products_in_cart = Product.objects.select_for_update().filter(
            id__in=product_ids,
            is_active=True,
            vendor__is_approved=True # <<< Vendor Check
        ).select_related('vendor')
        product_dict = {str(p.id): p for p in products_in_cart}

        order_items_data = []
        final_order_total = Decimal('0.00')
        stock_issue = False

        for product_id, item_data in cart_session.items():
            product = product_dict.get(product_id)
            quantity = item_data.get('quantity', 0)

            if not product or quantity <= 0:
                messages.error(request, f"Item (ID: {product_id}) is invalid or has zero quantity. Please review your cart.")
                stock_issue = True; break

            if product.stock < quantity:
                messages.error(request, f"'{product.name}' stock changed. Only {product.stock} available, but you requested {quantity}. Please update your cart.")
                stock_issue = True; break

            item_total = product.price * quantity
            order_items_data.append({
                'product': product, 'quantity': quantity,
                'price': product.price, 'name': product.name,
            })
            final_order_total += item_total

        if stock_issue: return redirect('cart')

        order = Order.objects.create(
            user=request.user, total_amount=final_order_total,
            shipping_address=shipping_address, billing_address=billing_address,
            shipping_address_text=f"{shipping_address.full_name}\n{shipping_address.street_address}\n{shipping_address.apartment_address or ''}\n{shipping_address.city}, {shipping_address.state} {shipping_address.zip_code}\n{shipping_address.country}\n{shipping_address.phone_number or ''}".strip(),
            billing_address_text=f"{billing_address.full_name}\n{billing_address.street_address}\n{billing_address.apartment_address or ''}\n{billing_address.city}, {billing_address.state} {billing_address.zip_code}\n{billing_address.country}\n{billing_address.phone_number or ''}".strip(),
            status='pending', payment_status='pending'
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
                    # vendor=product_instance.vendor, # <<< Add if FK added to OrderItem
                )
            )
            product_instance.stock -= item_data['quantity']
            products_to_update_stock.append(product_instance)

        OrderItem.objects.bulk_create(order_items_to_create)
        Product.objects.bulk_update(products_to_update_stock, ['stock'])

        # --- TODO: Payment Processing ---

        del request.session['cart']
        request.session.modified = True

        messages.success(request, f"Order #{order.order_id} placed successfully!")
        return redirect('core:order_detail', order_id=order.order_id)

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
            Prefetch('items', queryset=OrderItem.objects.select_related('product__vendor')) # Prefetch vendor too
        ),
        order_id=order_id, user=request.user
    )
    context = {'order': order}
    return render(request, 'core/order_detail.html', context)


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
# --- START: REPLACED add_product_review VIEW ---
@login_required
@require_POST
def add_product_review(request, product_id):
    print("\n>>> ENTERING add_product_review VIEW <<<") # <<< ADDED THIS LINE AT THE START
    """Handles submission of a product review."""
    product = get_object_or_404(Product, id=product_id, is_active=True, vendor__is_approved=True)
    form = ProductReviewForm(request.POST, request.FILES) # <<< Include request.FILES here

    # Check if user already reviewed this product
    if ProductReview.objects.filter(user=request.user, product=product).exists():
        print(">>> add_product_review: Already reviewed branch <<<") # Optional print
        messages.warning(request, "You have already reviewed this product.")
        return redirect(product.get_absolute_url())

    if form.is_valid():
        print(">>> add_product_review: Form IS valid branch <<<") # Optional print
        # Double-check for existing review (race condition mitigation)
        if ProductReview.objects.filter(user=request.user, product=product).exists():
            messages.warning(request, "You have already reviewed this product.")
            return redirect(product.get_absolute_url())

        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        # review.is_approved = False # Set to False if moderation is required
        review.save()
        messages.success(request, "Your review has been submitted successfully.")
        return redirect(product.get_absolute_url())
    else:
        print(">>> add_product_review: Form IS NOT valid branch (ELSE block) <<<") # <<< ADDED THIS LINE
        # --- START: MODIFIED DEBUGGING BLOCK ---
        print("-----------------------------")
        print("Product Review Form Errors:")
        print(form.errors.as_json()) # Print errors as JSON to the console
        print("POST Data:", request.POST) # Print the submitted data
        print("-----------------------------")
        # --- END: MODIFIED DEBUGGING BLOCK ---

        error_msg = "There was an error submitting your review. Please check the form. (See console for details)" # Updated message
        messages.error(request, error_msg)
        return redirect(product.get_absolute_url())
# --- END: REPLACED add_product_review VIEW ---


@login_required
@require_POST # Ensure this action is only done via POST
def add_vendor_review(request, vendor_id):
    print("\n>>> ENTERING add_vendor_review VIEW <<<") # <<< ADDED THIS LINE AT THE START
    """Handles submission of a vendor review."""
    vendor = get_object_or_404(Vendor, id=vendor_id, is_approved=True)
    form = VendorReviewForm(request.POST)

    # Check if user already reviewed this vendor
    if VendorReview.objects.filter(user=request.user, vendor=vendor).exists():
        print(">>> add_vendor_review: Already reviewed branch <<<") # Optional print
        messages.warning(request, "You have already reviewed this vendor.")
        return redirect(vendor.get_absolute_url())

    if form.is_valid():
        print(">>> add_vendor_review: Form IS valid branch <<<") # Optional print
        # Double-check for existing review (race condition mitigation)
        if VendorReview.objects.filter(user=request.user, vendor=vendor).exists():
            messages.warning(request, "You have already reviewed this vendor.")
            return redirect(vendor.get_absolute_url())

        review = form.save(commit=False)
        review.user = request.user
        review.vendor = vendor
        # review.is_approved = False # Set to False if moderation is required
        review.save()
        messages.success(request, "Your review has been submitted successfully.")
        return redirect(vendor.get_absolute_url()) # Redirect back to vendor page
    else:
        print(">>> add_vendor_review: Form IS NOT valid branch (ELSE block) <<<") # <<< ADDED THIS LINE
        # --- START: MODIFIED DEBUGGING BLOCK ---
        print("-----------------------------")
        print("VENDOR Review Form Errors:") # <<< Indicate it's the VENDOR view
        print(form.errors.as_json())
        print("POST Data:", request.POST)
        print("-----------------------------")
        # --- END: MODIFIED DEBUGGING BLOCK ---
        error_message = "There was an error submitting your review. Please check the form. (Vendor View Console)" # Updated message
        messages.error(request, error_message)
        return redirect(vendor.get_absolute_url())
# --- END: MODIFIED REVIEW VIEWS ---

# --- Search View ---
def search_results(request):
    """Handles product search queries."""
    query = request.GET.get('q', '').strip() # Get query, remove leading/trailing whitespace
    results = Product.objects.none() # Start with an empty queryset

    if query: # Only search if query is not empty
        # Search across multiple fields (name, description, category name, vendor name)
        # Using Q objects for OR conditions and icontains for case-insensitive search
        results = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(vendor__name__icontains=query),
            is_active=True, # Only show active products
            vendor__is_approved=True # Only from approved vendors
        ).select_related('vendor', 'category').distinct() # Avoid duplicates if matches in multiple fields

    context = {
        'query': query,
        'results': results,
    }
    return render(request, 'core/search_results.html', context)

# --- Location Update View ---
def update_location(request):
    """Updates the delivery location stored in the session."""
    if request.method == 'POST':
        new_location = request.POST.get('location_input', '').strip()
        if new_location: # Only update if something was entered
            request.session['delivery_location'] = new_location
            messages.success(request, f"Delivery location updated to {new_location}.")
        else:
            messages.warning(request, "Please enter a location.")
        # Redirect back to the previous page, or home if referrer is not available
        return redirect(request.META.get('HTTP_REFERER', reverse('core:home')))
    # If GET request, just redirect home (or show an error/form if desired)
    return redirect(reverse('core:home'))

def daily_offers(request):
    """Displays products currently marked as featured/on offer."""
    # Using 'is_featured' as a proxy for offers for now.
    # Consider adding a dedicated 'is_on_offer' or 'discount_price' field later.
    offer_products = Product.objects.filter(
        is_featured=True,
        is_active=True,
        vendor__is_approved=True
    ).select_related('vendor', 'category').order_by('-created_at')

    context = {'offer_products': offer_products}
    return render(request, 'core/daily_offers.html', context)

def sell_on_nexus(request):
    """Displays information about selling on the platform."""
    # For now, just renders a static info page. Could add forms later.
    return render(request, 'core/sell_on_nexus.html')

# --- Vendor Registration View ---
@login_required
def register_vendor(request):
    """Handles the vendor registration application."""
    # Check if user already has a vendor profile
    if hasattr(request.user, 'vendor_profile'):
        messages.info(request, "You already have a vendor profile.")
        # Redirect to a vendor dashboard if it exists, otherwise home
        # return redirect(reverse('vendor_dashboard')) # Example redirect
        return redirect(reverse('core:home'))

    if request.method == 'POST':
        form = VendorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.user = request.user # Link to the logged-in user
            vendor.is_approved = False # Vendors need approval
            vendor.is_verified = False # Verification status
            # Verification details (docs, ID) will be collected later
            # Slug should be auto-generated on save by the model
            vendor.save()
            messages.success(request, "Your vendor application has been submitted successfully! It will be reviewed by our team.")
            # Redirect to a success/thank you page or user profile
            return redirect(reverse('core:home')) # Redirect home for now
        else:
            messages.error(request, "Please correct the errors below.")
    else: # GET request
        form = VendorRegistrationForm()

    context = {'form': form}
    return render(request, 'core/vendor_registration.html', context)

# --- Vendor Dashboard View ---
@login_required
def vendor_dashboard(request):
    """Displays the dashboard for the logged-in vendor."""
    try:
        # Get the vendor profile associated with the logged-in user
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        # If the user has no vendor profile, they shouldn't be here.
        # Maybe they haven't applied yet?
        messages.warning(request, "You do not have a vendor profile. Please apply first.")
        return redirect(reverse('core:sell_on_nexus')) # Redirect to the 'Sell on Nexus' info page

    # --- START: Report Data Calculation ---
    vendor_products = Product.objects.filter(vendor=vendor)
    vendor_order_items = OrderItem.objects.filter(product__vendor=vendor) # Get all items sold by this vendor

    # Calculate Total Sales (Consider filtering by order status like 'delivered' or 'shipped' for more accuracy)
    # For simplicity now, summing all items linked to the vendor.
    total_sales_data = vendor_order_items.aggregate(
        total=models.Sum(models.F('price') * models.F('quantity'))
    )
    total_sales = total_sales_data['total'] or Decimal('0.00')

    # Calculate Total Orders (Distinct orders containing vendor's products)
    vendor_orders = Order.objects.filter(items__in=vendor_order_items).distinct()
    total_orders_count = vendor_orders.count()
    recent_orders = vendor_orders.order_by('-created_at')[:5] # Get 5 most recent orders

    # Product Counts
    total_products_count = vendor_products.count()
    active_products_count = vendor_products.filter(is_active=True).count()
    low_stock_products = vendor_products.filter(is_active=True, stock__lte=5).order_by('stock')[:5] # Products with stock <= 5
    # --- END: Report Data Calculation ---

    # --- Determine Completion Status for Each Section ---
    # Define required fields for each section (adjust based on your model/requirements)
    shop_info_complete = all([vendor.name, vendor.description, vendor.contact_email, vendor.phone_number, vendor.logo])

    # Business info depends on registration type, assume verification form handles this logic
    # For now, let's check if *either* business or individual docs are submitted
    # We might refine this later based on the chosen registration_type
    business_info_submitted = vendor.business_registration_doc or vendor.national_id_doc
    # A simple check for now, might need admin verification flag later
    business_info_status = "PENDING" # Default to PENDING until fully verified by admin
    if vendor.is_verified:
         business_info_status = "COMPLETED"
    elif business_info_submitted:
         business_info_status = "PENDING REVIEW" # Or just PENDING

    # Refined checks for new sections
    shipping_info_complete = bool(vendor.shipping_policy) # Check if shipping_policy has content
    payment_info_complete = bool(vendor.mobile_money_provider and vendor.mobile_money_number) # Check if both MoMo fields are filled
    additional_info_complete = True # Keep as True for now

    all_sections_complete = all([shop_info_complete, vendor.is_verified, shipping_info_complete, payment_info_complete, additional_info_complete])

    context = {
        'vendor': vendor,
        'shop_info_complete': shop_info_complete,
        'business_info_status': business_info_status, # Use status string
        'shipping_info_complete': shipping_info_complete,
        'payment_info_complete': payment_info_complete,
        'additional_info_complete': additional_info_complete,
        'all_sections_complete': all_sections_complete,
        # --- Add Report Data to Context ---
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
        return redirect(reverse('core:register_vendor')) # Or 'sell_on_nexus'

    # Prevent re-verification if already verified or pending admin approval
    # if vendor.is_verified:
    #     messages.info(request, "Your account is already verified.")
    #     return redirect(reverse('core:vendor_dashboard'))
    # Add similar logic if you have a 'pending_verification' status

    if request.method == 'POST':
        form = VendorVerificationForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            form.save()
            # Optionally: Set a status like 'pending_verification' if admin approval is needed
            # vendor.verification_status = 'pending'
            # vendor.save()
            messages.success(request, "Verification documents submitted successfully. They will be reviewed by our team.")
            return redirect(reverse('core:vendor_dashboard'))
        else:
            messages.error(request, "Please correct the errors below.")
    else: # GET request
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
        return redirect(reverse('core:home')) # Or 'sell_on_nexus'

    if request.method == 'POST':
        # Assume VendorProfileUpdateForm exists in forms.py
        form = VendorProfileUpdateForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect(reverse('core:vendor_dashboard')) # Redirect back to dashboard
        else:
            messages.error(request, "Please correct the errors below.")
    else: # GET request
        # Assume VendorProfileUpdateForm exists in forms.py
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
    else: # GET request
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
    else: # GET request
        form = VendorPaymentForm(instance=vendor)

    context = {'form': form, 'vendor': vendor}
    return render(request, 'core/edit_vendor_payment.html', context)

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
        form = PromotionForm(request.POST, vendor=vendor) # Pass vendor to filter products
        if form.is_valid():
            promotion = form.save(commit=False)
            promotion.applicable_vendor = vendor # Set the vendor
            promotion.save()
            form.save_m2m() # Important for ManyToMany fields
            messages.success(request, f"Promotion '{promotion.name}' created successfully.")
            return redirect(reverse('core:vendor_promotion_list'))
        else:
            messages.error(request, "Please correct the errors below.")
    else: # GET request
        form = PromotionForm(vendor=vendor) # Pass vendor to filter products

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
        form = PromotionForm(request.POST, instance=promotion, vendor=vendor) # Pass vendor
        if form.is_valid():
            form.save() # save_m2m is handled automatically for existing instances
            messages.success(request, f"Promotion '{promotion.name}' updated successfully.")
            return redirect(reverse('core:vendor_promotion_list'))
        else:
            messages.error(request, "Please correct the errors below.")
    else: # GET request
        form = PromotionForm(instance=promotion, vendor=vendor) # Pass vendor

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
        form = AdCampaignForm(request.POST, vendor=vendor) # Pass vendor
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.vendor = vendor # Set the vendor
            campaign.save()
            messages.success(request, f"Ad Campaign '{campaign.name}' created successfully.")
            return redirect(reverse('core:vendor_campaign_list'))
        else:
            messages.error(request, "Please correct the errors below.")
    else: # GET request
        form = AdCampaignForm(vendor=vendor) # Pass vendor

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
    context = {'products': products, 'vendor': vendor}
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
        form = VendorProductForm(request.POST, request.FILES) # Include FILES for potential images later
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = vendor # Assign vendor automatically
            product.save()
            # TODO: Handle ProductImage uploads if using a gallery formset
            messages.success(request, f"Product '{product.name}' created successfully.")
            return redirect(reverse('core:vendor_product_list'))
        else:
            messages.error(request, "Please correct the errors below.")
    else: # GET request
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
            # TODO: Handle ProductImage updates/deletions
            messages.success(request, f"Product '{product.name}' updated successfully.")
            return redirect(reverse('core:vendor_product_list'))
        else:
            messages.error(request, "Please correct the errors below.")
    else: # GET request
        form = VendorProductForm(instance=product)

    context = {'form': form, 'vendor': vendor, 'product': product, 'form_title': f'Edit Product: {product.name}'}
    return render(request, 'core/vendor_product_form.html', context)

@login_required
@require_POST # Ensure this is only accessible via POST
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
        # Redirect to a relevant page, maybe the dashboard or home
        return redirect(reverse('core:home'))

    # Get OrderItems sold by this vendor, prefetch related order and product for efficiency
    vendor_order_items = OrderItem.objects.filter(product__vendor=vendor).select_related('order', 'product', 'order__user')

    # Get distinct Orders containing those items, ordered by creation date (most recent first)
    orders = Order.objects.filter(items__in=vendor_order_items).distinct().order_by('-created_at')

    context = {'orders': orders, 'vendor': vendor}
    # We'll need to create this template: 'core/vendor_order_list.html'
    return render(request, 'core/vendor_order_list.html', context)
# --- END: Vendor Orders View ---

# TODO: Add vendor_campaign_edit view similar to vendor_promotion_edit
# TODO: Add delete views for both promotions and campaigns if needed

# --- Language Update View ---
def update_language(request):
    """
    View to handle language change requests from the modal.
    Sets language in session and cookie.
    """
    if request.method == 'POST':
        language_code = request.POST.get('language_input')
        if language_code and check_for_language(language_code):
            # Set the language in the session
            # Use the constant defined by Django for the session key
            request.session['_language'] = language_code # <<< Use the correct session key string
            # Activate the language for the current request/response cycle (optional but good practice)
            activate(language_code)

            # Redirect back to the previous page or home
            # Using HTTP_REFERER can be unreliable, fallback to home
            next_url = request.POST.get('next', request.META.get('HTTP_REFERER', reverse('core:home')))

            # Optional: If using URL-based language prefixes, try to translate the URL
            # next_url = translate_url(next_url, language_code)

            response = HttpResponseRedirect(next_url)
            # Also set the language cookie for persistence if not using sessions exclusively
            # Use constants from settings for cookie parameters
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language_code,
                                max_age=settings.LANGUAGE_COOKIE_AGE,
                                path=settings.LANGUAGE_COOKIE_PATH,
                                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                                secure=settings.LANGUAGE_COOKIE_SECURE,
                                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                                samesite=settings.LANGUAGE_COOKIE_SAMESITE)
            messages.success(request, f"Language updated to {language_code}.") # Consider using get_language_info
            return response
        else:
             messages.warning(request, "Invalid language selected.")

    # If not POST or invalid language, redirect home or back
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('core:home')))


# --- Authentication Views (Largely unchanged) ---
def signin(request):
    # ... (existing signin logic) ...
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
                # Basic security check for next_url
                if next_url and not next_url.startswith('/') and ':' not in next_url:
                     next_url = reverse('core:home') # Default if invalid
                return redirect(next_url or reverse('core:home'))
            else:
                 messages.error(request, "Invalid username or password.") # Add error for failed auth
        else:
             messages.error(request, "Invalid username or password.") # Add error for invalid form
    else:
        form = AuthenticationForm()

    context = {'form': form, 'next': request.GET.get('next', '')}
    return render(request, 'core/signin.html', context)


def signout(request):
    # ... (existing signout logic) ...
    current_user_name = request.user.username if request.user.is_authenticated else None
    logout(request)
    if current_user_name:
        messages.info(request, f"You have been successfully logged out, {current_user_name}.")
    else:
        messages.info(request, "You have been successfully logged out.")
    return redirect('signin')


# --- Static Page Views (Unchanged) ---
def terms(request):
    return render(request, 'core/terms.html')

def privacy(request):
    return render(request, 'core/privacy.html')

def help_page(request):
    return render(request, 'core/help.html')
