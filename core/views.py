# c:\Users\Hp\Desktop\Nexus\core\views.py
import logging
import json, datetime
from kombu.exceptions import OperationalError # Import OperationalError to handle broker connection issues
import random # For selecting random spotlights
from decimal import Decimal
from django.core.mail import EmailMessage
from typing import Optional
from django.contrib.syndication.views import Feed
from django.template.defaultfilters import truncatewords
import stripe
import requests # For making HTTP requests to Paystack
import uuid # For generating unique references
import hmac, hashlib, base64 # For Facebook data deletion signature verification
from itertools import chain
from operator import attrgetter
from django.db.models.fields.files import FieldFile # Import FieldFile for type checking
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import update_session_auth_hash
from django.contrib.messages.views import SuccessMessageMixin
from django import forms
from django.contrib.sessions.models import Session # Added import
from django.core.files.storage import FileSystemStorage, DefaultStorage
from django.core.files.base import ContentFile # Added import
from django.core.files import File
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, HttpResponseRedirect, FileResponse, Http404
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa
from formtools.wizard.views import SessionWizardView
from django.views.decorators.http import require_POST, require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View, TemplateView, FormView
from django.db import transaction
from django.db.models import Q, Avg, Count, Sum, F, ExpressionWrapper, fields, Prefetch, Max, OuterRef, Subquery, Exists
from django.utils import timezone
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django_countries import countries
from channels.layers import get_channel_layer
from django.core.cache import cache # Import the cache
from asgiref.sync import async_to_sync
from django.core.paginator import Paginator
from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator # For checking 2FA methods with django-allauth
from io import BytesIO
from django.contrib.auth import get_user_model
from authapp.models import CustomUser # <<< Import CustomUser from authapp
import os
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.functions import TruncDay, TruncMonth
from .origin_verification_views import (
    ajax_validate_product_origin,
    ajax_get_origin_suggestions,
    ajax_check_authenticity_risk,
)
from .artisan_verification_views import (
    ajax_verify_artisan_product,
    ajax_validate_acquisition_info,
    ajax_get_acquisition_options,
    ajax_get_vendor_tier_requirements,
)
from .models import ( # Ensure UserProfile is imported
    Product, Category, Cart, CartItem, Order, OrderItem, Address,
    Wishlist, ProductReview, Vendor, VendorReview, Promotion, AdCampaign,
    Notification, UserProfile, Transaction, Escrow, Dispute, Message, Conversation, ProductImage, ProductVideo, SavedForLaterItem, # Added ProductImage, ProductVideo
    ShippingMethod, PaymentGateway, TaxRate, Currency, SiteSettings, BlogPost, BlogCategory,
    FAQ, SupportTicket, TicketResponse, UserActivity, AuditLog, APIKey, WebhookEvent,
    FeatureFlag, ABTest, UserSegment, EmailTemplate, SMSTemplate, PushNotificationTemplate, Reward,
    Affiliate, AffiliateClick, AffiliatePayout, LoyaltyProgram, LoyaltyTier, UserPoints,
    UserCoupon, GiftCard, UserGiftCard, PricingPlan,
    TermsAndConditions, PrivacyPolicy, # For chatbot knowledge base
    # CustomUser, # Assuming CustomUser is your user model - THIS LINE IS NOW COMMENTED OUT
    ProductVariant, # Added for product variants
    ServiceBooking, PayoutRequest,
    ServiceAvailability, # Added for service availability
    ServiceAddon, ServiceImage, ServiceVideo, # Added for service addons
    Product, Cart, CartItem, ServicePackage, Order, # Added for reorder view
    UserFeedback, # Added for general user feedback
    SystemNotification, # Added for system-wide notifications
    UserPreferences, # Added for user preferences
    SecurityLog, # Added for security-related logs
    OrderNote, # Added for order notes
    # ... any other models you have ...
    RiderProfile, DeliveryTask, RiderApplication, ActiveRiderBoost, # Import RiderProfile, DeliveryTask, RiderApplication, ActiveRiderBoost
    BoostPackage,
    Service, ServiceCategory, ServicePackage, ServiceReview, ServiceProviderProfile, PortfolioItem, ProductQuestion, ProductAnswer, Coupon,
    FraudReport, NewsletterSubscriber,
    AuthenticityReview, AuthenticityFeedback, # Phase 4: Authenticity models
)
from .forms import ( # Ensure RiderApplication is imported if needed by forms, but it's a model
    AddressForm, ProductReviewForm, VendorReviewForm,
    VendorRegistrationForm, VendorProfileUpdateForm, MessageForm, ServiceProviderProfileForm, # VendorVerificationForm, # Commented out
    ProductQuestionForm, ProductAnswerForm, ServiceBookingDetailsForm, ServiceAvailabilityForm,
    ServiceForm, ServicePackageFormSet, ServiceReviewForm, ServiceSearchForm, ServiceAvailabilityFormSet, ServiceProviderPayoutForm,
    PortfolioItemForm, VendorPayoutRequestForm, CouponApplyForm, # Added VendorPayoutRequestForm and CouponApplyForm
    VendorShippingForm, VendorPaymentForm, VendorAdditionalInfoForm, RiderPayoutRequestForm, # Added RiderPayoutRequestForm
    VerificationMethodSelectionForm, ServiceProviderPayoutRequestForm, # New multi-step forms, Added ServiceProviderPayoutRequestForm
    BusinessDetailsForm,             # New multi-step forms
    IndividualDetailsForm,           # New multi-step forms
    VerificationConfirmationForm,    # New multi-step forms,
    VendorProductForm, PromotionForm, AdCampaignForm, AuthenticityFeedbackForm,
    VendorProductTypeStepForm, VendorProductBasicInfoStepForm,
    VendorProductVerificationCategoryStepForm, VendorProductVerificationDetailsStepForm,
    VendorProductPricingStepForm, VendorProductFulfillmentStepForm, VendorProductMediaStepForm,
    # ... any other forms you have ...
    RiderProfileApplicationForm,RiderProfileUpdateForm, UserProfileForm, UserPreferencesForm,
)
from authapp.forms import UserProfileUpdateForm as AuthUserProfileUpdateForm

from .utils import (
    send_order_confirmation_email, generate_invoice_pdf,
    calculate_shipping_cost, process_payment_with_gateway, haversine
)
# from .tasks import process_order_task # Example for Celery tasks
from .signals import order_placed
from .ai_services_gemini import (
    generate_text_with_gemini,
    generate_response_from_image_and_text,
    enhance_image_with_gemini,
    get_chatbot_response,
    generate_structured_text_with_gemini,
    remove_image_background, # These will be used in tasks.py
)
from .filters import ProductFilter
from .fraud_detection import calculate_fraud_score


@login_required
@require_POST
def vendor_email_packing_slip(request, pk):
    """
    Generates a PDF packing slip and emails it to the vendor.
    """
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, _("You are not a registered vendor."))
        return redirect('core:vendor_dashboard')

    if not vendor.user.email:
        messages.error(request, _("Your profile does not have an email address to send the packing slip to."))
        return redirect('core:vendor_order_detail', pk=pk)

    order = get_object_or_404(Order, pk=pk)

    # Security check: ensure the order actually contains items from this vendor
    vendor_items = order.items.filter(product__vendor=vendor)
    if not vendor_items.exists():
        messages.error(request, _("You do not have permission to email a packing slip for this order."))
        return redirect('core:vendor_order_list')

    context = {
        'order': order,
        'vendor_items': vendor_items,
        'vendor': vendor,
    }

    # Render the HTML template to a string
    html = render_to_string('core/vendor/packing_slip.html', context)

    # Create a PDF in memory
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)

    if pisa_status.err:
        logger.error(f"PDF generation failed for emailing order {order.order_id} for vendor {vendor.name}. Error: {pisa_status.err}")
        messages.error(request, _("There was an error generating the PDF for the email. Please try again later."))
        return redirect('core:vendor_order_detail', pk=pk)

    pdf_buffer.seek(0)

    subject = _("Packing Slip for Your Order #{order_id}").format(order_id=order.order_id)
    body = _("Hello {vendor_name},\n\nPlease find the packing slip for order #{order_id} attached.\n\nThank you,\nThe GOWBUY Team").format(vendor_name=vendor.name, order_id=order.order_id)
    email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [vendor.user.email])
    email.attach(f'packing_slip_{order.order_id}.pdf', pdf_buffer.getvalue(), 'application/pdf')
    email.send(fail_silently=False)

    messages.success(request, _("The packing slip has been sent to {email}.").format(email=vendor.user.email))
    return redirect('core:vendor_order_detail', pk=pk)


# Initialize logger
logger = logging.getLogger(__name__)

# Initialize Stripe (if you're using it)
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)


from .tasks import process_image_enhancement, process_background_removal
# --- Helper Functions (Consider moving to utils.py if they grow) ---

def _get_ai_review_summary(product: Product, reviews: list) -> str | None:
    """
    Generates a concise summary for a product based on its reviews using an AI model.
    Returns the summary text or a fallback message if generation fails or is not possible.
    """
    if not reviews:
        return _("There are no reviews yet to summarize for this product.")

    # --- START: Caching Logic ---
    cache_key = f"ai_summary_prod_{product.id}"
    cached_summary = cache.get(cache_key)
    if cached_summary:
        logger.debug(f"AI Review Summary - Cache HIT for product {product.id}")
        return cached_summary
    logger.debug(f"AI Review Summary - Cache MISS for product {product.id}")
    # --- END: Caching Logic ---

    review_texts = []
    # Take up to 15 most recent approved reviews for the prompt
    for i, r in enumerate(reviews[:15]):
        review_text = f"{i+1}. Rating: {r.rating}/5. Review: {r.review}"
        if r.video:
            review_text += " (Includes video)"
        review_texts.append(review_text)

    reviews_str = "\n".join(review_texts)

    prompt_for_summary = f"""You are an e-commerce assistant for GOWBUY marketplace.
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
        final_summary = summary_text.strip()
        # --- START: Caching Logic ---
        cache.set(cache_key, final_summary, timeout=3600) # Cache for 1 hour
        # --- END: Caching Logic ---
        return final_summary
    else:
        logger.error(f"AI Review Summary - Gemini error for '{product.name}': {summary_text}")
        return _("Could not generate a review summary at this time.")

def _get_ai_recommendations(product: Product) -> list:
    """
    Generates a list of recommended product objects using an AI model.
    Returns a list of Product objects or an empty list on failure.
    """
    # --- START: Caching Logic ---
    cache_key = f"ai_recs_prod_{product.id}"
    cached_recs = cache.get(cache_key)
    if cached_recs is not None: # Check for None, as an empty list is a valid cached value
        logger.debug(f"AI Recs - Cache HIT for product {product.id}")
        return cached_recs
    # --- END: Caching Logic ---

    try:
        # 1. Fetch candidate products
        max_candidates_for_ai = 15
        candidate_products_list = list(
            Product.objects.filter(category=product.category, is_active=True)
            .exclude(id=product.id)
            .order_by('?')[:max_candidates_for_ai]
        )

        # Fallback logic if not enough candidates
        if len(candidate_products_list) < 5:
            current_ids = {p.id for p in candidate_products_list} | {product.id}
            fallback_candidates = list(
                Product.objects.filter(is_active=True, is_featured=True)
                .exclude(id__in=current_ids)
                .order_by('?')[:max_candidates_for_ai - len(candidate_products_list)]
            )
            candidate_products_list.extend(fallback_candidates)
            candidate_products_list = list(dict.fromkeys(candidate_products_list)) # Remove duplicates

        candidate_products = candidate_products_list[:max_candidates_for_ai]
        logger.debug(f"AI Recs - Product: {product.name}, Final candidate products count: {len(candidate_products)}")

        if not candidate_products:
            return []

        # 2. Construct the prompt
        candidate_list_str = "\n".join(
            [f"- {p.name} (Category: {p.category.name}, Price: {p.price})" for p in candidate_products]
        )
        prompt_for_ai = f"""You are an expert e-commerce recommendation engine for an online marketplace called GOWBUY.
A user is currently viewing the following product:
Product Name: "{product.name}"
Category: "{product.category.name}"
Description Snippet: "{product.description[:250]}..."

Your task is to select exactly 3 distinct products from the 'Available Products List' below that this user might also be interested in.
Return ONLY the names of the 3 recommended products, each on a new line. Do NOT include any other text.

Available Products List:
{candidate_list_str}
"""
        # 3. Call Gemini API and process response
        raw_recommendations_text = generate_text_with_gemini(prompt_for_ai)
        if raw_recommendations_text and not raw_recommendations_text.startswith("Error:"):
            recommended_names = [name.strip() for name in raw_recommendations_text.split('\n') if name.strip()]
            if recommended_names:
                recommended_products = list(Product.objects.filter(name__in=recommended_names, is_active=True).distinct()[:3])
                # --- START: Caching Logic ---
                cache.set(cache_key, recommended_products, timeout=86400) # Cache for 24 hours
                # --- END: Caching Logic ---
                return recommended_products
    except Exception as e:
        logger.error(f"Error generating AI recommendations for product {product.id}: {e}", exc_info=True)
    # --- START: Caching Logic ---
    cache.set(cache_key, [], timeout=600) # Cache failure (empty list) for 10 mins to prevent retries
    # --- END: Caching Logic ---
    return []

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

# --- A simple decorator for API key authentication ---
def api_key_required(view_func):
    """
    Decorator to require an API key for a view.
    Assumes the key is passed in the 'X-API-KEY' header.
    """
    @csrf_exempt # API clients won't have a CSRF token
    def _wrapped_view(request, *args, **kwargs):
        api_key_str = request.headers.get('X-API-KEY')
        if not api_key_str:
            return JsonResponse({'error': 'API key is missing.'}, status=401)
        
        try:
            api_key = APIKey.objects.get(key=api_key_str, is_active=True)
            request.user = api_key.user # Authenticate the user associated with the key
            
            # Update last_used timestamp
            api_key.last_used = timezone.now()
            api_key.save(update_fields=['last_used'])

        except APIKey.DoesNotExist:
            return JsonResponse({'error': 'Invalid or inactive API key.'}, status=401)
        
        if not hasattr(request.user, 'vendor_profile') or not request.user.vendor_profile:
             return JsonResponse({'error': 'User is not a vendor.'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
# --- Core Views ---

class IsVendorMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and \
               hasattr(self.request.user, 'vendor_profile') and \
               self.request.user.vendor_profile is not None

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(reverse('authapp:signin') + f'?next={self.request.path}') # Corrected redirect
        messages.info(self.request, _("You need to register as a vendor to access this page."))
        return redirect('core:sell_on_gowbuy') # Changed from vendor_registration to sell_on_gowbuy


class IsServiceProviderMixin(UserPassesTestMixin):
    """
    Mixin to check if the user is a service provider (approved or pending).
    """
    def test_func(self):
        return (
            self.request.user.is_authenticated and
            hasattr(self.request.user, 'service_provider_profile') and
            self.request.user.service_provider_profile is not None
        )

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(reverse('authapp:signin') + f'?next={self.request.path}')
        if not hasattr(self.request.user, 'service_provider_profile'):
            messages.info(self.request, _("You need to register as a service provider to access this page."))
            return redirect('core:become_service_provider')
        else:
            messages.warning(self.request, _("Your service provider profile is pending approval."))
            return redirect('core:user_profile')


class IsRiderMixin(UserPassesTestMixin):
    """
    Mixin to check if the user is an approved rider.
    """
    def test_func(self):
        return (
            self.request.user.is_authenticated and
            hasattr(self.request.user, 'rider_profile') and
            self.request.user.rider_profile is not None and
            self.request.user.rider_profile.is_approved
        )

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(reverse('authapp:signin') + f'?next={self.request.path}')
        if not hasattr(self.request.user, 'rider_profile'):
            messages.info(self.request, _("You need to apply to be a rider to access this page."))
            return redirect('core:become_rider_info_page')
        else:
            messages.warning(self.request, _("Your rider profile is pending approval."))
            return redirect('core:user_profile')


# --- Vendor Dashboard Views ---

class VendorDashboardView(LoginRequiredMixin, IsVendorMixin, TemplateView):
    template_name = 'core/vendor_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.request.user.vendor_profile

        # Sales and Order Stats
        completed_orders = Order.objects.filter(
            items__product__vendor=vendor,
            status__in=['COMPLETED', 'DELIVERED', 'PENDING_PAYOUT', 'SHIPPED']
        ).distinct()

        total_sales = completed_orders.aggregate(
            total=Sum(F('items__price') * F('items__quantity'), filter=Q(items__product__vendor=vendor))
        )['total'] or Decimal('0.00')

        total_orders_count = Order.objects.filter(items__product__vendor=vendor).distinct().count()

        # Product Stats
        total_products_count = Product.objects.filter(vendor=vendor).count()
        active_products_count = Product.objects.filter(vendor=vendor, is_active=True).count()
        low_stock_products = Product.objects.filter(vendor=vendor, stock__lte=5, stock__gt=0, is_active=True)
        products_without_origin = Product.objects.filter(vendor=vendor, origin_country__isnull=True)

        # Recent Orders
        recent_orders = Order.objects.filter(items__product__vendor=vendor).distinct().order_by('-created_at')[:5]

        # Onboarding status
        onboarding_steps = {
            'shop_info': vendor.is_shop_info_complete(),
            'business_info': vendor.get_business_info_status_display() == 'COMPLETED',
            'shipping_info': vendor.is_shipping_info_complete(),
            'payment_info': vendor.is_payment_info_complete(),
            'additional_info': vendor.is_additional_info_complete(),
        }
        onboarding_complete = all(onboarding_steps.values())

        context.update({
            'vendor': vendor,
            'total_sales': total_sales,
            'total_orders_count': total_orders_count,
            'total_products_count': total_products_count,
            'active_products_count': active_products_count,
            'low_stock_products': low_stock_products,
            'products_without_origin': products_without_origin,
            'recent_orders': recent_orders,
            'onboarding_steps': onboarding_steps,
            'onboarding_complete': onboarding_complete,
            'page_title': _("Vendor Dashboard"),
        })
        return context


# --- Multi-Step Vendor Verification ---
class MultiStepVendorVerificationView(LoginRequiredMixin, IsVendorMixin, SessionWizardView):
    file_storage = DefaultStorage()

    form_list = [
        ("method", VerificationMethodSelectionForm),
        ("individual", IndividualDetailsForm), # Swapped with business
        ("business", BusinessDetailsForm),   # Swapped with individual
        ("confirmation", VerificationConfirmationForm),
    ]

    def dispatch(self, request, *args, **kwargs):
        vendor = self.request.user.vendor_profile
        
        # Prevent access if verification is complete or pending
        if vendor.verification_status == Vendor.VERIFICATION_STATUS_VERIFIED:
            messages.info(request, _("Your account is already verified."))
            return redirect('core:vendor_dashboard')
        
        if vendor.verification_status == Vendor.VERIFICATION_STATUS_PENDING_REVIEW:
            messages.info(request, _("Your verification is currently under review."))
            return redirect('core:vendor_dashboard')

        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        if self.steps.current == 'confirmation':
            return ['core/vendor_verification_step_confirmation.html']
        return ['core/vendor_verification_wizard_step.html']

    def get_form_instance(self, step):
        # This method must return a model instance for ModelForms, not a form instance.
        if step in ['business', 'individual']:
            return self.request.user.vendor_profile
        return None

    def condition_business(self):
        cleaned_data = self.get_cleaned_data_for_step('method') or {}
        return cleaned_data.get('verification_method', '') == Vendor.VERIFICATION_METHOD_BUSINESS

    def condition_individual(self):
        cleaned_data = self.get_cleaned_data_for_step('method') or {}
        return cleaned_data.get('verification_method', '') == Vendor.VERIFICATION_METHOD_INDIVIDUAL

    def get_condition_dict(self):
        return {
            'business': self.condition_business,
            'individual': self.condition_individual,
        }

    def done(self, form_list, **kwargs):
        vendor = self.request.user.vendor_profile
        all_cleaned_data = self.get_all_cleaned_data()

        # Update the vendor instance from the collected data in one go.
        # This is more efficient and robust than multiple saves.
        vendor.verification_method = all_cleaned_data.get('verification_method')

        # Update fields from the conditional forms, using existing value as a fallback.
        vendor.business_registration_document = all_cleaned_data.get('business_registration_document', vendor.business_registration_document)
        vendor.tax_id_number = all_cleaned_data.get('tax_id_number', vendor.tax_id_number)
        vendor.national_id_type = all_cleaned_data.get('national_id_type', vendor.national_id_type)
        vendor.national_id_number = all_cleaned_data.get('national_id_number', vendor.national_id_number)
        vendor.national_id_document = all_cleaned_data.get('national_id_document', vendor.national_id_document)

        vendor.verification_status = Vendor.VERIFICATION_STATUS_PENDING_REVIEW
        vendor.save()

        messages.success(self.request, _("Your verification documents have been submitted for review."))
        return redirect('core:vendor_dashboard')

class EditVendorProfileView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, UpdateView):
    model = Vendor
    form_class = VendorProfileUpdateForm
    template_name = 'core/edit_vendor_profile.html'
    success_url = reverse_lazy('core:edit_vendor_profile')
    success_message = _("Your profile has been updated successfully.")

    def get_object(self, queryset=None):
        return self.request.user.vendor_profile


class EditVendorShippingView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, UpdateView):
    model = Vendor
    form_class = VendorShippingForm
    template_name = 'core/edit_vendor_shipping.html'
    success_url = reverse_lazy('core:vendor_shipping_settings')
    success_message = _("Your shipping settings have been updated successfully.")

    def get_object(self, queryset=None):
        return self.request.user.vendor_profile


class EditVendorPaymentView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, UpdateView):
    model = Vendor
    form_class = VendorPaymentForm
    template_name = 'core/edit_vendor_payment.html'
    success_url = reverse_lazy('core:vendor_payment_settings')
    success_message = _("Your payment settings have been updated successfully.")

    def get_object(self, queryset=None):
        return self.request.user.vendor_profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Payout Settings")
        context['active_page'] = 'vendor_payout_settings'
        return context



class EditVendorAdditionalInfoView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, UpdateView):
    model = Vendor
    form_class = VendorAdditionalInfoForm
    template_name = 'core/edit_vendor_additional_info.html'
    success_url = reverse_lazy('core:edit_vendor_additional_info')
    success_message = _("Your additional information has been updated successfully.")

    def get_object(self, queryset=None):
        return self.request.user.vendor_profile


class VendorOrderListView(LoginRequiredMixin, IsVendorMixin, ListView):
    model = Order
    template_name = 'core/vendor_order_list.html'
    context_object_name = 'orders'
    paginate_by = 15

    def get_queryset(self):
        vendor = self.request.user.vendor_profile
        return Order.objects.filter(items__product__vendor=vendor).distinct().order_by('-created_at')


class VendorOrderDetailView(LoginRequiredMixin, IsVendorMixin, DetailView):
    model = Order
    template_name = 'core/vendor_order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        vendor = self.request.user.vendor_profile
        return Order.objects.filter(items__product__vendor=vendor).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.request.user.vendor_profile
        order = self.get_object()
        context['vendor_items'] = order.items.filter(product__vendor=vendor)
        return context


@login_required
@require_POST
def vendor_mark_all_notifications_read(request):
    """
    Marks all unread notifications for the current user as read.
    """
    # Ensure the user is a vendor before proceeding
    if not hasattr(request.user, 'vendor_profile') or not request.user.vendor_profile:
        messages.error(request, _("You are not authorized to perform this action."))
        return redirect('core:home')

    updated_count = Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)

    if updated_count > 0:
        messages.success(request, _("{count} notification(s) marked as read.").format(count=updated_count))
    else:
        messages.info(request, _("You have no unread notifications."))

    return redirect('core:vendor_notification_list')


@login_required
@require_POST
def vendor_delete_notification(request, pk):
    """
    Deletes a single notification for the current user.
    """
    # Ensure the user is a vendor before proceeding
    if not hasattr(request.user, 'vendor_profile') or not request.user.vendor_profile:
        messages.error(request, _("You are not authorized to perform this action."))
        return redirect('core:home')

    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.delete()
    messages.success(request, _("Notification deleted."))
    return redirect('core:vendor_notification_list')


@login_required
@require_POST
def vendor_delete_all_notifications(request):
    """
    Deletes all notifications for the current user.
    """
    # Ensure the user is a vendor before proceeding
    if not hasattr(request.user, 'vendor_profile') or not request.user.vendor_profile:
        messages.error(request, _("You are not authorized to perform this action."))
        return redirect('core:home')

    deleted_count, _ = Notification.objects.filter(recipient=request.user).delete()

    if deleted_count > 0:
        messages.success(request, _("{count} notification(s) have been deleted.").format(count=deleted_count))
    else:
        messages.info(request, _("You had no notifications to delete."))

    return redirect('core:vendor_notification_list')


@login_required
@require_POST
def vendor_mark_order_shipped(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    vendor = request.user.vendor_profile

    # Security check
    if not order.items.filter(product__vendor=vendor).exists():
        messages.error(request, _("You do not have permission to modify this order."))
        return redirect('core:vendor_order_list')

    if order.status == 'PROCESSING':
        order.status = 'SHIPPED'
        
        # Capture tracking info from the form submission
        tracking_number = request.POST.get('tracking_number')
        tracking_url = request.POST.get('tracking_url')
        if tracking_number:
            order.tracking_number = tracking_number
        if tracking_url:
            order.tracking_url = tracking_url
            
        order.save(update_fields=['status', 'tracking_number', 'tracking_url'])
        messages.success(request, _("Order #{order_id} has been marked as shipped.").format(order_id=order.order_id))
    else:
        messages.warning(request, _("This order cannot be marked as shipped at its current status."))

    return redirect('core:vendor_order_detail', pk=order.pk)


class VendorReportsView(LoginRequiredMixin, IsVendorMixin, TemplateView):
    template_name = 'core/vendor_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.request.user.vendor_profile

        # Total revenue
        completed_orders = Order.objects.filter(
            items__product__vendor=vendor,
            status__in=['COMPLETED', 'DELIVERED', 'PENDING_PAYOUT', 'SHIPPED']
        ).distinct()
        total_revenue = completed_orders.aggregate(
            total=Sum(F('items__price') * F('items__quantity'), filter=Q(items__product__vendor=vendor))
        )['total'] or Decimal('0.00')

        # Total items sold
        total_items_sold = OrderItem.objects.filter(
            order__in=completed_orders, product__vendor=vendor
        ).aggregate(total=Sum('quantity'))['total'] or 0

        # Order status counts
        order_status_counts = Order.objects.filter(items__product__vendor=vendor).values('status').annotate(count=Count('id')).order_by('status')

        context['vendor'] = vendor
        context['total_revenue'] = total_revenue
        context['total_items_sold'] = total_items_sold
        context['total_orders_count'] = completed_orders.count()
        context['order_status_counts'] = order_status_counts
        context['low_stock_products'] = Product.objects.filter(vendor=vendor, stock__lte=5, stock__gt=0, is_active=True)
        context['page_title'] = _("Reports")
        return context

# --- Vendor Plan & Upgrade Views ---

class VendorUpgradeView(LoginRequiredMixin, IsVendorMixin, ListView):
    """
    Displays available pricing plans for vendors to upgrade their accounts.
    """
    model = PricingPlan
    template_name = 'core/vendor_upgrade.html' # Ensure this template exists
    context_object_name = 'plans'

    def get_queryset(self):
        """
        Returns only active vendor premium plans.
        """
        return PricingPlan.objects.filter(is_active=True, plan_type='vendor_premium').order_by('display_order', 'price')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Upgrade Your Vendor Account")
        return context


class VendorPromotionListView(LoginRequiredMixin, IsVendorMixin, ListView):
    model = Promotion
    template_name = 'core/vendor_promotion_list.html'
    context_object_name = 'promotions'
    paginate_by = 10

    def get_queryset(self):
        return Promotion.objects.filter(applicable_vendor=self.request.user.vendor_profile)


class VendorPromotionCreateView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, CreateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'core/vendor_promotion_form.html'
    success_url = reverse_lazy('core:vendor_promotion_list')
    success_message = _("Promotion created successfully.")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['vendor'] = self.request.user.vendor_profile
        return kwargs

    def form_valid(self, form):
        form.instance.applicable_vendor = self.request.user.vendor_profile
        return super().form_valid(form)


class VendorPromotionUpdateView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, UpdateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'core/vendor_promotion_form.html'
    success_url = reverse_lazy('core:vendor_promotion_list')
    success_message = _("Promotion updated successfully.")

    def get_queryset(self):
        return Promotion.objects.filter(applicable_vendor=self.request.user.vendor_profile)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['vendor'] = self.request.user.vendor_profile
        return kwargs


class VendorPromotionDeleteView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, DeleteView):
    model = Promotion
    template_name = 'core/vendor_promotion_confirm_delete.html'
    success_url = reverse_lazy('core:vendor_promotion_list')
    success_message = _("Promotion deleted successfully.")

    def get_queryset(self):
        return Promotion.objects.filter(applicable_vendor=self.request.user.vendor_profile)


class VendorCampaignListView(LoginRequiredMixin, IsVendorMixin, ListView):
    model = AdCampaign
    template_name = 'core/vendor_campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 10

    def get_queryset(self):
        queryset = AdCampaign.objects.filter(vendor=self.request.user.vendor_profile)

        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset.order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['vendor'] = self.request.user.vendor_profile
        return context

class VendorCampaignCreateView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, CreateView):
    model = AdCampaign
    form_class = AdCampaignForm
    template_name = 'core/vendor_campaign_form.html'
    success_url = reverse_lazy('core:vendor_campaign_list')
    success_message = _("Ad Campaign created successfully.")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['vendor'] = self.request.user.vendor_profile
        return kwargs

    def form_valid(self, form):
        form.instance.vendor = self.request.user.vendor_profile
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Create New Campaign")
        context['vendor'] = self.request.user.vendor_profile
        return context


class VendorCampaignUpdateView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, UpdateView):
    model = AdCampaign
    form_class = AdCampaignForm
    template_name = 'core/vendor_campaign_form.html'
    success_url = reverse_lazy('core:vendor_campaign_list')
    success_message = _("Ad Campaign updated successfully.")

    def get_queryset(self):
        return AdCampaign.objects.filter(vendor=self.request.user.vendor_profile)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['vendor'] = self.request.user.vendor_profile
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = _("Edit Campaign")
        context['vendor'] = self.request.user.vendor_profile
        return context


class VendorCampaignDeleteView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, DeleteView):
    model = AdCampaign
    template_name = 'core/vendor_campaign_confirm_delete.html'
    success_url = reverse_lazy('core:vendor_campaign_list')
    success_message = _("Ad Campaign deleted successfully.")

    def get_queryset(self):
        return AdCampaign.objects.filter(vendor=self.request.user.vendor_profile)


class VendorNotificationListView(LoginRequiredMixin, IsVendorMixin, ListView):
    model = Notification
    template_name = 'core/vendor_notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)

        # Filter by search query
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(message__icontains=search_query)

        # Filter by status (read/unread)
        status = self.request.GET.get('status')
        if status == 'unread':
            queryset = queryset.filter(is_read=False)
        elif status == 'read':
            queryset = queryset.filter(is_read=True)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Your Notifications")
        context['search_query'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        return context

class VendorProductListView(LoginRequiredMixin, IsVendorMixin, ListView):
    model = Product
    template_name = 'core/vendor_product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user.vendor_profile).order_by('-created_at')


class VendorProductCreateView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = VendorProductForm
    template_name = 'core/vendor_product_form.html'
    success_url = reverse_lazy('core:vendor_product_list')
    success_message = _("Product created successfully.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # For create forms with errors, show previously uploaded files if they exist
        context['is_update_form'] = False
        # Initialize empty lists - won't show on create form, but consistency
        context['existing_images'] = []
        context['existing_videos'] = []
        return context

    def form_valid(self, form):
        # Save the product instance but don't commit to the database yet
        form.instance.vendor = self.request.user.vendor_profile
        self.object = form.save() # This saves the product and returns the instance

        # Check if AI enhancement or background removal is requested
        enhance_image = form.cleaned_data.get('enhance_image')
        remove_background = form.cleaned_data.get('remove_background')

        # Handle multiple image uploads
        images = self.request.FILES.getlist('images')
        for image_file in images:
            product_image = ProductImage.objects.create(product=self.object, image=image_file, alt_text=f"Image for {self.object.name}")
            try:
                if enhance_image:
                    process_image_enhancement.delay(product_image.id)
                if remove_background:
                    process_background_removal.delay(product_image.id)
            except OperationalError as e:
                logger.error(f"Celery broker connection failed for product {self.object.id}: {e}")
                messages.warning(self.request, _("Product saved, but background image processing is temporarily unavailable."))

        # Handle video uploads
        videos = self.request.FILES.getlist('videos')
        for video_file in videos:
            ProductVideo.objects.create(product=self.object, video=video_file)

        # Check if "Save & Continue Later" button was clicked
        save_draft = self.request.POST.get('save_draft')
        if save_draft:
            messages.success(self.request, _("Product saved! You can continue editing it later."))
            # Redirect back to edit form instead of product list
            return HttpResponseRedirect(reverse_lazy('core:vendor_product_update', kwargs={'pk': self.object.pk}))

        messages.success(self.request, self.get_success_message(form.cleaned_data))

        # Non-blocking suggestion: remind vendors to set origin if it's blank
        if not (self.object.origin_country and str(self.object.origin_country).strip()):
            messages.info(
                self.request,
                _("Tip: consider setting the product's origin country so it appears in 'Shop by Country'.")
            )

        return HttpResponseRedirect(self.get_success_url())


WIZARD_UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'tmp')
os.makedirs(WIZARD_UPLOAD_DIR, exist_ok=True)


class VendorProductWizardView(LoginRequiredMixin, IsVendorMixin, View):
    """
    Multi-step product creation wizard with proper session management.
    Steps: 1) Type selection, 2) Basic info, 3) Pricing & inventory
    """
    template_name = 'core/vendor_product_wizard.html'
    success_url = reverse_lazy('core:vendor_product_list')
    
    STEPS = ['type', 'basic', 'verify_category', 'verify_details', 'pricing', 'fulfillment', 'media']
    
    def get_session_key(self):
        return 'vendor_product_wizard'
    
    def get_wizard_data(self):
        """Get all wizard data from session."""
        default = {
            'current_step': 'type',
            'completed_steps': [],
            'form_data': {}
        }
        return self.request.session.get(self.get_session_key(), default)
    
    def save_wizard_data(self, data):
        """Save wizard data to session."""
        self.request.session[self.get_session_key()] = data
        self.request.session.modified = True
        logger.info(f"[WIZARD] Saved data. Current step: {data.get('current_step')}, Completed: {data.get('completed_steps')}")
    
    def clear_wizard_data(self):
        """Clear wizard from session."""
        if self.get_session_key() in self.request.session:
            del self.request.session[self.get_session_key()]
            self.request.session.modified = True

    def _wizard_storage(self):
        return FileSystemStorage(location=WIZARD_UPLOAD_DIR)

    def _save_uploaded_file(self, uploaded_file):
        storage = self._wizard_storage()
        safe_name = os.path.basename(uploaded_file.name)
        unique_name = f"wizard/{uuid.uuid4().hex}_{safe_name}"
        return storage.save(unique_name, uploaded_file)
    
    def get_step_form(self, step, data=None, files=None):
        """Get form instance for a specific step."""
        if step == 'type':
            return VendorProductTypeStepForm(data)
        elif step == 'basic':
            return VendorProductBasicInfoStepForm(data, files=files)
        elif step == 'verify_category':
            return VendorProductVerificationCategoryStepForm(data)
        elif step == 'verify_details':
            return VendorProductVerificationDetailsStepForm(data, files=files)
        elif step == 'pricing':
            return VendorProductPricingStepForm(data, files=files)
        elif step == 'fulfillment':
            # Get product type and fulfillment method from wizard data for conditional validation
            wizard_data = self.get_wizard_data()
            form_data = wizard_data.get('form_data', {})
            product_type = form_data.get('type', {}).get('product_type')
            fulfillment_method = data.get('fulfillment_method') if data else None
            return VendorProductFulfillmentStepForm(data, files=files, product_type=product_type, fulfillment_method=fulfillment_method)
        elif step == 'media':
            return VendorProductMediaStepForm(data, files=files)
        return None
    
    def get_next_step(self, current_step):
        """Get the next step after current."""
        try:
            idx = self.STEPS.index(current_step)
            if idx < len(self.STEPS) - 1:
                return self.STEPS[idx + 1]
        except (ValueError, IndexError):
            pass
        return None
    
    def get_previous_step(self, current_step):
        """Get the previous step."""
        try:
            idx = self.STEPS.index(current_step)
            if idx > 0:
                return self.STEPS[idx - 1]
        except (ValueError, IndexError):
            pass
        return None
    
    def get(self, request):
        """Display current step."""
        wizard_data = self.get_wizard_data()
        current_step = wizard_data.get('current_step', 'type')
        form_data = wizard_data.get('form_data', {})
        
        # Get saved data for this step
        step_data = form_data.get(current_step, {})
        form = self.get_step_form(current_step, data=None)
        
        # Pre-fill form with saved data
        if step_data and form:
            for field, value in step_data.items():
                if field in form.fields:
                    field_widget = getattr(form.fields[field], 'widget', None)
                    if getattr(field_widget, 'input_type', None) == 'file':
                        continue
                    form.fields[field].initial = value
        
        logger.info(f"[WIZARD GET] Step: {current_step}, Has data: {bool(step_data)}")
        
        context = {
            'wizard': {
                'form': form,
                'steps': {
                    'current': current_step,
                    'all': self.STEPS,
                    'count': len(self.STEPS),
                    'step0': self.STEPS.index(current_step),
                    'step1': self.STEPS.index(current_step) + 1,
                    'first': self.STEPS[0],
                    'last': self.STEPS[-1],
                    'prev': self.get_previous_step(current_step),
                    'next': self.get_next_step(current_step),
                },
                'management_form': {
                    'current_step': current_step,
                }
            },
            'form': form,
            'current_step': current_step,
            'step_number': self.STEPS.index(current_step) + 1,
            'total_steps': len(self.STEPS),
            'form_title': _("Create Product"),
            'is_update_form': False,
        }
        
        # Add product type for conditional display
        if 'type' in form_data:
            context['product_type'] = form_data['type'].get('product_type')

        if 'verify_category' in form_data:
            context['verification_category'] = form_data['verify_category'].get('verification_category')
        
        # Add fulfillment method for conditional display
        if 'fulfillment' in form_data:
            context['fulfillment_method'] = form_data['fulfillment'].get('fulfillment_method')
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle form submission."""
        wizard_data = self.get_wizard_data()
        current_step = wizard_data.get('current_step', 'type')
        form_data = wizard_data.get('form_data', {})
        completed_steps = wizard_data.get('completed_steps', [])
        
        # Check for navigation buttons
        if 'wizard_goto_step' in request.POST:
            target_step = request.POST['wizard_goto_step']
            if target_step in completed_steps or target_step == self.STEPS[0]:
                wizard_data['current_step'] = target_step
                self.save_wizard_data(wizard_data)
                return redirect(request.path)
        
        # Validate current step form
        form = self.get_step_form(current_step, data=request.POST, files=request.FILES)
        
        if form.is_valid():
            logger.info(f"[WIZARD POST] Step {current_step} valid")

            def _serialize_value(value):
                if isinstance(value, Decimal):
                    return str(value)
                if hasattr(value, 'pk'):
                    return value.pk
                if hasattr(value, 'code'):
                    return value.code
                if hasattr(value, 'isoformat'):
                    try:
                        return value.isoformat()
                    except Exception:
                        pass
                if isinstance(value, (list, tuple)):
                    return [_serialize_value(item) for item in value]
                if isinstance(value, dict):
                    return {key: _serialize_value(val) for key, val in value.items()}
                return value

            # Save form data - convert model instances to IDs for JSON serialization
            cleaned_data = {key: _serialize_value(value) for key, value in form.cleaned_data.items()}

            # Persist uploaded files to temp storage and store paths
            if form.files:
                for field_name in form.files:
                    file_list = form.files.getlist(field_name)
                    saved_paths = [self._save_uploaded_file(f) for f in file_list]
                    if not saved_paths:
                        continue
                    cleaned_data[field_name] = saved_paths if len(saved_paths) > 1 else saved_paths[0]

            form_data[current_step] = cleaned_data
            
            # Mark step as completed
            if current_step not in completed_steps:
                completed_steps.append(current_step)
            
            # Check if this is the last step
            if current_step == self.STEPS[-1]:
                # Create the product
                return self.create_product(request, form_data)
            
            # Move to next step
            next_step = self.get_next_step(current_step)
            wizard_data['current_step'] = next_step
            wizard_data['form_data'] = form_data
            wizard_data['completed_steps'] = completed_steps
            
            self.save_wizard_data(wizard_data)
            logger.info(f"[WIZARD POST] Moving to step: {next_step}")
            
            return redirect(request.path)
        
        else:
            # Form invalid - redisplay with errors
            logger.error(f"[WIZARD POST] Step {current_step} invalid: {form.errors}")
            
            context = {
                'wizard': {
                    'form': form,
                    'steps': {
                        'current': current_step,
                        'all': self.STEPS,
                        'count': len(self.STEPS),
                        'step0': self.STEPS.index(current_step),
                        'step1': self.STEPS.index(current_step) + 1,
                        'first': self.STEPS[0],
                        'last': self.STEPS[-1],
                        'prev': self.get_previous_step(current_step),
                        'next': self.get_next_step(current_step),
                    },
                    'management_form': {
                        'current_step': current_step,
                    }
                },
                'form': form,
                'current_step': current_step,
                'step_number': self.STEPS.index(current_step) + 1,
                'total_steps': len(self.STEPS),
                'form_title': _("Create Product"),
                'is_update_form': False,
            }
            
            if 'type' in form_data:
                context['product_type'] = form_data['type'].get('product_type')

            if 'verify_category' in form_data:
                context['verification_category'] = form_data['verify_category'].get('verification_category')
            
            return render(request, self.template_name, context)
    
    def create_product(self, request, form_data):
        """Create product from all collected data."""
        from django.db import transaction, IntegrityError
        
        try:
            logger.info(f"[WIZARD CREATE] Creating product with data from {len(form_data)} steps")
            
            # Combine all form data
            all_data = {}
            for step_data in form_data.values():
                all_data.update(step_data)

            # Convert ISO date strings back to date objects where needed
            date_fields = {
                'print_date', 'expiry_date', 'manufacturing_date'
            }
            for field_name in date_fields:
                if field_name in all_data and isinstance(all_data[field_name], str):
                    try:
                        all_data[field_name] = datetime.date.fromisoformat(all_data[field_name])
                    except Exception:
                        pass
            
            # Retrieve model instances from IDs
            category = None
            if 'category' in all_data and all_data['category']:
                try:
                    from .models import Category
                    category = Category.objects.get(pk=all_data['category'])
                except Category.DoesNotExist:
                    pass
            
            # Create product
            product = Product(
                vendor=request.user.vendor_profile,
                name=all_data.get('name', 'Unnamed Product'),
                category=category,
                product_type=all_data.get('product_type'),
                brand=all_data.get('brand'),
                manufacturer=all_data.get('manufacturer'),
                manufacturer_address=all_data.get('manufacturer_address'),
                manufacturer_part_number=all_data.get('manufacturer_part_number'),
                sku=all_data.get('sku'),
                origin_country=all_data.get('origin_country'),
                origin_city=all_data.get('origin_city'),
                made_in_label=all_data.get('made_in_label'),
                upc_ean_barcode=all_data.get('upc_ean_barcode'),
                batch_lot_number=all_data.get('batch_lot_number'),
                isbn=all_data.get('isbn'),
                book_edition=all_data.get('book_edition'),
                publisher_name=all_data.get('publisher_name'),
                print_date=all_data.get('print_date'),
                expiry_date=all_data.get('expiry_date'),
                allergen_information=all_data.get('allergen_information'),
                storage_instructions=all_data.get('storage_instructions'),
                size_variant=all_data.get('size_variant'),
                material_composition=all_data.get('material_composition'),
                care_label_instructions=all_data.get('care_label_instructions'),
                brand_authentication_code=all_data.get('brand_authentication_code'),
                handmade_or_massproduced=all_data.get('handmade_or_massproduced'),
                manufacturing_process=all_data.get('manufacturing_process'),
                sustainability=all_data.get('sustainability'),
                device_identifier_type=all_data.get('device_identifier_type'),
                device_identifier_value=all_data.get('device_identifier_value'),
                model_number=all_data.get('model_number'),
                manufacturing_date=all_data.get('manufacturing_date'),
                certification_numbers=all_data.get('certification_numbers'),
                warranty_service_code=all_data.get('warranty_service_code'),
                safety_warnings=all_data.get('safety_warnings'),
                description=all_data.get('description', ''),
                bullet_points=all_data.get('bullet_points'),
                keywords_for_ai=all_data.get('keywords_for_ai'),
                price=all_data.get('price'),
                stock=all_data.get('stock', 0),
                product_condition=all_data.get('product_condition'),
                fulfillment_method=all_data.get('fulfillment_method'),
                vendor_delivery_fee=all_data.get('vendor_delivery_fee'),
                shipping_options=all_data.get('shipping_options'),
                item_weight=all_data.get('item_weight'),
                item_dimensions=all_data.get('item_dimensions'),
            )
            
            # Use transaction to ensure atomic creation
            with transaction.atomic():
                product.save()

                storage = self._wizard_storage()

                def _attach_file(field_name):
                    file_path = all_data.get(field_name)
                    if not file_path:
                        return
                    if isinstance(file_path, (list, tuple)):
                        file_path = file_path[0]
                    try:
                        with storage.open(file_path, 'rb') as f:
                            getattr(product, field_name).save(os.path.basename(file_path), File(f), save=False)
                    except Exception as e:
                        logger.warning(f"[WIZARD CREATE] Unable to attach file {field_name}: {e}")

                for field_name in ['certifications', 'compliance_documents', 'digital_file', 'three_d_model', 'ar_model']:
                    _attach_file(field_name)

                product.save()

                image_paths = all_data.get('images') or []
                if isinstance(image_paths, str):
                    image_paths = [image_paths]
                for image_path in image_paths:
                    try:
                        with storage.open(image_path, 'rb') as f:
                            ProductImage.objects.create(
                                product=product,
                                image=File(f, name=os.path.basename(image_path)),
                                alt_text=f"Image for {product.name}"
                            )
                    except Exception as e:
                        logger.warning(f"[WIZARD CREATE] Unable to attach image: {e}")

                video_paths = all_data.get('videos') or []
                if isinstance(video_paths, str):
                    video_paths = [video_paths]
                for video_path in video_paths:
                    try:
                        with storage.open(video_path, 'rb') as f:
                            ProductVideo.objects.create(
                                product=product,
                                video=File(f, name=os.path.basename(video_path))
                            )
                    except Exception as e:
                        logger.warning(f"[WIZARD CREATE] Unable to attach video: {e}")
            
            logger.info(f"[WIZARD CREATE] Product saved successfully! ID: {product.id}")
            
            # Clear wizard data
            self.clear_wizard_data()
            
            messages.success(request, _("Product created successfully!"))
            return redirect(self.success_url)
        
        except IntegrityError as e:
            logger.error(f"[WIZARD CREATE] IntegrityError: {e}", exc_info=True)
            error_msg = str(e)
            if 'slug' in error_msg:
                messages.error(request, _("A product with a similar name already exists. Please use a different product name or try again."))
            else:
                messages.error(request, _("Database error creating product. Please check your data and try again."))
            return redirect(request.path)
            
        except Exception as e:
            logger.error(f"[WIZARD CREATE] Error: {e}", exc_info=True)
            messages.error(request, _("Error creating product: ") + str(e))
            return redirect(request.path)


class VendorProductUpdateView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = VendorProductForm
    template_name = 'core/vendor_product_form.html'
    success_url = reverse_lazy('core:vendor_product_list')
    success_message = _("Product updated successfully.")

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user.vendor_profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update_form'] = True
        # Add existing images and videos to context
        context['existing_images'] = self.object.images.all()
        context['existing_videos'] = self.object.videos.all()
        return context

    def form_invalid(self, form):
        """Handle form validation errors while preserving displayed images/videos."""
        print(f"DEBUG: Form is INVALID. Errors: {form.errors}")
        messages.error(self.request, _("There were errors with your submission. Please check the form."))
        # When form is invalid, re-render with existing images/videos still visible
        # This ensures they don't disappear if the vendor has a validation error
        return super().form_invalid(form)

    def form_valid(self, form):
        print(f"DEBUG: Form is VALID - Starting form_valid method")
        print(f"DEBUG: Form cleaned_data: {form.cleaned_data.keys()}")
        
        # Save the product instance
        self.object = form.save()
        print(f"DEBUG: Product saved. ID: {self.object.id}, Name: {self.object.name}, Origin: {self.object.origin_country}")

        # Handle deletion of images
        images_to_delete = self.request.POST.getlist('delete_images')
        print(f"DEBUG: Images to delete: {images_to_delete}")
        print(f"DEBUG: All POST data: {self.request.POST}")
        if images_to_delete:
            deleted_count = ProductImage.objects.filter(id__in=images_to_delete, product=self.object).delete()
            print(f"DEBUG: Deleted {deleted_count} images")
            messages.success(self.request, _(f"Deleted {deleted_count[0]} image(s)."))

        # Handle deletion of videos
        videos_to_delete = self.request.POST.getlist('delete_videos')
        print(f"DEBUG: Videos to delete: {videos_to_delete}")
        if videos_to_delete:
            deleted_count = ProductVideo.objects.filter(id__in=videos_to_delete, product=self.object).delete()
            print(f"DEBUG: Deleted {deleted_count} videos")
            messages.success(self.request, _(f"Deleted {deleted_count[0]} video(s)."))

        # Handle new image uploads
        new_images = self.request.FILES.getlist('images')
        print(f"DEBUG: New images to upload: {len(new_images)}")
        if new_images:
            for image_file in new_images:
                ProductImage.objects.create(product=self.object, image=image_file, alt_text=f"Image for {self.object.name}")
            messages.success(self.request, _(f"Uploaded {len(new_images)} new image(s)."))

        # Handle new video uploads
        new_videos = self.request.FILES.getlist('videos')
        print(f"DEBUG: New videos to upload: {len(new_videos)}")
        if new_videos:
            for video_file in new_videos:
                ProductVideo.objects.create(product=self.object, video=video_file)
            messages.success(self.request, _(f"Uploaded {len(new_videos)} new video(s)."))

        messages.success(self.request, self.get_success_message(form.cleaned_data))

        # Non-blocking suggestion: remind vendors to set origin if it's blank
        if not (self.object.origin_country and str(self.object.origin_country).strip()):
            messages.info(
                self.request,
                _("Tip: consider setting the product's origin country so it appears in 'Shop by Country'.")
            )

        return HttpResponseRedirect(self.get_success_url())
    
    def post(self, request, *args, **kwargs):
        """Override post to add debugging."""
        print(f"DEBUG: POST request received for VendorProductUpdateView")
        print(f"DEBUG: POST data keys: {list(request.POST.keys())}")
        print(f"DEBUG: FILES data keys: {list(request.FILES.keys())}")
        print(f"DEBUG: delete_images: {request.POST.getlist('delete_images')}")
        print(f"DEBUG: delete_videos: {request.POST.getlist('delete_videos')}")
        print(f"DEBUG: origin_country from POST: {request.POST.get('origin_country')}")
        return super().post(request, *args, **kwargs)


class VendorProductDeleteView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, DeleteView):
    model = Product
    template_name = 'core/vendor_product_confirm_delete.html'
    success_url = reverse_lazy('core:vendor_product_list')
    success_message = _("Product deleted successfully.")

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user.vendor_profile)


class VendorPayoutListView(LoginRequiredMixin, IsVendorMixin, ListView):
    model = PayoutRequest
    template_name = 'core/vendor/vendor_payout_list.html'
    context_object_name = 'payout_requests'
    paginate_by = 10

    def get_queryset(self):
        vendor = self.request.user.vendor_profile
        queryset = PayoutRequest.objects.filter(vendor_profile=vendor)

        # Filtering logic from GET parameters
        self.search_query = self.request.GET.get('q', '')
        if self.search_query:
            # Assuming search by ID
            queryset = queryset.filter(id__icontains=self.search_query)

        self.current_status = self.request.GET.get('status', '')
        if self.current_status:
            queryset = queryset.filter(status=self.current_status)

        return queryset.order_by('-requested_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.request.user.vendor_profile

        # --- Payout Summary Calculations ---
        completed_orders_value = OrderItem.objects.filter(
            product__vendor=vendor,
            order__status__in=['COMPLETED', 'DELIVERED', 'PENDING_PAYOUT']
        ).aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or Decimal('0.00')

        commission_rate = getattr(settings, 'PLATFORM_COMMISSION_RATE', Decimal('0.10'))
        total_commission = completed_orders_value * commission_rate
        net_earnings = completed_orders_value - total_commission

        total_paid_out = PayoutRequest.objects.filter(
            vendor_profile=vendor, status='completed'
        ).aggregate(total=Sum('amount_requested'))['total'] or Decimal('0.00')

        pending_payouts = PayoutRequest.objects.filter(
            vendor_profile=vendor, status__in=['pending', 'processing']
        ).aggregate(total=Sum('amount_requested'))['total'] or Decimal('0.00')

        context['available_for_payout'] = max(Decimal('0.00'), net_earnings - total_paid_out - pending_payouts)
        context['pending_payouts'] = pending_payouts
        context['total_paid_out'] = total_paid_out
        context['can_request_payout'] = context['available_for_payout'] >= getattr(settings, 'MINIMUM_VENDOR_PAYOUT_AMOUNT', 50)
        context['search_query'] = self.search_query
        context['current_status'] = self.current_status
        context['page_title'] = _("Payouts")
        context['vendor'] = vendor
        return context

class VendorPayoutRequestCreateView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, CreateView):
    model = PayoutRequest
    form_class = VendorPayoutRequestForm
    template_name = 'core/vendor/vendor_payout_request_form.html'
    success_url = reverse_lazy('core:vendor_payout_request_list')
    success_message = _("Your payout request has been submitted.")

    def get_form_kwargs(self):
        """Passes the maximum available payout amount and vendor profile to the form."""
        kwargs = super().get_form_kwargs()
        vendor = self.request.user.vendor_profile

        # --- Payout Summary Calculations (mirrors VendorPayoutListView) ---
        completed_orders_value = OrderItem.objects.filter(
            product__vendor=vendor,
            order__status__in=['COMPLETED', 'DELIVERED', 'PENDING_PAYOUT']
        ).aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or Decimal('0.00')

        commission_rate = getattr(settings, 'PLATFORM_COMMISSION_RATE', Decimal('0.10'))
        total_commission = completed_orders_value * commission_rate
        net_earnings = completed_orders_value - total_commission

        total_paid_out = PayoutRequest.objects.filter(
            vendor_profile=vendor, status='completed'
        ).aggregate(total=Sum('amount_requested'))['total'] or Decimal('0.00')

        pending_payouts = PayoutRequest.objects.filter(
            vendor_profile=vendor, status__in=['pending', 'processing']
        ).aggregate(total=Sum('amount_requested'))['total'] or Decimal('0.00')

        kwargs['max_amount'] = max(Decimal('0.00'), net_earnings - total_paid_out - pending_payouts)
        kwargs['vendor_profile'] = vendor # Pass the vendor profile to the form
        return kwargs

    def form_valid(self, form):
        form.instance.vendor_profile = self.request.user.vendor_profile
        
        # Get the selected payout method and construct the details string
        payout_method_key = form.cleaned_data.get('payout_method')
        vendor = self.request.user.vendor_profile
        details_string = "Payout method not found." # Fallback

        if payout_method_key == 'mobile_money':
            details_string = f"Mobile Money: {vendor.mobile_money_provider} - {vendor.mobile_money_number}"
        elif payout_method_key == 'bank':
            details_string = f"Bank Account: {vendor.bank_name}, Acc No: {vendor.bank_account_number}, Name: {vendor.bank_account_name}"
        elif payout_method_key == 'paypal':
            details_string = f"PayPal: {vendor.paypal_email}"
        elif payout_method_key == 'stripe':
            details_string = f"Stripe: {vendor.stripe_account_id}"
        elif payout_method_key == 'payoneer':
            details_string = f"Payoneer: {vendor.payoneer_email}"
        elif payout_method_key == 'wise':
            details_string = f"Wise: {vendor.wise_email}"
        elif payout_method_key == 'crypto':
            details_string = f"Crypto: {vendor.crypto_wallet_network} - {vendor.crypto_wallet_address}"
        
        form.instance.payment_method_details = details_string
        
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Request New Payout")
        context['vendor'] = self.request.user.vendor_profile
        return context

class VendorReviewListView(LoginRequiredMixin, IsVendorMixin, ListView):
    model = VendorReview
    template_name = 'core/vendor/vendor_review_list.html' # Corrected path
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        vendor = self.request.user.vendor_profile
        queryset = VendorReview.objects.filter(vendor=vendor).order_by('-created_at')

        # Get the rating from the URL query parameters
        rating_filter = self.request.GET.get('rating')
        if rating_filter and rating_filter.isdigit():
            queryset = queryset.filter(rating=int(rating_filter))

        # Get the search query from the URL
        search_query = self.request.GET.get('q')
        if search_query:
            # The model has `review`, not `comment`.
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(review__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.request.user.vendor_profile

        # Get all reviews for the vendor for accurate stats, ignoring filters
        all_reviews_for_vendor = VendorReview.objects.filter(vendor=vendor)

        context['page_title'] = _("Your Reviews")
        context['total_reviews'] = all_reviews_for_vendor.count()
        context['average_rating'] = all_reviews_for_vendor.aggregate(Avg('rating'))['rating__avg']

        # Pass the current filter state to the template
        context['current_rating'] = self.request.GET.get('rating')
        context['search_query'] = self.request.GET.get('q', '')

        return context

class VendorReviewReplyView(LoginRequiredMixin, IsVendorMixin, SuccessMessageMixin, UpdateView):
    model = VendorReview
    fields = ['reply'] # Use fields directly for simplicity
    success_url = reverse_lazy('core:vendor_review_list')
    success_message = _("Your reply has been posted successfully.")

    def get_queryset(self):
        # Ensure vendor can only reply to reviews for their own store
        return VendorReview.objects.filter(vendor=self.request.user.vendor_profile)

    def form_valid(self, form):
        # Set the reply timestamp when the form is submitted
        if form.instance.reply and not form.instance.replied_at:
             form.instance.replied_at = timezone.now()
        elif not form.instance.reply: # Clear timestamp if reply is removed
            form.instance.replied_at = None
        return super().form_valid(form)


# --- Core Views ---




def home(request):
    # Example: Fetch some products and categories for the homepage
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:16]
    new_arrivals = Product.objects.filter(is_active=True).order_by('-created_at')[:20]
    top_categories = Category.objects.annotate(num_products=Count('products')).filter(num_products__gt=0, is_active=True).order_by('-num_products')[:6]

    # Get a featured product as deal of the day (pick one with good image)
    deal_of_day = Product.objects.filter(is_active=True, is_featured=True).select_related('vendor').order_by('?').first()

    # Example: Fetch some services
    featured_services = Service.objects.filter(is_active=True, is_featured=True).select_related('provider', 'provider__service_provider_profile')[:4] # Assuming an 'is_featured' field

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

    # Aggregate product counts by origin country (only active products)
    country_counts = (
        Product.objects.filter(is_active=True)
        .exclude(origin_country__isnull=True)
        .values('origin_country')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )

    # Convert to list of dicts with human-readable name
    top_countries = []
    for entry in country_counts:
        code = entry.get('origin_country') or ''
        name = countries.name(code) if code else ''
        top_countries.append({'code': code, 'name': name or code, 'count': entry.get('count', 0)})

    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'top_categories': top_categories,
        'featured_services': featured_services,
        'top_vendors': top_vendors,
        'page_title': _("Welcome to GOWBUY Marketplace"),
        'featured_rider_profiles': featured_rider_profiles,
        'top_countries': top_countries,
        'deal_of_day': deal_of_day,
    }
    return render(request, 'core/home.html', context)

def menu(request):
    """
    Displays a full menu of all product and service categories.
    """
    # Eager-load three levels of subcategories to avoid N+1 queries when rendering nested trees
    product_categories = Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related(
        Prefetch('subcategories', queryset=Category.objects.filter(is_active=True).order_by('name').prefetch_related(
            Prefetch('subcategories', queryset=Category.objects.filter(is_active=True).order_by('name').prefetch_related(
                Prefetch('subcategories', queryset=Category.objects.filter(is_active=True).order_by('name'))
            ))
        ))
    )
    service_categories = ServiceCategory.objects.filter(is_active=True, parent__isnull=True).prefetch_related(
        Prefetch('subcategories', queryset=ServiceCategory.objects.filter(is_active=True).order_by('name'))
    )

    context = {
        'product_categories': product_categories,
        'service_categories': service_categories,
        'page_title': _("Menu"),
    }
    return render(request, 'core/menu.html', context)

def sell_on_gowbuy(request):
    """
    Displays the 'Sell on Gowbuy' landing page.
    """
    context = {'page_title': _("Sell on GOWBUY")}
    return render(request, 'core/sell_on_gowbuy.html', context)

@login_required
def vendor_registration_view(request):
    if hasattr(request.user, 'vendor_profile') and request.user.vendor_profile:
        messages.info(request, _("You are already a registered vendor."))
        return redirect('core:vendor_dashboard')

    if request.method == 'POST':
        form = VendorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.user = request.user
            vendor.is_approved = False
            vendor.is_verified = False
            vendor.save()
            messages.success(request, _("Your vendor application has been submitted! It will be reviewed by our team shortly."))
            # The vendor dashboard template is missing the logic to display messages.
            # Redirecting to the product list, which does display messages, until the
            # dashboard is updated.
            return redirect('core:vendor_product_list')
    else:
        form = VendorRegistrationForm()

    context = {'form': form, 'page_title': _("Become a Vendor")}
    return render(request, 'core/vendor_registration.html', context)


class VendorVerificationView(LoginRequiredMixin, IsVendorMixin, FormView):
    template_name = 'core/vendor_verification.html'
    form_class = VerificationMethodSelectionForm # Using the first step form as an example
    success_url = reverse_lazy('core:vendor_dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # This is a simplified handler. The multi-step view is the primary one.
        messages.success(self.request, _("Verification form submitted."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor'] = self.request.user.vendor_profile
        context['page_title'] = _("Vendor Verification")
        return context


# --- Static & Legal Pages ---

class Creating3DModelsHelpView(TemplateView):
    """
    Displays the help page for creating 3D models.
    """
    template_name = 'core/help/creating_3d_models.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("How to Create 3D Models")
        return context

class HelpCenterView(TemplateView):
    """
    Displays the Help Center page with FAQs.
    """
    template_name = 'core/help_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Help & Support")
        context['faqs'] = FAQ.objects.filter(is_active=True)
        return context

# This alias is used by urls.py to render the support center page.
HelpPageView = HelpCenterView


class LegalDocumentView(TemplateView):
    """
    A generic view to display the content of an active legal document.
    Subclasses should specify the `model` and `page_title_base`.
    """
    template_name = 'core/legal_document.html' # A generic template for legal docs
    model = None
    page_title_base = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_document = None
        if self.model:
            # Get the most recently effective, active document
            active_document = self.model.objects.filter(is_active=True).order_by('-effective_date').first()
        
        context['document'] = active_document
        context['page_title'] = self.page_title_base
        if active_document:
            context['page_title'] = f"{self.page_title_base} (v{active_document.version})"
        return context

class TermsView(LegalDocumentView):
    """
    Displays the currently active Terms and Conditions.
    This resolves the ImportError from the project's urls.py.
    """
    model = TermsAndConditions
    page_title_base = _("Terms and Conditions")

class PrivacyPolicyView(LegalDocumentView):
    """
    Displays the currently active Privacy Policy.
    """
    model = PrivacyPolicy
    page_title_base = _("Privacy Policy")
class ProductListView(ListView):
    model = Product
    template_name = 'core/product_list.html'
    context_object_name = 'products'
    paginate_by = 12 # Show 12 products per page

    def get_queryset(self):
        queryset = super().get_queryset() # Your existing logic
        self.filterset = ProductFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context


class OriginDetailView(ListView):
    """Lists products for a specific origin country (SEO-friendly page).
    Also provides categories and subcategories specific to that country and
    top vendors and featured products for the country home page.
    """
    model = Product
    template_name = 'core/origin_detail.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        code = self.kwargs.get('country_code', '').strip().upper()
        qs = Product.objects.filter(is_active=True, origin_country=code)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        code = self.kwargs.get('country_code', '').strip().upper()
        context['country_code'] = code
        try:
            context['country_name'] = countries.name(code) if code else ''
        except Exception:
            context['country_name'] = code

        # Categories (top-level) that have active products from this country
        country_categories = (
            Category.objects.filter(is_active=True, products__origin_country=code, products__is_active=True)
            .annotate(product_count=Count('products', filter=Q(products__origin_country=code, products__is_active=True)))
            .distinct()
            .order_by('-product_count')
        )

        # For each category, get subcategories that also have products from this country
        categories_with_subs = []
        for cat in country_categories:
            subs = (
                cat.subcategories.filter(is_active=True, products__origin_country=code, products__is_active=True)
                .annotate(product_count=Count('products', filter=Q(products__origin_country=code, products__is_active=True)))
                .distinct().order_by('-product_count')
            )
            categories_with_subs.append({'category': cat, 'subcategories': subs})

        # Top vendors in this country by number of products (limit 6)
        top_vendors = (
            Vendor.objects.filter(products__origin_country=code, products__is_active=True)
            .annotate(product_count=Count('products', filter=Q(products__origin_country=code, products__is_active=True)))
            .distinct().order_by('-product_count')[:6]
        )

        # Featured products from this country
        featured_products = Product.objects.filter(is_active=True, origin_country=code, is_featured=True)[:8]

        # Meta description: include top categories for SEO
        top_cat_names = ', '.join([c.name for c in country_categories[:3]])
        meta_description = f"Discover products from {context['country_name'] or code}. Top categories: {top_cat_names}. Buy directly from verified vendors on GOWBUY."

        context.update({
            'country_categories': country_categories,
            'categories_with_subs': categories_with_subs,
            'top_vendors': top_vendors,
            'featured_products_by_country': featured_products,
            'page_title': f"Products from {context['country_name'] or code}",
            'meta_description': meta_description,
        })
        return context

class CategoryDetailView(ListView):
    model = Product
    template_name = 'core/category_detail.html' # Assumes this template exists
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['category_slug'], is_active=True)

        # Get all descendant categories. This is not the most performant way for deep trees
        # but is self-contained. For large-scale apps, consider `django-mptt`.
        all_categories = [self.category]
        queue = [self.category]
        while queue:
            parent = queue.pop(0)
            for child in parent.subcategories.all():
                all_categories.append(child)
                queue.append(child)

        return Product.objects.filter(
            category__in=all_categories,
            is_active=True,
            vendor__is_approved=True
        ).select_related('vendor').prefetch_related('images').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['page_title'] = self.category.name
        context['is_product_list'] = True # For template consistency
        return context

def daily_offers(request):
    """
    Displays products that are currently on promotion.
    """
    now = timezone.now()
    active_promotions = Promotion.objects.filter(
        is_active=True, start_date__lte=now, end_date__gte=now
    )

    promoted_product_ids = set()
    for promo in active_promotions:
        if promo.scope == 'all':
            promoted_product_ids.update(Product.objects.filter(is_active=True, is_featured=True).values_list('id', flat=True)[:20])
            break
        elif promo.scope == 'product':
            promoted_product_ids.update(promo.applicable_products.values_list('id', flat=True))
        elif promo.scope == 'category':
            products_in_cat = Product.objects.filter(category__in=promo.applicable_categories.all(), is_active=True)
            promoted_product_ids.update(products_in_cat.values_list('id', flat=True))
        elif promo.scope == 'vendor' and promo.applicable_vendor:
            products_from_vendor = Product.objects.filter(vendor=promo.applicable_vendor, is_active=True)
            promoted_product_ids.update(products_from_vendor.values_list('id', flat=True))

    products = Product.objects.filter(id__in=list(promoted_product_ids)).select_related('category', 'vendor').prefetch_related('images')
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'page_title': _("Daily Offers"),
        'is_product_list': True, # To help template rendering
    }
    # We can reuse the product_list.html template for this view
    return render(request, 'core/product_list.html', context)

@login_required
@require_POST
def apply_coupon(request):
    now = timezone.now()
    form = CouponApplyForm(request.POST)
    if form.is_valid():
        code = form.cleaned_data['code']
        try:
            promo = Promotion.objects.get(code__iexact=code, is_active=True)
            cart = Cart.objects.get(user=request.user, ordered=False)
            cart_total = cart.get_cart_total()

            # --- Start Validation ---
            if not (promo.start_date <= now <= promo.end_date):
                messages.error(request, _("This coupon is not currently active."))
                return redirect('core:checkout')

            if promo.usage_limit is not None and promo.usage_count >= promo.usage_limit:
                messages.error(request, _("This coupon has reached its usage limit."))
                return redirect('core:checkout')

            if promo.minimum_purchase_amount is not None and cart_total < promo.minimum_purchase_amount:
                msg = _("Your cart total does not meet the minimum purchase amount of {amount} for this coupon.").format(amount=promo.minimum_purchase_amount)
                messages.error(request, msg)
                return redirect('core:checkout')

            if promo.uses_per_customer is not None:
                times_used = Order.objects.filter(user=request.user, promotion=promo).count()
                if times_used >= promo.uses_per_customer:
                    messages.error(request, _("You have already used this coupon the maximum number of times."))
                    return redirect('core:checkout')

            # Scope validation
            applicable_items_total = Decimal('0.00')
            cart_items = cart.items.all()

            if promo.scope == 'all':
                applicable_items_total = cart_total
            elif promo.scope == 'vendor' and promo.applicable_vendor:
                for item in cart_items:
                    if item.product and item.product.vendor == promo.applicable_vendor:
                        applicable_items_total += item.get_total_item_price()
            elif promo.scope == 'category':
                applicable_categories = promo.applicable_categories.all()
                if applicable_categories.exists():
                    for item in cart_items:
                        if item.product and item.product.category in applicable_categories:
                            applicable_items_total += item.get_total_item_price()
            elif promo.scope == 'product':
                applicable_products = promo.applicable_products.all()
                if applicable_products.exists():
                    for item in cart_items:
                        if item.product and item.product in applicable_products:
                            applicable_items_total += item.get_total_item_price()

            if applicable_items_total == Decimal('0.00'):
                messages.error(request, _("This coupon is not valid for any of the items in your cart."))
                return redirect('core:checkout')
            # --- End Validation ---

            # --- Calculate Discount ---
            discount_amount = Decimal('0.00')
            if promo.promo_type == 'percentage':
                discount_amount = (applicable_items_total * (promo.discount_value / Decimal(100))).quantize(Decimal('0.01'))
            elif promo.promo_type == 'fixed_amount':
                discount_amount = min(promo.discount_value, applicable_items_total)

            # --- Store in session ---
            request.session['promotion_id'] = promo.id
            request.session['discount_amount'] = str(discount_amount)

            messages.success(request, _("Coupon '{code}' applied successfully.").format(code=promo.code))

        except Promotion.DoesNotExist:
            messages.error(request, _("Invalid coupon code."))
            # Clear any existing coupon from session if a new invalid one is entered
            if 'promotion_id' in request.session: del request.session['promotion_id']
            if 'discount_amount' in request.session: del request.session['discount_amount']
        except Cart.DoesNotExist:
            messages.error(request, _("Your cart is empty."))
    
    return redirect('core:checkout')

@login_required
def remove_coupon(request):
    """Removes the applied coupon from the session."""
    if 'promotion_id' in request.session:
        del request.session['promotion_id']
    if 'discount_amount' in request.session:
        del request.session['discount_amount']
    messages.info(request, _("Coupon has been removed."))
    return redirect('core:checkout')


class ProductDetailView(DetailView):
    model = Product
    template_name = 'core/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'product_slug'
    slug_field = 'slug'

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
            context['user_has_reviewed_product'] = ProductReview.objects.filter(product=product, user=self.request.user).exists()
        else:
            context['in_wishlist'] = False # Or handle session-based wishlist
            context['user_has_reviewed_product'] = False

        # --- START: Product Q&A ---
        context['questions'] = ProductQuestion.objects.filter(product=product).prefetch_related(
            Prefetch('answers', queryset=ProductAnswer.objects.select_related('user', 'user__userprofile').order_by('created_at'))
        ).select_related('user', 'user__userprofile').order_by('-created_at')
        context['question_form'] = ProductQuestionForm()
        context['answer_form'] = ProductAnswerForm() # Pass one instance for the template to use in loops
        # --- END: Product Q&A ---

        # Add 3D model URL to context
        context['three_d_model_url'] = product.three_d_model.url if product.three_d_model else None

        # --- START: Unified Media Gallery ---
        media_gallery = []
        for img in product.images.all():
            media_gallery.append({'id': img.id, 'type': 'image', 'url': img.image.url, 'thumbnail_url': img.image.url})
        for vid in product.videos.all():
            media_gallery.append({'id': vid.id, 'type': 'video', 'url': vid.video.url, 'thumbnail_url': settings.STATIC_URL + 'assets/img/video_placeholder.png'})
        context['media_gallery'] = media_gallery
        # --- END: Unified Media Gallery ---

        # --- START: Refactored AI Features ---
        context['ai_review_summary'] = _get_ai_review_summary(product, list(context['reviews']))
        context['ai_recommended_products'] = _get_ai_recommendations(product)
        # --- END: Refactored AI Features ---

        # --- Phase 4: Authenticity & Origin Information ---
        context['authenticity_feedback_form'] = AuthenticityFeedbackForm()
        context['authenticity_reviews'] = AuthenticityReview.objects.filter(product=product).order_by('-flagged_at')
        context['authenticity_feedback'] = AuthenticityFeedback.objects.filter(product=product, is_verified=True).order_by('-created_at')[:5]
        context['feedback_count'] = AuthenticityFeedback.objects.filter(product=product).count()
        context['user_has_purchased_product'] = product.user_has_purchased(self.request.user)
        # --- END: Phase 4: Authenticity & Origin Information ---

        return context


class ConversationListView(LoginRequiredMixin, ListView):
    """
    A generic view to display a list of conversations for any logged-in user.
    It dynamically selects the template and context based on the user's role
    (vendor, service provider, or customer).
    """
    model = Conversation
    context_object_name = 'conversations'
    paginate_by = 15

    def get_template_names(self):
        """Dynamically determine the template based on the URL's name."""
        resolver_match = self.request.resolver_match
        url_name = resolver_match.url_name if resolver_match else ''

        if url_name == 'vendor_message_list':
            return ['core/vendor/vendor_conversation_list.html']
        elif url_name == 'service_provider_message_list':
            return ['core/service_provider/conversation_list.html']
        elif url_name == 'customer_message_list':
            return ['core/customer/customer_message_list.html']
        else:
            # Fallback for any other case, defaults to customer view.
            return ['core/customer/customer_message_list.html']

    def get_queryset(self):
        """
        Returns conversations for the current user, annotated with last message details.
        This efficient query is now shared by all user types.
        """
        last_message_subquery = Message.objects.filter(conversation=OuterRef('pk')).order_by('-timestamp').values('content')[:1]
        last_message_sender_subquery = Message.objects.filter(conversation=OuterRef('pk')).order_by('-timestamp').values('sender_id')[:1]
        unread_subquery = Message.objects.filter(conversation=OuterRef('pk'), is_read=False).exclude(sender=self.request.user)

        queryset = Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related(
            'participants__userprofile'
        ).annotate(
            last_message_time=Max('messages__timestamp'),
            last_message_content=Subquery(last_message_subquery),
            last_message_sender_id=Subquery(last_message_sender_subquery),
            is_unread_by_user=Exists(unread_subquery)
        ).order_by(F('last_message_time').desc(nulls_last=True))

        # --- START: Add Search and Filter Logic ---
        self.search_query = self.request.GET.get('q', '')
        if self.search_query:
            # Filter based on the other participant's name/username or conversation subject
            other_participant_filter = (
                Q(participants__username__icontains=self.search_query) |
                Q(participants__first_name__icontains=self.search_query) |
                Q(participants__last_name__icontains=self.search_query)
            )
            # Exclude the current user from the search criteria to only match the other participant
            queryset = queryset.filter(
                Q(subject__icontains=self.search_query) |
                (other_participant_filter & ~Q(participants=self.request.user))
            ).distinct()

        self.current_status = self.request.GET.get('status', '')
        if self.current_status == 'unread':
            queryset = queryset.filter(is_unread_by_user=True)
        # --- END: Add Search and Filter Logic ---

        return queryset

    def get_context_data(self, **kwargs):
        """Adds the 'other_participant' to each conversation for easy template access."""
        context = super().get_context_data(**kwargs)
        for conv in context.get('conversations', []):
            conv.other_participant = conv.get_other_participant(self.request.user)
        context['page_title'] = _("Messages")

        # Pass search and filter state to the template
        context['search_query'] = getattr(self, 'search_query', '')
        context['current_status'] = getattr(self, 'current_status', '')

        return context

class ServiceProviderConversationListView(LoginRequiredMixin, IsServiceProviderMixin, ListView):
    """
    Displays a list of conversations for the logged-in service provider.
    """
    model = Conversation
    template_name = 'core/service_provider/conversation_list.html'
    context_object_name = 'conversations'
    paginate_by = 15

    def get_queryset(self):
        """
        Returns conversations for the current user, annotated with last message details.
        This logic is shared across different user types viewing their message lists.
        """
        last_message_subquery = Message.objects.filter(conversation=OuterRef('pk')).order_by('-timestamp').values('content')[:1]
        last_message_sender_subquery = Message.objects.filter(conversation=OuterRef('pk')).order_by('-timestamp').values('sender_id')[:1]
        unread_subquery = Message.objects.filter(conversation=OuterRef('pk'), is_read=False).exclude(sender=self.request.user)

        queryset = Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related(
            'participants__userprofile'
        ).annotate(
            last_message_time=Max('messages__timestamp'),
            last_message_content=Subquery(last_message_subquery),
            last_message_sender_id=Subquery(last_message_sender_subquery),
            is_unread_by_user=Exists(unread_subquery)
        ).order_by(F('last_message_time').desc(nulls_last=True))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for conv in context.get('conversations', []):
            conv.other_participant = conv.get_other_participant(self.request.user)
        return context


class StartConversationView(LoginRequiredMixin, View):
    """
    Initiates a conversation with a vendor from a product page.
    Finds an existing 2-person conversation or creates a new one.
    """
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        vendor_user = product.vendor.user
        current_user = request.user

        if vendor_user == current_user:
            messages.error(request, _("You cannot start a conversation with yourself."))
            return redirect(product.get_absolute_url())

        # Find an existing conversation with exactly these two participants
        conversation = Conversation.objects.annotate(
            num_participants=Count('participants')
        ).filter(
            participants=current_user, num_participants=2
        ).filter(
            participants=vendor_user
        ).first()

        if conversation:
            # Redirect to the existing conversation
            return redirect('core:vendor_message_detail', pk=conversation.pk)
        else:
            # Create a new conversation
            new_conversation = Conversation.objects.create(subject=f"Inquiry about: {product.name}")
            new_conversation.participants.add(current_user, vendor_user)
            return redirect('core:vendor_message_detail', pk=new_conversation.pk)

class ConversationDetailView(LoginRequiredMixin, View):
    """
    Displays a single conversation thread and handles new messages.
    This view is generic and can be accessed by any participant of the conversation.
    """
    def get_template_names(self):
        """Dynamically selects the template based on the URL's name."""
        resolver_match = self.request.resolver_match
        url_name = resolver_match.url_name if resolver_match else ''

        if url_name == 'vendor_message_detail':
            return ['core/vendor/conversation_detail.html']
        elif url_name == 'service_provider_message_detail':
            return ['core/service_provider/conversation_detail.html']
        # Default to the customer template
        return ['core/customer/customer_conversation_detail.html']

    def get(self, request, *args, **kwargs):
        template_to_render = self.get_template_names()[0]

        # Securely fetch the conversation, ensuring the current user is a participant.
        conversation = get_object_or_404(
            Conversation.objects.prefetch_related(
                Prefetch('messages', queryset=Message.objects.order_by('timestamp').select_related('sender__userprofile'))
            ),
            pk=self.kwargs['pk'],
            participants=request.user
        )

        # Mark messages as read
        unread_messages = conversation.messages.filter(is_read=False).exclude(sender=request.user)
        unread_message_ids = list(unread_messages.values_list('id', flat=True))

        if unread_message_ids:
            unread_messages.update(is_read=True, read_at=timezone.now())

            # Broadcast that these messages have been read
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{conversation.id}',
                {
                    'type': 'read_receipts_broadcast',
                    'message_ids': unread_message_ids,
                    'read_by': request.user.username
                }
            )

        # This logic now correctly handles finding the other participant(s)
        other_participants = conversation.participants.exclude(id=request.user.id)
        other_participant_names = ", ".join([p.username for p in other_participants])

        # Add the other participant to the conversation object for the template
        conversation.other_participant = conversation.get_other_participant(request.user)
        
        form = kwargs.get('form', MessageForm())

        context = {
            'conversation': conversation,
            'other_participants': other_participants, # Pass the queryset of other participants
            'other_participant_names': other_participant_names, # Pass the formatted string of names
            'form': form,
            'page_title': _("Conversation with %(participants)s") % {'participants': other_participant_names or '...'},
        }

        # Add a dynamic back URL to the context based on the template being rendered
        if 'vendor' in template_to_render:
            context['back_url'] = reverse('core:vendor_message_list')
            context['back_text'] = _("Back to Messages")
        elif 'service_provider' in template_to_render:
            context['back_url'] = reverse('core:service_provider_message_list')
            context['back_text'] = _("Back to Messages")
        else:
            context['back_url'] = reverse('core:customer_message_list')
            context['back_text'] = _("Back to My Messages")

        return render(request, template_to_render, context)

    def post(self, request, *args, **kwargs):
        # Securely fetch the conversation for posting as well.
        conversation = get_object_or_404(Conversation, pk=self.kwargs['pk'], participants=request.user)
 
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            # Redirect back to the correct detail page based on the URL used
            return redirect(request.resolver_match.view_name, pk=conversation.pk)

        # If form is invalid, re-render the page with errors
        # Re-calling get() to rebuild the context correctly
        return self.get(request, form=form, *args, **kwargs)


@login_required
@require_POST
def add_product_question(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    form = ProductQuestionForm(request.POST)
    if form.is_valid():
        question = form.save(commit=False)
        question.product = product
        question.user = request.user
        question.save()
        messages.success(request, _("Your question has been submitted successfully."))
    else:
        messages.error(request, _("There was an error submitting your question. Please try again."))
    return redirect(product.get_absolute_url())

@login_required
@require_POST
def add_product_answer(request, question_id):
    question = get_object_or_404(ProductQuestion, id=question_id)
    form = ProductAnswerForm(request.POST)
    if form.is_valid():
        answer = form.save(commit=False)
        answer.question = question
        answer.user = request.user
        answer.save()
        messages.success(request, _("Your answer has been posted."))
    else:
        messages.error(request, _("There was an error posting your answer."))
    return redirect(question.product.get_absolute_url())

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
@require_POST # This view should only accept POST requests for removal
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user, cart__ordered=False)
    cart = cart_item.cart
    item_name = cart_item.name # Use the property from the model

    # --- START: Clean up session data for service bookings ---
    if cart_item.service_package:
        booking_details_session = request.session.get('booking_details', {})
        if str(cart_item.id) in booking_details_session:
            del booking_details_session[str(cart_item.id)]
            request.session['booking_details'] = booking_details_session
            request.session.modified = True
    # --- END: Clean up session data ---
    
    cart_item.delete()

    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart_total = cart.get_cart_total()
        cart_items_count = cart.get_item_count()
        return JsonResponse({
            'success': True,
            'message': _("'{item_name}' removed from your cart.").format(item_name=item_name),
            'cart_total': f'{cart_total:,.2f}',
            'cart_items_count': cart_items_count,
        })

    # For standard form submissions, redirect with a message
    messages.info(request, _("'{item_name}' removed from your cart.").format(item_name=item_name))
    return redirect('core:cart_detail')

@login_required
@require_POST
def update_cart_item(request, item_id):
    # This view is now primarily for AJAX requests.
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Fallback for non-AJAX form submissions
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user, cart__ordered=False)
        quantity = request.POST.get('quantity')
        try:
            quantity = int(quantity)
            if quantity > 0:
                if cart_item.product.stock is not None and quantity > cart_item.product.stock:
                     messages.error(request, _('Not enough stock. Only {stock} items left.').format(stock=cart_item.product.stock))
                else:
                    cart_item.quantity = quantity
                    cart_item.save()
                    messages.success(request, _(f"Quantity for '{cart_item.product.name}' updated."))
            elif quantity == 0:
                cart_item.delete()
                messages.info(request, _(f"'{cart_item.product.name}' removed from cart."))
            else:
                messages.error(request, _("Invalid quantity."))
        except (ValueError, TypeError):
            messages.error(request, _("Invalid quantity format."))
        return redirect('core:cart_detail')

    # AJAX request logic
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user, cart__ordered=False)
        data = json.loads(request.body)
        quantity = int(data.get('quantity'))

        if quantity < 1:
            return JsonResponse({'success': False, 'error': _('Quantity must be at least 1.')}, status=400)

        product_stock = cart_item.product.stock
        if product_stock is not None and quantity > product_stock:
            return JsonResponse({
                'success': False,
                'error': _('Not enough stock. Only {stock} items left.').format(stock=product_stock),
                'new_quantity': product_stock
            }, status=400)

        cart_item.quantity = quantity
        cart_item.save()

        cart = cart_item.cart
        return JsonResponse({
            'success': True,
            'message': _('Cart updated.'),
            'new_quantity': cart_item.quantity,
            'item_subtotal': f'{cart_item.get_total_item_price():,.2f}',
            'cart_total': f'{cart.get_cart_total():,.2f}',
            'cart_items_count': cart.get_item_count(),
        })

    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': _('Item not found.')}, status=404)
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'success': False, 'error': _('Invalid data.')}, status=400)
    except Exception as e:
        logger.error(f"AJAX Error updating cart item {item_id}: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': _('An unexpected error occurred.')}, status=500)


@login_required
def cart_detail(request):
    cart_data = get_cart_data(request.user)
    saved_for_later_items = SavedForLaterItem.objects.filter(user=request.user)

    # --- START: Augment cart items with booking details from session ---
    booking_details_session = request.session.get('booking_details', {})
    for item in cart_data['cart_items']:
        if item.service_package:
            item_details = booking_details_session.get(str(item.id))
            if item_details:
                item.booking_details = item_details
                # Optionally parse date for display
                date_str = item_details.get('preferred_start_date')
                if date_str:
                    try:
                        item.booking_details['preferred_start_date_obj'] = datetime.datetime.fromisoformat(date_str)
                    except (ValueError, TypeError):
                        item.booking_details['preferred_start_date_obj'] = None
    # --- END: Augment cart items with booking details from session ---

    context = {
        'cart_items': cart_data['cart_items'],
        'cart_total': cart_data['cart_total'],
        'saved_for_later_items': saved_for_later_items,
        'page_title': _("Your Shopping Cart"),
    }
    return render(request, 'core/cart_detail.html', context)

@login_required
@require_POST
def save_for_later(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    # Create or update a saved-for-later item
    saved_item, created = SavedForLaterItem.objects.get_or_create(
        user=request.user,
        product=cart_item.product,
        service_package=cart_item.service_package,
        defaults={'quantity': cart_item.quantity}
    )
    
    if not created:
        # If item already exists in saved list, we just add the quantity
        saved_item.quantity += cart_item.quantity
        saved_item.save()

    cart = cart_item.cart
    item_name = cart_item.name
    cart_item.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        image_url = settings.STATIC_URL + 'assets/img/placeholder.png'
        # Determine the image URL for the saved item
        if saved_item.product and saved_item.product.images.first():
            image_url = saved_item.product.images.first().image.url
        elif saved_item.service_package and saved_item.service_package.service.images.first():
            image_url = saved_item.service_package.service.images.first().image.url

        saved_item_data = {
            'id': saved_item.id,
            'name': saved_item.name,
            'price': f'{saved_item.price:,.2f}',
            'image_url': image_url,
            'quantity': saved_item.quantity,
        }
        saved_items_count = SavedForLaterItem.objects.filter(user=request.user).count()
        
        return JsonResponse({
            'success': True,
            'message': _("'{item_name}' moved to Saved for Later.").format(item_name=item_name),
            'cart_total': f'{cart.get_cart_total():,.2f}',
            'cart_items_count': cart.get_item_count(),
            'saved_item': saved_item_data,
            'saved_items_count': saved_items_count,
            'created_new_saved_item': created,
        })
    
    messages.success(request, _("'{item_name}' moved to Saved for Later.").format(item_name=item_name))
    return redirect('core:cart_detail')

@login_required
@require_POST
def move_to_cart(request, saved_item_id):
    saved_item = get_object_or_404(SavedForLaterItem, id=saved_item_id, user=request.user)
    cart, created = Cart.objects.get_or_create(user=request.user, ordered=False)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=saved_item.product,
        service_package=saved_item.service_package,
        defaults={'quantity': saved_item.quantity}
    )

    if not created:
        cart_item.quantity += saved_item.quantity
        if cart_item.product and cart_item.product.product_type == 'physical' and cart_item.quantity > cart_item.product.stock:
            error_message = _("Cannot move to cart. Not enough stock for '{item_name}'.").format(item_name=cart_item.name)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_message}, status=400)
            messages.error(request, error_message)
            return redirect('core:cart_detail')
        cart_item.save()

    item_name = saved_item.name
    saved_item.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': _("'{item_name}' moved to cart.").format(item_name=item_name)})

    messages.success(request, _("'{item_name}' moved to cart.").format(item_name=item_name))
    return redirect('core:cart_detail')

@login_required
@require_POST
def delete_saved_item(request, saved_item_id):
    saved_item = get_object_or_404(SavedForLaterItem, id=saved_item_id, user=request.user)
    item_name = saved_item.name
    saved_item.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': _("'{item_name}' removed from your saved items.").format(item_name=item_name)})
    messages.info(request, _("'{item_name}' removed from your saved items.").format(item_name=item_name))
    return redirect('core:cart_detail')

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
@require_POST
def reorder(request, order_id):
    """
    Adds all available items from a previous order to the user's current cart.
    """
    # 1. Find the original order, ensuring it belongs to the current user for security.
    original_order = get_object_or_404(Order, order_id=order_id, user=request.user)

    # 2. Get the user's current active cart.
    current_cart, _ = Cart.objects.get_or_create(user=request.user, ordered=False)

    added_count = 0
    unavailable_items = []

    # 3. Iterate through items in the original order.
    for item in original_order.items.all():
        # Determine if the item is a product or a service package
        target_item = item.product or item.service_package
        
        if not target_item:
            # This handles cases where the linked product/service has been deleted from the database.
            name = item.product_name or item.service_package_name or _("An item")
            unavailable_items.append(str(name))
            continue

        # Check if the product/service is still available for purchase.
        # We use getattr to safely get the value without calling it if it's a bool,
        # but handle it if it happens to be a method.
        is_active_attr = getattr(target_item, 'is_active', True)
        is_available = is_active_attr() if callable(is_active_attr) else is_active_attr

        if isinstance(target_item, Product):
            is_available = is_available and getattr(target_item, 'stock', 1) > 0
        
        if is_available:
            # 4. Add or update the item in the current cart.
            cart_item, created = CartItem.objects.get_or_create(
                cart=current_cart,
                product=item.product,
                service_package=item.service_package,
                defaults={'quantity': item.quantity}
            )

            if not created:
                # If the item was already in the cart, just add the quantity from the old order.
                cart_item.quantity += item.quantity
                cart_item.save()
            
            added_count += 1
        else:
            # Item is no longer available (e.g., out of stock, inactive).
            name_attr = 'name' if hasattr(target_item, 'name') else 'title'
            unavailable_items.append(getattr(target_item, name_attr, _("Unknown Item")))

    # 5. Provide clear feedback to the user.
    if added_count > 0:
        messages.success(request, _(f"{added_count} items from order #{original_order.order_id} have been added to your cart."))
    
    if unavailable_items:
        unavailable_list = ", ".join(unavailable_items)
        messages.warning(request, _(f"Some items could not be added as they are no longer available: {unavailable_list}"))
    
    if added_count == 0 and not unavailable_items:
        messages.info(request, _("There were no items in the original order to add."))

    return redirect('core:cart_detail')

@login_required
def checkout(request):
    cart_data = get_cart_data(request.user)
    if not cart_data['cart_items']:
        messages.info(request, _("Your cart is empty. Add some items to proceed to checkout."))
        return redirect('core:product_list') # Or home

    # --- START: Service Booking Details Logic ---
    service_booking_items = []
    booking_details_session = request.session.get('booking_details', {})
    for item in cart_data['cart_items']:
        if item.service_package:
            item_details = booking_details_session.get(str(item.id))
            if item_details:
                item.booking_details = item_details
                # Optionally parse date for display
                date_str = item_details.get('preferred_start_date')
                if date_str:
                    try:
                        # The date is stored as 'Y-m-d' string
                        item.booking_details['preferred_start_date_obj'] = datetime.date.fromisoformat(date_str)
                    except (ValueError, TypeError):
                        item.booking_details['preferred_start_date_obj'] = None
            service_booking_items.append(item)

    requires_service_location = len(service_booking_items) > 0
    # --- END: Service Booking Details Logic ---

    billing_addresses = Address.objects.filter(user=request.user, address_type='billing')
    shipping_addresses = Address.objects.filter(user=request.user, address_type='shipping')

    # Determine if shipping is required (e.g., if any cart item is physical)
    requires_shipping = any(item.product and item.product.product_type == 'physical' for item in cart_data['cart_items'])

    # --- START: Calculate Estimated Delivery Fees for Display ---
    estimated_platform_delivery_fee = Decimal('0.00')
    estimated_total_vendor_delivery_fees = Decimal('0.00')
    estimated_total_delivery_fee = Decimal('0.00')

    # For now, we'll assume the first shipping address is used for estimation if multiple exist.
    # A more robust solution might involve AJAX updates if the address changes on the page.
    default_shipping_address = shipping_addresses.filter(is_default=True).first() or shipping_addresses.first()

    if requires_shipping and default_shipping_address:
        estimated_platform_delivery_fee = calculate_shipping_cost(cart=cart_data['cart_items'][0].cart, shipping_address=default_shipping_address) # Pass the cart object

        for item in cart_data['cart_items']: # This loop is for vendor fees
            if item.product: # Only calculate for products
                product_fulfillment = item.product.fulfillment_method
                vendor_default_fulfillment = item.product.vendor.default_fulfillment_method if item.product.vendor else 'vendor'
                actual_fulfillment = product_fulfillment if product_fulfillment else vendor_default_fulfillment
                if actual_fulfillment == 'vendor' and item.product.product_type == 'physical' and item.product.vendor_delivery_fee is not None:
                    estimated_total_vendor_delivery_fees += item.product.vendor_delivery_fee # Assuming vendor_delivery_fee is per product line
    estimated_total_delivery_fee = estimated_platform_delivery_fee + estimated_total_vendor_delivery_fees
    # --- END: Calculate Estimated Delivery Fees for Display ---

    # --- START: Promotion Logic ---
    coupon_apply_form = CouponApplyForm()
    discount_amount = Decimal(request.session.get('discount_amount', '0.00'))
    promotion = None
    promotion_id = request.session.get('promotion_id')
    if promotion_id:
        try:
            promotion = Promotion.objects.get(id=promotion_id)
        except Promotion.DoesNotExist:
            if 'promotion_id' in request.session: del request.session['promotion_id']
            if 'discount_amount' in request.session: del request.session['discount_amount']
    # --- END: Promotion Logic ---
    
    # Calculate final total
    grand_total = cart_data['cart_total'] + estimated_total_delivery_fee - discount_amount

    context = {
        'cart_items': cart_data['cart_items'],
        'cart_total': cart_data['cart_total'],
        'billing_addresses': billing_addresses,
        'shipping_addresses': shipping_addresses,
        'service_booking_items': service_booking_items,
        'requires_service_location': requires_service_location,
        'address_form': AddressForm(), # For adding new addresses
        'requires_shipping': requires_shipping,
        'estimated_platform_delivery_fee': estimated_platform_delivery_fee,
        'estimated_total_vendor_delivery_fees': estimated_total_vendor_delivery_fees,
        'estimated_total_delivery_fee': estimated_total_delivery_fee,
        'coupon_apply_form': coupon_apply_form,
        'discount_amount': discount_amount,
        'grand_total': grand_total,
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

        requires_shipping = any(item.product and item.product.product_type == 'physical' for item in cart_items_qs)
        requires_service_location = any(item.service_package for item in cart_items_qs)

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

            service_location_address = None
            if requires_service_location:
                use_billing_for_service = request.POST.get('use_billing_for_service_location') == 'on'
                if use_billing_for_service:
                    service_location_address = billing_address
                else:
                    service_location_address_id = request.POST.get('service_location_address_id')
                    if not service_location_address_id:
                        messages.error(request, _("A service location address is required."))
                        return redirect('core:checkout')
                    # An address saved for shipping can be used for service location
                    service_location_address = get_object_or_404(Address, id=service_location_address_id, user=request.user)

        except (Address.DoesNotExist, ValueError, TypeError) as e:
            logger.error(f"Address selection error in place_order: {e}")
            messages.error(request, _("Invalid address selected. Please try again."))
            return redirect('core:checkout')

        # Calculate cart subtotal (sum of item.price * item.quantity)
        cart_subtotal = user_cart.get_cart_total()

        # --- Get promotion from session and re-validate ---
        promotion_id = request.session.get('promotion_id')
        discount_amount = Decimal(request.session.get('discount_amount', '0.00'))
        promotion = None
        if promotion_id:
            try:
                # Lock the promotion row to prevent race conditions on usage_count
                promotion = Promotion.objects.select_for_update().get(id=promotion_id)
                # Re-validate usage limit just before placing the order
                if promotion.usage_limit is not None and promotion.usage_count >= promotion.usage_limit:
                    messages.error(request, _("Sorry, the coupon '{code}' has just reached its usage limit.").format(code=promotion.code))
                    # Clear from session and redirect
                    if 'promotion_id' in request.session: del request.session['promotion_id']
                    if 'discount_amount' in request.session: del request.session['discount_amount']
                    return redirect('core:checkout')
            except Promotion.DoesNotExist:
                # If promo was deleted, ensure discount is zero
                discount_amount = Decimal('0.00')
        # --- End promotion handling ---

        # --- Initialize delivery fee components ---
        platform_calculated_delivery_fee = Decimal('0.00')
        current_order_item_total_delivery_charges = Decimal('0.00') # This will sum up vendor-set fees

        # Calculate platform delivery fee for Nexus-fulfilled items
        if requires_shipping:
            # calculate_shipping_cost now internally filters for Nexus-fulfilled items
            platform_calculated_delivery_fee = calculate_shipping_cost(user_cart, shipping_address)

        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Determine currency from session or default
        currency_code = request.session.get('currency_code', getattr(settings, 'DEFAULT_CURRENCY_CODE', 'GBP'))


        order = Order.objects.create(
            user=request.user,
            billing_address=billing_address,
            shipping_address=shipping_address if requires_shipping else None,
            delivery_fee=Decimal('0.00'), # Initialize, will be updated after items
            total_amount=Decimal('0.00'),   # Initialize, will be updated after items
            platform_delivery_fee=platform_calculated_delivery_fee, # Store the Gowbuy part
            promotion=promotion, # Link the promotion
            discount_amount=discount_amount, # Store the discount
            currency=currency_code, # Set currency based on session
            payment_method=payment_method_choice,
            status='PENDING',
            ip_address=ip
        )

        # --- START: Pre-validation for service availability ---
        booking_details_session = request.session.get('booking_details', {})
        for cart_item in cart_items_qs:
            if cart_item.service_package:
                item_booking_details = booking_details_session.get(str(cart_item.id))
                if item_booking_details and item_booking_details.get('availability_slot_id'):
                    slot_id = item_booking_details.get('availability_slot_id')
                    try:
                        # Lock the row for update to prevent race conditions
                        slot = ServiceAvailability.objects.select_for_update().get(id=slot_id)
                        if slot.is_booked:
                            messages.error(request, _("Sorry, the time slot for '{service}' has just been booked by someone else. Please remove it from your cart and select a new time.").format(service=cart_item.name))
                            # No need to delete order, it's in a transaction that will be rolled back
                            return redirect('core:cart_detail')
                    except ServiceAvailability.DoesNotExist:
                        messages.error(request, _("Sorry, a selected time slot for '{service}' no longer exists. Please remove it from your cart and select a new one.").format(service=cart_item.name))
                        return redirect('core:cart_detail')
        # --- END: Pre-validation for service availability ---

        for cart_item in cart_items_qs:
            if cart_item.product:
                # --- Handle Product Items ---
                product_fulfillment = cart_item.product.fulfillment_method
                vendor_default_fulfillment = cart_item.product.vendor.default_fulfillment_method if cart_item.product.vendor else 'vendor'
                actual_fulfillment = product_fulfillment if product_fulfillment else vendor_default_fulfillment

                item_specific_delivery_charge = Decimal('0.00')
                if actual_fulfillment == 'vendor' and cart_item.product.product_type == 'physical' and cart_item.product.vendor_delivery_fee is not None:
                    item_specific_delivery_charge = cart_item.product.vendor_delivery_fee

                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    fulfillment_method=actual_fulfillment,
                    item_delivery_charge=item_specific_delivery_charge
                )
                current_order_item_total_delivery_charges += item_specific_delivery_charge

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
            
            elif cart_item.service_package:
                # --- Handle Service Items ---
                service_pkg = cart_item.service_package
                order_item = OrderItem.objects.create( # Assign to variable
                    order=order,
                    service_package=service_pkg,
                    quantity=cart_item.quantity,
                    price=service_pkg.price,
                    provider=service_pkg.service.provider,
                    # Services don't have delivery charges in this model
                    item_delivery_charge=Decimal('0.00'),
                    # Services are fulfilled by the provider, equivalent to 'vendor' fulfillment
                    fulfillment_method='vendor' 
                )
                # --- START: Create ServiceBooking from session data ---
                booking_details_session = request.session.get('booking_details', {})
                item_booking_details = booking_details_session.get(str(cart_item.id))
                
                start_date = None
                availability_slot_id = None

                if item_booking_details:
                    availability_slot_id = item_booking_details.get('availability_slot_id')
                    date_str = item_booking_details.get('preferred_start_date')
                    if date_str:
                        # Convert ISO format string back to datetime object
                        try:
                            start_date = datetime.date.fromisoformat(date_str)
                        except (ValueError, TypeError):
                            start_date = None # Handle malformed date string

                    # --- Mark the availability slot as booked ---
                    if availability_slot_id:
                        try:
                            # We already locked and checked this slot above, so we can just update it.
                            slot_to_book = ServiceAvailability.objects.get(id=availability_slot_id)
                            slot_to_book.is_booked = True
                            slot_to_book.save(update_fields=['is_booked'])
                            logger.info(f"ServiceAvailability slot {slot_to_book.id} marked as booked for Order {order.order_id}.")
                        except ServiceAvailability.DoesNotExist:
                            # This case should be caught by the pre-validation loop.
                            # If it happens, it's an issue, but the transaction will roll back.
                            logger.error(f"Could not find ServiceAvailability slot {availability_slot_id} to mark as booked during order placement for Order {order.order_id}.")
                            # The transaction will rollback, so no inconsistent state is saved.
                            messages.error(request, _("An error occurred with a booking time slot. Please try again."))
                            return redirect('core:cart_detail')

                    ServiceBooking.objects.create(
                        order=order,
                        service_package=service_pkg,
                        user=request.user,
                        provider=service_pkg.service.provider,
                        preferred_start_date=start_date,
                        location_address=service_location_address, # Assumes ServiceBooking model has a ForeignKey to Address
                        specific_requirements=item_booking_details.get('specific_requirements', ''),
                        status='PENDING' # Initial status for a new booking
                    )
                else:
                    # Fallback if no details found in session (e.g., session expired)
                    # Still create a basic booking record
                    ServiceBooking.objects.create(
                        order=order,
                        service_package=service_pkg,
                        user=request.user,
                        provider=service_pkg.service.provider,
                        location_address=service_location_address, # Assumes ServiceBooking model has a ForeignKey to Address
                        status='PENDING'
                    )
                    logger.warning(f"No booking details found in session for CartItem {cart_item.id}. Created a basic ServiceBooking for Order {order.order_id}.")
                # --- END: Create ServiceBooking from session data ---
                # No stock to decrement for services

            else:
                logger.warning(f"CartItem {cart_item.id} in cart {user_cart.id} has neither a product nor a service. Skipping.")

        # Now update the order's total delivery fee and total amount
        order.delivery_fee = order.platform_delivery_fee + current_order_item_total_delivery_charges
        order.total_amount = cart_subtotal + order.delivery_fee - order.discount_amount
        order.save(update_fields=['delivery_fee', 'total_amount', 'platform_delivery_fee', 'promotion', 'discount_amount'])

        # --- Increment promotion usage count if applicable ---
        if promotion:
            # Use F() expression for a race-condition-safe increment
            promotion.usage_count = F('usage_count') + 1
            promotion.save(update_fields=['usage_count'])

        # --- Fraud Detection ---
        fraud_check_result = calculate_fraud_score(order)
        if fraud_check_result["score"] >= 50: # Threshold can be adjusted
            FraudReport.objects.create(
                order=order,
                risk_score=fraud_check_result["score"],
                reasons=fraud_check_result["reasons"]
            )
            order.status = 'ON_HOLD_FRAUD_REVIEW'
            order.save(update_fields=['status'])
            messages.warning(request, _("Your order has been placed and is currently under review. You will be notified shortly."))
            return redirect(order.get_absolute_url())

        user_cart.ordered = True
        user_cart.save()

        # --- START: Clean up all booking details from session after order is placed ---
        if 'booking_details' in request.session:
            del request.session['booking_details']
        # --- Clean up promotion from session ---
        if 'promotion_id' in request.session:
            del request.session['promotion_id']
        if 'discount_amount' in request.session:
            del request.session['discount_amount']
        # --- END: Clean up all booking details from session ---

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
                # If 'direct' is chosen for a non-negotiable order, route it to the standard online payment.
                messages.warning(request, _("This order requires online payment. You will be redirected to our secure payment page."))
                order.payment_method = 'card' # Change to a valid online method
                order.status = 'AWAITING_ESCROW_PAYMENT'
                order.save(update_fields=['payment_method', 'status'])
                return redirect('core:initiate_stripe_payment', order_id=order.id)

        # This now handles 'escrow' (legacy), 'card', and 'digital_wallet'
        elif order.payment_method in ['escrow', 'card', 'digital_wallet']:
            order.status = 'AWAITING_ESCROW_PAYMENT'
            order.save(update_fields=['status'])
            # The message is now generic as Stripe handles the specific method display
            messages.info(request, _("Please proceed to our secure payment page for order {order_id}.").format(order_id=order.order_id))
            return redirect('core:initiate_stripe_payment', order_id=order.id)

        elif order.payment_method == 'bank_transfer':
            order.status = 'AWAITING_BANK_TRANSFER'
            order.save(update_fields=['status'])
            messages.info(request, _("Please complete your bank transfer using the details provided below."))
            return redirect('core:order_detail', order_id=order.order_id)
        else:
            messages.error(request, _("There was an issue with your order's payment method. Please contact support."))
            return redirect(order.get_absolute_url())

    else:
        messages.error(request, _("Invalid request method."))
        return redirect('core:checkout')


@login_required
def add_checkout_address(request):
    if request.method == 'POST':
        address_type = request.POST.get('address_type', 'billing')  # Default to billing if not provided
        
        form = AddressForm(request.POST)

        if form.is_valid():
            # Pass the user to the form's save method
            address = form.save(commit=False, user=request.user)
            address.user = request.user
            address.address_type = address_type  # Set address_type from POST data

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
        context['active_page'] = 'orders'
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

        # --- Bank Transfer Info ---
        if order.status == 'AWAITING_BANK_TRANSFER':
            context['bank_transfer_info'] = {
                'bank_name': 'GOWBUY Corporate Bank',
                'account_name': 'Gowbuy Marketplace Ltd.',
                'account_number': '1234567890',
                'sort_code': '00-11-22',
                'reference': order.order_id
            }

        # --- Add Map Data for Customer ---
        # Find a relevant delivery task for this order (e.g., the first Gowbuy-fulfilled one)
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
        messages.info(request, _("Please proceed to our secure payment page."))
        return redirect('core:initiate_stripe_payment', order_id=order.id)

    elif payment_method_choice == 'direct':
        order.status = 'AWAITING_DIRECT_PAYMENT'
        order.save()
        messages.success(request, _("You've chosen Direct Arrangement. Please contact the service provider to arrange payment. Your order status has been updated."))
        return redirect('core:order_detail', order_id=order.order_id)

    elif payment_method_choice == 'paypal':
        order.status = 'AWAITING_ESCROW_PAYMENT' # Use same status as Paystack
        order.save()
        messages.info(request, _("Please proceed to make your payment via PayPal."))
        return redirect('core:process_payment', order_id=order.id)

    elif payment_method_choice in ['card', 'digital_wallet']:
        order.status = 'AWAITING_ESCROW_PAYMENT' # Using Stripe for cards
        order.save()
        return redirect('core:initiate_stripe_payment', order_id=order.id)

    elif payment_method_choice == 'bank_transfer':
        order.status = 'AWAITING_BANK_TRANSFER'
        order.save()
        messages.info(request, _("Please complete your bank transfer using the details provided below."))
        return redirect('core:order_detail', order_id=order.order_id)

    else:
        messages.error(request, _("An unexpected error occurred. Please try again."))
        return redirect('core:order_detail', order_id=order.order_id)

@login_required
def initiate_stripe_payment(request, order_id):
    """
    Initiates a Stripe Checkout Session for the order.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status != 'AWAITING_ESCROW_PAYMENT':
        messages.error(request, _("This order is not eligible for payment at this time."))
        return redirect('core:order_detail', order_id=order.order_id)

    # Ensure Stripe API key is set
    if not settings.STRIPE_SECRET_KEY:
        logger.critical("STRIPE_SECRET_KEY is missing in settings.")
        messages.error(request, _("Payment gateway configuration error. Please contact support."))
        return redirect('core:order_detail', order_id=order.order_id)
    
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        # Create a checkout session
        # We use a single line item for the total to avoid rounding discrepancies with discounts/taxes
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card', 'klarna', 'amazon_pay'],
            line_items=[{
                'price_data': {
                    'currency': order.currency.lower(),
                    'product_data': {
                        'name': f'Order #{order.order_id}',
                        'description': _('Payment for order on GOWBUY Marketplace'),
                    },
                    'unit_amount': int(order.total_amount * 100), # Stripe expects amount in cents/pence
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('core:stripe_payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('core:stripe_payment_cancel')),
            client_reference_id=order.order_id,
            customer_email=request.user.email,
            metadata={
                'order_id': order.id,
                'user_id': request.user.id
            }
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        logger.error(f"Stripe initialization error: {e}")
        print(f"STRIPE ERROR: {e}") # Debug print for Render logs
        messages.error(request, _("Could not connect to payment gateway. Please try again later."))
        return redirect('core:order_detail', order_id=order.order_id)

@login_required
def stripe_payment_success(request):
    session_id = request.GET.get('session_id')
    if session_id:
        # In a production app, you might verify the session via API here or rely on Webhooks
        # For immediate UI feedback, we assume success if redirected here with an ID
        messages.success(request, _("Payment successful! Your order is being processed."))
        # You might want to retrieve the order based on session client_reference_id if not in session
        # For now, redirecting to order history is safe
        return redirect('core:order_history')
    return redirect('core:home')

@login_required
def stripe_payment_cancel(request):
    messages.warning(request, _("Payment process was cancelled."))
    return redirect('core:order_history')

def _fulfill_stripe_order(session):
    """Helper to fulfill order upon successful Stripe payment."""
    client_reference_id = session.get('client_reference_id')
    if client_reference_id:
        try:
            order = Order.objects.get(order_id=client_reference_id)
            
            # Only update if not already processed
            if order.status == 'AWAITING_ESCROW_PAYMENT':
                order.status = 'PROCESSING'
                order.transaction_id = session.get('payment_intent')
                order.save(update_fields=['status', 'transaction_id'])
                
                # Record the transaction
                Transaction.objects.create(
                    user=order.user, order=order, transaction_type='payment',
                    amount=Decimal(session.get('amount_total', 0)) / 100, # Convert cents to main currency unit
                    currency=session.get('currency', 'usd').upper(), status='completed',
                    gateway_transaction_id=session.get('payment_intent'),
                    description=f"Stripe Payment for Order {order.order_id}"
                )
                logger.info(f"Order {order.order_id} updated via Stripe Webhook.")
        except Order.DoesNotExist:
            logger.error(f"Order {client_reference_id} not found during Stripe webhook.")

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handles Stripe webhooks to securely update order status.
    Supports multiple signing secrets for different events.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    # Collect all configured secrets
    secrets = []
    if getattr(settings, 'STRIPE_WEBHOOK_SECRET', None):
        secrets.append(settings.STRIPE_WEBHOOK_SECRET)
    if getattr(settings, 'STRIPE_WEBHOOK_SECRET_ASYNC_FAILED', None):
        secrets.append(settings.STRIPE_WEBHOOK_SECRET_ASYNC_FAILED)
    if getattr(settings, 'STRIPE_WEBHOOK_SECRET_ASYNC_SUCCEEDED', None):
        secrets.append(settings.STRIPE_WEBHOOK_SECRET_ASYNC_SUCCEEDED)

    if not secrets:
        logger.error("No STRIPE_WEBHOOK_SECRETS configured in settings.")
        return HttpResponse("Webhook secrets not configured", status=400)

    event = None

    # Try to verify signature with each secret until one works
    for secret in secrets:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, secret)
            break # Verification successful
        except stripe.error.SignatureVerificationError:
            continue # Try next secret
        except ValueError:
            return HttpResponse(status=400) # Invalid payload
            
    if event is None:
        logger.warning("Stripe webhook signature verification failed for all configured secrets.")
        return HttpResponse(status=400)

    # 1. Handle Immediate Success (e.g., Cards)
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Only fulfill if payment is actually 'paid'. 
        # If it's 'unpaid', it means it's a delayed method (handled below).
        if session.get('payment_status') == 'paid':
            _fulfill_stripe_order(session)

    # 2. Handle Delayed Success (e.g., Bank Transfers clearing days later)
    elif event['type'] == 'checkout.session.async_payment_succeeded':
        session = event['data']['object']
        _fulfill_stripe_order(session)

    # 3. Handle Delayed Failure (e.g., Insufficient funds days later)
    elif event['type'] == 'checkout.session.async_payment_failed':
        session = event['data']['object']
        # Log the failure
        logger.warning(f"Async payment failed for session {session.get('id')}")
        # Optional: You could add logic here to email the user asking them to retry

    return HttpResponse(status=200)

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
def vendor_generate_packing_slip(request, pk):
    """
    Generates and serves a PDF packing slip for a vendor's specific order.
    """
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        return HttpResponseForbidden(_("You are not a registered vendor."))

    order = get_object_or_404(Order, pk=pk)
    vendor_items = order.items.filter(product__vendor=vendor)
    if not vendor_items.exists():
        return HttpResponseForbidden(_("You do not have permission to generate a packing slip for this order."))

    context = {'order': order, 'vendor_items': vendor_items, 'vendor': vendor}
    html = render_to_string('core/vendor/packing_slip.html', context)
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)
    if pisa_status.err:
        return HttpResponse("Error generating PDF")
    pdf_buffer.seek(0)
    return FileResponse(pdf_buffer, as_attachment=False, filename=f'packing_slip_{order.order_id}.pdf')

def _generate_customer_invoice_pdf(order: Order) -> Optional[BytesIO]:
    """
    Renders the customer invoice HTML to a PDF and returns it in a BytesIO buffer.
    Returns None on failure.
    """
    try:
        html = render_to_string('core/customer_invoice.html', {'order': order})
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)
        if pisa_status.err:
            logger.error(f"PDF generation failed for order {order.order_id}. Error: {pisa_status.err}")
            return None
        pdf_buffer.seek(0)
        return pdf_buffer
    except Exception as e:
        logger.error(f"An unexpected error occurred during PDF generation for order {order.order_id}: {e}", exc_info=True)
        return None


@login_required
def download_invoice(request, order_id):
    """
    Generates and serves a PDF invoice for a customer's specific order.
    """
    order = get_object_or_404(Order, order_id=order_id)

    # Security check: ensure the user is the owner of the order or staff
    if not (request.user == order.user or request.user.is_staff):
        messages.error(request, _("You do not have permission to view this invoice."))
        return redirect('core:order_history')

    pdf_buffer = _generate_customer_invoice_pdf(order)

    if not pdf_buffer:
        messages.error(request, _("There was an error generating the invoice PDF. Please try again later."))
        return redirect('core:order_detail', order_id=order.order_id)

    # --- Email the invoice ---
    try:
        if request.user.email:
            subject = _("Your GOWBUY Invoice for Order #{}").format(order.order_id)
            # Context for email template
            email_context = {
                'user': request.user,
                'order': order,
                'order_url': request.build_absolute_uri(order.get_absolute_url())
            }
            html_message = render_to_string('core/customer_invoice_email.html', email_context)
            
            email = EmailMessage(
                subject,
                html_message,
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
            )
            email.content_subtype = "html" # Main content is now text/html
            email.attach(f'invoice_{order.order_id}.pdf', pdf_buffer.getvalue(), 'application/pdf')
            email.send(fail_silently=True)
    except Exception as e:
        logger.error(f"Failed to email invoice for order {order.order_id}: {e}")

    # Reset buffer position for FileResponse
    pdf_buffer.seek(0)
    return FileResponse(pdf_buffer, as_attachment=True, filename=f'invoice_{order.order_id}.pdf')


@login_required
@require_POST
def cancel_order(request, order_id):
    """
    Allows a customer to cancel their order if it hasn't been shipped yet.
    """
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Define statuses that allow cancellation
    cancellable_statuses = ['PENDING', 'AWAITING_ESCROW_PAYMENT', 'AWAITING_BANK_TRANSFER', 'AWAITING_DIRECT_PAYMENT', 'PROCESSING']
    
    if order.status in cancellable_statuses:
        order.status = 'CANCELLED'
        order.save(update_fields=['status'])
        
        # Restore stock for physical products
        for item in order.items.all():
            if item.product and item.product.product_type == 'physical':
                Product.objects.filter(pk=item.product.pk).update(stock=F('stock') + item.quantity)

        messages.success(request, _("Order #{} has been cancelled successfully.").format(order.order_id))
    else:
        messages.error(request, _("This order cannot be cancelled because it has already been shipped or completed."))
        
    return redirect('core:order_detail', order_id=order.order_id)

@login_required
@require_POST
def customer_email_invoice(request, order_id):
    """
    Generates a PDF invoice and emails it to the customer.
    """
    order = get_object_or_404(Order, order_id=order_id)

    # Security check
    if not (request.user == order.user or request.user.is_staff):
        messages.error(request, _("You do not have permission to email this invoice."))
        return redirect('core:order_history')

    if not request.user.email:
        messages.error(request, _("Your profile does not have an email address to send the invoice to."))
        return redirect('core:order_detail', order_id=order.order_id)

    # Use the utility function from utils.py to generate and send the invoice
    # This centralizes the logic and makes it reusable.
    if generate_invoice_pdf(order=order, user=request.user, request=request):
        messages.success(request, _("The invoice has been sent to {email}.").format(email=request.user.email))
    else:
        messages.error(request, _("There was a problem sending the email. Please try again."))

    return redirect('core:order_detail', order_id=order.order_id)


@login_required
@require_POST
def submit_payment_proof(request, order_id):
    """
    Allows customers to submit a transaction reference for manual bank transfers.
    Does NOT automatically approve the order to prevent fraud.
    """
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    if order.status != 'AWAITING_BANK_TRANSFER':
        messages.error(request, _("This order is not awaiting bank transfer payment."))
        return redirect('core:order_detail', order_id=order.order_id)
        
    reference = request.POST.get('payment_reference')
    if not reference:
        messages.error(request, _("Please provide a payment reference."))
        return redirect('core:order_detail', order_id=order.order_id)
        
    # Store the reference provided by the user
    order.transaction_id = reference
    # NOTE: We do NOT change status to 'PROCESSING' here. 
    # Fraud Prevention: Admin must verify funds in bank before changing status.
    order.save(update_fields=['transaction_id'])
    
    # --- Send Admin Notification ---
    try:
        User = get_user_model()
        staff_emails = list(User.objects.filter(is_staff=True, is_active=True).exclude(email='').values_list('email', flat=True))
        
        if staff_emails:
            subject = _("New Payment Proof: Order #{}").format(order.order_id)
            admin_url = request.build_absolute_uri(reverse('admin:core_order_change', args=[order.id]))
            
            body = _(
                "User {username} has submitted a payment proof for Order #{order_id}.\n\n"
                "Transaction Reference: {reference}\n"
                "Amount: {currency} {amount}\n\n"
                "Please verify the payment in the bank account and approve the order here:\n{admin_url}"
            ).format(
                username=request.user.username,
                order_id=order.order_id,
                reference=reference,
                currency=order.currency,
                amount=order.total_amount,
                admin_url=admin_url
            )
            
            email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, staff_emails)
            email.send(fail_silently=True)
            logger.info(f"Admin notification sent for payment proof on Order {order.order_id}")
    except Exception as e:
        logger.error(f"Failed to send admin notification for payment proof (Order {order.order_id}): {e}")
    
    messages.success(request, _("Payment reference submitted! We will verify the transfer and process your order shortly."))
    return redirect('core:order_detail', order_id=order.order_id)


@login_required
def initiate_paystack_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_method not in ['escrow', 'card', 'digital_wallet', 'bank_transfer'] or \
       order.status not in ['AWAITING_ESCROW_PAYMENT', 'AWAITING_BANK_TRANSFER']:
        messages.error(request, _("This order is not eligible for Paystack payment at this time."))
        return redirect('core:order_detail', order_id=order.order_id)

    # --- START: Add check for Paystack secret key ---
    if not settings.PAYSTACK_SECRET_KEY:
        logger.critical("PAYSTACK_SECRET_KEY is not configured in settings. Payment cannot proceed.")
        messages.error(request, _("The payment gateway is not configured correctly. Please contact support."))
        return redirect('core:order_detail', order_id=order.order_id)
    # --- END: Add check for Paystack secret key ---

    url = "https://api.paystack.co/transaction/initialize"
    amount_in_kobo = int(order.total_amount * 100)

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "email": request.user.email,
        "amount": amount_in_kobo,
        "currency": order.currency,
        "reference": order.paystack_ref or f"GOWBUY_ORD_{order.order_id}_{uuid.uuid4().hex[:6]}",
        "callback_url": request.build_absolute_uri(reverse('core:paystack_callback')),
        "metadata": {
            "order_id": str(order.order_id),
            "user_id": str(request.user.id),
            "description": f"Payment for Order #{order.order_id}"
        }
    }

    # Temporarily disable channel restriction to avoid 400 Bad Request errors if unsupported
    # if order.payment_method == 'bank_transfer':
    #     payload['channels'] = ['bank_transfer']

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
        if e.response is not None:
            logger.error(f"Paystack Error Response: {e.response.text}")
        print(f"PAYSTACK ERROR: {e}") # Debug print for Render logs
        messages.error(request, _("Could not connect to payment gateway. Please try again later."))

    return redirect('core:order_detail', order_id=order.order_id)

@login_required
def initiate_plan_payment(request, plan_id):
    """
    Initiates payment for a vendor subscription plan via Paystack.
    """
    plan = get_object_or_404(PricingPlan, id=plan_id, is_active=True)
    vendor = get_object_or_404(Vendor, user=request.user)

    # --- START: Add check for Paystack secret key ---
    if not settings.PAYSTACK_SECRET_KEY:
        logger.critical("PAYSTACK_SECRET_KEY is not configured in settings. Payment cannot proceed.")
        messages.error(request, _("The payment gateway is not configured correctly. Please contact support."))
        return redirect('core:vendor_upgrade')
    # --- END: Add check for Paystack secret key ---

    url = "https://api.paystack.co/transaction/initialize"
    amount_in_kobo = int(plan.price * 100)
    reference = f"GOWBUY-PLAN-{plan.id}-{vendor.id}-{uuid.uuid4().hex[:6]}"

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": request.user.email,
        "amount": amount_in_kobo,
        "currency": plan.currency,
        "reference": reference,
        "callback_url": request.build_absolute_uri(reverse('core:plan_payment_callback')),
        "metadata": {
            "plan_id": plan.id,
            "vendor_id": vendor.id,
            "user_id": request.user.id,
            "type": "vendor_plan_purchase"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("status"):
            Transaction.objects.create(
                user=request.user,
                transaction_type='vendor_plan_purchase',
                amount=plan.price,
                currency=plan.currency,
                status='pending',
                gateway_transaction_id=reference,
                description=f"Payment for plan '{plan.name}' by vendor '{vendor.name}'."
            )
            authorization_url = response_data["data"]["authorization_url"]
            return redirect(authorization_url)
        else:
            messages.error(request, _("Could not initialize payment: {error}").format(error=response_data.get("message", "Unknown error")))
    except requests.exceptions.RequestException as e:
        logger.error(f"Paystack API request failed for plan payment: {e}")
        print(f"PAYSTACK PLAN ERROR: {e}") # Debug print for Render logs
        messages.error(request, _("Could not connect to payment gateway. Please try again later."))

    return redirect('core:vendor_upgrade')

def search_results(request):
    query = request.GET.get('q', '')
    product_results = Product.objects.filter(is_active=True, vendor__is_approved=True)
    if query:
        product_results = product_results.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query)
        ).distinct()

    context = {'products': product_results, 'query': query}
    return render(request, 'core/search_results.html', context)

def compare_products(request):
    """
    View to compare products.
    Retrieves product IDs from URL query parameters (e.g., ?ids=1,2,3).
    """
    ids_str = request.GET.get('ids', '')
    product_list = []

    if ids_str:
        try:
            # Parse IDs, ensuring they are integers
            ids = [int(i) for i in ids_str.split(',') if i.strip().isdigit()]
            
            if ids:
                # Fetch products corresponding to the IDs
                products = Product.objects.filter(id__in=ids, is_active=True)
                
                # Preserve the order of IDs as passed in the URL
                products_dict = {p.id: p for p in products}
                for pid in ids:
                    if pid in products_dict:
                        product_list.append(products_dict[pid])
        except Exception as e:
            logger.error(f"Error parsing product IDs for comparison: {e}")

    context = {
        'products': product_list,
        'page_title': _("Compare Products"),
    }
    return render(request, 'core/compare_products.html', context)

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
                if order.status in ['AWAITING_ESCROW_PAYMENT', 'AWAITING_BANK_TRANSFER']:
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

@csrf_exempt
def plan_payment_callback(request):
    """
    Callback URL for Paystack to verify vendor plan payments.
    """
    reference = request.GET.get('reference')
    if not reference:
        messages.error(request, _("Payment reference not found in callback."))
        return redirect('core:vendor_upgrade')

    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("status") and response_data["data"]["status"] == "success":
            transaction = get_object_or_404(Transaction, gateway_transaction_id=reference)
            metadata = response_data["data"].get("metadata", {})
            vendor_id = metadata.get("vendor_id")
            plan_id = metadata.get("plan_id")

            if transaction.status == 'pending':
                with transaction.atomic():
                    transaction.status = 'completed'
                    transaction.save(update_fields=['status'])
                    vendor = get_object_or_404(Vendor, id=vendor_id)
                    plan = get_object_or_404(PricingPlan, id=plan_id)
                    if "3d" in plan.name.lower():
                        vendor.has_premium_3d_generation_access = True
                        vendor.save(update_fields=['has_premium_3d_generation_access'])
                    messages.success(request, _("Your payment was successful and your plan has been activated!"))
            else:
                messages.info(request, _("This payment has already been processed."))
            return redirect('core:vendor_dashboard')
        else:
            messages.error(request, _("Payment verification failed. If you were charged, please contact support."))
    except (requests.exceptions.RequestException, Transaction.DoesNotExist, Vendor.DoesNotExist, PricingPlan.DoesNotExist) as e:
        logger.error(f"Error in plan_payment_callback for reference {reference}: {e}")
        messages.error(request, _("An error occurred during payment confirmation. Please contact support."))
    return redirect('core:vendor_upgrade')

@login_required
def user_profile_view(request):
    profile_owner = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=profile_owner)
    user_preferences, created = UserPreferences.objects.get_or_create(user=profile_owner)

    # --- Email Verification Status ---
    # This will be used to show verification status and management links on the profile.
    primary_email_obj = EmailAddress.objects.get_primary(profile_owner)
    is_email_verified = primary_email_obj.verified if primary_email_obj else False

    # --- 2FA Status Check ---
    # Check which 2FA methods are enabled for the user to display in the dashboard.
    authenticators = Authenticator.objects.filter(user=profile_owner)
    has_totp_enabled = authenticators.filter(type=Authenticator.Type.TOTP).exists()
    has_fido_enabled = authenticators.filter(type=Authenticator.Type.WEBAUTHN).exists()
    has_any_2fa_enabled = has_totp_enabled or has_fido_enabled

    # --- Profile Completeness Calculation ---
    # Fields to check for completeness in CustomUser and UserProfile
    completeness_fields = {
        'first_name': profile_owner.first_name,
        'last_name': profile_owner.last_name,
        'email': profile_owner.email,
        'profile_picture': user_profile.profile_picture,
        'bio': user_profile.bio,
        'date_of_birth': user_profile.date_of_birth,
        'phone_number': user_profile.phone_number,
        'location': user_profile.location,
        'website_url': user_profile.website_url,
        'linkedin_url': user_profile.linkedin_url,
        'twitter_url': user_profile.twitter_url,
        'github_url': user_profile.github_url,
    }

    total_fields = len(completeness_fields)
    completed_fields = sum(1 for field_value in completeness_fields.values() if field_value)
    profile_completeness = int((completed_fields / total_fields) * 100) if total_fields > 0 else 0

    # --- Fetch Recent Orders for Dashboard ---
    # --- Determine Next Step for Profile Completion ---
    next_step_text = ''
    next_step_url = ''
    if not user_profile.profile_picture:
        next_step_text = _("Add a profile picture")
        next_step_url = reverse('core:edit_user_profile')
    elif not user_profile.phone_number:
        next_step_text = _("Add your phone number")
        next_step_url = reverse('core:edit_user_profile')
    elif not Address.objects.filter(user=profile_owner).exists():
        next_step_text = _("Add an address")
        next_step_url = reverse('core:address_list')
    elif not user_profile.bio:
        next_step_text = _("Write a short bio")
        next_step_url = reverse('core:edit_user_profile')
    recent_orders = Order.objects.filter(user=profile_owner).order_by('-created_at')[:5]

    # --- Fetch Recent Reviews for Dashboard ---
    product_reviews = ProductReview.objects.filter(user=profile_owner).select_related('product').order_by('-created_at')[:3]
    vendor_reviews = VendorReview.objects.filter(user=profile_owner).select_related('vendor').order_by('-created_at')[:3]
    service_reviews = ServiceReview.objects.filter(user=profile_owner).select_related('service', 'service__provider').order_by('-created_at')[:3]

    # Combine and sort all recent reviews by creation date
    all_recent_reviews = sorted(
        chain(product_reviews, vendor_reviews, service_reviews),
        key=attrgetter('created_at'),
        reverse=True
    )[:5] # Limit to a total of 5 recent reviews on the dashboard

    # --- Wishlist Summary ---
    wishlist, created = Wishlist.objects.get_or_create(user=profile_owner)
    wishlist_summary_items = wishlist.products.all()[:3] # Get first 3 items
    wishlist_total_count = wishlist.products.count()

    # --- Loyalty Points ---
    user_points, created = UserPoints.objects.get_or_create(user=profile_owner)
    user_points_balance = user_points.points_balance
    # --- Check for other user roles ---
    # --- START: New context data for added sections ---

    # --- Fetch Default Addresses ---
    default_billing_address = Address.objects.filter(user=profile_owner, address_type='billing', is_default=True).first()
    default_shipping_address = Address.objects.filter(user=profile_owner, address_type='shipping', is_default=True).first()

    # --- Fetch Saved Payment Methods (Placeholder) ---
    # In a real application, this would come from your payment gateway's vault.
    # For demonstration, we'll create a dummy list.
    saved_payment_methods = [
        {'card_type': 'visa', 'last4': '4242', 'exp_month': '12', 'exp_year': '2025'},
        {'card_type': 'mastercard', 'last4': '5555', 'exp_month': '08', 'exp_year': '2026'},
    ]

    # --- Fetch Digital Products ---
    # Find all order items for this user where the product is digital and the order is complete.
    # Using a database-agnostic method to get distinct products, as DISTINCT ON is not supported by all backends.
    all_digital_order_items = OrderItem.objects.filter(
        order__user=profile_owner,
        product__product_type='digital',
        order__status__in=['COMPLETED', 'DELIVERED', 'PENDING_PAYOUT'] # Use relevant statuses
    ).select_related('product').order_by('product_id', '-order__created_at')
    # Get the most recent OrderItem for each unique product.
    # The dictionary comprehension ensures uniqueness based on product.id.
    digital_products = list({item.product.id: item for item in all_digital_order_items}.values())

    # --- Fetch Active Subscriptions (Placeholder) ---
    # In a real application, this would come from a Subscription model.
    # For demonstration, we'll create a dummy list.
    active_subscriptions = [
        {'plan': {'name': 'Gowbuy Pro Monthly'}, 'expires_at': timezone.now() + timezone.timedelta(days=25)},
        {'plan': {'name': 'Gowbuy Content Creator Tier'}, 'expires_at': timezone.now() + timezone.timedelta(days=150)},
    ]

    # --- END: New context data ---

    # --- Check for other user roles ---
    is_vendor = hasattr(request.user, 'vendor_profile') and request.user.vendor_profile is not None
    is_service_provider = hasattr(request.user, 'service_provider_profile') and request.user.service_provider_profile is not None
    is_rider = hasattr(request.user, 'rider_profile') and request.user.rider_profile is not None

    context = {
        'page_title': _('User Dashboard'),
        'profile_owner': profile_owner,
        'user_profile': user_profile,
        'user_preferences': user_preferences,
        'profile_completeness': profile_completeness,
        'recent_orders': recent_orders,
        'recent_reviews': all_recent_reviews,
        'wishlist_summary_items': wishlist_summary_items,
        'wishlist_total_count': wishlist_total_count,
        'user_points_balance': user_points_balance,
        'active_page': 'dashboard', # For new sidebar navigation
        'is_vendor': is_vendor,
        'is_service_provider': is_service_provider,
        'is_rider': is_rider,
        'primary_email': primary_email_obj,
        'is_email_verified': is_email_verified,
        'has_totp_enabled': has_totp_enabled,
        'has_fido_enabled': has_fido_enabled,
        'has_any_2fa_enabled': has_any_2fa_enabled,
        # --- Add new context variables ---
        'default_billing_address': default_billing_address,
        'default_shipping_address': default_shipping_address,
        'saved_payment_methods': saved_payment_methods,
        'digital_products': digital_products,
        'active_subscriptions': active_subscriptions,
        'next_step_text': next_step_text,
        'next_step_url': next_step_url,
    }
    return render(request, 'core/user_profile.html', context)


@login_required
def edit_user_profile(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    user_preferences, created = UserPreferences.objects.get_or_create(user=user)

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile, user=user)
        preferences_form = UserPreferencesForm(request.POST, instance=user_preferences)

        if profile_form.is_valid() and preferences_form.is_valid():
            profile_form.save()
            preferences_form.save()
            messages.success(request, _("Profile and preferences updated successfully!"))
            return redirect('core:user_profile')
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        profile_form = UserProfileForm(instance=user_profile, user=user)
        preferences_form = UserPreferencesForm(instance=user_preferences)

    context = {
        'profile_form': profile_form,
        'preferences_form': preferences_form,
        'page_title': _("Edit Profile"),
        'profile_owner': request.user,
        'active_page': 'profile',
    }
    return render(request, 'core/edit_user_profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            # --- START: Send Password Change Notification ---
            mail_subject = _('Your GOWBUY Password Has Been Changed')
            message = render_to_string('core/emails/password_change_notification.html', {
                'user': user,
                'change_time': timezone.now(),
                'ip_address': request.META.get('REMOTE_ADDR'),
            })
            user.email_user(mail_subject, message)
            # --- END: Send Password Change Notification ---

            messages.success(request, _('Your password was successfully updated!'))
            return redirect('core:user_profile')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        form = PasswordChangeForm(request.user)
    context = {
        'form': form,
        'page_title': _("Change Password"),
        'active_page': 'profile', # Part of the profile section
    }
    return render(request, 'core/change_password.html', context)

@login_required
def view_wishlist(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    context = {
        'wishlist_items': wishlist.products.all(),
        'page_title': _("My Wishlist"),
        'active_page': 'wishlist', # For new sidebar navigation
    }
    return render(request, 'core/wishlist.html', context)

@login_required
@require_POST
def add_to_wishlist(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    message = ""
    added = False

    product_id = request.POST.get('product_id')
    service_id = request.POST.get('service_id')

    if product_id:
        product = get_object_or_404(Product, id=product_id)
        if product in wishlist.products.all():
            wishlist.products.remove(product)
            added = False
            message = _(f"'{product.name}' removed from your wishlist.")
        else:
            wishlist.products.add(product)
            added = True
            message = _(f"'{product.name}' added to your wishlist.")
    elif service_id:
        service = get_object_or_404(Service, id=service_id)
        if service in wishlist.services.all():
            wishlist.services.remove(service)
            added = False
            message = _(f"'{service.title}' removed from your wishlist.")
        else:
            wishlist.services.add(service)
            added = True
            message = _(f"'{service.title}' added to your wishlist.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        count = wishlist.products.count()
        if hasattr(wishlist, 'services'):
            count += wishlist.services.count()
        return JsonResponse({'added': added, 'message': message, 'wishlist_count': count})

    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


@login_required
@require_POST
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    if product in wishlist.products.all():
        wishlist.products.remove(product)
        messages.success(request, _(f"'{product.name}' removed from your wishlist."))
    else:
        messages.info(request, _(f"'{product.name}' was not in your wishlist."))
    return redirect('core:wishlist_detail')


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
            queryset = queryset.filter(category=self.category)


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
        ).select_related('provider', 'category').prefetch_related('images', 'packages')[:4]

        context['top_service_categories'] = ServiceCategory.objects.filter(
            is_active=True
        ).annotate(
            num_services=Count('services', filter=Q(services__is_active=True))
        ).filter(num_services__gt=0).order_by('-num_services')[:8]

        context['categories'] = ServiceCategory.objects.filter(is_active=True).order_by('name')
        context['current_category'] = self.category
        context['search_query'] = self.search_query
        context['page_title'] = self.category.name if self.category else _("All Services")
        if self.search_query:
            context['page_title'] = _("Search results for '{query}'").format(query=self.search_query)

        return context

class CategoryServiceListView(ServiceListView):
    """
    A specific view to list services by category, inheriting all the logic
    from the main ServiceListView. The URL pattern provides the 'category_slug'.
    The base ServiceListView already handles this kwarg.
    """
    template_name = 'core/service_list.html' # Reuse the same template

class ServiceCategoryDetailView(ListView):
    model = Service
    template_name = 'core/service_category_detail.html' # Assumes this template exists
    context_object_name = 'services'
    paginate_by = 9

    def get_queryset(self):
        self.category = get_object_or_404(ServiceCategory, slug=self.kwargs['category_slug'], is_active=True)

        all_categories = [self.category]
        queue = [self.category]
        while queue:
            parent = queue.pop(0)
            for child in parent.subcategories.all():
                all_categories.append(child)
                queue.append(child)

        return Service.objects.filter(
            category__in=all_categories,
            is_active=True,
        ).select_related(
            'provider', 'provider__service_provider_profile', 'category'
        ).prefetch_related('images', 'packages').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['page_title'] = self.category.name
        return context


# --- Placeholder views for missing URLs ---

@login_required
def address_list_view(request):
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', 'address_type')
    form = AddressForm()
    context = {
        'addresses': addresses,
        'form': form,
        'page_title': _("My Addresses"),
        'active_page': 'addresses',
    }
    return render(request, 'core/address_list.html', context)

@login_required
def address_edit_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, _("Address updated successfully."))
            return redirect('core:address_list')
    else:
        form = AddressForm(instance=address)
    context = {
        'form': form,
        'page_title': _("Edit Address"),
        'active_page': 'addresses',
    }
    return render(request, 'core/address_form.html', context)

@login_required
def address_delete_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, _("Address deleted successfully."))
        return redirect('core:address_list')
    context = {
        'address': address,
        'page_title': _("Confirm Delete Address"),
        'active_page': 'addresses',
    }
    return render(request, 'core/address_confirm_delete.html', context)

@login_required
def download_digital_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, product_type='digital')

    # Check if the user has purchased this product
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        product=product,
        order__status__in=['COMPLETED', 'DELIVERED', 'PROCESSING'] # Or whatever statuses grant access
    ).exists()

    if not has_purchased:
        messages.error(request, _("You have not purchased this digital product or the order is not complete."))
        return redirect('core:order_history')

    if not product.digital_file:
        messages.error(request, _("The file for this product is not available."))
        return redirect(product.get_absolute_url())

    # Serve the file for download
    try:
        return FileResponse(product.digital_file.open('rb'), as_attachment=True, filename=product.digital_file.name)
    except FileNotFoundError:
        raise Http404(_("Digital file not found."))

@require_POST
def update_location(request):
    location = request.POST.get('location_input')
    if location:
        request.session['delivery_location'] = location
        messages.success(request, _("Delivery location updated to {location}.").format(location=location))
    return redirect('core:home')

@require_POST
def update_currency(request):
    currency_code = request.POST.get('currency_code')
    # Comprehensive validation list with 37 global currencies
    allowed_currencies = [
        'GBP', 'USD', 'EUR', 'GHS', 'NGN', 'CAD', 'AUD', 'JPY', 'CNY', 'INR', 
        'ZAR', 'KES', 'BRL', 'MXN', 'AED', 'SAR', 'CHF', 'SEK', 'NOK', 'DKK',
        'PLN', 'TRY', 'RUB', 'THB', 'SGD', 'MYR', 'PHP', 'IDR', 'VND', 'EGP',
        'MAD', 'NZD', 'HKD', 'KRW', 'ILS', 'CZK', 'HUF'
    ]
    if currency_code and currency_code in allowed_currencies:
        request.session['currency_code'] = currency_code
        messages.success(request, _(f"Currency updated to {currency_code}."))
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))

@require_POST
def update_language(request):
    lang_code = request.POST.get('language_input')
    if lang_code and lang_code in [code for code, name in settings.LANGUAGES]:
        translation.activate(lang_code)
        request.session['_language'] = lang_code
        messages.success(request, _("Language updated successfully."))
        
        response = redirect(request.META.get('HTTP_REFERER', 'core:home'))
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            lang_code,
            max_age=getattr(settings, 'LANGUAGE_COOKIE_AGE', 31536000), # Default to 1 year
            path=getattr(settings, 'LANGUAGE_COOKIE_PATH', '/'),
            domain=getattr(settings, 'LANGUAGE_COOKIE_DOMAIN', None),
            secure=getattr(settings, 'LANGUAGE_COOKIE_SECURE', False),
            httponly=getattr(settings, 'LANGUAGE_COOKIE_HTTPONLY', False),
            samesite=getattr(settings, 'LANGUAGE_COOKIE_SAMESITE', 'Lax'),
        )
        return response
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))

@login_required
def customer_review_list(request):
    product_reviews = ProductReview.objects.filter(user=request.user).select_related('product').order_by('-created_at')
    vendor_reviews = VendorReview.objects.filter(user=request.user).select_related('vendor').order_by('-created_at')
    service_reviews = ServiceReview.objects.filter(user=request.user).select_related('service').order_by('-created_at')

    context = {
        'product_reviews': product_reviews,
        'vendor_reviews': vendor_reviews,
        'service_reviews': service_reviews,
        'page_title': _("My Reviews"),
        'active_page': 'reviews',
    }
    return render(request, 'core/customer_review_list.html', context)

@login_required
def edit_review(request, review_type, review_id):
    # This is a complex view. A full implementation would require a generic form and model handling.
    # For now, this placeholder is more realistic.
    messages.info(request, _("Editing reviews is not yet implemented."))
    return redirect('core:customer_review_list')

@login_required
def delete_review(request, review_type, review_id):
    messages.info(request, _("Deleting reviews is not yet implemented."))
    return redirect('core:customer_review_list')

class RecentComparisonsView(LoginRequiredMixin, TemplateView):
    template_name = 'core/recent_comparisons.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Recent Comparisons")
        context['active_page'] = 'recent_comparisons'
        return context

@login_required
def render_rewards_page(request):
    messages.info(request, _("The rewards program is coming soon!"))
    return render(request, 'core/rewards_page.html', {'page_title': _("My Rewards")})

class LoginHistoryView(LoginRequiredMixin, ListView):
    model = SecurityLog
    template_name = 'core/login_history.html' # Assumed template
    context_object_name = 'logs'
    def get_queryset(self):
        return SecurityLog.objects.filter(user=self.request.user, action__in=['login_success', 'login_failed'])

@login_required
def session_management_view(request):
    # Placeholder
    return HttpResponse("Session Management View")

@login_required
def logout_other_sessions_view(request):
    # Placeholder
    return HttpResponse("Logout Other Sessions View")

class ProviderDashboardView(LoginRequiredMixin, IsServiceProviderMixin, TemplateView):
    template_name = 'core/service_provider/provider_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider_profile = self.request.user.service_provider_profile
        
        # Show warning if profile is not yet approved
        if not provider_profile.is_approved:
            messages.warning(
                self.request, 
                _("Your service provider profile is pending approval. Your services will go live once approved by our admin team.")
            )
        
        return context

@login_required
def become_service_provider(request):
    if hasattr(request.user, 'service_provider_profile') and request.user.service_provider_profile:
        messages.info(request, _("You are already a registered service provider."))
        return redirect('core:provider_dashboard')

    if request.method == 'POST':
        form = ServiceProviderProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, _("Your service provider application has been submitted successfully!"))
            return redirect('core:service_provider_dashboard')
    else:
        form = ServiceProviderProfileForm()

    context = {
        'form': form,
        'page_title': _("Become a Service Provider")
    }
    return render(request, 'core/become_service_provider.html', context)


class ServiceProviderVerificationView(LoginRequiredMixin, IsServiceProviderMixin, TemplateView):
    """
    Handles service provider verification/account approval display.
    Shows the current verification status and allows providers to submit verification if needed.
    """
    template_name = 'core/service_provider_verification.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider_profile = self.request.user.service_provider_profile
        
        context['page_title'] = _("Service Provider Verification")
        context['provider_profile'] = provider_profile
        context['is_verified'] = provider_profile.is_approved
        
        return context

class ProviderProfileDetailView(DetailView):
    model = ServiceProviderProfile
    template_name = 'core/provider_profile_detail.html'
    context_object_name = 'provider_profile'

    def get_object(self):
        return get_object_or_404(ServiceProviderProfile, user__username=self.kwargs['username'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider_profile = self.get_object()

        # The template expects 'profile_owner', which is the user associated with the profile.
        context['profile_owner'] = provider_profile.user

        # Fetch related data for the public profile page
        context['services'] = Service.objects.filter(provider=provider_profile.user, is_active=True).prefetch_related('packages', 'images')
        context['portfolio_items'] = PortfolioItem.objects.filter(provider_profile=provider_profile)
        context['reviews'] = ServiceReview.objects.filter(service__provider=provider_profile.user, is_approved=True).select_related('user', 'service')
        context['average_rating'] = context['reviews'].aggregate(Avg('rating'))['rating__avg']
        context['page_title'] = provider_profile.business_name or provider_profile.user.get_full_name() or provider_profile.user.username
        return context

@login_required
def edit_service_provider_profile(request):
    """
    Handles both updating the service provider's profile and adding new portfolio items.
    """
    provider_profile = get_object_or_404(ServiceProviderProfile, user=request.user)
    portfolio_items = PortfolioItem.objects.filter(provider_profile=provider_profile).order_by('-uploaded_at')

    if request.method == 'POST':
        # Determine which form was submitted based on the submit button's name
        if 'submit_profile' in request.POST:
            profile_form = ServiceProviderProfileForm(request.POST, request.FILES, instance=provider_profile)
            portfolio_item_form = PortfolioItemForm()  # Provide an empty form for the other section
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, _("Your provider profile has been updated successfully."))
                return redirect('core:edit_service_provider_profile')
        elif 'submit_portfolio_item' in request.POST:
            portfolio_item_form = PortfolioItemForm(request.POST, request.FILES)
            profile_form = ServiceProviderProfileForm(instance=provider_profile)  # Keep the profile form populated with existing data
            if portfolio_item_form.is_valid():
                portfolio_item = portfolio_item_form.save(commit=False)
                portfolio_item.provider_profile = provider_profile
                portfolio_item.save()
                messages.success(request, _("New item added to your portfolio."))
                return redirect('core:edit_service_provider_profile')
        else:
            # Fallback if no specific submit button name is found
            profile_form = ServiceProviderProfileForm(instance=provider_profile)
            portfolio_item_form = PortfolioItemForm()
            messages.error(request, _("An unexpected error occurred. Please try again."))
    else:
        # For GET requests, create unbound instances of both forms
        profile_form = ServiceProviderProfileForm(instance=provider_profile)
        portfolio_item_form = PortfolioItemForm()

    context = {
        'profile_form': profile_form,
        'portfolio_item_form': portfolio_item_form,
        'portfolio_items': portfolio_items,
        'page_title': _("Edit Provider Profile & Portfolio"),
        'active_page': 'provider_profile',
    }
    return render(request, 'core/edit_service_provider_profile.html', context)

class EditServiceProviderPayoutView(LoginRequiredMixin, IsServiceProviderMixin, SuccessMessageMixin, UpdateView):
    model = ServiceProviderProfile
    form_class = ServiceProviderPayoutForm # Use the dedicated form for service providers
    template_name = 'core/payout_settings.html'
    success_url = reverse_lazy('core:service_provider_payout_settings')
    success_message = _("Your payout settings have been updated successfully.")

    def get_object(self, queryset=None):
        return self.request.user.service_provider_profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Payout Settings")
        context['active_page'] = 'provider_payout_settings'
        return context

class PortfolioItemUpdateView(LoginRequiredMixin, IsServiceProviderMixin, SuccessMessageMixin, UpdateView):
    """
    View for a service provider to edit one of their portfolio items.
    """
    model = PortfolioItem
    form_class = PortfolioItemForm
    template_name = 'core/portfolio_item_form.html' # A new template for editing
    success_url = reverse_lazy('core:edit_service_provider_profile')
    success_message = _("Portfolio item updated successfully.")
    pk_url_kwarg = 'item_id'

    def get_queryset(self):
        # Ensure the user can only edit their own portfolio items
        provider_profile = get_object_or_404(ServiceProviderProfile, user=self.request.user)
        return PortfolioItem.objects.filter(provider_profile=provider_profile)


@login_required
def delete_portfolio_item(request, item_id):
    item = get_object_or_404(PortfolioItem, id=item_id, provider_profile__user=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, _("Portfolio item deleted."))
        return redirect('core:edit_service_provider_profile')
    context = {
        'item': item,
        'page_title': _("Confirm Delete Portfolio Item"),
    }
    return render(request, 'core/portfolio_item_confirm_delete.html', context)

@csrf_exempt
def ajax_get_item_details(request):
    """
    AJAX endpoint to fetch basic details for a list of product and/or service IDs.
    Used by the chatbot to render result cards.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed.'}, status=405)

    try:
        data = json.loads(request.body)
        product_ids = data.get('product_ids', [])
        service_ids = data.get('service_ids', [])

        if not isinstance(product_ids, list) or not isinstance(service_ids, list):
            return JsonResponse({'error': 'product_ids and service_ids must be lists.'}, status=400)

        # Fetch products
        products = Product.objects.filter(id__in=product_ids, is_active=True).prefetch_related('images')
        product_details = [{
            'id': p.id, 'type': 'product', 'name': p.name,
            'price': f'{p.price:,.2f}', 'url': p.get_absolute_url(),
            'image_url': p.images.first().image.url if p.images.first() else settings.STATIC_URL + 'assets/img/placeholder.png'
        } for p in products]

        # Fetch services
        services = Service.objects.filter(id__in=service_ids, is_active=True).prefetch_related('images')
        service_details = [{
            'id': s.id, 'type': 'service', 'name': s.title,
            'price': f'{s.price:,.2f}' if s.price else 'Varies', 'url': s.get_absolute_url(),
            'image_url': s.images.first().image.url if s.images.first() else settings.STATIC_URL + 'assets/img/placeholder.png'
        } for s in services]

        # Combine and return
        all_items = product_details + service_details
        
        # If you need to preserve order, you'd need a more complex sorting logic here
        # based on the original order of IDs. For now, this is sufficient.

        return JsonResponse({'items': all_items})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
    except Exception as e:
        logger.error(f"Error in ajax_get_item_details view: {e}", exc_info=True)
        return JsonResponse({'error': 'An internal error occurred.'}, status=500)

@csrf_exempt
def ajax_get_product_details(request):
    """
    AJAX endpoint to fetch basic details for a list of product IDs.
    Used by the chatbot to render recommended products.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed.'}, status=405)

    try:
        data = json.loads(request.body)
        product_ids = data.get('product_ids')

        if not isinstance(product_ids, list):
            return JsonResponse({'error': 'product_ids must be a list.'}, status=400)

        # Fetch products and ensure the order is preserved
        products = Product.objects.filter(id__in=product_ids, is_active=True).prefetch_related('images')
        products_dict = {p.id: p for p in products}
        
        # Build the response list in the same order as the input IDs
        product_details = []
        for pid in product_ids:
            product = products_dict.get(pid)
            if product:
                first_image = product.images.first()
                image_url = first_image.image.url if first_image else settings.STATIC_URL + 'assets/img/placeholder.png'
                
                product_details.append({
                    'id': product.id,
                    'name': product.name,
                    'price': f'{product.price:,.2f}',
                    'url': product.get_absolute_url(),
                    'image_url': image_url,
                })

        return JsonResponse({'products': product_details})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
    except Exception as e:
        logger.error(f"Error in ajax_get_product_details view: {e}", exc_info=True)
        return JsonResponse({'error': 'An internal error occurred.'}, status=500)

@csrf_exempt
def ajax_enhance_product_description(request):
    """
    This view was misnamed but contained the chatbot logic.
    It is kept here for reference but the URL now points to `ajax_chatbot_message`.
    A real implementation for enhancing a description would be different.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed.'}, status=405)

    try:
        data = json.loads(request.body)
        product_description = data.get('description')
        keywords = data.get('keywords', '')

        if not product_description:
            return JsonResponse({'error': 'Description is required.'}, status=400)

        prompt = f"""
You are an expert e-commerce copywriter for a marketplace called GOWBUY.
Your task is to rewrite and enhance the following product description to be more engaging, persuasive, and SEO-friendly.

Focus on highlighting the benefits for the customer. Use clear, concise language and break up the text with bullet points for readability.

If provided, incorporate these keywords naturally: {keywords}

Original Description:
"{product_description}"

Enhanced Description:
"""
        enhanced_description = generate_text_with_gemini(prompt)

        if enhanced_description and not enhanced_description.startswith("Error:"):
            return JsonResponse({'enhanced_description': enhanced_description.strip()})
        else:
            logger.error(f"AI description enhancement failed. Raw response: {enhanced_description}")
            return JsonResponse({'error': 'Failed to enhance description with AI.'}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
    except Exception as e:
        logger.error(f"Error in ajax_enhance_product_description view: {e}", exc_info=True)
        return JsonResponse({'error': 'An internal error occurred.'}, status=500)


@csrf_exempt
def ajax_visual_search(request):
    return JsonResponse({'error': 'Not implemented'}, status=501)

@csrf_exempt
def ajax_generate_3d_model(request):
    return JsonResponse({'error': 'Not implemented'}, status=501)

@csrf_exempt
def ajax_enhance_product_image(request):
    return JsonResponse({'error': 'Not implemented'}, status=501)

@csrf_exempt
def ajax_remove_image_background(request):
    return JsonResponse({'error': 'Not implemented'}, status=501)

@login_required
def ajax_suggest_product_origin(request, pk):
    """Provide an automated origin suggestion for a single product (AJAX).

    - Only the product's vendor or staff can call this.
    - Tries ML predictor first, falls back to rule-based heuristics when ML is unavailable.
    Returns JSON: { suggested_country, confidence, method, explanation }
    """
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    from core.models import Product

    product = get_object_or_404(Product, pk=pk)

    # Permission check: vendor owns product or staff
    user = request.user
    if not (user.is_staff or (hasattr(user, 'vendor_profile') and product.vendor == user.vendor_profile)):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    # Try ML predictor
    try:
        from core.ml.origin_trainer import predict_products
        summary = predict_products(queryset=Product.objects.filter(pk=pk), apply=False, min_confidence=0.0, limit=1)
        samples = summary.get('samples', [])
        if samples:
            s = samples[0]
            return JsonResponse({'suggested_country': s.get('predicted_country'), 'confidence': float(s.get('confidence', 0.0)), 'method': 'ml', 'explanation': 'ML model prediction'})
    except Exception as e:
        # ML unavailable or model not found — fallback to rule-based heuristics
        logger.debug('ML suggestion failed or unavailable: %s', e)

    # Rule-based fallback
    try:
        from core.management.commands.generate_origin_suggestions import COUNTRY_NAME_REGEX, find_country_code_by_name
    except Exception:
        COUNTRY_NAME_REGEX = None
        find_country_code_by_name = None

    suggestion = None
    confidence = None
    explanation = None

    # Heuristic 1: 'made in X' in description
    if product.description and COUNTRY_NAME_REGEX:
        m = COUNTRY_NAME_REGEX.search(product.description)
        if m and find_country_code_by_name:
            name = m.group(1)
            code = find_country_code_by_name(name)
            if code:
                suggestion = code
                confidence = 0.95
                explanation = f"matched 'made in' -> {name}"

    # Heuristic 2: vendor location
    if not suggestion and getattr(product, 'vendor', None):
        v_country = getattr(product.vendor, 'location_country', None)
        if v_country and find_country_code_by_name:
            code = find_country_code_by_name(v_country) or v_country
            suggestion = code
            confidence = 0.6
            explanation = 'vendor location'

    # Heuristic 3: keywords_for_ai tokens
    if not suggestion and product.keywords_for_ai and find_country_code_by_name:
        for token in (t.strip() for t in product.keywords_for_ai.split(',')):
            code = find_country_code_by_name(token)
            if code:
                suggestion = code
                confidence = 0.7
                explanation = f'keyword match: {token}'
                break

    if suggestion:
        return JsonResponse({'suggested_country': suggestion, 'confidence': float(confidence or 0.0), 'method': 'rule', 'explanation': explanation})

    return JsonResponse({'suggested_country': None, 'confidence': 0.0, 'method': None, 'explanation': 'no suggestion'})


@require_POST
@login_required
def ajax_apply_product_origin(request, pk):
    """Apply a chosen origin country to a product. Expects JSON: { country: 'US', confidence: 0.9, method: 'ml' }

    Only the vendor owner or staff may apply.
    """
    import json
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    from django.utils import timezone
    from core.models import Product, OriginLabel

    product = get_object_or_404(Product, pk=pk)
    user = request.user
    if not (user.is_staff or (hasattr(user, 'vendor_profile') and product.vendor == user.vendor_profile)):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        data = {}

    country = data.get('country') or None
    confidence = data.get('confidence')
    method = data.get('method')

    if not country:
        return JsonResponse({'error': 'country is required'}, status=400)

    # Apply the selection
    product.origin_country = country
    product.origin_inference_status = 'accepted'
    if method in ('ml', 'rule'):
        product.origin_inferred_by = method
    else:
        product.origin_inferred_by = 'manual'
    product.origin_inferred_at = timezone.now()
    product.save(update_fields=['origin_country', 'origin_inference_status', 'origin_inferred_by', 'origin_inferred_at'])

    # Create an OriginLabel for audit trail
    try:
        OriginLabel.objects.create(product=product, label_country=country, labeler=user, confidence=confidence, note='Accepted suggestion via vendor UI', source='admin')
    except Exception:
        logger.exception('Failed to create OriginLabel on vendor apply')

    return JsonResponse({'success': True, 'origin_country': country})

@api_key_required
def api_upload_3d_model(request, product_id):
    return JsonResponse({'error': 'Not implemented'}, status=501)

class ServiceSearchResultsView(ListView):
    model = Service
    template_name = 'core/service_list.html'

class ServiceCreateView(LoginRequiredMixin, IsServiceProviderMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'core/service_form.html'
    success_url = reverse_lazy('core:service_provider_dashboard')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        # If formsets are not passed in kwargs (from form_invalid), create them.
        if 'package_formset' not in kwargs:
            data['package_formset'] = ServicePackageFormSet()
        if 'availability_formset' not in kwargs:
            data['availability_formset'] = ServiceAvailabilityFormSet()
        return data

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        package_formset = ServicePackageFormSet(request.POST)
        availability_formset = ServiceAvailabilityFormSet(request.POST)

        if form.is_valid() and package_formset.is_valid() and availability_formset.is_valid():
            return self.form_valid(form, package_formset, availability_formset)
        else:
            messages.error(request, _("Please correct the errors below. Note: You may need to re-upload images and videos."))
            # Pass the invalid forms and formsets to the context for re-rendering
            return self.render_to_response(
                self.get_context_data(form=form,
                                      package_formset=package_formset,
                                      availability_formset=availability_formset)
            )

    def form_valid(self, form, package_formset, availability_formset):
        # Set the provider on the service instance before saving
        form.instance.provider = self.request.user
        self.object = form.save()

        # Save formsets
        package_formset.instance = self.object
        package_formset.save()
        
        availability_formset.instance = self.object
        availability_formset.save()

        # Handle multiple image uploads
        images = self.request.FILES.getlist('service_images')
        for image_file in images:
            ServiceImage.objects.create(service=self.object, image=image_file)

        # Handle multiple video uploads
        videos = self.request.FILES.getlist('service_videos')
        for video_file in videos:
            ServiceVideo.objects.create(service=self.object, video=video_file)

        messages.success(self.request, _("Your service has been created successfully."))
        return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        """Pass the current user to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class ServiceDetailView(DetailView):
    model = Service
    template_name = 'core/service_detail.html'
    context_object_name = 'service'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Service.objects.filter(is_active=True).select_related(
            'provider', 'provider__service_provider_profile', 'category'
        ).prefetch_related('images', 'packages', 'reviews', 'videos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.object
        context['related_services'] = Service.objects.filter(
            category=service.category,
            is_active=True
        ).exclude(id=service.id)[:4]
        context['availability_slots'] = ServiceAvailability.objects.filter(
            service=service,
            is_booked=False,
            start_time__gte=timezone.now()
        ).order_by('start_time')[:60]
        context['reviews'] = service.reviews.filter(is_approved=True).order_by('-created_at')
        
        if self.request.user.is_authenticated:
            context['in_wishlist'] = Wishlist.objects.filter(user=self.request.user, services=service).exists()
        else:
            context['in_wishlist'] = False
            
        return context

class ServiceUpdateView(LoginRequiredMixin, IsServiceProviderMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'core/service_form.html'
    success_url = reverse_lazy('core:service_provider_dashboard')
    slug_url_kwarg = 'service_slug'
    slug_field = 'slug'

    def get_form_kwargs(self):
        """Pass the current user to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['package_formset'] = ServicePackageFormSet(self.request.POST, instance=self.object)
            data['availability_formset'] = ServiceAvailabilityFormSet(self.request.POST, instance=self.object)
        else:
            data['package_formset'] = ServicePackageFormSet(instance=self.object)
            data['availability_formset'] = ServiceAvailabilityFormSet(instance=self.object)
        return data

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        context = self.get_context_data()
        package_formset = context['package_formset']
        availability_formset = context['availability_formset']

        if form.is_valid() and package_formset.is_valid() and availability_formset.is_valid():
            return self.form_valid(form, package_formset, availability_formset)
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form, package_formset, availability_formset):
        self.object = form.save()
        package_formset.instance = self.object
        package_formset.save()
        availability_formset.instance = self.object
        availability_formset.save()

        # Handle multiple image uploads
        images = self.request.FILES.getlist('service_images')
        if images:
            self.object.images.all().delete()
            for image_file in images:
                ServiceImage.objects.create(service=self.object, image=image_file)

        # Handle multiple video uploads
        videos = self.request.FILES.getlist('service_videos')
        if videos:
            self.object.videos.all().delete()
            for video_file in videos:
                ServiceVideo.objects.create(service=self.object, video=video_file)

        messages.success(self.request, _("Your service has been updated successfully."))
        return HttpResponseRedirect(self.get_success_url())

class ServiceDeleteView(LoginRequiredMixin, IsServiceProviderMixin, DeleteView):
    model = Service
    template_name = 'core/service_confirm_delete.html'
    success_url = reverse_lazy('core:service_provider_dashboard')

@login_required
def submit_service_review(request, slug):
    service = get_object_or_404(Service, slug=slug)
    if request.method == 'POST':
        form = ServiceReviewForm(request.POST)

        if ServiceReview.objects.filter(service=service, user=request.user).exists():
            messages.warning(request, _("You have already reviewed this service."))
            return redirect(service.get_absolute_url())
        
        # Check if the user has purchased and completed the service
        has_completed_booking = ServiceBooking.objects.filter(
            user=request.user,
            service_package__service=service,
            status='COMPLETED'
        ).exists()

        if not has_completed_booking:
            messages.error(request, _("You can only review services you have purchased and completed."))
            return redirect(service.get_absolute_url())

        if form.is_valid():
            review = form.save(commit=False)
            review.service = service
            review.user = request.user
            review.save()

            # --- Create a notification for the service provider ---
            provider = service.provider
            Notification.objects.create(
                recipient=provider,
                message=_("You have a new {rating}-star review for your service '{service_title}' from {user}.").format(rating=review.rating, service_title=service.title, user=request.user.get_full_name() or request.user.username),
                link=reverse('core:service_provider_review_reply', kwargs={'pk': review.pk})
            )
            messages.success(request, _("Your review has been submitted successfully!"))
            return redirect(service.get_absolute_url())
    return redirect(service.get_absolute_url())

@login_required
@require_POST
def contact_service_provider(request, service_slug):
    service = get_object_or_404(Service, slug=service_slug)
    provider_user = service.provider
    current_user = request.user

    if provider_user == current_user:
        messages.error(request, _("You cannot contact yourself."))
        return redirect(service.get_absolute_url())

    subject = request.POST.get('subject', f"Inquiry about {service.title}")
    message_text = request.POST.get('message')

    if not message_text:
        messages.error(request, _("Please enter a message."))
        return redirect(service.get_absolute_url())

    # Find existing conversation or create new one
    conversation = Conversation.objects.annotate(
        num_participants=Count('participants')
    ).filter(
        participants=current_user, num_participants=2
    ).filter(
        participants=provider_user
    ).first()

    if not conversation:
        conversation = Conversation.objects.create(subject=subject)
        conversation.participants.add(current_user, provider_user)
    
    # Create the message
    Message.objects.create(
        conversation=conversation,
        sender=current_user,
        content=message_text
    )

    messages.success(request, _("Message sent successfully!"))
    return redirect('core:customer_message_detail', pk=conversation.pk)

@login_required
def create_service_booking(request, package_id):
    package = get_object_or_404(ServicePackage, id=package_id)
    slot_id = request.GET.get('slot_id')

    if not slot_id:
        messages.error(request, _("Please select an availability slot."))
        return redirect(package.service.get_absolute_url())

    # Ensure slot exists and is available
    slot = get_object_or_404(ServiceAvailability, id=slot_id, is_booked=False)

    # Add to cart
    cart, created = Cart.objects.get_or_create(user=request.user, ordered=False)
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        service_package=package,
        defaults={'quantity': 1}
    )

    # Store booking details in session keyed by the cart item ID
    if 'booking_details' not in request.session:
        request.session['booking_details'] = {}
    
    request.session['booking_details'][str(cart_item.id)] = {
        'availability_slot_id': slot.id,
        'preferred_start_date': slot.start_time.date().isoformat(),
        'start_time': slot.start_time.strftime('%H:%M'),
        'end_time': slot.end_time.strftime('%H:%M'),
        'service_name': package.service.title,
        'package_name': package.name
    }
    request.session.modified = True

    messages.success(request, _("Service added to cart. Please proceed to checkout."))
    return redirect('core:cart_detail')

class BecomeRiderView(LoginRequiredMixin, CreateView):
    model = RiderApplication
    form_class = RiderProfileApplicationForm
    template_name = 'core/become_rider.html'
    success_url = reverse_lazy('core:user_profile')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, _("Your rider application has been submitted successfully! We will review it shortly."))
        return super().form_valid(form)

class RiderDashboardView(LoginRequiredMixin, IsRiderMixin, TemplateView):
    template_name = 'core/rider_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rider_profile = self.request.user.rider_profile

        # Tasks assigned to this rider
        my_accepted_tasks = DeliveryTask.objects.filter(
            rider=rider_profile,
            status__in=['ACCEPTED_BY_RIDER', 'PICKED_UP', 'OUT_FOR_DELIVERY']
        ).select_related('order').order_by('created_at')

        # Tasks available for any rider to accept
        available_tasks = []
        if rider_profile.is_available:
            available_tasks = DeliveryTask.objects.filter(
                status='PENDING_ASSIGNMENT'
                # TODO: Add proximity filter here later
            ).select_related('order').order_by('-created_at')[:10]

        context.update({
            'rider_profile': rider_profile,
            'my_accepted_tasks': my_accepted_tasks,
            'available_tasks': available_tasks,
            'page_title': _("Rider Dashboard"),
            'status_message': _("Welcome to your dashboard. Here you can manage your tasks and availability."),
        })
        return context

@login_required
@require_POST
def toggle_rider_availability(request):
    rider_profile = get_object_or_404(RiderProfile, user=request.user)
    rider_profile.is_available = not rider_profile.is_available
    rider_profile.save(update_fields=['is_available'])
    if rider_profile.is_available:
        messages.success(request, _("You are now ONLINE and available for deliveries."))
    else:
        messages.info(request, _("You are now OFFLINE and will not receive new tasks."))
    return redirect('core:rider_dashboard')

@login_required
@require_POST
def accept_delivery_task(request, task_id):
    with transaction.atomic():
        task = get_object_or_404(DeliveryTask.objects.select_for_update(), task_id=task_id, status='PENDING_ASSIGNMENT')
        rider_profile = get_object_or_404(RiderProfile, user=request.user, is_approved=True, is_available=True)

        task.rider = rider_profile
        task.status = 'ACCEPTED_BY_RIDER'
        task.save()

        messages.success(request, _("Task #{task_id} accepted successfully!").format(task_id=task.task_id))
    return redirect('core:rider_dashboard')

class RiderTaskDetailView(LoginRequiredMixin, IsRiderMixin, DetailView):
    model = DeliveryTask
    template_name = 'core/rider_task_detail.html'
    pk_url_kwarg = 'task_id'
    context_object_name = 'task'

    def get_queryset(self):
        # Rider can only view tasks assigned to them
        return DeliveryTask.objects.filter(rider=self.request.user.rider_profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.get_object()
        context['page_title'] = _("Task Details - {task_id}").format(task_id=task.task_id)
        context['google_maps_api_key'] = settings.GOOGLE_MAPS_API_KEY
        return context

@login_required
@require_POST
def update_task_status_picked_up(request, task_id):
    task = get_object_or_404(DeliveryTask, task_id=task_id, rider=request.user.rider_profile, status='ACCEPTED_BY_RIDER')
    task.status = 'PICKED_UP'
    task.actual_pickup_time = timezone.now()
    task.save()
    messages.success(request, _("Task status updated to 'Picked Up'."))
    return redirect('core:rider_task_detail', task_id=task.task_id)

@login_required
@require_POST
def update_task_status_delivered(request, task_id):
    task = get_object_or_404(DeliveryTask, task_id=task_id, rider=request.user.rider_profile, status__in=['PICKED_UP', 'OUT_FOR_DELIVERY'])
    task.status = 'DELIVERED'
    task.actual_delivery_time = timezone.now()
    task.save()
    messages.success(request, _("Task marked as 'Delivered'. Great job!"))
    return redirect('core:rider_dashboard')

class RiderEarningsReportsView(LoginRequiredMixin, IsRiderMixin, TemplateView):
    template_name = 'core/rider_earnings_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Earnings Reports")
        # Add reporting data here
        return context

class RiderProfileView(LoginRequiredMixin, IsRiderMixin, DetailView):
    model = RiderProfile
    template_name = 'core/rider_profile_view.html'
    def get_object(self):
        return self.request.user.rider_profile

class RiderProfileEditView(LoginRequiredMixin, IsRiderMixin, UpdateView):
    model = RiderProfile
    form_class = RiderProfileUpdateForm
    template_name = 'core/rider_profile_edit.html'
    success_url = reverse_lazy('core:rider_profile_view')
    def get_object(self):
        return self.request.user.rider_profile

class RiderVerificationView(LoginRequiredMixin, IsRiderMixin, TemplateView):
    template_name = 'core/rider_verification.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rider_profile'] = self.request.user.rider_profile
        context['page_title'] = _("My Verification Documents")
        return context

class RiderBoostVisibilityView(LoginRequiredMixin, IsRiderMixin, TemplateView):
    template_name = 'core/rider_boost_visibility.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['boost_packages'] = BoostPackage.objects.filter(is_active=True).order_by('display_order')
        context['page_title'] = _("Boost Your Visibility")
        return context

class ActivateRiderBoostView(LoginRequiredMixin, IsRiderMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("Activate Rider Boost")

@csrf_exempt
def paystack_boost_callback(request):
    return HttpResponse("Paystack Boost Callback")
class RequestPayoutView(LoginRequiredMixin, IsRiderMixin, CreateView):
    model = PayoutRequest
    form_class = RiderPayoutRequestForm
    template_name = 'core/rider_request_payout.html'
    success_url = reverse_lazy('core:rider_earnings')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Calculate available balance
        # This is a simplified calculation. A real app would be more robust.
        total_earnings = DeliveryTask.objects.filter(
            rider=self.request.user.rider_profile, status='DELIVERED'
        ).aggregate(total=Sum('rider_earning'))['total'] or Decimal('0.00')

        total_paid_out = PayoutRequest.objects.filter(
            rider_profile=self.request.user.rider_profile, status='completed'
        ).aggregate(total=Sum('amount_requested'))['total'] or Decimal('0.00')

        kwargs['max_amount'] = total_earnings - total_paid_out
        return kwargs

    def form_valid(self, form):
        form.instance.rider_profile = self.request.user.rider_profile
        messages.success(self.request, _("Your payout request has been submitted for review."))
        return super().form_valid(form)

class RiderEarningsView(LoginRequiredMixin, IsRiderMixin, TemplateView):
    template_name = 'core/rider_earnings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rider_profile = self.request.user.rider_profile

        # Simplified earnings calculation
        total_earnings = DeliveryTask.objects.filter(
            rider=rider_profile, status='DELIVERED'
        ).aggregate(total=Sum('rider_earning'))['total'] or Decimal('0.00')

        total_paid_out = PayoutRequest.objects.filter(
            rider_profile=rider_profile, status='completed'
        ).aggregate(total=Sum('amount_requested'))['total'] or Decimal('0.00')

        pending_payouts = PayoutRequest.objects.filter(
            rider_profile=rider_profile, status__in=['pending', 'processing']
        ).aggregate(total=Sum('amount_requested'))['total'] or Decimal('0.00')

        available_balance = total_earnings - total_paid_out - pending_payouts

        context.update({
            'total_earnings': total_earnings,
            'total_paid_out': total_paid_out,
            'pending_payouts': pending_payouts,
            'available_balance': available_balance,
            'payout_history': PayoutRequest.objects.filter(rider_profile=rider_profile).order_by('-requested_at'),
            'page_title': _("My Earnings"),
        })
        return context

class RiderNotificationListView(LoginRequiredMixin, IsRiderMixin, ListView):
    model = Notification
    template_name = 'core/rider_notification_list.html'
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

class BecomeRiderInfoView(TemplateView):
    template_name = 'core/become_rider_info.html'

class ServiceProviderServicesListView(LoginRequiredMixin, IsServiceProviderMixin, ListView):
    model = Service
    template_name = 'core/service_provider/service_provider_services_list.html' # Corrected path to match your file
    context_object_name = 'services'
    paginate_by = 10

    def get_queryset(self):
        queryset = Service.objects.filter(provider=self.request.user).select_related('category').prefetch_related('packages').order_by('-created_at')

        # --- Search logic ---
        self.search_query = self.request.GET.get('q', '')
        if self.search_query:
            queryset = queryset.filter(
                Q(title__icontains=self.search_query) |
                Q(category__name__icontains=self.search_query)
            )

        # --- Status filter logic ---
        self.current_status = self.request.GET.get('status', '')
        if self.current_status == 'active':
            queryset = queryset.filter(is_active=True)
        elif self.current_status == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("My Services")
        context['search_query'] = self.search_query
        context['current_status'] = self.current_status
        return context

def shop_local(request):
    """
    View to find and display local vendors based on the user's location.
    """
    user_lat = request.GET.get('lat')
    user_lon = request.GET.get('lon')
    radius_km_str = request.GET.get('radius', '25') # Default radius of 25km

    nearby_vendors = []
    context = {
        'has_location': False,
        'nearby_vendors': [],
        'search_radius': int(radius_km_str),
        'page_title': _("Shop Local"),
    }

    if user_lat and user_lon:
        context['has_location'] = True
        try:
            user_lat_dec = Decimal(user_lat)
            user_lon_dec = Decimal(user_lon)
            radius_km = int(radius_km_str)

            # Filter for approved vendors that have coordinates
            vendors = Vendor.objects.filter(is_approved=True, latitude__isnull=False, longitude__isnull=False)

            for vendor in vendors:
                distance = haversine(user_lat_dec, user_lon_dec, vendor.latitude, vendor.longitude)
                if distance <= radius_km:
                    vendor.distance = round(distance, 1) # Add distance attribute to vendor object
                    nearby_vendors.append(vendor)

            # Sort vendors by distance, closest first
            context['nearby_vendors'] = sorted(nearby_vendors, key=lambda v: v.distance)

        except (ValueError, TypeError) as e:
            logger.error(f"Error processing location for Shop Local: {e}")

    return render(request, 'core/shop_local.html', context)
@login_required
def service_provider_advertisements(request):
    # This view displays service provider advertisements.
    context = {
        'page_title': _("Advertisements"),
        'is_service_provider_view': True, # To help the template adapt
    }
    return render(request, 'core/service_provider/advertisements.html', context)


def _get_chatbot_knowledge_base():
    """
    Compiles a string of general knowledge from FAQs, T&C, and Privacy Policy
    to be used as context for the chatbot.
    """
    knowledge_base = []

    # Add FAQs
    faqs = FAQ.objects.filter(is_active=True)
    if faqs.exists():
        knowledge_base.append("--- Frequently Asked Questions (FAQs) ---")
        for faq in faqs:
            knowledge_base.append(f"Q: {faq.question}\nA: {faq.answer}")
        knowledge_base.append("--- End of FAQs ---")

    # Add Terms and Conditions
    terms = TermsAndConditions.objects.filter(is_active=True).order_by('-effective_date').first()
    if terms:
        knowledge_base.append("\n--- Summary of Terms and Conditions ---")
        # Provide a summary or key points instead of the full text for brevity
        knowledge_base.append(terms.content[:2000] + "...") # Truncate for prompt length
        knowledge_base.append("--- End of Terms and Conditions ---")

    # Add Privacy Policy
    privacy = PrivacyPolicy.objects.filter(is_active=True).order_by('-effective_date').first()
    if privacy:
        knowledge_base.append("\n--- Summary of Privacy Policy ---")
        knowledge_base.append(privacy.content[:2000] + "...") # Truncate
        knowledge_base.append("--- End of Privacy Policy ---")

    return "\n".join(knowledge_base)

def _search_platform(query: str, limit: int = 5):
    """
    Performs a comprehensive search across products and services.
    """
    product_results = Product.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query) | Q(vendor__name__icontains=query),
        is_active=True, vendor__is_approved=True
    ).distinct().prefetch_related('images')[:limit]

    service_results = Service.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query) | Q(provider__service_provider_profile__business_name__icontains=query),
        is_active=True, provider__service_provider_profile__is_approved=True
    ).distinct().prefetch_related('images', 'packages')[:limit]

    return list(product_results), list(service_results)

@csrf_exempt
def ajax_chatbot_message(request):
    """
    Handles incoming messages for the AI chatbot, determines intent,
    and returns a structured response.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed.'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message')
        conversation_history = data.get('history', []) # Get conversation history

        if not user_message:
            return JsonResponse({'error': 'Message is required.'}, status=400)

        # 1. Get Knowledge Base Context
        knowledge_base = _get_chatbot_knowledge_base()

        # 2. Construct the Prompt for the AI
        prompt = f"""You are GOWBUY AI, a helpful and friendly e-commerce assistant for the GOWBUY marketplace.
Your goal is to assist users with their questions and help them find products or services.

Today's Date: {timezone.now().strftime('%Y-%m-%d')}

--- Conversation History ---
{conversation_history}

--- User's Latest Message ---
"{user_message}"

--- Platform Knowledge Base (for answering general questions) ---
{knowledge_base}
--- End of Knowledge Base ---

Based on the user's latest message and the conversation history, determine the user's intent and respond in a structured JSON format.

The JSON object must have two fields: "intent" and "response_text".

1.  **intent**: Can be one of the following strings:
    - "answer_question": If the user is asking a general question about the platform (e.g., "what is your return policy?", "how do I sell?").
    - "search_platform": If the user is looking for specific products or services (e.g., "show me red shoes", "I need a logo designer").
    - "chit_chat": For greetings or conversational filler (e.g., "hello", "thank you").

2.  **response_text**: A friendly, conversational text response to the user.

3.  **search_query** (ONLY if intent is "search_platform"): A concise, keyword-focused search query string derived from the user's message.

Example 1 (General Question):
User Message: "How long does shipping take?"
Your JSON Output: {{"intent": "answer_question", "response_text": "Shipping times can vary depending on the vendor and your location. You can find more details in the shipping policy on each product or vendor page."}}

Example 2 (Product Search):
User Message: "I'm looking for a handmade leather wallet for men"
Your JSON Output: {{"intent": "search_platform", "response_text": "Of course! Searching for handmade leather wallets for you now...", "search_query": "handmade leather wallet men"}}

Example 3 (Chit-chat):
User Message: "Hi there"
Your JSON Output: {{"intent": "chit_chat", "response_text": "Hello! How can I help you today?"}}

Now, analyze the user's message and provide the JSON output. Do not include markdown formatting like ```json.
"""

        # 3. Get Structured Response from AI
        ai_response_data = get_chatbot_response(prompt)
        
        if not ai_response_data:
            return JsonResponse({'error': 'Failed to get a response from the AI assistant.'}, status=500)

        # 4. Process the AI's intent, but first check for API errors
        if 'error' in ai_response_data:
            # For user-facing errors like rate limiting, it's better to return a 200 OK
            # with the error in the JSON payload. This simplifies frontend handling,
            # as the JavaScript is already set up to display data.error.
            return JsonResponse(ai_response_data, status=200)
        elif ai_response_data.get('intent') == 'search_platform' and ai_response_data.get('search_query'):
            search_query = ai_response_data['search_query']
            products, services = _search_platform(search_query)
            ai_response_data['product_ids'] = [p.id for p in products] # Send back IDs
            ai_response_data['service_ids'] = [s.id for s in services] # Send back IDs

        return JsonResponse(ai_response_data)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
    except Exception as e:
        logger.error(f"Error in ajax_chatbot_message view: {e}", exc_info=True)
        return JsonResponse({'error': 'An internal error occurred.'}, status=500)

class ServiceProviderAdCampaignCreateView(LoginRequiredMixin, IsServiceProviderMixin, CreateView):
    # This view is a placeholder. A full implementation would require a dedicated form.
    model = AdCampaign
    fields = ['name', 'promoted_product', 'placement', 'start_date', 'end_date', 'budget']
    template_name = 'core/service_provider/service_provider_ad_campaign_form.html'
    success_url = reverse_lazy('core:service_provider_advertisements')

class ServiceProviderBookingsListView(LoginRequiredMixin, IsServiceProviderMixin, ListView):
    model = ServiceBooking
    template_name = 'core/provider_bookings_list.html'
    def get_queryset(self):
        return ServiceBooking.objects.filter(provider=self.request.user)

class ServiceProviderBookingDetailView(LoginRequiredMixin, IsServiceProviderMixin, DetailView):
    """
    Displays the details of a single booking for a service provider.
    """
    model = ServiceBooking
    template_name = 'core/service_provider/service_provider_booking_detail.html'
    context_object_name = 'booking'
    pk_url_kwarg = 'booking_id' # To match the URL parameter

    def get_queryset(self):
        """
        Ensures that providers can only see bookings for services they offer.
        """
        return ServiceBooking.objects.filter(provider=self.request.user).select_related('location_address', 'user', 'service_package__service')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Booking Details")

        # Pass map data if location is available
        if self.object.location_address and self.object.location_address.latitude and self.object.location_address.longitude:
            context['google_maps_api_key'] = settings.GOOGLE_MAPS_API_KEY
            context['latitude'] = self.object.location_address.latitude
            context['longitude'] = self.object.location_address.longitude
        return context

class ServiceProviderReviewListView(LoginRequiredMixin, IsServiceProviderMixin, ListView):
    model = ServiceReview
    template_name = 'core/service_provider/service_provider_review_list.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        provider_user = self.request.user
        queryset = ServiceReview.objects.filter(service__provider=provider_user).select_related(
            'user', 'service'
        ).order_by('-created_at')

        # Get the rating from the URL query parameters
        self.rating_filter = self.request.GET.get('rating')
        if self.rating_filter and self.rating_filter.isdigit():
            queryset = queryset.filter(rating=int(self.rating_filter))

        # Get the search query from the URL
        self.search_query = self.request.GET.get('q')
        if self.search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=self.search_query) |
                Q(review__icontains=self.search_query) |
                Q(service__title__icontains=self.search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider_user = self.request.user

        # Get all reviews for the provider for accurate stats, ignoring filters
        all_reviews_for_provider = ServiceReview.objects.filter(service__provider=provider_user)

        context['page_title'] = _("Client Reviews")
        context['total_reviews'] = all_reviews_for_provider.count()
        context['average_rating'] = all_reviews_for_provider.aggregate(Avg('rating'))['rating__avg']

        # Pass the current filter state to the template
        context['current_rating'] = self.rating_filter
        context['search_query'] = self.search_query

        return context

class ServiceProviderReviewReplyView(LoginRequiredMixin, IsServiceProviderMixin, SuccessMessageMixin, UpdateView):
    model = ServiceReview
    fields = ['reply']
    template_name = 'core/service_provider/service_provider_review_reply_form.html'
    success_url = reverse_lazy('core:service_provider_review_list')
    success_message = _("Your reply has been posted successfully.")

    def get_queryset(self):
        # Ensure provider can only reply to reviews for their own services
        return ServiceReview.objects.filter(service__provider=self.request.user)

    def form_valid(self, form):
        # Set the reply timestamp when the form is submitted
        if form.instance.reply and not getattr(form.instance, 'replied_at', None):
             form.instance.replied_at = timezone.now()
        elif not form.instance.reply: # Clear timestamp if reply is removed
            form.instance.replied_at = None
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review'] = self.get_object()
        return context

class ServiceProviderNotificationListView(LoginRequiredMixin, IsServiceProviderMixin, ListView):
    model = Notification
    template_name = 'core/service_provider/service_provider_notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)
        self.search_query = self.request.GET.get('q', '')
        if self.search_query:
            queryset = queryset.filter(message__icontains=self.search_query)
        self.current_status = self.request.GET.get('status', '')
        if self.current_status == 'unread':
            queryset = queryset.filter(is_read=False)
        elif self.current_status == 'read':
            queryset = queryset.filter(is_read=True)
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Your Notifications")
        context['search_query'] = self.search_query
        context['current_status'] = self.current_status
        return context

@login_required
@require_POST
def service_provider_mark_all_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, _("All notifications marked as read."))
    return redirect('core:service_provider_notification_list')

@login_required
@require_POST
def service_provider_delete_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.delete()
    messages.success(request, _("Notification deleted."))
    return redirect('core:service_provider_notification_list')

@login_required
@require_POST
def service_provider_delete_all_notifications(request):
    Notification.objects.filter(recipient=request.user).delete()
    messages.success(request, _("All notifications have been deleted."))
    return redirect('core:service_provider_notification_list')

@login_required
@require_POST
def service_provider_confirm_booking(request, booking_id):
    """
    View for a service provider to confirm a pending booking.
    """
    booking = get_object_or_404(ServiceBooking, id=booking_id, provider=request.user)

    if booking.status == 'pending':
        booking.status = 'confirmed'
        booking.save(update_fields=['status'])
        messages.success(request, _("Booking #{booking_id} has been confirmed successfully.").format(booking_id=booking.id))
        # TODO: Send a notification to the customer
    else:
        messages.warning(request, _("This booking cannot be confirmed as it is not in a 'pending' state."))

    return redirect('core:service_provider_booking_detail', booking_id=booking.id)

class ServiceProviderPayoutRequestListView(LoginRequiredMixin, IsServiceProviderMixin, ListView):
    model = PayoutRequest
    template_name = 'core/service_provider/service_provider_payout_request_list.html' # Corrected path
    context_object_name = 'payout_requests'
    paginate_by = 10

    def get_queryset(self):
        provider_profile = self.request.user.service_provider_profile
        queryset = PayoutRequest.objects.filter(service_provider_profile=provider_profile)

        # Filtering logic from GET parameters
        self.search_query = self.request.GET.get('q', '')
        if self.search_query:
            queryset = queryset.filter(id__icontains=self.search_query)

        self.current_status = self.request.GET.get('status', '')
        if self.current_status:
            queryset = queryset.filter(status=self.current_status)

        return queryset.order_by('-requested_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider_profile = self.request.user.service_provider_profile

        # --- Payout Summary Calculations ---
        completed_orders_value = OrderItem.objects.filter(
            provider=provider_profile.user,
            order__status__in=['COMPLETED', 'DELIVERED', 'PENDING_PAYOUT']
        ).aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or Decimal('0.00')

        # Ensure commission_rate is a Decimal to avoid TypeError
        commission_rate = Decimal(str(getattr(settings, 'PLATFORM_SERVICE_COMMISSION_RATE', '0.10')))
        total_commission = completed_orders_value * commission_rate
        net_earnings = completed_orders_value - total_commission

        total_paid_out = PayoutRequest.objects.filter(
            service_provider_profile=provider_profile, status='completed'
        ).aggregate(total=Sum('amount_requested'))['total'] or Decimal('0.00')

        pending_payouts = PayoutRequest.objects.filter(
            service_provider_profile=provider_profile, status__in=['pending', 'processing']
        ).aggregate(total=Sum('amount_requested'))['total'] or Decimal('0.00')

        context['available_for_payout'] = max(Decimal('0.00'), net_earnings - total_paid_out - pending_payouts)
        context['pending_payouts'] = pending_payouts
        context['total_paid_out'] = total_paid_out
        context['can_request_payout'] = context['available_for_payout'] >= getattr(settings, 'MINIMUM_VENDOR_PAYOUT_AMOUNT', 50) # You might want a separate setting for providers
        context['search_query'] = self.search_query
        context['current_status'] = self.current_status
        context['page_title'] = _("Payouts")
        return context

class ServiceProviderPayoutRequestCreateView(LoginRequiredMixin, IsServiceProviderMixin, CreateView):
    model = PayoutRequest
    form_class = ServiceProviderPayoutRequestForm # Use the dedicated form
    template_name = 'core/provider_payout_request_form.html' # Corrected template path
    success_url = reverse_lazy('core:service_provider_payout_requests')
    success_message = _("Your payout request has been submitted.")

    def get_form_kwargs(self):
        """Passes the maximum available payout amount and provider profile to the form."""
        kwargs = super().get_form_kwargs()
        provider_profile = self.request.user.service_provider_profile

        # --- Payout Summary Calculations ---
        completed_orders_value = OrderItem.objects.filter(
            provider=provider_profile.user,
            order__status__in=['COMPLETED', 'DELIVERED', 'PENDING_PAYOUT']
        ).aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or Decimal('0.00')

        commission_rate = Decimal(str(getattr(settings, 'PLATFORM_SERVICE_COMMISSION_RATE', '0.10')))
        total_commission = completed_orders_value * commission_rate
        net_earnings = completed_orders_value - total_commission

        total_paid_out = PayoutRequest.objects.filter(
            service_provider_profile=provider_profile, status='completed'
        ).aggregate(total=Sum('amount_requested'))['total'] or Decimal('0.00')

        pending_payouts = PayoutRequest.objects.filter(
            service_provider_profile=provider_profile, status__in=['pending', 'processing']
        ).aggregate(total=Sum('amount_requested'))['total'] or Decimal('0.00')

        kwargs['max_amount'] = max(Decimal('0.00'), net_earnings - total_paid_out - pending_payouts)
        # The form expects 'vendor_profile', so we'll adapt by passing the provider profile.
        # The form will then check for payout methods on this profile object.
        kwargs['vendor_profile'] = provider_profile
        return kwargs

    def form_valid(self, form):
        form.instance.service_provider_profile = self.request.user.service_provider_profile

        # Get the selected payout method and construct the details string
        payout_method_key = form.cleaned_data.get('payout_method')
        provider_profile = self.request.user.service_provider_profile
        details_string = "Payout method not found." # Fallback

        if payout_method_key == 'mobile_money':
            details_string = f"Mobile Money: {provider_profile.mobile_money_provider} - {provider_profile.mobile_money_number}"
        elif payout_method_key == 'bank':
            details_string = f"Bank Account: {provider_profile.bank_name}, Acc No: {provider_profile.bank_account_number}, Name: {provider_profile.bank_account_name}"
        elif payout_method_key == 'paypal':
            details_string = f"PayPal: {provider_profile.paypal_email}"
        elif payout_method_key == 'stripe':
            details_string = f"Stripe: {provider_profile.stripe_account_id}"
        elif payout_method_key == 'payoneer':
            details_string = f"Payoneer: {provider_profile.payoneer_email}"
        elif payout_method_key == 'wise':
            details_string = f"Wise: {provider_profile.wise_email}"
        elif payout_method_key == 'crypto':
            details_string = f"Crypto: {provider_profile.crypto_wallet_network} - {provider_profile.crypto_wallet_address}"
        
        form.instance.payment_method_details = details_string
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("Request New Payout")
        return context

class ServiceAvailabilityListView(LoginRequiredMixin, IsServiceProviderMixin, ListView):
    model = ServiceAvailability
    template_name = 'core/provider_availability_list.html'
    def get_queryset(self):
        return ServiceAvailability.objects.filter(service__provider=self.request.user)

class ServiceAvailabilityCreateView(LoginRequiredMixin, IsServiceProviderMixin, SuccessMessageMixin, CreateView):
    model = ServiceAvailability
    form_class = ServiceAvailabilityForm
    template_name = 'core/provider_availability_form.html'
    success_url = reverse_lazy('core:service_provider_availability_list')
    success_message = _("Availability slot created successfully.")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['service'].queryset = Service.objects.filter(provider=self.request.user)
        return form

class ServiceAvailabilityUpdateView(LoginRequiredMixin, IsServiceProviderMixin, SuccessMessageMixin, UpdateView):
    model = ServiceAvailability
    form_class = ServiceAvailabilityForm
    template_name = 'core/provider_availability_form.html'
    success_url = reverse_lazy('core:service_provider_availability_list')
    success_message = _("Availability slot updated successfully.")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['service'].queryset = Service.objects.filter(provider=self.request.user)
        return form

class ServiceAvailabilityDeleteView(LoginRequiredMixin, IsServiceProviderMixin, DeleteView):
    model = ServiceAvailability
    template_name = 'core/provider_availability_confirm_delete.html'
    success_url = reverse_lazy('core:service_provider_availability_list')

class CustomerNotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'core/customer_notification_list.html'
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

@csrf_exempt
def facebook_data_deletion(request):
    """
    Callback for Facebook Data Deletion Request.
    """
    try:
        signed_request = request.POST.get('signed_request')
        if not signed_request:
            return JsonResponse({'error': 'No signed request'}, status=400)

        encoded_sig, payload = signed_request.split('.', 1)
        secret = os.environ.get('FACEBOOK_CLIENT_SECRET', '')

        # Decode signature
        sig = base64.urlsafe_b64decode(encoded_sig + "=" * ((4 - len(encoded_sig) % 4) % 4))
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * ((4 - len(payload) % 4) % 4)))

        if secret:
            expected_sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
            if sig != expected_sig:
                return JsonResponse({'error': 'Bad signature'}, status=400)

        return JsonResponse({
            'url': request.build_absolute_uri(reverse('core:home')),
            'confirmation_code': data.get('user_id', 'deleted')
        })
    except Exception as e:
        logger.error(f"Facebook Data Deletion Error: {e}")
        return JsonResponse({'error': 'Processing failed'}, status=400)

class BlogPostListView(ListView):
    model = BlogPost
    template_name = 'core/blog_post_list.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        return BlogPost.objects.filter(status='published').order_by('-publish_date')

class BlogPostDetailView(DetailView):
    model = BlogPost
    template_name = 'core/blog_post_detail.html'
    context_object_name = 'post'

class LatestPostsFeed(Feed):
    title = "NEXUS Marketplace Blog"
    link = reverse_lazy('core:blog_post_list')
    description = "New updates and articles from NEXUS Marketplace."

    def items(self):
        return BlogPost.objects.filter(status='published').order_by('-publish_date')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return truncatewords(item.content, 30)

@require_POST
def subscribe_newsletter(request):
    email = request.POST.get('email')
    if not email:
        return JsonResponse({'status': 'error', 'message': 'Email is required.'}, status=400)
    
    try:
        obj, created = NewsletterSubscriber.objects.get_or_create(email=email)
        if created:
            return JsonResponse({'status': 'success', 'message': 'Thanks for subscribing!'})
        else:
            return JsonResponse({'status': 'info', 'message': 'You are already subscribed.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'An error occurred. Please try again.'}, status=500)


# --- Phase 4: Authenticity Feedback Endpoint ---
@login_required
@require_http_methods(["POST"])
def report_product_authenticity(request, pk):
    """AJAX endpoint for buyers to report suspected fake/inauthentic products."""
    try:
        product = Product.objects.get(pk=pk, is_active=True)
    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Product not found.'}, status=404)
    
    form = AuthenticityFeedbackForm(request.POST, request.FILES)
    if form.is_valid():
        feedback = form.save(commit=False)
        feedback.product = product
        feedback.reporter = request.user
        feedback.save()
        
        # Automatically create an AuthenticityReview for admin
        AuthenticityReview.objects.get_or_create(
            product=product,
            status='pending',
            defaults={
                'flagged_by': request.user,
                'reason': f"Buyer feedback: {feedback.get_feedback_type_display()}"
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message': _('Thank you for reporting. Our team will review this shortly.'),
            'feedback_id': feedback.id
        })
    else:
        errors = form.errors.as_json()
        return JsonResponse({
            'status': 'error',
            'message': _('Please fix the errors and try again.'),
            'errors': json.loads(errors)
        }, status=400)