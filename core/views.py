# c:\Users\Hp\Desktop\Nexus\core\views.py
import logging
import json
import random # For selecting random spotlights
from decimal import Decimal
import stripe
import requests # For making HTTP requests to Paystack
import uuid # For generating unique references
from django.db.models.fields.files import FieldFile # Import FieldFile for type checking
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import update_session_auth_hash
from django import forms # <<< Add this import
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View, TemplateView, FormView # Added FormView
from django.db import transaction
from django.db.models import Q, Avg, Count, Sum, F, ExpressionWrapper, fields
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.paginator import Paginator
from authapp.models import CustomUser # <<< Import CustomUser from authapp
from django.core.files.uploadedfile import InMemoryUploadedFile # Import for type checking
from django.db.models.functions import TruncMonth # <<< Import TruncMonth
from .models import ( # Ensure UserProfile is imported
    Product, Category, Cart, CartItem, Order, OrderItem, Address,
    Wishlist, ProductReview, Vendor, VendorReview, Promotion, AdCampaign,
    Service, ServiceCategory, ServicePackage, ServiceReview, ServiceProviderProfile, PortfolioItem,
    Notification, UserProfile, Transaction, Escrow, Dispute, Message, Conversation, ProductImage, ProductVideo, # Added ProductImage, ProductVideo
    ShippingMethod, PaymentGateway, TaxRate, Currency, SiteSettings, BlogPost, BlogCategory,
    FAQ, SupportTicket, TicketResponse, UserActivity, AuditLog, APIKey, WebhookEvent,
    FeatureFlag, ABTest, UserSegment, EmailTemplate, SMSTemplate, PushNotificationTemplate,
    Affiliate, AffiliateClick, AffiliatePayout, LoyaltyProgram, LoyaltyTier, UserPoints,
    Reward, UserReward, Coupon, UserCoupon, GiftCard, UserGiftCard,
    VendorShipping, VendorPayment, VendorAdditionalInfo, # Added for vendor onboarding
    FAQ, TermsAndConditions, PrivacyPolicy, # For chatbot knowledge base
    # CustomUser, # Assuming CustomUser is your user model - THIS LINE IS NOW COMMENTED OUT
    ProductVariant, # Added for product variants
    ServiceBooking, # Added for service bookings PayoutRequest, # Already imported
    ServiceAvailability, # Added for service availability
    ServiceAddon, # Added for service addons
    UserFeedback, # Added for general user feedback
    SystemNotification, # Added for system-wide notifications
    UserPreferences, # Added for user preferences
    SecurityLog, # Added for security-related logs
    TermsAndConditions, PrivacyPolicy, # Added for legal documents
    ProductImage, # Added for multiple product images
    OrderNote, # Added for order notes
    # ... any other models you have ...
    RiderProfile, DeliveryTask, RiderApplication, ActiveRiderBoost, # Import RiderProfile, DeliveryTask, RiderApplication, ActiveRiderBoost
    BoostPackage, PayoutRequest # Import PayoutRequest
)
from .forms import ( # Ensure RiderApplication is imported if needed by forms, but it's a model
    AddressForm, ProductReviewForm, VendorReviewForm,
    VendorRegistrationForm, VendorProfileUpdateForm, # VendorVerificationForm, # Commented out
    VendorProductForm, PromotionForm, AdCampaignForm,
    ServiceForm, ServicePackageFormSet, ServiceReviewForm, ServiceSearchForm,
    ServiceProviderRegistrationForm, PortfolioItemForm, VendorPayoutRequestForm, # Added VendorPayoutRequestForm
    VendorShippingForm, VendorPaymentForm, VendorAdditionalInfoForm, RiderPayoutRequestForm, # Added RiderPayoutRequestForm
    VerificationMethodSelectionForm, ServiceProviderPayoutRequestForm, # New multi-step forms, Added ServiceProviderPayoutRequestForm
    BusinessDetailsForm,             # New multi-step forms
    IndividualDetailsForm,           # New multi-step forms
    VerificationConfirmationForm,    # New multi-step forms
    # ... any other forms you have ...
    RiderProfileApplicationForm,RiderProfileUpdateForm  # Import Rider form
)
from authapp.forms import UserProfileUpdateForm as AuthUserProfileUpdateForm # Renamed to avoid clash

from .utils import (
    send_order_confirmation_email, generate_invoice_pdf,
    calculate_shipping_cost, process_payment_with_gateway,
    # ... any other utility functions ...
)
# from .tasks import process_order_task # Example for Celery tasks
from .signals import order_placed # Example for signals
from .ai_services_gemini import generate_text_with_gemini, generate_response_from_image_and_text # Import Gemini services

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize Stripe (if you're using it)
# stripe.api_key = settings.STRIPE_SECRET_KEY


# --- Helper Functions (Consider moving to utils.py if they grow) ---
def get_cart_data(user):
    """
    Retrieves cart items and total for a given user.
    """
    if user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=user, ordered=False)
        cart_items = cart.items.all()
        cart_total = cart.get_cart_total()
        item_count = cart.get_item_count()
    else:
        # Handle session-based cart for anonymous users (simplified)
        cart_session = {} # Placeholder for session cart logic
        cart_items = []
        cart_total = Decimal('0.00')
        item_count = 0
    return {'cart_items': cart_items, 'cart_total': cart_total, 'item_count': item_count}

# --- Core Views ---

def home(request):
    # Example: Fetch some products and categories for the homepage
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    new_arrivals = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    top_categories = Category.objects.annotate(num_products=Count('products')).filter(num_products__gt=0, is_active=True).order_by('-num_products')[:6]

    # Example: Fetch some services
    featured_services = Service.objects.filter(is_active=True, is_featured=True)[:4] # Assuming an 'is_featured' field

    # Example: Fetch some vendors
    top_vendors = Vendor.objects.filter(is_approved=True, is_verified=True).annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')[:4] # Assuming 'reviews' related_name

    # Fetch Featured Riders
    now = timezone.now()
    featured_rider_profiles = RiderProfile.objects.filter(
        is_approved=True,
        is_available=True, # Optional: only show if currently available
        active_boosts__boost_package__boost_type='featured_profile',
        active_boosts__is_active=True,
        active_boosts__expires_at__gt=now
    ).distinct().select_related('user', 'user__userprofile').order_by('?')[:4] # Show a few random featured riders

    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'top_categories': top_categories,
        'featured_services': featured_services,
        'top_vendors': top_vendors,
        'page_title': _("Welcome to NEXUS Marketplace"),
        'featured_rider_profiles': featured_rider_profiles,
    }
    return render(request, 'core/home.html', context)

class ProductListView(ListView):
    model = Product
    template_name = 'core/product_list.html'
    context_object_name = 'products'
    paginate_by = 12 # Show 12 products per page

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).order_by('-created_at')
        category_slug = self.kwargs.get('category_slug')
        query = self.request.GET.get('q')

        if category_slug:
            category = get_object_or_404(Category, slug=category_slug, is_active=True)
            queryset = queryset.filter(category=category)
            self.category = category # For use in get_context_data
        else:
            self.category = None

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(vendor__name__icontains=query)
            )
            self.search_query = query
        else:
            self.search_query = None

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True).annotate(product_count=Count('products')).filter(product_count__gt=0)
        context['current_category'] = getattr(self, 'category', None)
        context['search_query'] = getattr(self, 'search_query', None)
        if self.category:
            context['page_title'] = self.category.name
        elif self.search_query:
            context['page_title'] = _("Search Results for '{}'").format(self.search_query)
        else:
            context['page_title'] = _("All Products")
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'core/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'product_slug' # If using slug in URL

    def get_queryset(self):
        # Ensure only active products are accessible
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['related_products'] = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
        context['reviews'] = ProductReview.objects.filter(product=product, is_approved=True).order_by('-created_at')
        context['review_form'] = ProductReviewForm()
        context['average_rating'] = context['reviews'].aggregate(Avg('rating'))['rating__avg']
        context['page_title'] = product.name
        # Check if product is in wishlist
        if self.request.user.is_authenticated:
            context['in_wishlist'] = Wishlist.objects.filter(user=self.request.user, products=product).exists()
        else:
            context['in_wishlist'] = False # Or handle session-based wishlist

        # Add 3D model URL to context
        if product.three_d_model:
            context['three_d_model_url'] = product.three_d_model.url
        else:
            context['three_d_model_url'] = None

        # --- CORRECTED PLACEMENT for product_images and debug print ---
        context['product_images'] = product.images.all() # Assuming 'images' is the related_name from ProductImage to Product

        # --- DEBUG PRINT ---
        print(f"DEBUG (ProductDetailView): Product: {product.name}, Images found: {context['product_images']}")
        # --- END DEBUG PRINT ---

        context['product_videos'] = product.videos.all() # Assuming 'videos' is the related_name for ProductVideo
        # context['average_product_rating'] = product.average_rating # This was already set from context['average_rating']
        context['product_reviews'] = context['reviews'] # Re-use for clarity if needed

        # For the review form
        if self.request.user.is_authenticated:
            context['user_has_reviewed_product'] = ProductReview.objects.filter(product=product, user=self.request.user).exists()
        else:
            context['user_has_reviewed_product'] = False

        # --- START: AI Review Summarization ---
        context['ai_review_summary'] = None
        # Use existing reviews, limit to a reasonable number for the prompt
        reviews_for_summary = list(context['reviews'][:15]) # Take up to 15 most recent approved reviews

        if reviews_for_summary:
            review_texts = []
            for i, r in enumerate(reviews_for_summary):
                review_text = f"{i+1}. Rating: {r.rating}/5. Review: {r.review}"
                if r.video: # Optionally mention if there's a video, though AI won't see it
                    review_text += " (Includes video)"
                review_texts.append(review_text)
            
            reviews_str = "\n".join(review_texts)

            prompt_for_summary = f"""You are an e-commerce assistant for NEXUS marketplace.
A user is looking at the product "{product.name}".
Based ONLY on the following customer reviews, provide a concise summary (around 50-70 words) highlighting the main positive and negative points.
If there are no clear negative points, focus on the positives.
If the reviews are generally mixed, reflect that.
Do not invent any information not present in the reviews.

Customer Reviews:
{reviews_str}

Concise Summary:
"""
            logger.debug(f"AI Review Summary - Prompt for '{product.name}':\n{prompt_for_summary}")
            summary_text = generate_text_with_gemini(prompt_for_summary)
            if summary_text and not summary_text.startswith("Error:"):
                context['ai_review_summary'] = summary_text.strip()
            else:
                logger.error(f"AI Review Summary - Gemini error for '{product.name}': {summary_text}")
                context['ai_review_summary'] = _("Could not generate a review summary at this time.")
        else:
            context['ai_review_summary'] = _("There are no reviews yet to summarize for this product.")
        # --- END: AI Review Summarization ---

        # --- START: AI Product Recommendations ---
        recommended_product_objects = []
        try:
            # 1. Fetch candidate products (e.g., from the same category, excluding current product)
            # Initial attempt: products from the same category
            primary_candidate_products = Product.objects.filter(
                category=product.category,
                is_active=True
            ).exclude(id=product.id).order_by('?')[:10] # Get up to 10 random candidates

            candidate_products_list = list(primary_candidate_products)
            min_candidates_for_ai = 5 # Let's say we want at least 5 candidates for the AI
            max_candidates_for_ai = 15 # Max to send to AI to keep prompt reasonable

            # If not enough candidates from the same category, try a broader fallback
            if len(candidate_products_list) < min_candidates_for_ai:
                logger.debug(f"AI Recs - Not enough candidates from same category ({len(candidate_products_list)}). Fetching fallback candidates.")
                
                # Fallback 1: Other Featured Products (not already included)
                current_candidate_ids = [p.id for p in candidate_products_list]
                featured_fallback = list(Product.objects.filter(
                    is_active=True, is_featured=True
                ).exclude(id=product.id).exclude(id__in=current_candidate_ids).order_by('-updated_at')[:max_candidates_for_ai - len(candidate_products_list)])
                candidate_products_list.extend(featured_fallback)
                candidate_products_list = list(dict.fromkeys(candidate_products_list)) # Remove duplicates while preserving order

                # Fallback 2: Recently Added Active Products (not already included)
                if len(candidate_products_list) < min_candidates_for_ai:
                    current_candidate_ids = [p.id for p in candidate_products_list]
                    recent_fallback = list(Product.objects.filter(
                        is_active=True
                    ).exclude(id=product.id).exclude(id__in=current_candidate_ids).order_by('-created_at')[:max_candidates_for_ai - len(candidate_products_list)])
                    candidate_products_list.extend(recent_fallback)
                    candidate_products_list = list(dict.fromkeys(candidate_products_list))

                # Fallback 3: Random Active Products (if still needed and other fallbacks didn't suffice)
                if len(candidate_products_list) < min_candidates_for_ai:
                    current_candidate_ids = [p.id for p in candidate_products_list]
                    random_fallback = list(Product.objects.filter(is_active=True).exclude(id=product.id).exclude(id__in=current_candidate_ids).order_by('?')[:max_candidates_for_ai - len(candidate_products_list)])
                    candidate_products_list.extend(random_fallback)
                    candidate_products_list = list(dict.fromkeys(candidate_products_list))

                # Combine primary and fallback, ensuring no duplicates and limiting total
            candidate_products = candidate_products_list[:max_candidates_for_ai] # Final list, capped at max_candidates_for_ai

            logger.debug(f"AI Recs - Product: {product.name}, Final candidate products count: {len(candidate_products)}")

            if candidate_products: # Check if the list is not empty
                # 2. Construct the prompt
                candidate_list_str = "\n".join(
                    [f"- {p.name} (Category: {p.category.name}, Price: {p.price})" for p in candidate_products]
                )
                # Refined Prompt
                prompt_for_ai = f"""You are an expert e-commerce recommendation engine for an online marketplace called NEXUS.
A user is currently viewing the following product:
Product Name: "{product.name}"
Category: "{product.category.name}"
Description Snippet: "{product.description[:250]}..."

Your task is to select exactly 3 distinct products from the 'Available Products List' below that this user might also be interested in, based on the product they are currently viewing.
The recommendations should be relevant and appealing.

Output Instructions:
Return ONLY the names of the 3 recommended products.
Each product name must be on a new, separate line.
Do NOT include any other text, numbering, bullet points, or explanations in your response.

Available Products List:
                {candidate_list_str}

Recommended product names (3 names, each on a new line):
                """

                logger.debug(f"AI Recs - Prompt sent to Gemini:\n{prompt_for_ai}")

                # 3. Call Gemini API
                raw_recommendations_text = generate_text_with_gemini(prompt_for_ai)
                logger.debug(f"AI Recs - Raw response from Gemini: '{raw_recommendations_text}'")

                if raw_recommendations_text and not raw_recommendations_text.startswith("Error:"):
                    recommended_names = [name.strip() for name in raw_recommendations_text.split('\n') if name.strip()]
                    logger.debug(f"AI Recs - Parsed recommended names: {recommended_names}")
                    # 4. Fetch actual product objects
                    if recommended_names:
                        recommended_product_objects = Product.objects.filter(name__in=recommended_names, is_active=True).distinct()[:3]
                        logger.debug(f"AI Recs - Fetched product objects from DB: {list(recommended_product_objects.values_list('name', flat=True))}")
            logger.debug(f"AI Recs - Final recommended_product_objects count: {len(recommended_product_objects)}")
        except Exception as e:
            logger.error(f"Error generating AI recommendations for product {product.id}: {e}")
        context['ai_recommended_products'] = recommended_product_objects
        # --- END CORRECTED PLACEMENT ---

        return context

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user, ordered=False)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not item_created:
        cart_item.quantity += 1
    cart_item.save()
    messages.success(request, _(f"'{product.name}' added to your cart."))
    return redirect('core:cart_detail') # Or redirect to product page or wherever makes sense

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user, cart__ordered=False)
    product_name = cart_item.product.name # product was not defined, changed to cart_item.product.name
    cart_item.delete()
    messages.info(request, _(f"'{product_name}' removed from your cart.")) # used product_name
    return redirect('core:cart_detail')

@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user, cart__ordered=False)
        quantity = request.POST.get('quantity')
        try:
            quantity = int(quantity)
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, _(f"Quantity for '{cart_item.product.name}' updated."))
            elif quantity == 0:
                cart_item.delete()
                messages.info(request, _(f"'{cart_item.product.name}' removed from cart."))
            else:
                messages.error(request, _("Invalid quantity."))
        except ValueError:
            messages.error(request, _("Invalid quantity format."))
    return redirect('core:cart_detail')


@login_required
def cart_detail(request):
    cart_data = get_cart_data(request.user)
    context = {
        'cart_items': cart_data['cart_items'],
        'cart_total': cart_data['cart_total'],
        'page_title': _("Your Shopping Cart"),
    }
    return render(request, 'core/cart_detail.html', context)

@login_required
def clear_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user, ordered=False)
    if cart.items.exists():
        cart.items.all().delete() # Delete all items in the cart
        # Optionally, you might want to reset the cart's total or other attributes if you store them directly on the Cart model
        # cart.total_amount = Decimal('0.00') # Example if you have such a field
        # cart.save()
        messages.success(request, _("Your cart has been cleared."))
    else:
        messages.info(request, _("Your cart is already empty."))
    return redirect('core:cart_detail') # Redirect back to the cart page

@login_required
def checkout(request):
    cart_data = get_cart_data(request.user)
    if not cart_data['cart_items']:
        messages.info(request, _("Your cart is empty. Add some items to proceed to checkout."))
        return redirect('core:product_list') # Or home

    billing_addresses = Address.objects.filter(user=request.user, address_type='billing')
    shipping_addresses = Address.objects.filter(user=request.user, address_type='shipping')

    # Determine if shipping is required (e.g., if any cart item is physical)
    requires_shipping = any(item.product.product_type == 'physical' for item in cart_data['cart_items'])

    # --- START: Calculate Estimated Delivery Fees for Display ---
    estimated_platform_delivery_fee = Decimal('0.00')
    estimated_total_vendor_delivery_fees = Decimal('0.00')
    estimated_total_delivery_fee = Decimal('0.00')

    # For now, we'll assume the first shipping address is used for estimation if multiple exist.
    # A more robust solution might involve AJAX updates if the address changes on the page.
    default_shipping_address = shipping_addresses.filter(is_default=True).first() or shipping_addresses.first()

    if requires_shipping and default_shipping_address:
        estimated_platform_delivery_fee = calculate_shipping_cost(cart=cart_data['cart_items'][0].cart, shipping_address=default_shipping_address) # Pass the cart object

        for item in cart_data['cart_items']:
            product_fulfillment = item.product.fulfillment_method
            vendor_default_fulfillment = item.product.vendor.default_fulfillment_method if item.product.vendor else 'vendor'
            actual_fulfillment = product_fulfillment if product_fulfillment else vendor_default_fulfillment
            if actual_fulfillment == 'vendor' and item.product.product_type == 'physical' and item.product.vendor_delivery_fee is not None:
                estimated_total_vendor_delivery_fees += item.product.vendor_delivery_fee # Assuming vendor_delivery_fee is per product line
    estimated_total_delivery_fee = estimated_platform_delivery_fee + estimated_total_vendor_delivery_fees
    # --- END: Calculate Estimated Delivery Fees for Display ---

    address_form = AddressForm() # For adding new addresses

    # --- Logic to determine available payment methods ---
    default_payment_choices = list(Order.PAYMENT_METHOD_CHOICES) # Make a mutable copy
    available_payment_choices = []

    cart_has_negotiable_product = False
    cart_is_digital_only = True if cart_data['cart_items'] else False # Assume true if cart has items, then check

    negotiable_slugs = getattr(settings, 'NEGOTIABLE_PRODUCT_CATEGORY_SLUGS', [])

    for item in cart_data['cart_items']:
        if item.product.product_type != 'digital':
            cart_is_digital_only = False
        if negotiable_slugs and item.product and item.product.category and item.product.category.slug in negotiable_slugs:
            cart_has_negotiable_product = True

    if cart_is_digital_only:
        available_payment_choices = [choice for choice in default_payment_choices if choice[0] == 'escrow']
    elif cart_has_negotiable_product:
        available_payment_choices = default_payment_choices
    else:
        available_payment_choices = [choice for choice in default_payment_choices if choice[0] == 'escrow']

    payment_method_choices = available_payment_choices

    context = {
        'cart_items': cart_data['cart_items'],
        'cart_total': cart_data['cart_total'],
        'billing_addresses': billing_addresses,
        'shipping_addresses': shipping_addresses,
        'address_form': address_form,
        'requires_shipping': requires_shipping,
        'payment_method_choices': payment_method_choices,
        'estimated_platform_delivery_fee': estimated_platform_delivery_fee,
        'estimated_total_vendor_delivery_fees': estimated_total_vendor_delivery_fees,
        'estimated_total_delivery_fee': estimated_total_delivery_fee,
        'page_title': _("Checkout"),
    }
    return render(request, 'core/checkout.html', context)


@login_required
@require_POST # Ensure only POST requests are accepted
def calculate_delivery_fee_ajax(request):
    """
    AJAX endpoint to calculate estimated delivery fee based on selected shipping address.
    """
    shipping_address_id = request.POST.get('shipping_address_id')
    use_billing_for_shipping = request.POST.get('use_billing_for_shipping') == 'true'

    user = request.user
    try:
        user_cart = Cart.objects.get(user=user, ordered=False)
        cart_items_qs = user_cart.items.select_related('product__vendor').filter(product__isnull=False) # Ensure product is not null
    except Cart.DoesNotExist:
        return JsonResponse({'error': _('Cart not found.')}, status=400)

    estimated_platform_delivery_fee = Decimal('0.00')
    estimated_total_vendor_delivery_fees = Decimal('0.00')
    estimated_total_delivery_fee = Decimal('0.00')
    requires_shipping = any(item.product.product_type == 'physical' for item in cart_items_qs if item.product) # Check if any physical items exist

    shipping_address = None
    if requires_shipping and not use_billing_for_shipping:
        if shipping_address_id:
            try:
                # Ensure the address belongs to the user
                shipping_address = Address.objects.get(id=shipping_address_id, user=user)
            except Address.DoesNotExist:
                 return JsonResponse({'error': _('Invalid shipping address selected.')}, status=400)
        # If shipping_address_id is None and not using billing, shipping_address remains None, fee will be 0

    if requires_shipping and shipping_address: # Only calculate if shipping is needed and an address is selected (and not using billing)
        # calculate_shipping_cost now internally filters for Nexus-fulfilled items
        estimated_platform_delivery_fee = calculate_shipping_cost(cart=user_cart, shipping_address=shipping_address)

        for item in cart_items_qs:
            if item.product and item.product.product_type == 'physical': # Only consider physical products
                product_fulfillment = item.product.fulfillment_method
                vendor_default_fulfillment = item.product.vendor.default_fulfillment_method if item.product.vendor else 'vendor'
                actual_fulfillment = product_fulfillment if product_fulfillment else vendor_default_fulfillment
                if actual_fulfillment == 'vendor' and item.product.vendor_delivery_fee is not None:
                     # Assuming vendor_delivery_fee is per product line item
                     estimated_total_vendor_delivery_fees += item.product.vendor_delivery_fee

    estimated_total_delivery_fee = estimated_platform_delivery_fee + estimated_total_vendor_delivery_fees

    return JsonResponse({
        'success': True,
        'estimated_platform_delivery_fee': str(estimated_platform_delivery_fee), # Convert Decimal to string for JSON
        'estimated_total_vendor_delivery_fees': str(estimated_total_vendor_delivery_fees),
        'estimated_total_delivery_fee': str(estimated_total_delivery_fee),
        'requires_shipping': requires_shipping,
    })
# --- END: AJAX Delivery Fee Calculation ---


@login_required
@transaction.atomic # Ensure all database operations are atomic
def place_order(request):
    if request.method == 'POST':
        cart_session = request.session.get('cart', {}) # Assuming you might use session cart
        user_cart, cart_created = Cart.objects.get_or_create(user=request.user, ordered=False)
        cart_items_qs = user_cart.items.all()

        if not cart_items_qs.exists():
            messages.error(request, _("Your cart is empty."))
            return redirect('core:cart_detail')

        payment_method_choice = request.POST.get('payment_method')
        logger.debug(f"Received payment_method from POST: {payment_method_choice}")
        valid_payment_methods = [choice[0] for choice in Order.PAYMENT_METHOD_CHOICES]
        logger.debug(f"Valid payment methods from Order model: {valid_payment_methods}")

        if not payment_method_choice or payment_method_choice not in valid_payment_methods:
            logger.error(f"Validation failed for payment_method: '{payment_method_choice}'. Valid options: {valid_payment_methods}")
            logger.debug(f"Full POST data when payment_method validation failed: {request.POST}")
            messages.error(request, _("Please select a valid payment method."))
            return redirect('core:checkout')

        requires_shipping = any(item.product.product_type == 'physical' for item in cart_items_qs)

        try:
            billing_address_id = request.POST.get('billing_address_id')
            if not billing_address_id:
                messages.error(request, _("Billing address is required."))
                return redirect('core:checkout')
            billing_address = get_object_or_404(Address, id=billing_address_id, user=request.user, address_type='billing')

            shipping_address = None
            if requires_shipping:
                use_billing_for_shipping = request.POST.get('use_billing_for_shipping') == 'on'
                if use_billing_for_shipping:
                    shipping_address = billing_address
                else:
                    shipping_address_id = request.POST.get('shipping_address_id')
                    if not shipping_address_id:
                        messages.error(request, _("Shipping address is required."))
                        return redirect('core:checkout')
                    shipping_address = get_object_or_404(Address, id=shipping_address_id, user=request.user, address_type='shipping')

        except (Address.DoesNotExist, ValueError, TypeError) as e:
            logger.error(f"Address selection error in place_order: {e}")
            messages.error(request, _("Invalid address selected. Please try again."))
            return redirect('core:checkout')

        # Calculate cart subtotal (sum of item.price * item.quantity)
        cart_subtotal = user_cart.get_cart_total()

        # --- Initialize delivery fee components ---
        platform_calculated_delivery_fee = Decimal('0.00')
        current_order_item_total_delivery_charges = Decimal('0.00') # This will sum up vendor-set fees

        # Calculate platform delivery fee for Nexus-fulfilled items
        if requires_shipping:
            # calculate_shipping_cost now internally filters for Nexus-fulfilled items
            platform_calculated_delivery_fee = calculate_shipping_cost(user_cart, shipping_address)

        order = Order.objects.create(
            user=request.user,
            billing_address=billing_address,
            shipping_address=shipping_address if requires_shipping else None,
            delivery_fee=Decimal('0.00'), # Initialize, will be updated after items
            total_amount=Decimal('0.00'),   # Initialize, will be updated after items
            platform_delivery_fee=platform_calculated_delivery_fee, # Store the Nexus part
            payment_method=payment_method_choice,
            status='PENDING'
        )

        for cart_item in cart_items_qs:
            # Determine fulfillment method for this item
            product_fulfillment = cart_item.product.fulfillment_method
            vendor_default_fulfillment = cart_item.product.vendor.default_fulfillment_method if cart_item.product.vendor else 'vendor'
            actual_fulfillment = product_fulfillment if product_fulfillment else vendor_default_fulfillment

            item_specific_delivery_charge = Decimal('0.00')
            if actual_fulfillment == 'vendor' and cart_item.product.product_type == 'physical' and cart_item.product.vendor_delivery_fee is not None:
                # Assuming vendor_delivery_fee is a flat fee per product type, not per quantity.
                # If it's per quantity, you'd multiply by cart_item.quantity here.
                # For simplicity, let's assume it's a flat fee for the product line item.
                item_specific_delivery_charge = cart_item.product.vendor_delivery_fee 
                # No, if it's a fee for the item, it should apply once for the line item, or be multiplied if it's per unit.
                # Let's assume vendor_delivery_fee is per product line item for now.
                # If it's per unit, it should be: item_specific_delivery_charge = cart_item.product.vendor_delivery_fee * cart_item.quantity

            order_item = OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
                # Set fulfillment method:
                # 1. Prioritize product-specific setting if it's a physical product.
                # 2. Fallback to vendor's default if product-specific is not set or not applicable.
                # 3. Default to 'vendor' if no other setting is found (e.g., for non-physical or if vendor/product has no setting).
                fulfillment_method=actual_fulfillment,
                item_delivery_charge=item_specific_delivery_charge
            )
            current_order_item_total_delivery_charges += item_specific_delivery_charge # Sum up all item-specific charges

            if cart_item.product.product_type == 'physical':
                product = cart_item.product
                if product.stock is not None:
                    if product.stock >= cart_item.quantity:
                        product.stock -= cart_item.quantity
                        product.save(update_fields=['stock'])
                    else:
                        messages.error(request, _(f"Not enough stock for {product.name}. Order cannot be completed."))
                        order.delete()
                        return redirect('core:cart_detail')

        # Now update the order's total delivery fee and total amount
        order.delivery_fee = order.platform_delivery_fee + current_order_item_total_delivery_charges
        order.total_amount = cart_subtotal + order.delivery_fee
        order.save(update_fields=['delivery_fee', 'total_amount', 'platform_delivery_fee'])

        user_cart.ordered = True
        user_cart.save()

        if 'cart' in request.session:
            del request.session['cart']
            request.session.modified = True

        order_placed.send(sender=Order, order=order)

        messages.success(request, _("Your order has been placed successfully! Order ID: {order_id}").format(order_id=order.order_id))

        is_negotiable_order = order.has_negotiable_category_products()

        if order.payment_method == 'direct':
            if is_negotiable_order:
                order.status = 'AWAITING_DIRECT_PAYMENT'
                order.save(update_fields=['status'])
                messages.info(request, _("Your order for negotiable items has been placed. Please arrange payment and delivery directly with the vendor(s)."))
                return redirect(order.get_absolute_url())
            else:
                messages.warning(request, _("This order requires escrow payment. You will be redirected to Paystack."))
                order.payment_method = 'escrow'
                order.status = 'AWAITING_ESCROW_PAYMENT'
                order.save(update_fields=['payment_method', 'status'])
                return redirect('core:initiate_paystack_payment', order_id=order.id)

        elif order.payment_method == 'escrow':
            order.status = 'AWAITING_ESCROW_PAYMENT'
            order.save(update_fields=['status'])
            messages.info(request, _("Please proceed to make your payment via Paystack for order {order_id}.").format(order_id=order.order_id))
            return redirect('core:initiate_paystack_payment', order_id=order.id)
        else:
            messages.error(request, _("There was an issue with your order's payment method. Please contact support."))
            return redirect(order.get_absolute_url())

    else:
        messages.error(request, _("Invalid request method."))
        return redirect('core:checkout')


@login_required
def add_checkout_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        address_type = request.POST.get('address_type')

        if form.is_valid():
            # Pass the user to the form's save method
            address = form.save(commit=False, user=request.user)
            address.user = request.user
            if not hasattr(address, 'address_type') or not address.address_type:
                 address.address_type = address_type

            if address.is_default:
                Address.objects.filter(user=request.user, address_type=address.address_type).update(is_default=False)

            address.save()
            messages.success(request, _(f"{address_type.capitalize()} address saved successfully."))
        else:
            error_message_list = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_message_list.append(f"{field.replace('_', ' ').capitalize()}: {error}")
            messages.error(request, _("Failed to save address. Please correct the errors: ") + "; ".join(error_message_list))

    return redirect('core:checkout')


class OrderHistoryView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'core/order_history.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("My Order History")
        return context

class OrderDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Order
    template_name = 'core/order_detail.html'
    context_object_name = 'order'

    def get_object(self, queryset=None):
        order_id_from_url = self.kwargs.get('order_id')
        if order_id_from_url:
            return get_object_or_404(Order, order_id=order_id_from_url)
        return super().get_object(queryset)

    def test_func(self):
        order = self.get_object()
        return self.request.user == order.user or self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        context['page_title'] = _("Order Details - {order_id}").format(order_id=order.order_id)

        order_has_physical_products = order.has_physical_products()
        order_has_services = order.has_services()

        context['order_has_physical_products'] = order_has_physical_products
        context['order_has_services'] = order_has_services

        can_confirm = False
        if order.user == self.request.user:
            if order.payment_method == 'escrow' and \
               order.status in ['PROCESSING', 'IN_PROGRESS'] and \
               not getattr(order, 'customer_confirmed_delivery_at', None) and \
               order_has_services:
                can_confirm = True
        context['can_confirm_completion'] = can_confirm

        can_confirm_delivery = False
        if order.user == self.request.user and \
           order.payment_method == 'escrow' and \
           order_has_physical_products and \
           order.status in ['PROCESSING', 'SHIPPED'] and \
           not getattr(order, 'customer_confirmed_delivery_at', None):
            can_confirm_delivery = True
        context['can_confirm_product_delivery'] = can_confirm_delivery

        # --- Add Map Data for Customer ---
        # Find a relevant delivery task for this order (e.g., the first Nexus-fulfilled one)
        delivery_task = order.delivery_tasks.filter(
            pickup_latitude__isnull=False,
            pickup_longitude__isnull=False,
            delivery_latitude__isnull=False,
            delivery_longitude__isnull=False
        ).first() # Get the first task with coordinates

        if delivery_task:
            context['show_map'] = True
            context['pickup_lat'] = float(delivery_task.pickup_latitude)
            context['pickup_lng'] = float(delivery_task.pickup_longitude)
            context['delivery_lat'] = float(delivery_task.delivery_latitude)
            context['delivery_lng'] = float(delivery_task.delivery_longitude)
        context['google_maps_api_key'] = settings.GOOGLE_MAPS_API_KEY
        context['can_confirm_product_delivery'] = can_confirm_delivery

        return context

@login_required
@require_POST
def process_checkout_choice(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user, status='PENDING')
    payment_method_choice = request.POST.get('payment_method')

    valid_payment_methods = [choice[0] for choice in Order.PAYMENT_METHOD_CHOICES]

    if not payment_method_choice or payment_method_choice not in valid_payment_methods:
        messages.error(request, _("Invalid payment method selected. Please try again."))
        return redirect('core:order_detail', order_id=order.order_id)

    order.payment_method = payment_method_choice
    order.ordered = True

    if payment_method_choice == 'escrow':
        order.status = 'AWAITING_ESCROW_PAYMENT'
        order.save()
        messages.info(request, _("Please proceed to make your payment via Paystack."))
        return redirect('core:initiate_paystack_payment', order_id=order.id)

    elif payment_method_choice == 'direct':
        order.status = 'AWAITING_DIRECT_PAYMENT'
        order.save()
        messages.success(request, _("You've chosen Direct Arrangement. Please contact the service provider to arrange payment. Your order status has been updated."))
        return redirect('core:order_detail', order_id=order.order_id)

    else:
        messages.error(request, _("An unexpected error occurred. Please try again."))
        return redirect('core:order_detail', order_id=order.order_id)

@login_required
@require_POST
def customer_confirm_service_completion(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    if order.payment_method == 'escrow' and \
       order.status in ['PROCESSING', 'IN_PROGRESS'] and \
       not order.customer_confirmed_delivery_at and \
       order.has_services(): # Changed from customer_confirmed_completion_at

        order.customer_confirmed_delivery_at = timezone.now() # Changed field name
        order.status = 'PENDING_PAYOUT' # Changed status
        order.save(update_fields=['customer_confirmed_delivery_at', 'status'])

        messages.success(request, _("Thank you for confirming the service completion! The provider will be notified."))
    else:
        messages.error(request, _("This order cannot be marked as completed at this time, or has already been confirmed."))

    return redirect('core:order_detail', order_id=order.order_id)


@login_required
@require_POST
def customer_confirm_product_delivery(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    if order.payment_method == 'escrow' and \
       order.has_physical_products() and \
       order.status in ['PROCESSING', 'SHIPPED'] and \
       not getattr(order, 'customer_confirmed_delivery_at', None):

        order.customer_confirmed_delivery_at = timezone.now()
        order.status = 'PENDING_PAYOUT'
        order.save(update_fields=['customer_confirmed_delivery_at', 'status'])

        messages.success(request, _("Thank you for confirming delivery! The vendor will be notified."))
    else:
        messages.error(request, _("This order's delivery cannot be confirmed at this time, or has already been confirmed."))

    return redirect('core:order_detail', order_id=order.order_id)


@login_required
def initiate_paystack_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_method != 'escrow' or order.status != 'AWAITING_ESCROW_PAYMENT':
        messages.error(request, _("This order is not eligible for Paystack payment at this time."))
        return redirect('core:order_detail', order_id=order.order_id)

    url = "https://api.paystack.co/transaction/initialize"
    amount_in_kobo = int(order.total_amount * 100)

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "email": request.user.email,
        "amount": amount_in_kobo,
        "currency": "GHS",
        "reference": order.paystack_ref or f"NEXUS_ORD_{order.order_id}_{uuid.uuid4().hex[:6]}",
        "callback_url": request.build_absolute_uri(reverse('core:paystack_callback')),
        "metadata": {
            "order_id": str(order.order_id),
            "user_id": str(request.user.id),
            "description": f"Payment for Order #{order.order_id}"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("status"):
            order.paystack_ref = response_data["data"]["reference"]
            order.save(update_fields=['paystack_ref'])
            authorization_url = response_data["data"]["authorization_url"]
            return redirect(authorization_url)
        else:
            messages.error(request, _("Could not initialize payment with Paystack: {error}").format(error=response_data.get("message", "Unknown error")))
    except requests.exceptions.RequestException as e:
        logger.error(f"Paystack API request failed: {e}")
        messages.error(request, _("Could not connect to payment gateway. Please try again later."))

    return redirect('core:order_detail', order_id=order.order_id)

@csrf_exempt
def paystack_callback(request):
    reference = request.GET.get('reference')
    if not reference:
        messages.error(request, _("Payment reference not found in callback."))
        return redirect('core:order_history')

    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("status") and response_data["data"]["status"] == "success":
            paystack_order_ref = response_data["data"]["reference"]
            try:
                order = Order.objects.get(paystack_ref=paystack_order_ref)
                if order.status == 'AWAITING_ESCROW_PAYMENT':
                    order.status = 'PROCESSING'
                    order.transaction_id = response_data["data"]["id"]
                    order.save(update_fields=['status', 'transaction_id'])
                    messages.success(request, _("Payment successful! Your order is being processed."))
                    return redirect('core:order_detail', order_id=order.order_id)
                else:
                    messages.info(request, _("This payment has already been processed."))
                    return redirect('core:order_detail', order_id=order.order_id)
            except Order.DoesNotExist:
                messages.error(request, _("Order associated with this payment reference not found."))
                logger.error(f"Paystack callback: Order not found for reference {paystack_order_ref}")
                return redirect('core:order_history')
        else:
            messages.error(request, _("Payment verification failed or payment was not successful. Please try again or contact support."))
            try:
                order = Order.objects.get(paystack_ref=reference)
                return redirect('core:order_detail', order_id=order.order_id)
            except Order.DoesNotExist:
                return redirect('core:order_history')
    except requests.exceptions.RequestException as e:
        logger.error(f"Paystack verification API request failed: {e}")
        messages.error(request, _("Could not verify payment status with the gateway. Please contact support if your payment was debited."))
        try:
            order = Order.objects.get(paystack_ref=reference)
            return redirect('core:order_detail', order_id=order.order_id)
        except Order.DoesNotExist:
             return redirect('core:order_history')
    except Exception as e:
        logger.error(f"Unexpected error in Paystack callback for reference {reference}: {e}")
        messages.error(request, _("An unexpected error occurred during payment verification."))
        return redirect('core:order_history')

@login_required
def user_profile_view(request):
    is_vendor = hasattr(request.user, 'vendor_profile') and request.user.vendor_profile is not None
    is_service_provider = hasattr(request.user, 'service_provider_profile') and request.user.service_provider_profile is not None

    if not is_vendor and not is_service_provider:
        messages.warning(request, _("You must be a vendor or service provider to view your profile."))
        return redirect('core:home')

    try:
        user_profile_instance = request.user.userprofile
    except UserProfile.DoesNotExist:
        user_profile_instance = UserProfile.objects.create(user=request.user)

    context = {
        'profile_owner': request.user,
        'user_profile': user_profile_instance,
        'page_title': _("My Profile"),
    }
    return render(request, 'core/user_profile.html', context)


@login_required
def edit_user_profile(request):
    is_vendor = hasattr(request.user, 'vendor_profile') and request.user.vendor_profile is not None
    is_service_provider = hasattr(request.user, 'service_provider_profile') and request.user.service_provider_profile is not None

    if not is_vendor and not is_service_provider:
        messages.warning(request, _("You must be a vendor or service provider to edit your profile."))
        return redirect('core:home')

    user = request.user
    try:
        user_profile_instance = user.userprofile
    except UserProfile.DoesNotExist:
        user_profile_instance = UserProfile.objects.create(user=user)

    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated successfully!"))
            return redirect('core:user_profile')
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        form = UserProfileUpdateForm(instance=user)

    print(f"DEBUG (VIEW): Form object in view: {form}")
    print(f"DEBUG (VIEW): Form fields in view: {form.fields if form else 'Form is None'}")

    context = {
        'form': form,
        'page_title': _("Edit Profile"),
        'profile_owner': request.user
    }
    print(f"DEBUG (VIEW): Context being passed to template: {context}")
    return render(request, 'core/edit_user_profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, _('Your password was successfully updated!'))
            return redirect('core:user_profile')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        form = PasswordChangeForm(request.user)
    context = {
        'form': form,
        'page_title': _("Change Password"),
    }
    return render(request, 'core/change_password.html', context)

@login_required
def view_wishlist(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    context = {
        'wishlist_items': wishlist.products.all(),
        'page_title': _("My Wishlist"),
    }
    return render(request, 'core/wishlist.html', context)

@login_required
@require_POST
def add_to_wishlist(request):
    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)

    if product in wishlist.products.all():
        wishlist.products.remove(product)
        added = False
        message = _(f"'{product.name}' removed from your wishlist.")
    else:
        wishlist.products.add(product)
        added = True
        message = _(f"'{product.name}' added to your wishlist.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'added': added, 'message': message, 'wishlist_count': wishlist.products.count()})

    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'core:product_list'))


@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    if product in wishlist.products.all():
        wishlist.products.remove(product)
        messages.success(request, _(f"'{product.name}' removed from your wishlist."))
    else:
        messages.info(request, _(f"'{product.name}' was not in your wishlist."))
    return redirect('core:wishlist_detail') # Changed from wishlist_view


@login_required
@require_POST
def submit_product_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    form = ProductReviewForm(request.POST, request.FILES)

    if ProductReview.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, _("You have already reviewed this product."))
        return redirect(product.get_absolute_url())

    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.save()
        messages.success(request, _("Your review has been submitted successfully!"))
        # product.update_average_rating() # Assuming this method exists on Product model
    else:
        # Correctly access field labels from the form instance
        error_messages = []
        for field_name, error_list in form.errors.items():
            field_label = form.fields.get(field_name).label if form.fields.get(field_name) else field_name.replace('_', ' ').capitalize()
            error_messages.append(f"{field_label}: {', '.join(error_list)}")
        error_str = "; ".join(error_messages)
        messages.error(request, _("Failed to submit review. Please correct the errors: {errors}").format(errors=error_str))

    return redirect(product.get_absolute_url())


class VendorListView(ListView):
    model = Vendor
    template_name = 'core/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 10

    def get_queryset(self):
        return Vendor.objects.filter(is_approved=True, is_verified=True).annotate(
            average_rating=Avg('reviews__rating'),
            product_count=Count('products', distinct=True)
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Our Vendors")
        return context

class VendorDetailView(DetailView):
    model = Vendor
    template_name = 'core/vendor_detail.html'
    context_object_name = 'vendor'
    slug_url_kwarg = 'vendor_slug'

    def get_queryset(self):
        return Vendor.objects.filter(is_approved=True, is_verified=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.get_object()
        context['products'] = Product.objects.filter(vendor=vendor, is_active=True)[:12]
        context['reviews'] = VendorReview.objects.filter(vendor=vendor, is_approved=True).order_by('-created_at')
        context['review_form'] = VendorReviewForm()
        context['average_rating'] = context['reviews'].aggregate(Avg('rating'))['rating__avg']
        context['page_title'] = vendor.name
        return context

@login_required
@require_POST
def submit_vendor_review(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    form = VendorReviewForm(request.POST)

    if VendorReview.objects.filter(vendor=vendor, user=request.user).exists():
        messages.warning(request, _("You have already reviewed this vendor."))
        return redirect(vendor.get_absolute_url())

    if form.is_valid():
        review = form.save(commit=False)
        review.vendor = vendor
        review.user = request.user
        review.save()
        messages.success(request, _("Your review for {vendor_name} has been submitted!").format(vendor_name=vendor.name))
        # vendor.update_average_rating() # Assuming this method exists
    else:
        error_str = " ".join([f"{field.label if field else ''}: {', '.join(errors)}" for field, errors in form.errors.items()])
        messages.error(request, _("Failed to submit review. Please correct the errors: {errors}").format(errors=error_str))
    return redirect(vendor.get_absolute_url())


class ServiceListView(ListView):
    model = Service
    template_name = 'core/service_list.html'
    context_object_name = 'services'
    paginate_by = 9

    def get_queryset(self):
        queryset = Service.objects.filter(
            is_active=True,
            provider__service_provider_profile__is_approved=True
        ).select_related(
            'provider',
            'provider__service_provider_profile', # Ensures this is loaded
            'provider__userprofile', # If you display user profile info
            'category'
        ).prefetch_related('packages', 'images').order_by('-created_at')

        # Get category from URL kwargs first, then from GET parameters as a fallback/override
        category_slug_kwarg = self.kwargs.get('category_slug')
        category_slug_get = self.request.GET.get('category')
        final_category_slug = category_slug_get or category_slug_kwarg # Prioritize GET param if present

        query = self.request.GET.get('q')

        self.category = None # Initialize
        if final_category_slug:
            self.category = get_object_or_404(ServiceCategory, slug=final_category_slug, is_active=True)
             # Ensure we are using self.category for filtering
            # If line 1095 was "queryset = queryset.filter(category=category)", this is the fix:
            queryset = queryset.filter(category=self.category) 
            print(f"Filtered by category: {self.category.name}")


        self.search_query = None # Initialize
        if query:
            self.search_query = query # Store the query for context
            search_filters = (
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(provider__username__icontains=query) |
                Q(provider__service_provider_profile__business_name__icontains=query) |
                Q(packages__name__icontains=query) # Added search in package names
            )
            queryset = queryset.filter(search_filters).distinct() # Apply filters and ensure distinct results

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['featured_services'] = Service.objects.filter(
            is_active=True,
            is_featured=True,
            provider__service_provider_profile__is_approved=True
        ).select_related('provider', 'category').prefetch_related('images', 'packages')[:4]

        context['top_service_categories'] = ServiceCategory.objects.filter(
            is_active=True,
            parent__isnull=True
        ).annotate(num_services=Count('services')).filter(num_services__gt=0).order_by('-num_services')[:6]

        context['all_service_categories'] = ServiceCategory.objects.filter(is_active=True, parent__isnull=True).annotate(
            num_services=Count('services')
        ).filter(num_services__gt=0).order_by('name')

        context['current_provider_id'] = self.request.GET.get('provider')
        context['search_form'] = ServiceSearchForm(initial={'q': getattr(self, 'search_query', None)})
        context['search_query'] = self.search_query # Use the instance variable
        context['current_category_slug'] = self.category.slug if self.category else self.request.GET.get('category')

        if context['current_category_slug']:
            try:
                current_category_obj = ServiceCategory.objects.get(slug=context['current_category_slug'], is_active=True)
                context['page_title'] = _("Services in {category_name}").format(category_name=current_category_obj.name)
            except ServiceCategory.DoesNotExist:
                context['page_title'] = _("Explore Services")
        elif context['search_query']:
            context['page_title'] = _("Search Results for Services: '{query}'").format(query=context['search_query'])
        else:
            context['page_title'] = _("Explore Our Services")
        return context


class ServiceSearchResultsView(ListView):
    model = Service
    template_name = 'core/service_search_results.html' # New template
    context_object_name = 'services'
    paginate_by = 9

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        self.search_query = query # Store for context

        if not query:
            return Service.objects.none() # Return no results if query is empty

        queryset = Service.objects.filter(
            is_active=True,
            provider__service_provider_profile__is_approved=True
        ).select_related(
            'provider', 'provider__service_provider_profile', 'category'
        ).prefetch_related('packages', 'images')

        search_filters = (
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(provider__username__icontains=query) |
            Q(provider__service_provider_profile__business_name__icontains=query) |
            Q(packages__name__icontains=query)
        )
        queryset = queryset.filter(search_filters).distinct().order_by('-created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = getattr(self, 'search_query', '')
        context['search_query'] = query
        context['page_title'] = _("Search Results for '{query}'").format(query=query) if query else _("Service Search")
        context['search_form'] = ServiceSearchForm(initial={'q': query}) # For a search bar on the results page
        # You might want to pass categories if you plan to allow filtering on the results page
        # context['all_service_categories'] = ServiceCategory.objects.filter(is_active=True).annotate(num_services=Count('services')).filter(num_services__gt=0).order_by('name')
        return context

class CategoryServiceListView(ListView):
    model = Service
    template_name = 'core/category_service_list.html' # We'll create this new template
    context_object_name = 'services'
    paginate_by = 9  # Adjust as needed

    def get_queryset(self):
        # Get the category object based on the slug from URL kwargs
        self.category = get_object_or_404(ServiceCategory, slug=self.kwargs['category_slug'], is_active=True)
        
        # Filter services by the fetched category and other standard criteria
        queryset = Service.objects.filter(
            category=self.category,
            is_active=True,
            provider__service_provider_profile__is_approved=True
        ).select_related(
            'provider',
            'provider__service_provider_profile',
            'provider__userprofile',
            'category'  # Though we are filtering by it, selecting it can be useful
        ).prefetch_related('packages', 'images').order_by('-created_at')

        # Handle search query within this category
        self.search_query = self.request.GET.get('q')
        if self.search_query:
            search_filters = (
                Q(title__icontains=self.search_query) |
                Q(description__icontains=self.search_query) |
                Q(provider__username__icontains=self.search_query) |
                Q(provider__service_provider_profile__business_name__icontains=self.search_query) |
                Q(packages__name__icontains=self.search_query)
            )
            queryset = queryset.filter(search_filters).distinct()
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_category'] = self.category
        context['current_category_slug'] = self.category.slug # For active state in sidebar
        context['page_title'] = _("Services in {category_name}").format(category_name=self.category.name)
        context['search_query'] = self.search_query
        
        # For the sidebar filter, we still need all active categories
        context['all_service_categories'] = ServiceCategory.objects.filter(is_active=True).annotate(
            num_services=Count('services', filter=Q(services__is_active=True, services__provider__service_provider_profile__is_approved=True))
        ).filter(num_services__gt=0).order_by('name')
        
        # If you have a specific search form you want to use:
        # context['search_form'] = ServiceSearchForm(initial={'q': self.search_query})
        return context



class ServiceDetailView(DetailView):
    model = Service
    template_name = 'core/service_detail.html'
    context_object_name = 'service'
    slug_url_kwarg = 'service_slug'

    def get_queryset(self):
        return Service.objects.filter(is_active=True).select_related(
            'provider', 'provider__service_provider_profile', 'category'
        ).prefetch_related('packages', 'images', 'videos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.get_object()
        context['reviews'] = ServiceReview.objects.filter(service=service, is_approved=True).order_by('-created_at')
        context['review_form'] = ServiceReviewForm()
        context['average_rating'] = context['reviews'].aggregate(Avg('rating'))['rating__avg']
        context['page_title'] = service.title
        context['service_packages'] = service.packages.filter(is_active=True).order_by('display_order', 'price')
        context['service_images'] = service.images.all()
        context['service_videos'] = service.videos.all()
        user_has_reviewed = False
        if self.request.user.is_authenticated:
            user_has_reviewed = ServiceReview.objects.filter(service=service, user=self.request.user).exists()
        context['user_has_reviewed'] = user_has_reviewed
        return context

@login_required
@require_POST
def submit_service_review(request, service_slug): # Changed from service_id to service_slug
    service = get_object_or_404(Service, slug=service_slug) # Changed to slug
    form = ServiceReviewForm(request.POST)

    if ServiceReview.objects.filter(service=service, user=request.user).exists():
        messages.warning(request, _("You have already reviewed this service."))
        return redirect(service.get_absolute_url())

    if form.is_valid():
        review = form.save(commit=False)
        review.service = service
        review.user = request.user
        review.save()
        messages.success(request, _("Your review for '{service_title}' has been submitted!").format(service_title=service.title))
        # service.update_average_rating() # Assuming this method exists
    else:
        error_str = " ".join([f"{field.label if field else ''}: {', '.join(errors)}" for field, errors in form.errors.items()])
        messages.error(request, _("Failed to submit review. Please correct the errors: {errors}").format(errors=error_str))
    return redirect(service.get_absolute_url())

@login_required
def add_service_to_order(request, package_id):
    package = get_object_or_404(ServicePackage, id=package_id, is_active=True)

    new_order = Order.objects.create(
        user=request.user,
        total_amount=package.price
    )
    OrderItem.objects.create(
        order=new_order,
        service_package=package,
        price=package.price,
        quantity=1
    )
    messages.success(request, _("'{package_name}' has been added to a new order. Please proceed to choose a payment method.").format(package_name=package.name))
    return redirect('core:order_detail', order_id=new_order.order_id)

class IsServiceProviderMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and \
               hasattr(self.request.user, 'service_provider_profile') and \
               self.request.user.service_provider_profile is not None and \
               self.request.user.service_provider_profile.is_approved

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(reverse('authapp:signin') + f'?next={self.request.path}') # Corrected redirect
        if not hasattr(self.request.user, 'service_provider_profile') or not self.request.user.service_provider_profile:
            messages.info(self.request, _("You need to register as a service provider first."))
            return redirect('core:become_service_provider')
        if not self.request.user.service_provider_profile.is_approved:
            messages.warning(self.request, _("Your service provider profile is pending approval."))
            return redirect('core:home')
        return super().handle_no_permission()


@login_required
def become_service_provider(request):
    if hasattr(request.user, 'service_provider_profile') and request.user.service_provider_profile:
        messages.info(request, _("You are already registered as a service provider."))
        return redirect('core:provider_dashboard')

    if request.method == 'POST':
        form = ServiceProviderRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, _("Congratulations! Your service provider profile has been created. It will be reviewed by our team shortly."))
            return redirect('core:provider_dashboard')
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        form = ServiceProviderRegistrationForm()

    context = {
        'form': form,
        'page_title': _("Become a Service Provider")
    }
    return render(request, 'core/become_service_provider.html', context)


class ProviderDashboardView(LoginRequiredMixin, IsServiceProviderMixin, TemplateView):
    template_name = 'core/provider_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider_profile = self.request.user.service_provider_profile
        services = Service.objects.filter(provider=self.request.user)
        context['services'] = services
        context['active_services_count'] = services.filter(is_active=True).count()
        context['total_services_count'] = services.count()
        service_orders = ServiceBooking.objects.filter(service_package__service__provider=self.request.user)
        context['service_orders'] = service_orders
        context['recent_service_orders'] = service_orders.order_by('-created_at')[:5]
        context['in_progress_service_orders_count'] = service_orders.filter(status__in=['PENDING', 'ACCEPTED', 'IN_PROGRESS']).count()
        context['completed_service_orders_count'] = service_orders.filter(status='COMPLETED').count()
        context['page_title'] = _("Provider Dashboard")
        context['provider_profile'] = provider_profile
        return context

class ServiceCreateView(LoginRequiredMixin, IsServiceProviderMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'core/service_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['package_formset'] = ServicePackageFormSet(self.request.POST, self.request.FILES, prefix='packages')
        else:
            context['package_formset'] = ServicePackageFormSet(prefix='packages')
        context['page_title'] = _("Offer a New Service")
        context['form_title'] = _("Create New Service")
        context['submit_button_text'] = _("Create Service")
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        package_formset = context['package_formset']
        with transaction.atomic():
            form.instance.provider = self.request.user
            self.object = form.save()
            if package_formset.is_valid():
                package_formset.instance = self.object
                package_formset.save()
                messages.success(self.request, _("Service '{service_title}' created successfully!").format(service_title=self.object.title))
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, _("Please correct the errors in the service packages below."))
                return self.form_invalid(form)

    def get_success_url(self):
        return reverse('core:provider_dashboard')

class ServiceUpdateView(LoginRequiredMixin, IsServiceProviderMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'core/service_form.html'
    slug_url_kwarg = 'service_slug'

    def get_queryset(self):
        return Service.objects.filter(provider=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['package_formset'] = ServicePackageFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='packages')
        else:
            context['package_formset'] = ServicePackageFormSet(instance=self.object, prefix='packages')
        context['page_title'] = _("Edit Service - {service_title}").format(service_title=self.object.title)
        context['form_title'] = _("Edit Service Details")
        context['submit_button_text'] = _("Save Changes")
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        package_formset = context['package_formset']
        with transaction.atomic():
            self.object = form.save()
            if package_formset.is_valid():
                package_formset.save()
                messages.success(self.request, _("Service '{service_title}' updated successfully!").format(service_title=self.object.title))
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, _("Please correct the errors in the service packages below."))
                return self.form_invalid(form)

    def get_success_url(self):
        return reverse('core:provider_dashboard')

class ServiceDeleteView(LoginRequiredMixin, IsServiceProviderMixin, DeleteView):
    model = Service
    template_name = 'core/service_confirm_delete.html'
    success_url = reverse_lazy('core:provider_dashboard')
    slug_url_kwarg = 'service_slug'

    def get_queryset(self):
        return Service.objects.filter(provider=self.request.user)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _("Service '{service_title}' has been deleted.").format(service_title=self.object.title))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Confirm Delete Service - {service_title}").format(service_title=self.object.title)
        return context


class ProviderProfileDetailView(DetailView):
    model = CustomUser
    template_name = 'core/provider_profile_detail.html'
    context_object_name = 'profile_owner'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_queryset(self):
        return CustomUser.objects.filter(
            service_provider_profile__isnull=False,
            service_provider_profile__is_approved=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_owner = self.get_object()
        provider_profile = getattr(profile_owner, 'service_provider_profile', None)
        context['provider_profile'] = provider_profile

        if provider_profile:
            context['services'] = Service.objects.filter(provider=profile_owner, is_active=True)
            context['service_reviews'] = ServiceReview.objects.filter(service__provider=profile_owner, is_approved=True).order_by('-created_at')[:5]
            context['average_rating'] = ServiceReview.objects.filter(service__provider=profile_owner, is_approved=True).aggregate(Avg('rating'))['rating__avg']
            context['review_count'] = ServiceReview.objects.filter(service__provider=profile_owner, is_approved=True).count()
            context['portfolio_items'] = PortfolioItem.objects.filter(provider_profile=provider_profile).order_by('-uploaded_at')
        else:
            context['services'] = Service.objects.none()
            context['service_reviews'] = ServiceReview.objects.none()
            context['average_rating'] = None
            context['review_count'] = 0
            context['portfolio_items'] = PortfolioItem.objects.none()

        context['page_title'] = _("{username}'s Provider Profile").format(username=profile_owner.username)
        return context


@login_required
def edit_service_provider_profile(request):
    try:
        provider_profile = request.user.service_provider_profile
    except ServiceProviderProfile.DoesNotExist:
        messages.error(request, _("You do not have a service provider profile to edit. Please register first."))
        return redirect('core:become_service_provider')

    if request.method == 'POST':
        if 'submit_profile' in request.POST:
            profile_form = ServiceProviderRegistrationForm(request.POST, request.FILES, instance=provider_profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, _("Provider profile updated successfully!"))
                return redirect('core:edit_service_provider_profile')
            else:
                messages.error(request, _("Error updating profile. Please correct the issues below."))
                portfolio_item_form = PortfolioItemForm()
        elif 'submit_portfolio_item' in request.POST:
            portfolio_item_form = PortfolioItemForm(request.POST, request.FILES)
            if portfolio_item_form.is_valid():
                item = portfolio_item_form.save(commit=False)
                item.provider_profile = provider_profile
                item.save()
                messages.success(request, _("Portfolio item added successfully!"))
                return redirect('core:edit_service_provider_profile')
            else:
                messages.error(request, _("Error adding portfolio item. Please correct the issues below."))
                profile_form = ServiceProviderRegistrationForm(instance=provider_profile)
        else:
            profile_form = ServiceProviderRegistrationForm(instance=provider_profile)
            portfolio_item_form = PortfolioItemForm()
    else:
        profile_form = ServiceProviderRegistrationForm(instance=provider_profile)
        portfolio_item_form = PortfolioItemForm()

    portfolio_items = PortfolioItem.objects.filter(provider_profile=provider_profile).order_by('-uploaded_at')

    context = {
        'profile_form': profile_form,
        'portfolio_item_form': portfolio_item_form,
        'portfolio_items': portfolio_items,
        'page_title': _("Edit Provider Profile & Portfolio")
    }
    return render(request, 'core/edit_service_provider_profile.html', context)


@login_required
@require_POST
def delete_portfolio_item(request, item_id):
    try:
        provider_profile = request.user.service_provider_profile
        item = get_object_or_404(PortfolioItem, id=item_id, provider_profile=provider_profile)
        item_title = item.title or "Untitled Item"
        item.delete()
        messages.success(request, _("Portfolio item '{title}' deleted successfully.").format(title=item_title))
    except ServiceProviderProfile.DoesNotExist:
        messages.error(request, _("You do not have a service provider profile."))
    except PortfolioItem.DoesNotExist:
        messages.error(request, _("Portfolio item not found or you do not have permission to delete it."))
    except Exception as e:
        messages.error(request, _("An error occurred: {error}").format(error=str(e)))
    return redirect('core:edit_service_provider_profile')


class IsVendorMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and \
               hasattr(self.request.user, 'vendor_profile') and \
               self.request.user.vendor_profile is not None

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(reverse('authapp:signin') + f'?next={self.request.path}') # Corrected redirect
        messages.info(self.request, _("You need to register as a vendor to access this page."))
        return redirect('core:sell_on_nexus') # Changed from vendor_registration to sell_on_nexus


@login_required
def vendor_registration_view(request):
    if hasattr(request.user, 'vendor_profile') and request.user.vendor_profile:
        messages.info(request, _("You are already registered as a vendor."))
        return redirect('core:vendor_dashboard')

    if request.method == 'POST':
        form = VendorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.user = request.user
            vendor.save()
            VendorShipping.objects.get_or_create(vendor=vendor)
            VendorPayment.objects.get_or_create(vendor=vendor)
            VendorAdditionalInfo.objects.get_or_create(vendor=vendor)
            messages.success(request, _("Vendor registration submitted! Your application will be reviewed."))
            return redirect('core:vendor_dashboard')
    else:
        form = VendorRegistrationForm()
    context = {
        'form': form,
        'page_title': _("Become a Vendor")
    }
    return render(request, 'core/vendor_registration.html', context)


class VendorDashboardView(LoginRequiredMixin, IsVendorMixin, TemplateView):
    template_name = 'core/vendor_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.request.user.vendor_profile

        context['shop_info_complete'] = vendor.is_shop_info_complete()
        context['business_info_status'] = vendor.get_business_info_status_display()
        context['shipping_info_complete'] = vendor.is_shipping_info_complete()
        context['payment_info_complete'] = vendor.is_payment_info_complete()
        context['additional_info_complete'] = vendor.is_additional_info_complete()
        context['all_sections_complete'] = all([
            context['shop_info_complete'],
            vendor.get_business_info_status_display() == 'COMPLETED',
            context['shipping_info_complete'],
            context['payment_info_complete'],
            context['additional_info_complete']
        ])

        vendor_order_items = OrderItem.objects.filter(product__vendor=vendor)
        context['total_sales'] = vendor_order_items.filter(order__status__in=['DELIVERED', 'COMPLETED']) \
                                   .aggregate(total=Sum(F('quantity') * F('price')))['total'] or Decimal('0.00')
        context['total_orders_count'] = Order.objects.filter(items__product__vendor=vendor).distinct().count()

        vendor_products = Product.objects.filter(vendor=vendor)
        context['active_products_count'] = vendor_products.filter(is_active=True).count()
        context['total_products_count'] = vendor_products.count()
        context['low_stock_products'] = vendor_products.filter(is_active=True, stock__lte=5, product_type='physical').order_by('stock')

        context['recent_orders'] = Order.objects.filter(items__product__vendor=vendor).distinct().order_by('-created_at')[:5]

        context['vendor'] = vendor
        context['page_title'] = _("Vendor Dashboard") 
        context['quick_links'] = [ # Ensure these names match your urls.py
            {'name': _('View Products'), 'url_name': 'core:vendor_products', 'icon': 'fas fa-box-open'},
            {'name': _('View Orders'), 'url_name': 'core:vendor_orders', 'icon': 'fas fa-receipt'},
            {'name': _('Edit Store Profile'), 'url_name': 'core:vendor_profile_edit', 'icon': 'fas fa-store'},
        ]
        
          # Add unread notification count
        if self.request.user.is_authenticated:
                context['unread_notification_count'] = Notification.objects.filter(recipient=self.request.user, is_read=False).count()
        else:
                context['unread_notification_count'] = 0 # Should not happen due to LoginRequiredMixin
        
        return context

class VendorProductListView(LoginRequiredMixin, IsVendorMixin, ListView):
    model = Product
    template_name = 'core/vendor_product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        vendor = self.request.user.vendor_profile
        queryset = Product.objects.filter(vendor=vendor).order_by('-created_at')

        stock_status = self.request.GET.get('stock_status')
        if stock_status == 'low':
            queryset = queryset.filter(stock__lte=5, product_type='physical')
        elif stock_status == 'out':
            queryset = queryset.filter(stock=0, product_type='physical')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor'] = self.request.user.vendor_profile
        context['page_title'] = _("Manage Products")
        context['current_stock_status'] = self.request.GET.get('stock_status', '')
        return context


class VendorProductCreateView(LoginRequiredMixin, IsVendorMixin, CreateView):
    model = Product
    form_class = VendorProductForm
    template_name = 'core/vendor_product_form.html'

    def form_valid(self, form):
        form.instance.vendor = self.request.user.vendor_profile
        self.object = form.save()
        product = self.object
        images = self.request.FILES.getlist('images')
        for img_file in images:
            ProductImage.objects.create(product=product, image=img_file)
        video_files = self.request.FILES.getlist('videos')
        for vid_file in video_files:
            ProductVideo.objects.create(product=product, video=vid_file)
        messages.success(self.request, _("Product '{product_name}' created successfully! Images and videos (if provided) have been uploaded.").format(product_name=product.name))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('core:vendor_product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Add New Product")
        context['form_title'] = _("Create Product")
        context['is_update_form'] = False
        return context

class VendorProductUpdateView(LoginRequiredMixin, IsVendorMixin, UpdateView):
    model = Product
    form_class = VendorProductForm
    template_name = 'core/vendor_product_form.html'

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user.vendor_profile)

    def form_valid(self, form):
        self.object = form.save()
        product = self.object
        new_images = self.request.FILES.getlist('images')
        for img_file in new_images:
            ProductImage.objects.create(product=product, image=img_file)
        new_video_files = self.request.FILES.getlist('videos')
        for vid_file in new_video_files:
            ProductVideo.objects.create(product=product, video=vid_file)
        messages.success(self.request, _("Product '{product_name}' updated successfully!").format(product_name=product.name))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('core:vendor_product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Edit Product - {product_name}").format(product_name=self.object.name)
        context['form_title'] = _("Edit Product")
        context['existing_images'] = self.object.images.all()
        context['existing_videos'] = self.object.videos.all()
        context['is_update_form'] = True
        return context

class VendorProductDeleteView(LoginRequiredMixin, IsVendorMixin, DeleteView):
    model = Product
    template_name = 'core/vendor_product_confirm_delete.html'
    success_url = reverse_lazy('core:vendor_product_list')

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user.vendor_profile)

    def delete(self, request, *args, **kwargs):
        product_name = self.get_object().name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _("Product '{product_name}' has been deleted.").format(product_name=product_name))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Confirm Delete Product - {product_name}").format(product_name=self.object.name)
        return context

class VendorOrderListView(LoginRequiredMixin, IsVendorMixin, ListView):
    model = Order
    template_name = 'core/vendor_order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        vendor = self.request.user.vendor_profile
        return Order.objects.filter(items__product__vendor=vendor).distinct().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor'] = self.request.user.vendor_profile
        context['page_title'] = _("Manage Orders")
        for order in context['orders']:
            order.vendor_items = order.items.filter(product__vendor=self.request.user.vendor_profile)
        return context

class VendorOrderDetailView(LoginRequiredMixin, IsVendorMixin, DetailView):
    model = Order
    template_name = 'core/vendor/vendor_order_detail.html' # Corrected path
    context_object_name = 'order'

    def get_queryset(self):
        vendor = self.request.user.vendor_profile
        return Order.objects.filter(items__product__vendor=vendor).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        vendor_profile = self.request.user.vendor_profile # Ensure vendor_profile is defined
        context['vendor_order_items'] = order.items.filter(product__vendor=self.request.user.vendor_profile)
        context['vendor'] = self.request.user.vendor_profile
        context['page_title'] = _("Order Details - {order_id}").format(order_id=order.order_id)
        context['google_maps_api_key'] = settings.GOOGLE_MAPS_API_KEY # Ensure this is always passed


 # --- Add Map Data for Vendor ---
        context['show_map'] = False
        context['vendor_location_lat'] = None
        context['vendor_location_lng'] = None
        context['delivery_lat'] = None
        context['delivery_lng'] = None

        # Check if vendor has coordinates
        vendor_has_coords = vendor_profile.latitude is not None and vendor_profile.longitude is not None
        if vendor_has_coords:
            context['vendor_location_lat'] = float(vendor_profile.latitude)
            context['vendor_location_lng'] = float(vendor_profile.longitude)

        # Check if order shipping address has coordinates
        shipping_address_has_coords = False
        if order.shipping_address:
            shipping_address_has_coords = order.shipping_address.latitude is not None and order.shipping_address.longitude is not None
            if shipping_address_has_coords:
                context['delivery_lat'] = float(order.shipping_address.latitude)
                context['delivery_lng'] = float(order.shipping_address.longitude)

        # Only show map if BOTH vendor and shipping address have coordinates
        if vendor_has_coords and shipping_address_has_coords:
            context['show_map'] = True

        return context

@login_required
@require_POST
def update_order_item_status_vendor(request, item_id):
    vendor = request.user.vendor_profile
    order_item = get_object_or_404(OrderItem, id=item_id, product__vendor=vendor)
    new_status = request.POST.get('status')
    allowed_statuses = ['PROCESSING', 'SHIPPED', 'DELIVERED_BY_VENDOR']

    if new_status in allowed_statuses:
        OrderNote.objects.create(
            order=order_item.order,
            user=request.user,
            note=f"Vendor {vendor.name} updated item '{order_item.product.name}' status to {new_status}."
        )
        messages.success(request, _("Status for item '{item_name}' updated to {status}.").format(item_name=order_item.product.name, status=new_status))
    else:
        messages.error(request, _("Invalid status update."))

    return redirect('core:vendor_order_detail', pk=order_item.order.pk)


class VendorReportsView(LoginRequiredMixin, IsVendorMixin, TemplateView):
    template_name = 'core/vendor_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.request.user.vendor_profile

        sales_data = OrderItem.objects.filter(
            product__vendor=vendor,
            order__status__in=['DELIVERED', 'COMPLETED']
        ).annotate(month=TruncMonth('order__created_at')).values('month').annotate(
            total_sales=Sum(F('quantity') * F('price'))
        ).order_by('month')

        context['sales_data_json'] = json.dumps(
            [{'month': item['month'].strftime('%Y-%m'), 'total_sales': float(item['total_sales'])} for item in sales_data],
            cls=DecimalEncoder
        )

        context['top_products'] = Product.objects.filter(vendor=vendor, order_items__order__status__in=['DELIVERED', 'COMPLETED']) \
                                  .annotate(total_sold=Sum('order_items__quantity')) \
                                  .order_by('-total_sold')[:5]

        context['vendor'] = vendor
        context['page_title'] = _("Sales & Performance Reports")
        return context

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class VendorProfileSectionUpdateView(LoginRequiredMixin, IsVendorMixin, UpdateView):
    model = Vendor
    template_name = 'core/vendor_profile_section_form.html'

    def get_object(self, queryset=None):
        return self.request.user.vendor_profile

    def form_valid(self, form):
        messages.success(self.request, _(f"{self.form_title} updated successfully!"))
        vendor = self.get_object()
        if vendor.is_onboarding_complete() and not vendor.is_approved:
            messages.info(self.request, _("Your shop setup is complete and pending final review."))
        return super().form_valid(form)
    
    def form_valid(self, form):
        vendor_profile = form.save(commit=False)
        vendor_profile.verification_status = Vendor.VERIFICATION_STATUS_PENDING_REVIEW
        vendor_profile.verification_documents_submitted = True # Mark that some docs were submitted
        vendor_profile.save()
        messages.success(self.request, _("Your verification information has been submitted for review."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = self.form_title
        context['page_title'] = _("Edit {title} - Vendor Dashboard").format(title=self.form_title)
        return context

class VendorReviewListView(LoginRequiredMixin, IsVendorMixin, ListView):
    model = VendorReview
    template_name = 'core/vendor/vendor_review_list.html' # We'll create this template
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        # Filter reviews for the current vendor
        return VendorReview.objects.filter(vendor=self.request.user.vendor_profile).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor'] = self.request.user.vendor_profile
        context['page_title'] = _("Your Customer Reviews")
        # Calculate average rating for the vendor
        context['average_rating'] = VendorReview.objects.filter(vendor=self.request.user.vendor_profile, is_approved=True).aggregate(Avg('rating'))['rating__avg']
        context['total_reviews'] = VendorReview.objects.filter(vendor=self.request.user.vendor_profile, is_approved=True).count()
        return context


class VendorPayoutListView(LoginRequiredMixin, IsVendorMixin, ListView):
    model = PayoutRequest # Assuming PayoutRequest model is for vendors too, or you have a VendorPayoutRequest model
    template_name = 'core/vendor/vendor_payout_list.html' # We'll need to create this template
    context_object_name = 'payout_requests'
    paginate_by = 10

    def get_queryset(self):
        # Filter payout requests for the current vendor
        # This assumes PayoutRequest has a ForeignKey to Vendor or Vendor's User
        # Adjust if your PayoutRequest model links to Vendor differently
        return PayoutRequest.objects.filter(vendor_profile=self.request.user.vendor_profile).order_by('-requested_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor'] = self.request.user.vendor_profile
        context['page_title'] = _("My Payouts")
        # You might want to add a form for requesting new payouts here if not on a separate page
        return context

    def get_success_url(self):
        return reverse_lazy('core:vendor_dashboard')


class EditVendorProfileView(VendorProfileSectionUpdateView):
    form_class = VendorProfileUpdateForm
    form_title = _("Shop Information")

# class EditVendorVerificationView(VendorProfileSectionUpdateView): # Commented out old view
#     form_class = VendorVerificationForm # This form is no longer defined or used
#     form_title = _("Business/Verification Information")

#     def form_valid(self, form):
#         vendor = form.save(commit=False)
#         vendor.save()
#         messages.success(self.request, _("Verification information updated. This may be subject to review."))
#         return HttpResponseRedirect(self.get_success_url())


class MultiStepVendorVerificationView(LoginRequiredMixin, IsVendorMixin, View):
    template_name = 'core/vendor_verification_multistep.html' # New template for multi-step

    STEP_METHOD = 'method_selection'
    STEP_BUSINESS = 'business_details'
    STEP_INDIVIDUAL = 'individual_details'
    STEP_CONFIRMATION = 'confirmation'

    step_forms = {
        STEP_METHOD: VerificationMethodSelectionForm,
        STEP_BUSINESS: BusinessDetailsForm,
        STEP_INDIVIDUAL: IndividualDetailsForm,
        STEP_CONFIRMATION: VerificationConfirmationForm,
    }

    def get_vendor_profile(self):
        return self.request.user.vendor_profile

    def dispatch(self, request, *args, **kwargs):
        if 'verification_step' not in request.session:
            request.session['verification_step'] = self.STEP_METHOD
            request.session['verification_data'] = {} # Initialize if not present
        return super().dispatch(request, *args, **kwargs)

    def get_current_step(self):
        return self.request.session.get('verification_step', self.STEP_METHOD)

    def get_form_class(self, step=None):
        current_step = step or self.get_current_step()
        return self.step_forms.get(current_step)

    def get_form_kwargs(self, step=None, form_class=None):
        kwargs = {}
        current_step = step or self.get_current_step()
        _form_class = form_class or self.get_form_class(current_step)

        if issubclass(_form_class, forms.ModelForm):
            kwargs['instance'] = self.get_vendor_profile()
        
        # Load initial data from session for the current step, if any
        # This is useful for non-ModelForms or if you want to pre-fill ModelForms from session
        # For ModelForms, the instance usually handles pre-filling from the DB.
        # However, for the 'method_selection' step, we might want to load the choice from session.
        session_data_for_step = self.request.session.get('verification_data', {}).get(current_step, {})
        
        # If editing and method already set on vendor, use that as initial for the first step
        if current_step == self.STEP_METHOD:
            vendor_profile = self.get_vendor_profile()
            if vendor_profile.verification_method and not session_data_for_step.get('verification_method'):
                session_data_for_step['verification_method'] = vendor_profile.verification_method
        
        if session_data_for_step:
            kwargs['initial'] = session_data_for_step
        return kwargs

    def get_next_step(self, current_step):
        # Get verification_method from session, as it's decided in the first step
        method = self.request.session.get('verification_data', {}).get(self.STEP_METHOD, {}).get('verification_method')
        # Fallback to vendor profile if session is somehow empty (e.g., direct access to a later step URL)
        if not method:
            method = self.get_vendor_profile().verification_method

        if current_step == self.STEP_METHOD:
            if method == Vendor.VERIFICATION_METHOD_BUSINESS:
                return self.STEP_BUSINESS
            elif method == Vendor.VERIFICATION_METHOD_INDIVIDUAL:
                return self.STEP_INDIVIDUAL
        elif current_step == self.STEP_BUSINESS or current_step == self.STEP_INDIVIDUAL:
            return self.STEP_CONFIRMATION
        return None # No next step after confirmation

    def get_previous_step(self, current_step):
        method = self.request.session.get('verification_data', {}).get(self.STEP_METHOD, {}).get('verification_method')
        if not method:
            method = self.get_vendor_profile().verification_method

        if current_step == self.STEP_CONFIRMATION:
            if method == Vendor.VERIFICATION_METHOD_BUSINESS:
                return self.STEP_BUSINESS
            elif method == Vendor.VERIFICATION_METHOD_INDIVIDUAL:
                return self.STEP_INDIVIDUAL
        elif current_step == self.STEP_BUSINESS or current_step == self.STEP_INDIVIDUAL:
            return self.STEP_METHOD
        return None # No previous step from method selection

    def get(self, request, *args, **kwargs):
        current_step = self.get_current_step()
        form_class = self.get_form_class(current_step)
        form = form_class(**self.get_form_kwargs(current_step, form_class))
        context = self.get_context_data(form=form, current_step=current_step)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        current_step = self.get_current_step()
        form_class = self.get_form_class(current_step)
        form_kwargs = self.get_form_kwargs(current_step, form_class)
        
        # For ModelForms, ensure instance is passed for updates
        # For simple forms, data and files are enough
        form_kwargs.update({'data': request.POST, 'files': request.FILES if request.FILES else None})
        
        form = form_class(**form_kwargs)
        vendor_profile = self.get_vendor_profile()

        action = request.POST.get('action')
        if action == 'previous':
            prev_step = self.get_previous_step(current_step)
            if prev_step:
                request.session['verification_step'] = prev_step
            # No need to save data when going previous, just redirect
            return redirect(reverse('core:vendor_verification_multistep'))

        if form.is_valid():
            # Store cleaned data in session
             session_step_data = {}
        for key, value in form.cleaned_data.items():
                if not isinstance(value, (InMemoryUploadedFile, FieldFile)): # Exclude file objects and FieldFile objects
                    session_step_data[key] = value
                # For file fields, we rely on form.save() for ModelForms.
                # If this step was a non-ModelForm with a file, we'd need to handle the file
                # (e.g., save to temp storage) and store a reference in session_step_data.
            
        self.request.session.setdefault('verification_data', {})[current_step] = session_step_data
        self.request.session.modified = True # Ensure session is saved

            # If it's a ModelForm step, save to the instance immediately
        if isinstance(form, forms.ModelForm):
                # Special handling for verification_method as it's on Vendor model but from a simple form
                if current_step == self.STEP_METHOD:
                    vendor_profile.verification_method = form.cleaned_data['verification_method']
                    vendor_profile.save(update_fields=['verification_method'])
                else: # For BusinessDetailsForm and IndividualDetailsForm
                    # Re-initialize form with instance for saving, if not already done by get_form_kwargs
                    # This ensures that `form.save()` updates the correct instance.
                    if 'instance' not in form_kwargs: # Should be there for ModelForms
                        form = form_class(request.POST, request.FILES, instance=vendor_profile)
                        if not form.is_valid(): # Re-validate if re-initialized
                            context = self.get_context_data(form=form, current_step=current_step)
                            return render(request, self.template_name, context)
                    form.save() # Saves data to the vendor_profile instance

        if current_step == self.STEP_CONFIRMATION:
                # Final submission logic: apply all session data to the vendor profile
                # This is mostly for non-ModelForm steps or if we want to re-apply all data
                # For ModelForms, data is already saved per step.
                # Here, we mainly set the final status.
                
                # Ensure verification_method is set from session if it was the first step
                method_data = self.request.session.get('verification_data', {}).get(self.STEP_METHOD, {})
                if 'verification_method' in method_data:
                    vendor_profile.verification_method = method_data['verification_method']

                vendor_profile.verification_status = Vendor.VERIFICATION_STATUS_PENDING_REVIEW
                vendor_profile.verification_documents_submitted = True # Mark that some docs were submitted
                vendor_profile.save() # Save final status and any other pending changes

                # Clear session data after successful submission
                if 'verification_step' in request.session: del request.session['verification_step']
                if 'verification_data' in request.session: del request.session['verification_data']
                request.session.modified = True

                messages.success(request, _("Your verification information has been submitted for review."))
                return redirect('core:vendor_dashboard')

        next_step = self.get_next_step(current_step)
        if next_step:
                request.session['verification_step'] = next_step
                return redirect(reverse('core:vendor_verification_multistep'))
        else: # Should be final step case handled above
                messages.error(request, _("An error occurred in the verification process flow."))
                return redirect('core:vendor_dashboard')
        
        # Form is not valid, re-render the current step with errors
        context = self.get_context_data(form=form, current_step=current_step)
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = {} # Initialize context
        current_step = kwargs.get('current_step', self.get_current_step())
        context['form'] = kwargs.get('form') # The form instance passed from get() or post()
        context['current_step'] = current_step
        context['page_title'] = _("Vendor Verification")
        context['form_title'] = self._get_step_title(current_step)
        context['show_previous_button'] = self.get_previous_step(current_step) is not None
        return context

    def _get_step_title(self, step):
        if step == self.STEP_METHOD: return _("Step 1: Select Verification Method")
        elif step == self.STEP_BUSINESS: return _("Step 2: Business Details")
        elif step == self.STEP_INDIVIDUAL: return _("Step 2: Individual Details")
        elif step == self.STEP_CONFIRMATION: return _("Step 3: Confirm and Submit")
        return _("Vendor Verification")


class EditVendorShippingView(VendorProfileSectionUpdateView):
    form_class = VendorShippingForm
    form_title = _("Shipping Information")

class EditVendorPaymentView(VendorProfileSectionUpdateView):
    form_class = VendorPaymentForm
    form_title = _("Payment Information")

class EditVendorAdditionalInfoView(VendorProfileSectionUpdateView):
    form_class = VendorAdditionalInfoForm
    form_title = _("Additional Information")

# --- START: Service Provider Dashboard Views ---
class IsServiceProviderMixin(UserPassesTestMixin):
    """
    Mixin to ensure the user is an authenticated service provider and their profile is approved.
    Redirects to a "become a provider" page or a "pending approval" page if not.
    """
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        try:
            # Check if the user has a service provider profile
            profile = self.request.user.service_provider_profile
            # Optionally, check if the profile is approved
            # return profile.is_approved
            return True # For now, just check if profile exists
        except ServiceProviderProfile.DoesNotExist:
            return False

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(self.request.get_full_path())
        # If user is authenticated but not a service provider (or not approved)
        # messages.info(self.request, _("You need to register as a service provider to access this page."))
        return redirect(reverse('core:become_service_provider')) # Or a specific "pending approval" page

class ServiceProviderDashboardView(LoginRequiredMixin, IsServiceProviderMixin, TemplateView):
    template_name = 'core/provider_dashboard.html' # Point to the template you want to keep

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider_profile = None
        services_qs = Service.objects.none() # Default to an empty queryset
        recent_bookings_qs = ServiceBooking.objects.none()

        try:
            provider_profile = self.request.user.service_provider_profile
            services_qs = Service.objects.filter(provider=self.request.user)
            # Fetch recent bookings related to this provider's services
            # Assuming ServiceBooking model links to ServicePackage which links to Service
            recent_bookings_qs = ServiceBooking.objects.filter(
                service_package__service__provider=self.request.user
            ).select_related('service_package__service', 'user').order_by('-created_at')[:5] # Get latest 5

        except ServiceProviderProfile.DoesNotExist:
            # This case should ideally be handled by IsServiceProviderMixin,
            # but good to have a fallback.
            pass

        context['service_provider_profile'] = provider_profile
        context['total_services_count'] = services_qs.count()
        context['active_services_count'] = services_qs.filter(is_active=True).count()
        context['recent_bookings'] = recent_bookings_qs
        context['page_title'] = _("Service Provider Dashboard")
        return context

class ServiceProviderServicesListView(LoginRequiredMixin, IsServiceProviderMixin, ListView):
    model = Service
    template_name = 'core/service_provider/service_provider_services_list.html' # New template
    context_object_name = 'services'
    paginate_by = 10

    def get_queryset(self):
        # Filter services to show only those belonging to the logged-in provider
        return Service.objects.filter(provider=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("My Services")
        # Optionally, add counts or other relevant info
        # context['active_services_count'] = self.get_queryset().filter(is_active=True).count()
        # context['inactive_services_count'] = self.get_queryset().filter(is_active=False).count()
        return context

# We can reuse existing Create, Update, Delete views for services,
# ensuring their querysets are filtered by the logged-in provider.
# ServiceCreateView, ServiceUpdateView, ServiceDeleteView are already defined.

# --- END: Service Provider Dashboard Views ---


class ServiceProviderBookingsListView(LoginRequiredMixin, IsServiceProviderMixin, ListView):
    model = ServiceBooking # Assuming you have a ServiceBooking model
    template_name = 'core/service_provider/service_provider_bookings_list.html' # New template
    context_object_name = 'bookings'
    paginate_by = 15

    def get_queryset(self):
        # Filter bookings to show only those related to the logged-in provider's services
        # This assumes ServiceBooking -> ServicePackage -> Service -> User (provider)
        return ServiceBooking.objects.filter(
            service_package__service__provider=self.request.user
        ).select_related(
            'service_package__service', 'user', 'service_package'
        ).order_by('-booking_date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("My Bookings")
        return context


class ServiceProviderPayoutRequestListView(LoginRequiredMixin, IsServiceProviderMixin, ListView):
    model = PayoutRequest
    template_name = 'core/service_provider/service_provider_payout_request_list.html' # New template
    context_object_name = 'payout_requests'
    paginate_by = 10

    def get_queryset(self):
        return PayoutRequest.objects.filter(service_provider_profile=self.request.user.service_provider_profile).order_by('-requested_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("My Payout Requests")
        # TODO: Calculate available balance for payout
        # context['available_balance_for_payout'] = ...
        return context

class ServiceProviderPayoutRequestCreateView(LoginRequiredMixin, IsServiceProviderMixin, CreateView):
    model = PayoutRequest
    form_class = ServiceProviderPayoutRequestForm
    template_name = 'core/service_provider/service_provider_payout_request_form.html' # New template
    success_url = reverse_lazy('core:service_provider_payout_requests') # Redirect to list after creation

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['service_provider_profile'] = self.request.user.service_provider_profile
        return kwargs

    def form_valid(self, form):
        form.instance.service_provider_profile = self.request.user.service_provider_profile
        messages.success(self.request, _("Your payout request has been submitted successfully."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Request New Payout")
        if hasattr(self.request.user, 'service_provider_profile') and self.request.user.service_provider_profile:
            context['available_balance_for_payout'] = self.request.user.service_provider_profile.get_available_payout_balance()
        return context


class VendorPromotionListView(LoginRequiredMixin, IsVendorMixin, ListView):
    model = Promotion
    template_name = 'core/vendor_promotion_list.html'
    context_object_name = 'promotions'
    paginate_by = 10

    def get_queryset(self):
        return Promotion.objects.filter(applicable_vendor=self.request.user.vendor_profile).order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Manage Promotions")
        return context

class VendorPromotionCreateView(LoginRequiredMixin, IsVendorMixin, CreateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'core/vendor_promotion_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['vendor'] = self.request.user.vendor_profile
        return kwargs

    def form_valid(self, form):
        form.instance.applicable_vendor = self.request.user.vendor_profile # Changed from vendor to applicable_vendor
        messages.success(self.request, _("Promotion created successfully."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('core:vendor_promotion_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Create New Promotion")
        context['form_title'] = _("Create Promotion")
        return context

class VendorPromotionUpdateView(LoginRequiredMixin, IsVendorMixin, UpdateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'core/vendor_promotion_form.html'

    def get_queryset(self):
        return Promotion.objects.filter(applicable_vendor=self.request.user.vendor_profile) # Changed from vendor

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['vendor'] = self.request.user.vendor_profile
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _("Promotion updated successfully."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('core:vendor_promotion_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Edit Promotion")
        context['form_title'] = _("Edit Promotion")
        return context

class VendorPromotionDeleteView(LoginRequiredMixin, IsVendorMixin, DeleteView):
    model = Promotion
    template_name = 'core/vendor_promotion_confirm_delete.html'
    success_url = reverse_lazy('core:vendor_promotion_list')

    def get_queryset(self):
        return Promotion.objects.filter(applicable_vendor=self.request.user.vendor_profile) # Changed from vendor

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _("Promotion deleted successfully."))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Confirm Delete Promotion")
        return context


class VendorCampaignListView(LoginRequiredMixin, IsVendorMixin, ListView):
    model = AdCampaign
    template_name = 'core/vendor_campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 10

    def get_queryset(self):
        return AdCampaign.objects.filter(vendor=self.request.user.vendor_profile).order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Manage Ad Campaigns")
        return context

class VendorCampaignCreateView(LoginRequiredMixin, IsVendorMixin, CreateView):
    model = AdCampaign
    form_class = AdCampaignForm
    template_name = 'core/vendor_campaign_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['vendor'] = self.request.user.vendor_profile
        return kwargs

    def form_valid(self, form):
        form.instance.vendor = self.request.user.vendor_profile
        messages.success(self.request, _("Ad Campaign created successfully."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('core:vendor_campaign_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Create New Ad Campaign")
        context['form_title'] = _("Create Ad Campaign")
        return context

class VendorCampaignUpdateView(LoginRequiredMixin, IsVendorMixin, UpdateView):
    model = AdCampaign
    form_class = AdCampaignForm
    template_name = 'core/vendor_campaign_form.html'

    def get_queryset(self):
        return AdCampaign.objects.filter(vendor=self.request.user.vendor_profile)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['vendor'] = self.request.user.vendor_profile
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _("Ad Campaign updated successfully."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('core:vendor_campaign_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Edit Ad Campaign")
        context['form_title'] = _("Edit Ad Campaign")
        return context

class VendorCampaignDeleteView(LoginRequiredMixin, IsVendorMixin, DeleteView):
    model = AdCampaign
    template_name = 'core/vendor_campaign_confirm_delete.html'
    success_url = reverse_lazy('core:vendor_campaign_list')

    def get_queryset(self):
        return AdCampaign.objects.filter(vendor=self.request.user.vendor_profile)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _("Ad Campaign deleted successfully."))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Confirm Delete Ad Campaign")
        return context

class AboutUsView(TemplateView):
    template_name = "core/static/about_us.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("About Us")
        return context

class ContactUsView(TemplateView):
    template_name = "core/static/contact_us.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Contact Us")
        return context

class TermsView(TemplateView):
    template_name = "core/static/terms_and_conditions.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['terms'] = TermsAndConditions.objects.latest('version')
        except TermsAndConditions.DoesNotExist:
            context['terms'] = None
        context['page_title'] = _("Terms and Conditions")
        return context

class PrivacyPolicyView(TemplateView):
    template_name = "core/static/privacy_policy.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['policy'] = PrivacyPolicy.objects.latest('version')
        except PrivacyPolicy.DoesNotExist:
            context['policy'] = None
        context['page_title'] = _("Privacy Policy")
        return context


def custom_404(request, exception):
    return render(request, 'errors/404.html', {}, status=404)

def custom_500(request):
    return render(request, 'errors/500.html', {}, status=500)

class HelpPageView(TemplateView):
    template_name = "core/help_page.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Help & Support")
        return context
    

@login_required
@require_POST
def ajax_enhance_product_description(request):
    """
    AJAX view to enhance product description using Gemini AI.
    Expects JSON POST data: product_name, category_name, current_description, keywords (optional)
    """
    if not (hasattr(request.user, 'vendor_profile') and request.user.vendor_profile):
        return JsonResponse({'error': _('User is not a vendor.')}, status=403)

    try:
        data = json.loads(request.body)
        product_name = data.get('product_name', '').strip()
        category_name = data.get('category_name', '').strip()
        current_description = data.get('current_description', '').strip()
        keywords = data.get('keywords', '').strip() # Get keywords from AJAX data

        if not product_name or not category_name:
            return JsonResponse({'error': _('Product name and category are required.')}, status=400)

        prompt = f"""You are an expert e-commerce copywriter tasked with enhancing a product description for NEXUS marketplace.
Product Name: "{product_name}"
Category: "{category_name}"
Current Description (if any): "{current_description if current_description else 'None provided. Please generate a compelling description from scratch.'}"
Optional Keywords provided by vendor: "{keywords if keywords else 'Not provided'}"

Task:
Rewrite or generate a compelling, engaging, and SEO-friendly product description of about 100-150 words.
Highlight key features and benefits.
Use a persuasive and professional tone.
If keywords are provided, try to naturally incorporate them.
Ensure the description is unique and well-structured.

Enhanced Description:
"""
        logger.info(f"AI Description Enhancement - Prompt for '{product_name}':\n{prompt}")
        enhanced_description = generate_text_with_gemini(prompt)

        if enhanced_description and not enhanced_description.startswith("Error:"):
            return JsonResponse({'enhanced_description': enhanced_description.strip()})
        else:
            logger.error(f"AI Description Enhancement - Gemini error for '{product_name}': {enhanced_description}")
            return JsonResponse({'error': _('Failed to enhance description with AI. Please try again or write manually.') + f" (Details: {enhanced_description})"}, status=500)
    except json.JSONDecodeError:
        return JsonResponse({'error': _('Invalid JSON data.')}, status=400)
    except Exception as e:
        logger.error(f"AI Description Enhancement - Unexpected error for '{product_name}': {e}", exc_info=True)
        return JsonResponse({'error': _('An unexpected error occurred.')}, status=500)
    
@login_required
@require_POST
def ajax_generate_3d_model(request):
    """
    AJAX view to simulate initiating an AI 3D model generation process for a product.
    Expects JSON POST data: product_id
    """
    vendor_profile = getattr(request.user, 'vendor_profile', None)
    if not vendor_profile:
        return JsonResponse({'error': _('User is not a vendor.')}, status=403)


    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')

        if not product_id:
            return JsonResponse({'error': _('Product ID is required.')}, status=400)

        product = get_object_or_404(Product, id=product_id, vendor=vendor_profile)

        # Check for premium feature access
        if not vendor_profile.has_premium_3d_generation_access:
            logger.warning(f"Vendor {vendor_profile.name} (ID: {vendor_profile.id}) attempted to use premium 3D generation without access for product {product.id}.")
            # Customize this message or redirect to an upgrade page
            return JsonResponse({'error': _('This is a premium feature. Please upgrade your plan or contact support to enable AI 3D model generation.')}, status=403)

        # Gather information that would be sent to the AI service
        product_name = product.name
        description = product.description
        category_name = product.category.name if product.category else "N/A"
        keywords = product.keywords_for_ai or ""
        existing_2d_images = [img.image.url for img in product.images.all() if img.image]
        # For actual API calls, you might need to pass image file paths or bytes, not just URLs.
        # This would require fetching the image files from storage.

        logger.info(
            f"AI 3D Model Generation Request for Product ID: {product.id}\n"
            f"Name: {product_name}\n"
            f"Category: {category_name}\n"
            f"Description: {description[:100]}...\n"
            f"Keywords: {keywords}\n"
            f"Number of 2D Images: {len(existing_2d_images)}"
        )

        # --- Placeholder for actual AI Service Integration ---
        # Example: Triggering a Celery task
        # from .tasks import generate_3d_model_task # You would create this Celery task

        # try:
        #     # Prepare data for the task (e.g., image file paths or bytes)
        #     image_paths_for_task = [img.image.path for img in product.images.all() if img.image and hasattr(img.image, 'path')]

        #     generate_3d_model_task.delay(
        #         product_id=product.id,
        #         product_name=product_name,
        #         description=description,
        #         image_paths=image_paths_for_task # Or image_bytes
        #         # ... other necessary parameters for the chosen AI service
        #     )
        #     logger.info(f"Celery task initiated for 3D model generation for product ID: {product.id}")
        #     return JsonResponse({'status': 'processing', 'message': _("AI 3D model generation has been started. You will be notified when it's ready. This may take several minutes.")})
        # except Exception as e:
        #     logger.error(f"Failed to initiate Celery task for 3D model generation (Product ID: {product.id}): {e}", exc_info=True)
        #     return JsonResponse({'error': _('Could not start the 3D model generation process. Please try again later.')}, status=500)

        return JsonResponse({'status': 'success', 'message': _("SIMULATED: AI 3D model generation process would be initiated here. You will be notified when it's ready. For now, please save any other product changes. The actual 3D model will need to be uploaded manually once available from the generation service.")})

    except Product.DoesNotExist:
        return JsonResponse({'error': _('Product not found or you do not have permission to access it.')}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': _('Invalid JSON data.')}, status=400)
    except Exception as e:
        logger.error(f"AI 3D Model Generation - Unexpected error for product ID '{product_id}': {e}", exc_info=True)
        return JsonResponse({'error': _('An unexpected error occurred while initiating 3D model generation.')}, status=500)

def get_chatbot_knowledge_base_content(user_message=""):
    """
    Constructs the knowledge base content for the chatbot.
    """
    knowledge_parts = []

    # Fetch active Terms and Conditions
    try:
        terms = TermsAndConditions.objects.filter(is_active=True).latest('effective_date')
        knowledge_parts.append(f"Terms and Conditions (Version: {terms.version}, Effective: {terms.effective_date}):\n{terms.content}\n---")
    except TermsAndConditions.DoesNotExist:
        logger.warning("Chatbot Knowledge Base: Active Terms and Conditions not found.")

    # Fetch active Privacy Policy
    try:
        policy = PrivacyPolicy.objects.filter(is_active=True).latest('effective_date')
        knowledge_parts.append(f"Privacy Policy (Version: {policy.version}, Effective: {policy.effective_date}):\n{policy.content}\n---")
    except PrivacyPolicy.DoesNotExist:
        logger.warning("Chatbot Knowledge Base: Active Privacy Policy not found.")

    # Fetch some relevant FAQs (e.g., top 5 or based on keywords in user_message - simplified here)
    faqs = FAQ.objects.filter(is_active=True).order_by('display_order')[:10] # Get top 10 active FAQs
    if faqs:
        faq_content = "\n\nFrequently Asked Questions (FAQs):\n"
        for faq_item in faqs:
            faq_content += f"Q: {faq_item.question}\nA: {faq_item.answer}\n---\n"
        knowledge_parts.append(faq_content)

    return "\n".join(knowledge_parts)

@require_POST # For now, let's assume chat messages are sent via POST
# @csrf_exempt # REMOVE THIS LINE - CSRF token will now be enforced by default if not present
def ajax_chatbot_message(request):
    """
    AJAX view to handle chatbot messages using Gemini AI.
    Expects JSON POST data: user_message, conversation_history (optional), page_context (optional)
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('user_message', '').strip()
        conversation_history = data.get('conversation_history', []) 
        page_context_data = data.get('page_context', {}) # Get page context

        if not user_message:
            return JsonResponse({'error': _('Message cannot be empty.')}, status=400)

        # --- Enhanced System Prompt ---
        system_prompt = """You are NEXUS Chat, a friendly and highly capable customer support assistant for the NEXUS online marketplace.
Your primary goal is to answer customer questions accurately and helpfully based *only* on the 'Provided Knowledge Base' below.
Do not use any external knowledge or make assumptions.
If the answer to the user's question cannot be found in the Provided Knowledge Base, or if the question is too complex for you to handle (e.g., requires personal account access, or is a complaint needing human review), you MUST clearly state that you don't have the specific information and will escalate the query to a human support agent.
Do NOT attempt to answer if the information is not in the knowledge base.
"""
        # --- Incorporate Page Context into the Prompt ---
        product_details_for_ai_prompt = "" # Initialize to empty string
        
        contextual_info_for_ai = ""
        if page_context_data:
            contextual_info_for_ai += "\n\n[User's Current Context on NEXUS Marketplace]:"
            if page_context_data.get('page_title'):
                contextual_info_for_ai += f"\n- Page Title: \"{page_context_data.get('page_title')}\""
            # The URL itself might be too noisy for the prompt unless specifically needed.
            # if page_context_data.get('url'):
            #     contextual_info_for_ai += f"\n- Viewing Page URL: {page_context_data.get('url')}"

            product_id_on_page = page_context_data.get('product_id_on_page')
            if product_id_on_page:
                try:
                    # IMPORTANT: Validate product_id_on_page thoroughly if used for DB queries
                    product_id = int(product_id_on_page) # Convert to integer
                    product = Product.objects.select_related('category').get(id=product_id, is_active=True) # Fetch safely
                    
                    # Prepare more detailed product information for the AI
                    # Replacing newlines in description to keep the prompt cleaner
                    clean_description = product.description[:250].replace('\n', ' ').replace('\r', '')
                    # This will be added after the main system prompt and before the knowledge base
                    product_details_for_ai_prompt = f"""\n\n[Details for Product Currently Being Viewed: "{product.name}"]:
Product Name: "{product.name}"
Product Category: "{product.category.name if product.category else 'N/A'}"
Description Snippet: "{clean_description}..."
Price: {product.price} 
Product Page: {request.build_absolute_uri(product.get_absolute_url())}""" # Use request to build full URL

                except (Product.DoesNotExist, ValueError, TypeError) as e:
                    # Log this, but don't break the chat if product ID is invalid or not found
                    logger.warning(f"Chatbot: Could not retrieve product details for product_id_on_page: {product_id_on_page} - {e}")
                    product_details_for_ai_prompt = "\n\n[User might be on a product page, but specific product details could not be retrieved for the provided ID.]"
            # Add more context as needed (e.g., category_on_page)
            if contextual_info_for_ai: # Add separator only if context exists
                contextual_info_for_ai += "\n---"

        # --- Fetch Knowledge Base Content ---
        knowledge_base_content = get_chatbot_knowledge_base_content(user_message)
        if not knowledge_base_content:
            knowledge_base_content = "No specific knowledge base articles are available for this query at the moment."

        # --- Construct the full prompt ---
        initial_prompt_content = system_prompt
        if contextual_info_for_ai: # Add if available
            initial_prompt_content += contextual_info_for_ai
        if product_details_for_ai_prompt: # Add if available
            initial_prompt_content += product_details_for_ai_prompt
        
        initial_prompt_content += f"\n\nUser's Question: \"{user_message}\""
        initial_prompt_content += f"\n\nProvided Knowledge Base:\n---\n{knowledge_base_content}\n---\n"

        prompt_parts = [initial_prompt_content]
        for entry in conversation_history: # conversation_history is now the sliced version from frontend
            role = "User" if entry.get('role') == 'user' else "NEXUS Chat"
            prompt_parts.append(f"{role}: {entry.get('text')}")
        prompt_parts.append("NEXUS Chat:") # Cue for the AI to respond
        full_prompt_text = "\n".join(prompt_parts)

        logger.info(f"Chatbot - Prompt (with context) for user message '{user_message}':\n{full_prompt_text}")
        ai_response_text = generate_text_with_gemini(full_prompt_text)

        if ai_response_text and not ai_response_text.startswith("Error:"):
            # TODO: Intent recognition and action mapping would go here for more advanced features.
            # Check if AI response indicates escalation
            if "escalate this query" in ai_response_text.lower() or \
               "escalate it to a human" in ai_response_text.lower() or \
               "human support agent" in ai_response_text.lower():
                logger.info(f"Chatbot indicated escalation for user: {request.user.username if request.user.is_authenticated else 'Anonymous'}, message: '{user_message}'")
                # Future: Create a SupportTicket or send an admin notification here.
                # SupportTicket.objects.create(user=request.user if request.user.is_authenticated else None, subject=f"Chatbot Escalation: {user_message[:50]}...", description=f"User: {user_message}\nAI: {ai_response_text}\nHistory: {conversation_history}")
            return JsonResponse({'ai_response': ai_response_text.strip()})
        else:
            logger.error(f"Chatbot - Gemini error for user message '{user_message}': {ai_response_text}")
            return JsonResponse({'error': _('AI assistant is currently unavailable. Please try again later.')}, status=500)

    except json.JSONDecodeError:
        logger.error("Chatbot - Invalid JSON data received.")
        return JsonResponse({'error': _('Invalid JSON data.')}, status=400)
    except Exception as e:
        logger.error(f"Chatbot - Unexpected error: {e}", exc_info=True)
        return JsonResponse({'error': _('An unexpected error occurred.')}, status=500)

@require_POST
# @csrf_exempt # For initial testing, remove for production and handle CSRF
def ajax_visual_search(request):
    if not request.FILES.get('image_file'):
        return JsonResponse({'error': _('No image file provided.')}, status=400)

    image_file = request.FILES['image_file']
    
    # Basic validation for image type and size (optional but recommended)
    if not image_file.content_type.startswith('image/'):
        return JsonResponse({'error': _('Invalid file type. Please upload an image.')}, status=400)
    if image_file.size > 5 * 1024 * 1024: # Max 5MB
        return JsonResponse({'error': _('Image file too large (max 5MB).')}, status=400)

    image_bytes = image_file.read()

    # --- Prepare a simplified catalog for the AI prompt ---
    # This is a crucial part and needs careful consideration for performance and prompt length.
    # For a real system, you'd likely use embeddings or a more sophisticated search.
    # Here, we'll just take a small, random sample of active products.
    
    # Fetch a sample of product names and brief descriptions for the AI prompt
    # This needs to be carefully managed to avoid overly long prompts.
    sample_products = Product.objects.filter(is_active=True, vendor__is_approved=True).order_by('?')[:50] # Sample 50 products
    
    catalog_excerpt_parts = []
    for p in sample_products:
        desc_snippet = (p.description[:75] + '...') if len(p.description) > 75 else p.description
        catalog_excerpt_parts.append(f"- Name: \"{p.name}\", Category: \"{p.category.name if p.category else 'N/A'}\", Description: \"{desc_snippet}\"")
    
    catalog_excerpt_str = "\n".join(catalog_excerpt_parts)

    if not catalog_excerpt_str:
        catalog_excerpt_str = "No catalog items available for comparison at the moment."

    # --- Construct the prompt for Gemini Vision ---
    prompt_text = f"""You are an expert visual product identification and recommendation assistant for NEXUS marketplace.
Task:
1. Analyze the uploaded image and identify the main product(s) visible.
2. Based on the identified product(s), search the 'Available Catalog Products' list below and suggest up to 3 distinct products from that list that are most similar or relevant.

Output Instructions:
Return ONLY the names of the 3 (or fewer, if not enough matches) most similar products from the 'Available Catalog Products' list.
Each product name must be on a new, separate line.
Do NOT include any other text, numbering, bullet points, explanations, or the identified product from the image in your response. Only list names from the provided catalog.

Available Catalog Products:
{catalog_excerpt_str}

Recommended product names from the catalog (up to 3, each on a new line):
"""

    logger.info(f"Visual Search - Prompt for AI (catalog excerpt length: {len(catalog_excerpt_str)} chars)")
    # logger.debug(f"Visual Search - Full Prompt: {prompt_text}") # Be careful logging full catalog

    ai_response_text = generate_response_from_image_and_text(image_bytes, prompt_text)

    if ai_response_text and not ai_response_text.startswith("Error:"):
        suggested_product_names = [name.strip() for name in ai_response_text.split('\n') if name.strip()]
        logger.info(f"Visual Search - AI suggested product names: {suggested_product_names}")

        found_products_data = []
        if suggested_product_names:
            # Fetch actual product objects from DB based on names
            # Using __in query and ensuring distinct results
            # This relies on names being unique enough or the AI picking exact names from the list.
            # A more robust method would be to pass IDs to the AI and get IDs back.
            matched_products = Product.objects.filter(
                name__in=suggested_product_names, 
                is_active=True, 
                vendor__is_approved=True
            ).distinct()[:3] # Limit to 3 results

            for prod in matched_products:
                first_image = prod.images.first()
                found_products_data.append({
                    'id': prod.id,
                    'name': prod.name,
                    'slug': prod.slug,
                    'price': str(prod.price),
                    'category': prod.category.name if prod.category else None,
                    'vendor': prod.vendor.name if prod.vendor else None,
                    'image_url': first_image.image.url if first_image and first_image.image else settings.STATIC_URL + 'assets/img/placeholder.png',
                    'absolute_url': request.build_absolute_uri(prod.get_absolute_url())
                })
        
        return JsonResponse({'suggested_products': found_products_data})
    else:
        logger.error(f"Visual Search - Gemini error: {ai_response_text}")
        return JsonResponse({'error': _('Could not process image search with AI. Please try again.') + f" (Details: {ai_response_text})"}, status=500)



class VendorNotificationListView(LoginRequiredMixin, IsVendorMixin, ListView):
    model = Notification
    template_name = 'core/vendor_notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 15 # Show 15 notifications per page

    def get_queryset(self):
        # Get notifications for the current logged-in user (who is a vendor)
        # and order them by newest first
        queryset = Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
        # Mark notifications as read when the vendor views this page
        # Notification.objects.filter(recipient=self.request.user, is_read=False).update(is_read=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Your Notifications")
        # Mark notifications as read when the vendor views this page - doing it here ensures it happens after queryset is evaluated
        Notification.objects.filter(recipient=self.request.user, is_read=False).update(is_read=True)
        return context
    
    
class VendorPayoutRequestCreateView(LoginRequiredMixin, IsVendorMixin, CreateView):
    model = PayoutRequest
    form_class = VendorPayoutRequestForm # We'll need to create this form
    template_name = 'core/vendor/vendor_payout_request_form.html' # And this template
    success_url = reverse_lazy('core:vendor_payout_requests') # Redirect to the list after successful creation

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['vendor_profile'] = self.request.user.vendor_profile
        return kwargs

    def form_valid(self, form):
        form.instance.vendor_profile = self.request.user.vendor_profile
        # You might want to set other default fields here if needed
        # e.g., form.instance.status = PayoutRequest.PENDING
        messages.success(self.request, _("Your payout request has been submitted successfully."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor'] = self.request.user.vendor_profile
        context['page_title'] = _("Request New Payout")
        return context


def menu(request):
    context = {
        'page_title': _("Menu"),
    }
    return render(request, 'core/menu.html', context)

class CategoryDetailView(DetailView):
    model = Category
    template_name = 'core/category_detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'category_slug'

    def get_queryset(self):
        return Category.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        context['products'] = Product.objects.filter(category=category, is_active=True, vendor__is_approved=True).order_by('-created_at')[:12]
        context['page_title'] = category.name
        return context

category_detail = CategoryDetailView.as_view()
product_detail = ProductDetailView.as_view()

def search_results(request):
    query = request.GET.get('q', '')
    products = Product.objects.none()
    services = Service.objects.none()

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(vendor__name__icontains=query),
            is_active=True, vendor__is_approved=True
        ).distinct().prefetch_related('images', 'category', 'vendor')

    context = {
        'query': query,
        'products': products,
        'services': services,
        'page_title': _("Search Results for '{query}'").format(query=query) if query else _("Search"),
    }
    return render(request, 'core/search_results.html', context)

def daily_offers(request):
    offer_products = Product.objects.filter(is_active=True, is_featured=True, promotions__isnull=False).distinct()[:12]
    context = {
        'offer_products': offer_products,
        'page_title': _("Today's Special Offers"),
    }
    return render(request, 'core/daily_offers.html', context)


def sell_on_nexus(request):
    context = {
        'page_title': _("Sell on NEXUS"),
    }
    return render(request, 'core/sell_on_nexus.html', context)

@login_required
@require_POST
def update_location(request):
    logger.info("Placeholder: update_location view called.")
    return JsonResponse({'status': 'info', 'message': 'Location update endpoint (placeholder).'})

@require_POST
def update_language(request):
    logger.info("Placeholder: update_language view called.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

class ServiceCategoryDetailView(DetailView):
    model = ServiceCategory
    template_name = 'core/service_category_detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'category_slug'

    def get_queryset(self):
        return ServiceCategory.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        context['services'] = Service.objects.filter(category=category, is_active=True, provider__service_provider_profile__is_approved=True).order_by('-created_at')[:12]
        context['page_title'] = category.name
        return context

service_category_detail = ServiceCategoryDetailView.as_view()


# --- START: Rider Views ---
class BecomeRiderView(LoginRequiredMixin, FormView):
    template_name = 'core/become_rider_form.html' # We'll create this template
    form_class = RiderProfileApplicationForm
    success_url = reverse_lazy('core:home') # Redirect to home or a "pending approval" page

    def dispatch(self, request, *args, **kwargs):
        # Check if user already has an approved profile or a pending application
        if hasattr(request.user, 'rider_profile') and request.user.rider_profile and request.user.rider_profile.is_approved:
            messages.info(request, _("You are already an approved rider."))
            return redirect('core:rider_dashboard')
        if hasattr(request.user, 'rider_application') and request.user.rider_application:
            messages.info(request, _("You have already submitted a rider application. Please check your dashboard for status updates."))
            return redirect('core:rider_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        application = form.save(commit=False) # form is RiderProfileApplicationForm, model is RiderApplication
        application.user = self.request.user
        # Pre-fill phone number if available from UserProfile and not provided in form
        if not application.phone_number and hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.phone_number:
            application.phone_number = self.request.user.userprofile.phone_number
        application.save()
        messages.success(self.request, _("Your rider application has been submitted! Our team will review it shortly."))
        # TODO: Send notification to admin
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Become a NEXUS Rider")
        return context

class RiderDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/rider_dashboard.html' # We'll create this

    def dispatch(self, request, *args, **kwargs):
        # Check if the user has an approved rider profile OR a pending application
        has_approved_profile = hasattr(request.user, 'rider_profile') and request.user.rider_profile and request.user.rider_profile.is_approved
        has_application = hasattr(request.user, 'rider_application') and request.user.rider_application

        if not has_approved_profile and not has_application:
            messages.info(request, _("You haven't applied to be a rider yet."))
            return redirect('core:become_rider') # Redirect to application page
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rider_profile = getattr(self.request.user, 'rider_profile', None) # Use getattr to avoid error if no profile
        rider_application = getattr(self.request.user, 'rider_application', None)
        context['rider_profile'] = rider_profile
        context['rider_application'] = rider_application

        if rider_profile and rider_profile.is_approved: # Check if rider_profile exists and is approved
            context['page_title'] = _("Rider Dashboard")
            # TODO: Add data for approved riders (e.g., assigned deliveries, earnings)
            context['status_message'] = _("Welcome to your Rider Dashboard!")
            
              # Fetch tasks assigned to this rider
            my_accepted_tasks = DeliveryTask.objects.filter(
                rider=rider_profile, 
                status__in=['ACCEPTED_BY_RIDER', 'PICKED_UP', 'OUT_FOR_DELIVERY'] # Add other active statuses as needed
            ).order_by('created_at')
            context['my_accepted_tasks'] = my_accepted_tasks

            
            
            # Fetch available delivery tasks if rider is available
            if rider_profile.is_available:
                available_tasks = DeliveryTask.objects.filter(status='PENDING_ASSIGNMENT').order_by('created_at')
                context['available_tasks'] = available_tasks
            else:
                context['available_tasks'] = [] # Empty list if not available
        else:
            # No approved profile, check application status
            context['page_title'] = _("Rider Application Status")
            if rider_application:
                if not rider_application.is_reviewed:
                    context['status_message'] = _("Your rider application has been submitted and is pending review. We'll notify you once a decision has been made.")
                elif rider_application.is_reviewed and not rider_application.is_approved: # Reviewed but not approved (i.e., rejected or needs more info)
                    context['status_message'] = _("Your rider application has been reviewed. Please check your notifications or contact support for more details.") # Generic message for now
            else: # Should not happen if dispatch logic is correct, but as a fallback
                context['status_message'] = _("There seems to be an issue with your rider application status. Please contact support.")
        return context

@login_required
@require_POST # Ensures this view can only be accessed via a POST request
def toggle_rider_availability(request):
    try:
        rider_profile = request.user.rider_profile
        if not rider_profile.is_approved:
            messages.error(request, _("Your rider profile is not yet approved."))
            return redirect('core:rider_dashboard')

        rider_profile.is_available = not rider_profile.is_available
        rider_profile.save(update_fields=['is_available'])

        if rider_profile.is_available:
            messages.success(request, _("You are now ONLINE and available for deliveries."))
        else:
            messages.success(request, _("You are now OFFLINE and will not receive new delivery assignments."))

    except RiderProfile.DoesNotExist:
        messages.error(request, _("Rider profile not found."))
    
    return redirect('core:rider_dashboard')

@login_required
@require_POST # Good practice for actions that change data
def accept_delivery_task(request, task_id):
    try:
        rider_profile = request.user.rider_profile
        if not rider_profile.is_approved or not rider_profile.is_available:
            messages.error(request, _("You must be an approved and available rider to accept tasks."))
            return redirect('core:rider_dashboard')

        # Use a transaction to prevent race conditions if multiple riders try to accept
        with transaction.atomic():
            task = DeliveryTask.objects.select_for_update().get(task_id=task_id, status='PENDING_ASSIGNMENT')
            
            task.rider = rider_profile
            task.status = 'ACCEPTED_BY_RIDER' # Or 'ASSIGNED'
            task.save(update_fields=['rider', 'status'])

            messages.success(request, _("Task for Order {order_id} accepted successfully!").format(order_id=task.order.order_id))
            # TODO: Notify vendor/customer if needed

    except RiderProfile.DoesNotExist:
        messages.error(request, _("Rider profile not found."))
    except DeliveryTask.DoesNotExist:
        messages.warning(request, _("This task is no longer available or has already been assigned."))
    
    return redirect('core:rider_dashboard')

class RiderTaskDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = DeliveryTask
    template_name = 'core/rider_task_detail.html' # We'll create this template
    context_object_name = 'task'
    pk_url_kwarg = 'task_id' # To match the UUID in the URL

    def get_object(self, queryset=None):
        # Fetch the task using the UUID from the URL
        return get_object_or_404(DeliveryTask, task_id=self.kwargs.get(self.pk_url_kwarg))

    def test_func(self):
        task = self.get_object()
        # Check if the logged-in user has a rider profile and is the assigned rider for this task
        return hasattr(self.request.user, 'rider_profile') and task.rider == self.request.user.rider_profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.get_object()
        context['page_title'] = _("Delivery Task Details - Order {order_id}").format(order_id=task.order.order_id)
        # Pass coordinates and API key for the map
        task = self.object
        if task.pickup_latitude and task.pickup_longitude and task.delivery_latitude and task.delivery_longitude:
            context['show_map'] = True
            context['pickup_lat'] = float(task.pickup_latitude)
            context['pickup_lng'] = float(task.pickup_longitude)
            context['delivery_lat'] = float(task.delivery_latitude)
            context['delivery_lng'] = float(task.delivery_longitude)
        context['google_maps_api_key'] = settings.GOOGLE_MAPS_API_KEY
        # You can add more context here if needed, e.g., related vendor details if not directly on task
        return context

@login_required
@require_POST
def update_task_status_picked_up(request, task_id):
    try:
        task = get_object_or_404(DeliveryTask, task_id=task_id)
        rider_profile = request.user.rider_profile

        if task.rider != rider_profile:
            messages.error(request, _("You are not assigned to this task."))
            return redirect('core:rider_dashboard')

        if task.status == 'ACCEPTED_BY_RIDER':
            task.status = 'PICKED_UP'
            task.actual_pickup_time = timezone.now()
            task.save(update_fields=['status', 'actual_pickup_time'])
            messages.success(request, _("Task for Order {order_id} marked as PICKED UP.").format(order_id=task.order.order_id))
            # TODO: Notify customer/vendor that item has been picked up
        else:
            messages.warning(request, _("Task cannot be marked as picked up from its current status: {status}.").format(status=task.get_status_display()))

    except RiderProfile.DoesNotExist:
        messages.error(request, _("Rider profile not found."))
        return redirect('core:home') # Or appropriate error page
    
    return redirect('core:rider_task_detail', task_id=task.task_id)

@login_required
@require_POST
def update_task_status_delivered(request, task_id):
    try:
        task = get_object_or_404(DeliveryTask, task_id=task_id)
        rider_profile = request.user.rider_profile

        if task.rider != rider_profile:
            messages.error(request, _("You are not assigned to this task."))
            return redirect('core:rider_dashboard')

        # Rider can mark as delivered if it's picked up or already out for delivery
        if task.status in ['PICKED_UP', 'OUT_FOR_DELIVERY']:
            task.status = 'DELIVERED'
            task.actual_delivery_time = timezone.now()
            task.save(update_fields=['status', 'actual_delivery_time'])
            messages.success(request, _("Task for Order {order_id} marked as DELIVERED.").format(order_id=task.order.order_id))
            # TODO: Notify customer/vendor that item has been delivered
            # TODO: Potentially trigger order status update to 'COMPLETED' or 'PENDING_PAYOUT' if all items delivered
        else:
            messages.warning(request, _("Task cannot be marked as delivered from its current status: {status}.").format(status=task.get_status_display()))

    except RiderProfile.DoesNotExist:
        messages.error(request, _("Rider profile not found."))
        return redirect('core:home')
    return redirect('core:rider_task_detail', task_id=task.task_id)

# --- START: Rider Dashboard Section Views ---

class RiderAccessMixin(UserPassesTestMixin):
    """
    Ensures the user is authenticated and has an approved rider profile.
    """
    def test_func(self):
        # This mixin is designed for pages *requiring* an approved profile.
        # For the Verification page, we'll handle access in its dispatch method.
        # Keep this mixin for other pages like Earnings, Boost, etc.
        if not self.request.user.is_authenticated: return False # Should be handled by LoginRequiredMixin first
        try:
            return self.request.user.rider_profile and self.request.user.rider_profile.is_approved
        # If RiderProfile doesn't exist or isn't approved, test_func fails, and handle_no_permission is called.
        except RiderProfile.DoesNotExist:
            return False

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(reverse('authapp:signin') + f'?next={self.request.path}')
        
        # Check if they have an application first, even if not an approved profile
        try:
            # If they have an application but no approved profile, redirect to dashboard status page
            if hasattr(self.request.user, 'rider_application') and self.request.user.rider_application and \
               not (hasattr(self.request.user, 'rider_profile') and self.request.user.rider_profile and self.request.user.rider_profile.is_approved):
                messages.info(self.request, _("Your rider application is still pending. You cannot access this page yet."))
                return redirect('core:rider_dashboard')
            # If no application and no profile, or profile exists but not approved (though test_func should catch this)
            if not (hasattr(self.request.user, 'rider_profile') and self.request.user.rider_profile):
                messages.info(self.request, _("You need to apply to be a rider first."))
                return redirect('core:become_rider')
        except (RiderProfile.DoesNotExist, RiderApplication.DoesNotExist): # Catch both potential exceptions
            messages.info(self.request, _("Rider profile or application not found. Please apply or contact support."))
            return redirect('core:become_rider') # Fallback to application page
        return super().handle_no_permission()

class RiderEarningsReportsView(LoginRequiredMixin, RiderAccessMixin, TemplateView):
    template_name = 'core/rider/rider_earnings_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rider_profile = self.request.user.rider_profile

        completed_tasks_qs = DeliveryTask.objects.filter(
            rider=rider_profile,
            status='DELIVERED',
            rider_earning__isnull=False
        )

        # Total earnings
        total_earned_agg = completed_tasks_qs.aggregate(total_earnings=Sum('rider_earning'))
        context['total_earned'] = total_earned_agg['total_earnings'] or Decimal('0.00')

        # Total completed deliveries
        context['total_completed_deliveries'] = completed_tasks_qs.count()

        # Average earning per delivery
        if context['total_completed_deliveries'] > 0:
            context['average_earning_per_delivery'] = context['total_earned'] / context['total_completed_deliveries']
        else:
            context['average_earning_per_delivery'] = Decimal('0.00')

        # TODO: Add more advanced reporting, e.g., earnings by month, charts, etc.
        # For example, earnings this month:
        # current_month_earnings = completed_tasks_qs.filter(actual_delivery_time__month=timezone.now().month, actual_delivery_time__year=timezone.now().year).aggregate(Sum('rider_earning'))
        # context['current_month_earnings'] = current_month_earnings['rider_earning__sum'] or Decimal('0.00')

        context['page_title'] = _("Earnings & Reports Overview")
        return context
 # --- END: RiderAccessMixin (Moved Up) ---
       
        
    
class RiderProfileView(LoginRequiredMixin, RiderAccessMixin, TemplateView):
    template_name = 'core/rider/rider_profile_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # RiderAccessMixin ensures rider_profile exists and is approved
        # We can safely access it here.
        rider_profile = self.request.user.rider_profile
        context['rider_profile'] = rider_profile
        context['page_title'] = _("My Rider Profile")
        return context
    

class RiderProfileEditView(LoginRequiredMixin, RiderAccessMixin, View): # Changed from TemplateView to View
    template_name = 'core/rider/rider_profile_edit.html' # Placeholder template
    form_class = RiderProfileUpdateForm

    def get_object(self):
        # Helper to get the RiderProfile instance
        # RiderAccessMixin should ensure rider_profile exists and is approved
        return self.request.user.rider_profile

    def get(self, request, *args, **kwargs):
        rider_profile = self.get_object()
        form = self.form_class(instance=rider_profile, user=request.user)
        context = {
            'form': form,
            'page_title': _("Edit My Profile"),
            'rider_profile': rider_profile
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        rider_profile = self.get_object()
        form = self.form_class(request.POST, request.FILES, instance=rider_profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Your profile has been updated successfully!"))
            return redirect('core:rider_profile_edit') # Redirect back to the same page
        else:
            messages.error(request, _("Please correct the errors below."))
        
        context = { 'form': form, 'page_title': _("Edit My Profile"), 'rider_profile': rider_profile }
        return render(request, self.template_name, context)

class RiderVerificationView(LoginRequiredMixin, RiderAccessMixin, TemplateView):
    template_name = 'core/rider/rider_verification.html'

    # Override dispatch to allow access if user has an application OR an approved profile
    # and to bypass RiderAccessMixin's test_func for this specific view.
    def dispatch(self, request, *args, **kwargs):
        # Debugging prints (can be removed after fixing)
        # print(f"--- RiderVerificationView.dispatch DEBUG ---")
        # print(f"self: {self}, type(self): {type(self)}")
        # print(f"RiderAccessMixin in scope: {RiderAccessMixin}")
        # print(f"AccessMixin in scope: {AccessMixin}") # Check if AccessMixin is available
        # print(f"Is self an instance of RiderAccessMixin? {isinstance(self, RiderAccessMixin)}")
        # print(f"MRO: {type(self).__mro__}")
        # print(f"--- End RiderVerificationView.dispatch DEBUG ---")

        # LoginRequiredMixin already ensures user is authenticated
        has_approved_profile = hasattr(request.user, 'rider_profile') and request.user.rider_profile and request.user.rider_profile.is_approved
        has_application = hasattr(request.user, 'rider_application') and request.user.rider_application
        if not has_approved_profile and not has_application:
            messages.info(request, _("You haven't applied to be a rider yet, or your application was not found."))
            return redirect('core:become_rider') # Redirect to application page

        # If they have an application or an approved profile, allow access to this view.
        # We call super(RiderAccessMixin, self).dispatch to bypass RiderAccessMixin's own dispatch
        # (which calls its test_func that requires a strictly approved profile).
        return TemplateView.dispatch(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Rider Verification")

        rider_profile = getattr(self.request.user, 'rider_profile', None)
        rider_application = getattr(self.request.user, 'rider_application', None)
        
        context['rider_profile'] = rider_profile # Pass profile to template
        context['rider_application'] = rider_application # Pass application to template for displaying details
        
        if rider_profile and rider_profile.is_approved:
            context['verification_status'] = 'approved'
            context['verification_status_message'] = _("Your rider profile is fully verified and active. You can update your documents if needed via your profile edit page.")
        elif rider_application:
            if not rider_application.is_reviewed:
                 context['verification_status'] = 'pending_review'
                 context['verification_status_message'] = _("Your rider application has been submitted and is pending review.")
            elif rider_application.is_reviewed and not rider_application.is_approved: # is_approved on RiderApplication
                context['verification_status'] = 'reviewed_not_approved'
                context['verification_status_message'] = _("Your application has been reviewed but not approved. Please check for any communications or contact support if you have questions.")
            # Add other rider_application states if necessary (e.g., if it can be 'approved' itself before profile reflects it)
        else:
            # This state should ideally be prevented by the dispatch method redirecting.
            context['verification_status'] = 'no_info'
            context['verification_status_message'] = _("No verification information found. Please ensure you have completed your rider application.")
        return context

class RiderBoostVisibilityView(LoginRequiredMixin, RiderAccessMixin, TemplateView):
    template_name = 'core/rider/rider_boost_visibility.html' # Placeholder template

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Boost Visibility")
        context['boost_packages'] = BoostPackage.objects.filter(is_active=True).order_by('display_order', 'price')
        return context
    
      # Get current rider's active boosts
        try:
            rider_profile = self.request.user.rider_profile
            context['active_rider_boosts'] = ActiveRiderBoost.objects.filter(
                rider_profile=rider_profile, is_active=True, expires_at__gt=timezone.now()
            ).select_related('boost_package').order_by('expires_at')
        except RiderProfile.DoesNotExist:
            context['active_rider_boosts'] = None
        return context

class ActivateRiderBoostView(LoginRequiredMixin, RiderAccessMixin, View):
    def post(self, request, *args, **kwargs):
        print("--- DEBUG: ActivateRiderBoostView POST method CALLED ---") # Add this line
        package_id = None # Initialize to see if it gets set
        package_id = request.POST.get('package_id')
        try:
            print(f"--- DEBUG: Inside TRY block. Request POST data: {request.POST}")
            package_id = request.POST.get('package_id')
            print(f"--- DEBUG: package_id from POST: {package_id}")

            if not package_id:
                print("--- DEBUG: package_id is None or empty. Aborting early.")
                messages.error(request, _("No boost package selected."))
                return redirect('core:rider_boost_visibility')

            boost_package = get_object_or_404(BoostPackage, id=package_id, is_active=True)
            print(f"--- DEBUG: Fetched Boost Package: {boost_package.name} (ID: {boost_package.id})")
            print(f"--- DEBUG: Package Price from DB: {boost_package.price} (Type: {type(boost_package.price)})")
            print(f"--- DEBUG: Package Duration from DB: {boost_package.duration_hours} hours")

            rider_profile = request.user.rider_profile # RiderAccessMixin ensures this exists and is approved
            print(f"--- DEBUG: Rider Profile: {rider_profile.user.username}")

            # --- START LOGGING (from previous attempts, now as print) ---
            logger.info(f"--- Boost Activation Attempt (logger.info) ---") # Keep one logger.info to test if it appears now
            logger.info(f"Package ID from POST: {package_id}")
            logger.info(f"Fetched Boost Package: {boost_package.name} (DB ID: {boost_package.id})")
            logger.info(f"Package Price from DB: {boost_package.price} (Type: {type(boost_package.price)})")
            logger.info(f"Package Duration from DB: {boost_package.duration_hours} hours")
            # --- END LOGGING ---

            if boost_package.price > 0:
                print(f"--- DEBUG: Price ({boost_package.price}) is > 0. Proceeding to Paystack.")
                logger.info(f"Price ({boost_package.price}) is > 0. Proceeding to Paystack. (logger.info)")
                # ... (Paystack initialization code from previous diff) ...
                url = "https://api.paystack.co/transaction/initialize"
                amount_in_kobo = int(boost_package.price * 100)
                boost_activation_ref = f"NEXUS_BST_{rider_profile.id}_{boost_package.id}_{uuid.uuid4().hex[:6]}"
                headers = {
                    "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "email": request.user.email,
                    "amount": amount_in_kobo,
                    "currency": "GHS",
                    "reference": boost_activation_ref,
                    "callback_url": request.build_absolute_uri(reverse('core:paystack_boost_callback')),
                    "metadata": {
                        "rider_profile_id": str(rider_profile.id),
                        "boost_package_id": str(boost_package.id),
                        "custom_fields": [
                            {"display_name": "Service", "variable_name": "service_name", "value": f"Boost: {boost_package.name}"}
                        ]
                    }
                }
                try:
                    print("--- DEBUG: Attempting Paystack API call ---")
                    response = requests.post(url, headers=headers, json=payload)
                    print(f"--- DEBUG: Paystack API response status: {response.status_code} ---")
                    print(f"--- DEBUG: Paystack API response content: {response.text[:500]} ---") # Log first 500 chars
                    response.raise_for_status()
                    response_data = response.json()
                    if response_data.get("status"):
                        request.session['pending_boost_activation_ref'] = boost_activation_ref
                        request.session['pending_boost_package_id'] = boost_package.id
                        authorization_url = response_data["data"]["authorization_url"]
                        print(f"--- DEBUG: Redirecting to Paystack: {authorization_url} ---")
                        logger.info(f"Redirecting to Paystack: {authorization_url} (logger.info)")
                        return redirect(authorization_url)
                    else:
                        error_msg = response_data.get("message", "Unknown Paystack error")
                        print(f"--- DEBUG: Paystack initialization failed: {error_msg} ---")
                        logger.error(f"Paystack initialization failed: {error_msg} (logger.error)")
                        messages.error(request, _("Could not initialize payment with Paystack: {error}").format(error=error_msg))
                except requests.exceptions.RequestException as e:
                    print(f"--- DEBUG: Paystack API request failed: {e} ---")
                    logger.error(f"Paystack API request failed for boost payment: {e} (logger.error)")
                    messages.error(request, _("Could not connect to payment gateway. Please try again later."))
                return redirect('core:rider_boost_visibility')

            else: # This is the block being hit if price is not > 0
                print(f"--- DEBUG: Price ({boost_package.price}) is NOT > 0. Activating as free boost.")
                logger.info(f"Price ({boost_package.price}) is NOT > 0. Activating as free boost. (logger.info)")
                expires_at_time = timezone.now() + boost_package.duration_timedelta
                ActiveRiderBoost.objects.create(
                    rider_profile=rider_profile,
                    boost_package=boost_package,
                    expires_at=expires_at_time
                )
                messages.success(request, _(f"The '{boost_package.name}' boost has been activated successfully! It will expire in {boost_package.duration_hours} hours."))
        
        except BoostPackage.DoesNotExist:
            print(f"--- DEBUG: BoostPackage with ID {package_id} does not exist or is not active. ---")
            logger.error(f"BoostPackage with ID {package_id} does not exist or is not active. (logger.error)")
            messages.error(request, _("Invalid boost package selected or it is no longer available."))
        except RiderProfile.DoesNotExist: # Should be caught by RiderAccessMixin, but good to have
            print(f"--- DEBUG: RiderProfile does not exist for user {request.user.username}. ---")
            logger.error(f"RiderProfile does not exist for user {request.user.username}. (logger.error)")
            messages.error(request, _("Rider profile not found."))
        except Exception as e:
            print(f"--- DEBUG: An unexpected error occurred: {e} ---")
            messages.error(request, _(f"An error occurred while activating the boost: {e}"))
            logger.error(f"Error activating boost for rider {request.user.username}, package_id {package_id}: {e}", exc_info=True)
        
        print("--- DEBUG: Reached end of POST method, redirecting to rider_boost_visibility ---")
        return redirect('core:rider_boost_visibility')

@csrf_exempt # Paystack might POST here, or redirect with GET. GET is more common for callbacks.
def paystack_boost_callback(request):
    paystack_reference = request.GET.get('reference') # Paystack usually sends reference in GET
    # session_reference = request.session.get('pending_boost_activation_ref') # Get our stored ref

    if not paystack_reference:
        messages.error(request, _("Payment reference not found in callback."))
        return redirect('core:rider_boost_visibility')

    # Verify the transaction with Paystack
    url = f"https://api.paystack.co/transaction/verify/{paystack_reference}"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("status") and response_data["data"]["status"] == "success":
            metadata = response_data["data"].get("metadata", {})
            rider_profile_id = metadata.get("rider_profile_id")
            boost_package_id = metadata.get("boost_package_id")
            
            # Clear session reference if used
            # if 'pending_boost_activation_ref' in request.session:
            #     del request.session['pending_boost_activation_ref']
            # if 'pending_boost_package_id' in request.session:
            #     del request.session['pending_boost_package_id']

            if not rider_profile_id or not boost_package_id:
                messages.error(request, _("Payment successful, but could not retrieve boost details. Please contact support."))
                logger.error(f"Paystack boost callback: Missing rider_profile_id or boost_package_id in metadata for ref {paystack_reference}. Metadata: {metadata}")
                return redirect('core:rider_boost_visibility')

            rider_profile = get_object_or_404(RiderProfile, id=rider_profile_id)
            boost_package = get_object_or_404(BoostPackage, id=boost_package_id)

            expires_at_time = timezone.now() + boost_package.duration_timedelta
            ActiveRiderBoost.objects.create(
                rider_profile=rider_profile,
                boost_package=boost_package,
                expires_at=expires_at_time
            )
            # Create a Transaction record for this boost payment
            Transaction.objects.create(
                user=rider_profile.user, # The user who made the payment
                transaction_type='boost_purchase',
                amount=boost_package.price, # The price of the boost
                currency="GHS", # Assuming GHS, or get from boost_package if it stores currency
                status='completed',
                gateway_transaction_id=paystack_reference, # Paystack's reference for this transaction
                description=f"Payment for '{boost_package.name}' boost by {rider_profile.user.username}."
            )
            logger.info(f"Transaction record created for boost purchase: {boost_package.name} by {rider_profile.user.username}, Ref: {paystack_reference}")
            messages.success(request, _(f"Payment successful! The '{boost_package.name}' boost has been activated."))
        else:
            messages.error(request, _("Payment verification failed or payment was not successful. Please try again or contact support."))
    except requests.exceptions.RequestException as e:
        logger.error(f"Paystack boost verification API request failed: {e}")
        messages.error(request, _("Could not verify payment status. If payment was made, please contact support."))
    
    return redirect('core:rider_boost_visibility')

class RiderNotificationListView(LoginRequiredMixin, RiderAccessMixin, ListView): # Using ListView for notifications
    model = Notification # Assuming you'll use the same Notification model
    template_name = 'core/rider/rider_notification_list.html' # Placeholder template
    context_object_name = 'notifications'
    paginate_by = 15

    def get_queryset(self):
        # Notifications for the current rider
        queryset = Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
        # Mark notifications as read when the rider views this page
        Notification.objects.filter(recipient=self.request.user, is_read=False).update(is_read=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("My Notifications")
        return context

# --- END: Rider Views ---


# --- START: Rider Earnings View ---
class RiderEarningsView(LoginRequiredMixin, RiderAccessMixin, ListView):
    model = DeliveryTask
    template_name = 'core/rider/rider_earnings.html'
    context_object_name = 'completed_tasks'
    paginate_by = 10 # Optional: if you want pagination for tasks

    def get_queryset(self):
        rider_profile = self.request.user.rider_profile
        return DeliveryTask.objects.filter(
            rider=rider_profile,
            status='DELIVERED',
            rider_earning__isnull=False
        ).select_related('order').order_by('-actual_delivery_time', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rider_profile = self.request.user.rider_profile

        # Calculate total earnings from delivered tasks
        total_earned_agg = DeliveryTask.objects.filter(
            rider=rider_profile,
            status='DELIVERED',
            rider_earning__isnull=False
        ).aggregate(total_earnings=Sum('rider_earning'))
        context['total_earned'] = total_earned_agg['total_earnings'] or Decimal('0.00')

        # Calculate total paid out (from 'payout' transactions for this rider)
        total_paid_out_agg = Transaction.objects.filter(
            user=self.request.user, # Assuming payout transactions are linked to the CustomUser
            transaction_type='payout',
            status='completed' # Only count completed payouts
        ).aggregate(total_payouts=Sum('amount'))
        context['total_paid_out'] = total_paid_out_agg['total_payouts'] or Decimal('0.00')

        context['current_balance'] = context['total_earned'] - context['total_paid_out']

        # Add PayoutRequestForm to context if balance is > 0 and no pending request
        if context['current_balance'] > 0 and not PayoutRequest.objects.filter(rider_profile=rider_profile, status='pending').exists():
            context['payout_form'] = RiderPayoutRequestForm(max_amount=context['current_balance'])
        else:
            context['payout_form'] = None

        # Fetch payout history (completed payout transactions for this rider)
        context['payout_history'] = Transaction.objects.filter(
            user=self.request.user,
            transaction_type='payout',
            status='completed'
        ).order_by('-created_at')

        context['page_title'] = _("My Earnings")
        return context
# --- END: Rider Earnings View ---

# --- START: Request Payout View ---
class RequestPayoutView(LoginRequiredMixin, RiderAccessMixin, View):
    def post(self, request, *args, **kwargs):
        rider_profile = request.user.rider_profile

        # Calculate current balance again to ensure accuracy
        total_earned_agg = DeliveryTask.objects.filter(
            rider=rider_profile, status='DELIVERED', rider_earning__isnull=False
        ).aggregate(total_earnings=Sum('rider_earning'))
        total_earned = total_earned_agg['total_earnings'] or Decimal('0.00')

        total_paid_out_agg = Transaction.objects.filter(
            user=request.user, transaction_type='payout', status='completed'
        ).aggregate(total_payouts=Sum('amount'))
        total_paid_out = total_paid_out_agg['total_payouts'] or Decimal('0.00')
        current_balance = total_earned - total_paid_out

        # Check if there's already a pending payout request
        if PayoutRequest.objects.filter(rider_profile=rider_profile, status='pending').exists():
            messages.warning(request, _("You already have a pending payout request. Please wait for it to be processed."))
            return redirect('core:rider_earnings')

        if current_balance <= 0:
            messages.error(request, _("You do not have a sufficient balance to request a payout."))
            return redirect('core:rider_earnings')

        form = RiderPayoutRequestForm(request.POST, max_amount=current_balance)
        if form.is_valid():
            amount_requested = form.cleaned_data['amount_requested']
            if amount_requested > current_balance: # Double check
                messages.error(request, _("Requested amount exceeds your available balance."))
            elif amount_requested < Decimal('1.00'): # Example minimum
                 messages.error(request, _("Minimum payout amount is GH₵1.00.")) # Adjust currency and amount
            else:
                PayoutRequest.objects.create(
                    rider_profile=rider_profile,
                    amount_requested=amount_requested
                )
                messages.success(request, _(f"Your payout request for GH₵{amount_requested:.2f} has been submitted successfully. It will be reviewed by our team."))
                # TODO: Notify admin about the new payout request
                return redirect('core:rider_earnings')
        else:
            # If form is invalid, usually means amount was > max_amount or < min_amount
            messages.error(request, _("Invalid amount requested. Please check the limits and try again."))
        return redirect('core:rider_earnings') # Redirect back to earnings page if form invalid or other issues
# --- END: Request Payout View ---

class BecomeRiderInfoView(TemplateView):
    template_name = "core/become_rider_info.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Why Ride with Nexus?" # Optional: if your base.html uses a page_title context variable
        return context

# --- START: RiderAccessMixin (Moved Up) ---
class RiderAccessMixin(UserPassesTestMixin):
    """
    Ensures the user is authenticated and has an approved rider profile.
    """
    def test_func(self):
        # This mixin is designed for pages *requiring* an approved profile.
        # For the Verification page, we'll handle access in its dispatch method.
        # Keep this mixin for other pages like Earnings, Boost, etc.
        if not self.request.user.is_authenticated: return False # Should be handled by LoginRequiredMixin first
        try:
            return self.request.user.rider_profile and self.request.user.rider_profile.is_approved
        # If RiderProfile doesn't exist or isn't approved, test_func fails, and handle_no_permission is called.
        except RiderProfile.DoesNotExist:
            return False

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(reverse('authapp:signin') + f'?next={self.request.path}')
        
        # Simplified logic: if not an approved rider, redirect to become_rider or rider_dashboard for status
        messages.info(self.request, _("You need an approved rider profile to access this page. Apply or check your application status."))
        return redirect('core:rider_dashboard') # Rider dashboard will show status or prompt to apply
# --- END: RiderAccessMixin (Moved Up) ---


# --- START: Customer Notification View ---
class CustomerNotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'core/customer/customer_notification_list.html' # New template path
    context_object_name = 'notifications'
    paginate_by = 15

    def get_queryset(self):
        # Notifications for the current customer (user)
        queryset = Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
        # Mark notifications as read when the customer views this page
        Notification.objects.filter(recipient=self.request.user, is_read=False).update(is_read=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("My Notifications")
        return context
# --- END: Customer Notification View ---
