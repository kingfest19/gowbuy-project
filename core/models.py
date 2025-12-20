# c:\Users\Hp\Desktop\Nexus\core\models.py
import logging # <<< Added import for logging
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings # To link to your custom user model
from django.utils.text import slugify # To generate slugs automatically
from django.utils import timezone # To record confirmation time
from django.urls import reverse # To generate URLs for models
from decimal import Decimal # For accurate price representation
from django.db.models import Sum # For Sum aggregation
from django.core.validators import MinValueValidator, MaxValueValidator # For review ratings
from django.utils.translation import gettext_lazy as _ # For verbose names in ProductImage
import uuid # For generating order IDs

logger = logging.getLogger(__name__) # <<< Added logger instance

# --- Category Model ---
class Category(models.Model):
    """
    Represents a product category (e.g., Electronics, Books, Clothing).
    Supports hierarchical categories (subcategories).
    """
    name = models.CharField(max_length=200, unique=True, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True, help_text="URL-friendly version of the name. Leave blank to auto-generate.")
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True, help_text="Optional image for the category.")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories', help_text="Assign if this is a subcategory.")
    is_active = models.BooleanField(default=True, help_text="Is this category currently visible/usable?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' -> '.join(full_path[::-1])

    def get_absolute_url(self):
        return reverse('core:category_detail', kwargs={'category_slug': self.slug})

# --- Helper function for vendor uploads ---
def vendor_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/vendors/<vendor_slug>/<filename>
    return f'vendors/{instance.slug}/{filename}'

# --- Vendor Model ---  <!-- <<< DEFINED BEFORE VendorReview -->
class Vendor(models.Model):
    """
    Represents a seller in the marketplace.
    """
    FULFILLMENT_CHOICES = [
        ('nexus', _('Fulfilled by Nexus')),
        ('vendor', _('Fulfilled by Vendor')),
    ]
    
    VERIFICATION_METHOD_BUSINESS = 'BUSINESS'
    VERIFICATION_METHOD_INDIVIDUAL = 'INDIVIDUAL'
    VERIFICATION_METHOD_CHOICES = [
        (VERIFICATION_METHOD_BUSINESS, _('I have a registered business')),
        (VERIFICATION_METHOD_INDIVIDUAL, _('I am registering as an individual (using National ID)')),
    ]

    VERIFICATION_STATUS_NOT_SUBMITTED = 'NOT_SUBMITTED'
    VERIFICATION_STATUS_PENDING_REVIEW = 'PENDING_REVIEW'
    VERIFICATION_STATUS_VERIFIED = 'VERIFIED'
    VERIFICATION_STATUS_REJECTED = 'REJECTED'
    VERIFICATION_STATUS_NEEDS_RESUBMISSION = 'NEEDS_RESUBMISSION' # If initial submission had issues
    VERIFICATION_STATUS_CHOICES = [
        (VERIFICATION_STATUS_NOT_SUBMITTED, _('Not Submitted')),
        (VERIFICATION_STATUS_PENDING_REVIEW, _('Pending Review')),
        (VERIFICATION_STATUS_VERIFIED, _('Verified')),
        (VERIFICATION_STATUS_REJECTED, _('Rejected')),
        (VERIFICATION_STATUS_NEEDS_RESUBMISSION, _('Needs Resubmission')),
    ]
    

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='vendor_profile', on_delete=models.CASCADE, help_text="The user account managing this vendor profile.")
    name = models.CharField(max_length=200, unique=True, help_text="Public name of the vendor/store.")
    slug = models.SlugField(max_length=200, unique=True, blank=True, help_text="URL-friendly version of the vendor name. Leave blank to auto-generate.")
    description = models.TextField(blank=True, null=True, help_text="Public description of the vendor.")
    story = models.TextField(blank=True, null=True, verbose_name=_("Our Story"), help_text=_("Share the story behind your brand. This will be visible on your public profile."))
    contact_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    logo = models.ImageField(upload_to=vendor_directory_path, blank=True, null=True, help_text="Optional logo for the vendor.")
    # --- Location Fields ---
    street_address = models.CharField(max_length=255, blank=True, null=True, help_text=_("Street address for the vendor's physical location.")) # New field
    location_city = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(_("Latitude"), max_digits=9, decimal_places=6, null=True, blank=True, help_text=_("Vendor's precise latitude for pickup."))
    longitude = models.DecimalField(_("Longitude"), max_digits=9, decimal_places=6, null=True, blank=True, help_text=_("Vendor's precise longitude for pickup."))
    location_country = models.CharField(max_length=100, blank=True, null=True) # Consider django-countries app later
    # -----------------------
   
    # --- Verification Fields ---
    is_verified_by_admin = models.BooleanField(default=False, help_text="Has this vendor been manually verified by an admin?") # This might be redundant with verification_status
    verification_documents_submitted = models.BooleanField(default=False, help_text="Have any verification documents been submitted?") # This might be redundant
    verification_method = models.CharField(
        _("Verification Method"), max_length=20, choices=VERIFICATION_METHOD_CHOICES, 
        blank=True, null=True, help_text=_("How is the vendor verifying their identity/business?")
    )
    verification_status = models.CharField(
        _("Verification Status"), max_length=20, choices=VERIFICATION_STATUS_CHOICES, 
        default=VERIFICATION_STATUS_NOT_SUBMITTED, help_text=_("Current status of vendor verification.")
    )
    # Consolidated Verification Fields:
    business_registration_document = models.FileField(upload_to=vendor_directory_path, blank=True, null=True, help_text=_("e.g., Business Registration Certificate, Certificate of Incorporation"))
    tax_id_number = models.CharField(_("Tax Identification Number (TIN)"), max_length=100, blank=True, null=True) # Using this name for consistency with forms
    other_supporting_document = models.FileField(upload_to=vendor_directory_path, blank=True, null=True, help_text=_("Any other supporting document for business verification."))
    national_id_type = models.CharField(_("Type of National ID"), max_length=50, blank=True, null=True, help_text=_("e.g., National ID Card, Passport, Driver's License")) # Consider choices if you have a fixed list
    national_id_number = models.CharField(_("National ID Number"), max_length=100, blank=True, null=True)
    national_id_document = models.FileField(upload_to=vendor_directory_path, blank=True, null=True, help_text=_("Scanned copy of the National ID document."))

    # --- Removed duplicate/alternative verification fields ---
    # business_registration_doc (use business_registration_document)
    # tin_number (using tax_id_number for consistency with forms, though tin_number was also present)
    # other_business_doc (use other_supporting_document)
    # national_id_doc (use national_id_document)
    # Redundant national_id_type and national_id_number were also present and are now consolidated.
    # --- Shipping & Payment Info ---
    shipping_policy = models.TextField(blank=True, null=True, verbose_name=_("Shipping Policy"))
    return_policy = models.TextField(blank=True, null=True, verbose_name=_("Return Policy")) # Moved here for grouping
    # Example Mobile Money Fields (Adjust as needed)
    mobile_money_provider = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Mobile Money Provider")) # e.g., MTN, Vodafone, AirtelTigo
    mobile_money_number = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Mobile Money Number"))
    paypal_email = models.EmailField(blank=True, null=True, verbose_name=_("PayPal Email Address"))
    bank_account_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Bank Account Holder's Name"))
    bank_account_number = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Bank Account Number"))
    bank_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Bank Name"))
    bank_branch = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Bank Branch Name/Address"))
    # --- START: Advanced Payout Options ---
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Stripe Connect Account ID"), help_text=_("Your Stripe Connect account ID (e.g., acct_xxxxxxxx)."))
    payoneer_email = models.EmailField(blank=True, null=True, verbose_name=_("Payoneer Email Address"))
    wise_email = models.EmailField(blank=True, null=True, verbose_name=_("Wise (formerly TransferWise) Email Address"))
    crypto_wallet_address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Cryptocurrency Wallet Address"))
    crypto_wallet_network = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Crypto Network"), help_text=_("e.g., Bitcoin, Ethereum (ERC20), Tron (TRC20), etc."))
    # --- END: Advanced Payout Options ---
    # --- START: Payout Information (similar to ServiceProviderProfile) ---
    paystack_recipient_code = models.CharField(
        max_length=100, blank=True, null=True, editable=False, # System-managed
        verbose_name=_("Paystack Recipient Code (for Vendor Payouts)")
    )
    # --- START: Public Contact Information (as discussed) ---
    public_phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Public Phone Number"))
    public_email = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_("Public Email Address"))
    website_url = models.URLField(max_length=255, blank=True, null=True, verbose_name=_("Website URL"))
    facebook_url = models.URLField(max_length=255, blank=True, null=True, verbose_name=_("Facebook Profile URL"))
    instagram_url = models.URLField(max_length=255, blank=True, null=True, verbose_name=_("Instagram Profile URL"))
    twitter_url = models.URLField(max_length=255, blank=True, null=True, verbose_name=_("Twitter (X) Profile URL"))
    linkedin_url = models.URLField(max_length=255, blank=True, null=True, verbose_name=_("LinkedIn Profile URL"))
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True,
                                       verbose_name=_("WhatsApp Number"),
                                       help_text=_("Include country code, e.g., +12345678900. This will be visible."))
    # --- END: Public Contact Information ---
    # --- Status Fields ---
    is_approved = models.BooleanField(default=False, help_text="Is this vendor approved to sell products?")
    is_verified = models.BooleanField(default=False, help_text="Has this vendor been verified by NEXUS staff (e.g., identity checked)?")
    has_premium_3d_generation_access = models.BooleanField(
        default=False,
        verbose_name=_("Premium 3D Generation Access"),
        help_text=_("Grants access to the AI-powered 3D model generation feature.")
    )
    # --- Timestamps ---
    default_fulfillment_method = models.CharField(max_length=10, choices=FULFILLMENT_CHOICES, default='vendor', verbose_name=_("Default Fulfillment Method"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Basic uniqueness check for slug
            counter = 1
            original_slug = self.slug
            while Vendor.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # Assumes you'll create a URL pattern named 'vendor_detail'
        return reverse('core:vendor_detail', kwargs={'vendor_slug': self.slug})

    def get_business_info_status_display(self):
        # This is a placeholder. You need to implement the logic based on your fields.
        # For example, if business_registration_doc and tax_id_number are filled,
        # and national_id_doc is filled (if individual), then it's 'COMPLETED'.
        # If some are filled but not all, 'IN_PROGRESS'. If none, 'NOT_STARTED'.
        # This needs to be robust. Using consolidated field names now.
        if (self.verification_method == self.VERIFICATION_METHOD_BUSINESS and self.business_registration_document and self.tax_id_number) or \
           (self.verification_method == self.VERIFICATION_METHOD_INDIVIDUAL and self.national_id_document and self.national_id_number and self.national_id_type):
            return 'COMPLETED' # Simplified example
        elif self.business_registration_document or self.tax_id_number or self.national_id_document or self.national_id_number or self.national_id_type: # Check if any doc is present for in_progress
            return 'IN_PROGRESS'
        return 'NOT_STARTED'


    # --- Onboarding Checklist Methods ---
    def is_shop_info_complete(self):
        """Checks if essential shop information is filled out."""
        # Adjust these fields based on your Vendor model's requirements
        return all([
            self.name,
            self.description,
            self.logo, # Checks if a logo file is associated
            self.contact_email,
            # self.address_line1, # Assuming address_line1 is a key part of shop info
            self.location_city, # Example: check city
            self.location_country, # Example: check country
        ])

    def is_shipping_info_complete(self):
        """Checks if shipping information is provided and complete."""
        # This check is now based on the 'shipping_policy' field directly on the Vendor model.
        return bool(self.shipping_policy)


    def is_payment_info_complete(self):
        """Checks if payment information is provided and complete."""
        # This check is now based on fields directly on the Vendor model.
        return all([
            self.mobile_money_provider,
            self.mobile_money_number,
        ])

    def is_additional_info_complete(self):
        """Checks if additional information is provided and complete."""
        # The 'VendorAdditionalInfoForm' now only handles 'return_policy'.
        # We can consider this section "complete" if a return policy is set.
        # If this section is optional, we could just return True.
        # Let's assume having a return policy means this is complete.
        return bool(self.return_policy)


    def is_onboarding_complete(self):
        """Checks if all onboarding sections are complete."""
        return all([
            self.is_shop_info_complete(),
            self.get_business_info_status_display() == 'COMPLETED',
            self.is_shipping_info_complete(),
            self.is_payment_info_complete(),
            self.is_additional_info_complete()
        ])


# --- Product Model ---
class Product(models.Model):
    """
    Represents an item available for sale, listed by a specific vendor.
    Can be a physical or digital product.
    """
    PRODUCT_TYPE_CHOICES = (
        ('physical', _('Physical Product')),
        ('digital', _('Digital Product')),
    )
    vendor = models.ForeignKey(
        Vendor,
        related_name='products',
        on_delete=models.CASCADE,
        help_text="The vendor selling this product."
    )
    # --------------------------
    category = models.ForeignKey(Category, related_name='products', on_delete=models.PROTECT, help_text="Category this product belongs to.")
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, help_text="URL-friendly version of the name. Leave blank to auto-generate.")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in USD (or your base currency).")

    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES, default='physical', help_text=_("Type of product"))
    stock = models.PositiveIntegerField(default=0, help_text=_("Number of physical items in stock. Not applicable for digital products."))
    digital_file = models.FileField(upload_to='products/digital/', blank=True, null=True, help_text=_("Upload the file for digital products."))
    vendor_delivery_fee = models.DecimalField(_("Vendor's Delivery Fee (if FBM)"), max_digits=10, decimal_places=2, null=True, blank=True, default=Decimal('0.00'), help_text=_("Set this if you fulfill this product yourself and want to charge a specific delivery fee. Only applies if 'Product Fulfillment Method' is 'Fulfilled by Vendor'."))
    fulfillment_method = models.CharField(max_length=10, choices=Vendor.FULFILLMENT_CHOICES, blank=True, null=True, verbose_name=_("Product Fulfillment Method"), help_text=_("Leave blank to use vendor's default setting."))

    is_active = models.BooleanField(default=True, db_index=True, help_text="Is the product available for purchase (requires vendor approval too)?")
    # requires_shipping = models.BooleanField(default=True, help_text="Does this product require shipping? (Auto-set based on type)") # Consider adding this later
    is_featured = models.BooleanField(default=False, db_index=True, help_text="Should this product be featured (e.g., on homepage)?")
    created_at = models.DateTimeField(auto_now_add=True)
    keywords_for_ai = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Keywords for AI Description"),
        help_text=_("Optional: Comma-separated keywords to guide AI description generation (e.g., durable, eco-friendly, best gift).")
    )
    updated_at = models.DateTimeField(auto_now=True)
    three_d_model = models.FileField(
        upload_to='products/3d_models/',
        blank=True,
        null=True,
        verbose_name=_("3D Model File"),
        help_text=_("Upload a 3D model file (e.g., .glb, .gltf) for 3D viewing.")
    )
    ar_model = models.FileField(
        _("AR 3D Model"),
        upload_to='ar_models/', 
        blank=True, 
        null=True,
        help_text=_("Upload a .glb or .usdz file for the AR experience.")
    )

    class Meta:
        ordering = ('-created_at', 'name',)
        indexes = [
            models.Index(fields=['slug', 'id']),
            models.Index(fields=['vendor', 'is_active']), # Index for vendor-specific product queries
        ]
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            counter = 1
            original_slug = self.slug
            # Ensure slug uniqueness (consider vendor context if needed)
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        # Automatically set stock/shipping based on type?
        # if self.product_type == 'digital':
        #     self.stock = 0 # Or maybe 1 if using licenses? Or leave as is?
        #     # self.requires_shipping = False # If using requires_shipping field
        super().save(*args, **kwargs)

    def __str__(self):
        # Handle case where vendor might be None during the transition
        vendor_name = self.vendor.name if self.vendor else "[No Vendor Assigned]"
        return f"{self.name} (by {vendor_name})"

    @property
    def image(self):
        return self.images.first()

    def get_specifications(self):
        return {
            "Product Type": self.get_product_type_display(),
            "Stock": self.stock if self.product_type == 'physical' else 'N/A',
            "Vendor": self.vendor.name if self.vendor else 'N/A',
            "Keywords": self.keywords_for_ai if self.keywords_for_ai else 'None'
        }

    def get_additional_specifications(self):
        return {
            "Weight": "1kg",
            "Dimensions": "10x20x30 cm",
            "Material": "Cotton",
        }

    def get_absolute_url(self):
        return reverse('core:product_detail', kwargs={'product_slug': self.slug})

    def is_available(self):
        """Check if product is active AND its vendor is approved."""
        # Ensure vendor exists before checking approval
        return self.is_active and self.vendor and self.vendor.is_approved
    is_available.boolean = True
    is_available.short_description = 'Available?'

    def is_in_stock(self):
        """Check if product is in stock (always true for digital)."""
        if self.product_type == 'digital':
            return True
        return self.stock > 0
    is_in_stock.boolean = True
    is_in_stock.short_description = 'In Stock?'

# --- Address Model ---
class Address(models.Model):
    ADDRESS_TYPES = ( ('shipping', 'Shipping'), ('billing', 'Billing'), )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='addresses', on_delete=models.CASCADE)
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES)
    full_name = models.CharField(max_length=150, help_text="Recipient's full name")
    street_address = models.CharField(max_length=255)
    apartment_address = models.CharField(max_length=100, blank=True, null=True, help_text="Apt, suite, unit, building, floor, etc.")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, help_text="State / Province / Region")
    zip_code = models.CharField(max_length=20, verbose_name="ZIP / Postal Code")
    latitude = models.DecimalField(_("Latitude"), max_digits=9, decimal_places=6, null=True, blank=True, help_text=_("Precise latitude for the address."))
    longitude = models.DecimalField(_("Longitude"), max_digits=9, decimal_places=6, null=True, blank=True, help_text=_("Precise longitude for the address."))
    country = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_default = models.BooleanField(default=False, help_text="Is this the default address for this type?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ('-is_default', '-created_at')
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        constraints = [ models.UniqueConstraint(fields=['user', 'address_type'], condition=models.Q(is_default=True), name='unique_default_address_per_type') ]
    def __str__(self):
        return f"{self.get_address_type_display()} Address for {self.user.username}: {self.street_address}, {self.city}"

# --- Order Model ---
class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending Payment Choice')
        AWAITING_ESCROW_PAYMENT = 'AWAITING_ESCROW_PAYMENT', _('Awaiting Escrow Payment')
        AWAITING_DIRECT_PAYMENT = 'AWAITING_DIRECT_PAYMENT', _('Awaiting Direct Payment')
        ON_HOLD_FRAUD_REVIEW = 'ON_HOLD_FRAUD_REVIEW', _('On Hold (Fraud Review)')
        PROCESSING = 'PROCESSING', _('Processing')
        IN_PROGRESS = 'IN_PROGRESS', _('Service In Progress')
        SHIPPED = 'SHIPPED', _('Shipped')
        DELIVERED = 'DELIVERED', _('Delivered')
        PENDING_PAYOUT = 'PENDING_PAYOUT', _('Pending Payout')
        COMPLETED = 'COMPLETED', _('Completed & Paid Out')
        CANCELLED = 'CANCELLED', _('Cancelled')
        REFUNDED = 'REFUNDED', _('Refunded')
        DISPUTED = 'DISPUTED', _('Disputed')

    PAYMENT_METHOD_CHOICES = (
        ('escrow', _('Escrow (Paystack)')),
        ('direct', _('Direct Arrangement')),
        ('paypal', _('PayPal')),
        # Add other methods like 'cod' (Cash on Delivery) if needed
    )
    promotion = models.ForeignKey(
        'Promotion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text=_("The promotion applied to this order, if any.")
    )
    discount_amount = models.DecimalField(
        _("Discount Amount"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("The total discount amount applied to the order.")
    )

    # PAYMENT_STATUS_CHOICES = ( ('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed'), ) # Can be simplified or derived from STATUS

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True)
    order_id = models.CharField(max_length=120, unique=True, blank=True, help_text="Unique order identifier. Auto-generated.")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING, db_index=True)
    # payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', db_index=True) # Consider removing if status covers it
    platform_delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name=_("Platform (Nexus) Delivery Fee Component"))
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name=_("Order Delivery Fee"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='GHS', help_text=_("Currency of the order (e.g., GHS, USD)"))
    ordered = models.BooleanField(default=False) # Indicates if checkout process started (useful for finding pending orders)
    shipping_address = models.ForeignKey(Address, related_name='shipping_orders', on_delete=models.SET_NULL, null=True, blank=True)
    billing_address = models.ForeignKey(Address, related_name='billing_orders', on_delete=models.SET_NULL, null=True, blank=True)
    shipping_address_text = models.TextField(blank=True, null=True, help_text="Snapshot of shipping address at time of order.")
    billing_address_text = models.TextField(blank=True, null=True, help_text="Snapshot of billing address at time of order.")
    transaction_id = models.CharField(max_length=255, blank=True, null=True, help_text="Payment gateway transaction ID.")
    notes = models.TextField(blank=True, null=True, help_text="Internal notes about the order.")
    # --- Fields for Dual Payment System ---
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True, # Allow blank initially until choice is made
        null=True   # Allow null initially
    )
    paystack_ref = models.CharField(max_length=100, blank=True, null=True, help_text="Paystack transaction reference for verification.")
    # customer_confirmed_completion_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Customer Confirmed Completion At")) # Commented out
    tip_amount = models.DecimalField(
        _("Rider Tip Amount"), max_digits=10, decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Amount tipped to the rider by the customer.")
    )
    customer_confirmed_delivery_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Customer Confirmed Delivery/Completion"))

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
    def save(self, *args, **kwargs):
        if not self.order_id: self.order_id = self._generate_order_id()
        if self.shipping_address and not self.shipping_address_text: self.shipping_address_text = str(self.shipping_address)
        if self.billing_address and not self.billing_address_text: self.billing_address_text = str(self.billing_address)
        super().save(*args, **kwargs)
    def _generate_order_id(self):
        import datetime
        now = datetime.datetime.now()
        random_part = uuid.uuid4().hex[:6].upper()
        return f"NEXUS-{now.strftime('%Y%m%d')}-{random_part}"
    def calculate_total(self):
        total = sum(item.get_total_item_price() for item in self.items.all())
        # self.total_amount = total # Avoid saving here, calculate on demand or when finalizing
        return total

    # Use calculate_total for display, maybe rename get_total_cost if it exists elsewhere
    def get_total_cost(self):
        return self.calculate_total()

    def get_absolute_url(self):
        return reverse('core:order_detail', kwargs={'order_id': self.order_id})

    # --- Helper methods to determine order content based on type and category ---
    def _get_negotiable_category_slugs(self):
        from django.conf import settings # Import here to avoid circular dependency issues at model load time
        return getattr(settings, 'NEGOTIABLE_PRODUCT_CATEGORY_SLUGS', [])

    def has_negotiable_category_products(self):
        """Checks if any product in the order belongs to a 'negotiable' category."""
        negotiable_slugs = self._get_negotiable_category_slugs()
        if not negotiable_slugs: # If no slugs are configured, no products are considered negotiable this way
            return False
        return self.items.filter(
            product__isnull=False,
            product__category__slug__in=negotiable_slugs
        ).exists()

    def has_digital_products(self):
        return self.items.filter(product__product_type='digital').exists()

    def has_physical_products(self):
        return self.items.filter(product__product_type='physical').exists()

    def has_services(self):
        return self.items.filter(service_package__isnull=False).exists()

    def has_only_services(self):
        """Checks if the order contains exclusively services and no products."""
        return self.has_services() and \
               not self.items.filter(product__isnull=False).exists()
    # --- End Helper methods ---


# --- START: Service Marketplace Models ---

class ServiceCategory(models.Model):
    """
    Represents a category for services (e.g., Graphic Design, Tutoring, Plumbing).
    """
    name = models.CharField(max_length=200, unique=True, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True, help_text="URL-friendly version of the name. Leave blank to auto-generate.")
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='services/categories/', blank=True, null=True, help_text="Optional image for the service category.")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories', help_text="Assign if this is a subcategory.")
    is_active = models.BooleanField(default=True, help_text="Is this category currently visible/usable?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Service Category'
        verbose_name_plural = 'Service Categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        # Similar logic to Product Category for displaying hierarchy
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' -> '.join(full_path[::-1])

    def get_absolute_url(self):
        return reverse('core:service_category_detail', kwargs={'category_slug': self.slug})

class Service(models.Model):
    """
    Represents a service offered by a user or vendor.
    """
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='provided_services', on_delete=models.CASCADE, help_text="The user offering this service.")
    # Or link to Vendor? models.ForeignKey(Vendor, related_name='services', on_delete=models.CASCADE) - Decide based on who offers services. Let's use User for now.
    category = models.ForeignKey(ServiceCategory, related_name='services', on_delete=models.PROTECT, help_text="Category this service belongs to.")
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, help_text="URL-friendly version of the title. Leave blank to auto-generate.")
    description = models.TextField(help_text=_("Detailed description of the service offered."))
    # --- START: Professional Profile Fields ---
    skills = models.TextField(blank=True, help_text=_("List relevant skills, separated by commas (e.g., Python, Graphic Design, Copywriting)."))
    experience = models.TextField(blank=True, help_text=_("Summarize your relevant experience (e.g., years in the field, key projects)."))
    education = models.TextField(blank=True, help_text=_("List relevant education or certifications."))
    # --- END: Professional Profile Fields ---
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Price if fixed, leave blank if variable/negotiable.")
    location = models.CharField(max_length=255, blank=True, help_text="Location where the service is offered (e.g., 'Accra', 'Remote').")
    is_active = models.BooleanField(default=True, db_index=True, help_text="Is the service currently available?")
    is_featured = models.BooleanField(default=False, db_index=True, help_text="Should this service be featured (e.g., on homepage)?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at', 'title',)
        verbose_name = 'Service'
        verbose_name_plural = 'Services'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Add uniqueness check for slug similar to Product/Vendor
            counter = 1
            original_slug = self.slug
            while Service.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} (by {self.provider.username})"

    def get_absolute_url(self):
        return reverse('core:service_detail', kwargs={'service_slug': self.slug})

# --- START: ServicePackage Model (Moved Up) ---
class ServicePackage(models.Model):
    """
    Represents a pricing tier/package for a specific service.
    (e.g., Basic, Standard, Premium).
    """
    service = models.ForeignKey(Service, related_name='packages', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, help_text=_("Give this package a descriptive name (e.g., 'Basic Logo', 'Full Website Setup', 'Hourly Consultation')."))
    description = models.TextField(help_text=_("Describe what's included in this package."))
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text=_("Price for this package."))
    delivery_time = models.PositiveIntegerField(help_text=_("Estimated delivery time in days."))
    revisions = models.PositiveIntegerField(default=0, help_text=_("Number of revisions included."))
    # Optional: Add more specific boolean features for packages if needed (e.g., feature_1 = models.BooleanField(default=False, ...))
    # feature_1 = models.BooleanField(default=False, ...)
    display_order = models.PositiveIntegerField(default=0, help_text=_("Order in which packages are displayed (0=first)."))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['service', 'display_order', 'price'] # Order by service, then display order, then price
        verbose_name = _("Service Package")
        verbose_name_plural = _("Service Packages")

    def __str__(self):
        return f"{self.service.title} - {self.name} (GH₵{self.price})"
# --- END: ServicePackage Model ---

# --- OrderItem Model ---
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    # --- Link to Product OR ServicePackage ---
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.SET_NULL, null=True, blank=True)
    service_package = models.ForeignKey(ServicePackage, related_name='order_items', on_delete=models.SET_NULL, null=True, blank=True)
    # Store the provider at the time of order creation (relevant for services)
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='provided_order_items')
    product_name = models.CharField(max_length=255, blank=True, help_text="Snapshot of product name at time of order.")
    service_package_name = models.CharField(max_length=255, blank=True, help_text="Snapshot of service package name at time of order.")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per unit at the time of order.")
    fulfillment_method = models.CharField(max_length=10, choices=Vendor.FULFILLMENT_CHOICES, default='vendor', verbose_name=_("Fulfillment Method")) # Added fulfillment method
    item_delivery_charge = models.DecimalField(_("Item Delivery Charge"), max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text=_("Delivery charge specifically for this item, if applicable (e.g., vendor-set)."))
    quantity = models.PositiveIntegerField(default=1)
    class Meta:
        ordering = ('order', 'product_name')
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
    def save(self, *args, **kwargs):
        if self.product and not self.product_name: self.product_name = self.product.name
        if self.service_package and not self.service_package_name:
            self.service_package_name = self.service_package.name
            # Store provider when saving a service package item
            if not self.provider:
                self.provider = self.service_package.service.provider
        super().save(*args, **kwargs)
    def __str__(self):
        if self.product:
            item_desc = self.product.name if self.product else self.product_name or "[Deleted Product]"
        elif self.service_package:
            item_desc = self.service_package.name if self.service_package else self.service_package_name or "[Deleted Service Package]"
        else:
            item_desc = "[Unknown Item]"
        return f"{self.quantity} x {item_desc} for Order {self.order.order_id}"
    def get_total_item_price(self):
        if self.price is not None and self.quantity is not None:
            return self.price * self.quantity
        return Decimal('0.00') # Default to 0.00 if price or quantity is None

    # Add a property to easily access the service title if needed
    @property
    def service_title(self):
        return self.service_package.service.title if self.service_package and self.service_package.service else _("N/A")

# --- Wishlist Model ---
class Wishlist(models.Model):
    """
    Represents a user's wishlist, containing multiple products.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_profile') # Each user has one wishlist
    products = models.ManyToManyField(Product, blank=True, related_name='wishlisted_by_users') # Products in this wishlist
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Wishlist")
        verbose_name_plural = _("Wishlists")

    def __str__(self):
        return f"Wishlist for {self.user.username}"
# --- WishlistItem Model ---
class WishlistItem(models.Model):
    """
    Represents a product added to a user's wishlist.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='wishlist_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='wishlisted_by', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ('-added_at',)
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'

    def __str__(self):
        return f"'{self.product.name}' in {self.user.username}'s wishlist"

# --- ProductReview Model ---
class ProductReview(models.Model):
    """
    Represents a review and rating submitted by a user for a product.
    """
    RATING_CHOICES = (
        (1, '1 - Terrible'),
        (2, '2 - Poor'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    )
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reviews', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True, null=True)
    video = models.FileField(upload_to='reviews/videos/', null=True, blank=True, help_text="Optional: Upload a short video review (MP4, WebM recommended).")
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True, help_text="Is this review visible to the public? (For moderation)")

    class Meta:
        unique_together = ('product', 'user')
        ordering = ('-created_at',)
        verbose_name = 'Product Review'
        verbose_name_plural = 'Product Reviews'

    def __str__(self):
        return f"Review for '{self.product.name}' by {self.user.username} ({self.rating} stars)"

# --- VendorReview Model --- <!-- <<< DEFINED AFTER Vendor -->
class VendorReview(models.Model):
    """
    Represents a review and rating submitted by a user for a Vendor.
    """
    RATING_CHOICES = (
        (1, '1 - Terrible'),
        (2, '2 - Poor'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    )
    vendor = models.ForeignKey(Vendor, related_name='reviews', on_delete=models.CASCADE) # Now 'Vendor' is defined
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='vendor_reviews', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(_("Review"), blank=True, null=True)
    reply = models.TextField(_("Vendor Reply"), blank=True, null=True)
    replied_at = models.DateTimeField(_("Replied At"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True, help_text="Is this review visible to the public?")

    class Meta:
        unique_together = ('vendor', 'user')
        ordering = ('-created_at',)
        verbose_name = 'Vendor Review'
        verbose_name_plural = 'Vendor Reviews'

    def __str__(self):
        return f"Review for '{self.vendor.name}' by {self.user.username} ({self.rating} stars)"

# --- ProductImage Model ---
class ProductImage(models.Model):
    """
    Represents an individual image associated with a Product.
    """
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/gallery/', help_text="Upload a product image.")
    alt_text = models.CharField(max_length=255, blank=True, null=True, help_text="Optional: Descriptive text for accessibility (e.g., 'Red T-shirt front view').")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at'] # Default order images are shown
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")

    def __str__(self):
        return f"Image for {self.product.name} ({self.id})"


# --- ProductVideo Model ---
class ProductVideo(models.Model):
    """
    Represents a video associated with a Product (e.g., promotional, tutorial).
    """
    product = models.ForeignKey(Product, related_name='videos', on_delete=models.CASCADE)
    video = models.FileField(upload_to='products/videos/', help_text="Upload a product video (MP4, WebM recommended).")
    title = models.CharField(max_length=255, blank=True, null=True, help_text="Optional title for the video.")
    description = models.TextField(blank=True, null=True, help_text="Optional description.")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # No additional fields needed here.
    class Meta:
        ordering = ['uploaded_at']
        verbose_name = _("Product Video")
    
    verbose_name_plural = _("Product Videos")

    def __str__(self):
        return self.title or f"Video for {self.product.name} ({self.id})"
# --- END: ServiceVideo Model ---

# --- Cart Model ---
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carts', null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True) # For anonymous users
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ordered = models.BooleanField(default=False) # Becomes True when an order is placed from this cart

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Anonymous Cart ({self.session_key or 'Unsaved'})"

    def get_cart_total(self):
        return sum(item.get_total_item_price() for item in self.items.all())

    def get_item_count(self):
        return sum(item.quantity for item in self.items.all())

# --- CartItem Model ---
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    service_package = models.ForeignKey('ServicePackage', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A cart can have a specific product once and a specific service package once.
        unique_together = (('cart', 'product'), ('cart', 'service_package'))

    def clean(self):
        # Enforce that a cart item is for one thing only.
        if self.product and self.service_package:
            raise ValidationError(_("A cart item cannot be for both a product and a service package simultaneously."))
        if not self.product and not self.service_package:
            raise ValidationError(_("A cart item must be for either a product or a service package."))

    def __str__(self):
        return f"{self.quantity} x {self.name} in cart {self.cart.id}"

    @property
    def name(self):
        if self.product:
            return self.product.name
        if self.service_package:
            return f"{self.service_package.service.title} - {self.service_package.name}"
        return _("Invalid Item")

    @property
    def price(self):
        if self.product:
            return self.product.price
        if self.service_package:
            return self.service_package.price
        return Decimal('0.00')

    def get_total_item_price(self):
        return self.price * self.quantity

# --- SavedForLaterItem Model ---
class SavedForLaterItem(models.Model):
    """
    Represents an item a user has saved for later from their cart.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_for_later_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    service_package = models.ForeignKey('ServicePackage', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1) # Keep the quantity from the cart
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'product'), ('user', 'service_package'))
        ordering = ['-added_at']
        verbose_name = _("Saved For Later Item")
        verbose_name_plural = _("Saved For Later Items")

    def clean(self):
        if self.product and self.service_package:
            raise ValidationError(_("A saved item cannot be for both a product and a service package simultaneously."))
        if not self.product and not self.service_package:
            raise ValidationError(_("A saved item must be for either a product or a service package."))

    def __str__(self):
        return f"{self.quantity} x {self.name} in {self.user.username}'s saved list"

    @property
    def name(self):
        if self.product: return self.product.name
        if self.service_package: return f"{self.service_package.service.title} - {self.service_package.name}"
        return _("Invalid Item")

    @property
    def price(self):
        if self.product: return self.product.price
        if self.service_package: return self.service_package.price
        return Decimal('0.00')


# --- Promotion Model ---
class Promotion(models.Model):
    """
    Represents a discount or promotion (e.g., coupon code, sale).
    """
    PROMOTION_TYPES = (
        ('percentage', 'Percentage Discount'),
        ('fixed_amount', 'Fixed Amount Discount'),
        # ('buy_x_get_y', 'Buy X Get Y Free'), # Future enhancement
    )
    SCOPE_CHOICES = (
        ('all', 'All Products'),
        ('category', 'Specific Category'),
        ('product', 'Specific Product(s)'),
        ('vendor', 'Specific Vendor'),
    )

    name = models.CharField(max_length=255, help_text="Internal name for the promotion (e.g., 'Summer Sale 20% Off')")
    description = models.TextField(blank=True, help_text="Optional description for customers.")
    code = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Coupon code users enter (optional, leave blank for automatic discounts).")
    promo_type = models.CharField(max_length=20, choices=PROMOTION_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage (e.g., 20.00 for 20%) or fixed amount.")
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='all')
    # --- Scope-specific relations ---
    applicable_categories = models.ManyToManyField(Category, blank=True, related_name='promotions', help_text="Select categories if scope is 'Specific Category'.")
    applicable_products = models.ManyToManyField(Product, blank=True, related_name='promotions', help_text="Select products if scope is 'Specific Product(s)'.")
    applicable_vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, blank=True, null=True, related_name='promotions', help_text="Select vendor if scope is 'Specific Vendor'.")
    # --- Conditions & Limits ---
    start_date = models.DateTimeField(help_text="When the promotion becomes active.")
    end_date = models.DateTimeField(help_text="When the promotion expires.")
    minimum_purchase_amount = models.DecimalField(
        _("Minimum Purchase Amount"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("The promotion will only apply if the cart total is above this amount. Leave blank for no minimum.")
    )
    usage_limit = models.PositiveIntegerField(
        _("Usage Limit"),
        null=True,
        blank=True,
        help_text=_("The total number of times this promotion can be used. Leave blank for unlimited uses.")
    )
    usage_count = models.PositiveIntegerField(
        _("Usage Count"),
        default=0,
        editable=False,
        help_text=_("The number of times this promotion has been used.")
    )
    uses_per_customer = models.PositiveIntegerField(blank=True, null=True, help_text="Maximum number of times a single customer can use this promotion (optional).")
    is_active = models.BooleanField(default=True, help_text="Is this promotion currently active (within dates and usage limits)?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-start_date',)
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"

    def __str__(self):
        return f"{self.name} ({self.code or 'Automatic'})"

    # TODO: Add methods to check validity (is_active, within dates, usage limits, scope applicability)

# --- AdCampaign Model ---
class AdCampaign(models.Model):
    """
    Represents a paid advertising campaign for a product or vendor.
    """
    PLACEMENT_CHOICES = (
        ('homepage_banner', 'Homepage Banner'),
        ('search_results_top', 'Search Results (Top)'),
        ('category_sidebar', 'Category Sidebar'),
        # Add more placements as needed
    )
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='ad_campaigns', help_text="The vendor running the campaign.")
    name = models.CharField(max_length=255, help_text="Internal name for the campaign.")
    promoted_product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True, related_name='ad_campaigns', help_text="Product being promoted (optional, if promoting the vendor store itself).")
    placement = models.CharField(max_length=50, choices=PLACEMENT_CHOICES, help_text="Where the ad will be displayed.")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Total budget for the campaign (optional).")
    is_active = models.BooleanField(default=True, help_text="Is the campaign currently running?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-start_date',)
        verbose_name = "Ad Campaign"
        verbose_name_plural = "Ad Campaigns"

    def __str__(self):
        target = self.promoted_product.name if self.promoted_product else self.vendor.name
        return f"Ad: {target} ({self.get_placement_display()})"

    # TODO: Add methods to check if active based on dates

# --- Notification Model ---
class Notification(models.Model):
    """
    Represents a notification for a user.
    """
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.URLField(blank=True, null=True, help_text="Optional link to navigate to when notification is clicked.")
    # Optional: Add a field for notification type if you have different kinds of notifications
    # NOTIFICATION_TYPES = ( ('info', 'Information'), ('alert', 'Alert'), ('update', 'Update'), )
    # notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='info')

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message[:50]}..."

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    def mark_as_unread(self):
        if self.is_read:
            self.is_read = False
            self.save(update_fields=['is_read'])

# --- UserProfile Model ---
class UserProfile(models.Model):
    """
    Stores additional information for a user.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='userprofile') # Changed related_name
    bio = models.TextField(blank=True, null=True, help_text=_("A short bio about the user."))
    profile_picture = models.ImageField(upload_to='users/profile_pics/', blank=True, null=True, help_text=_("User's profile picture."))
    date_of_birth = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Location"))
    website_url = models.URLField(max_length=200, blank=True, null=True, verbose_name=_("Website URL"))
    linkedin_url = models.URLField(max_length=200, blank=True, null=True, verbose_name=_("LinkedIn Profile URL"))
    twitter_url = models.URLField(max_length=200, blank=True, null=True, verbose_name=_("Twitter (X) Profile URL"))
    github_url = models.URLField(max_length=200, blank=True, null=True, verbose_name=_("GitHub Profile URL"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return f"Profile for {self.user.username}"

    # Example: Method to get profile picture URL or a default
    def get_profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        # Make sure you have a default image at 'core/static/core/images/default_profile_pic.png'
        # or adjust the path accordingly.
        return settings.STATIC_URL + 'core/images/default_profile_pic.png' 

# --- START: ServiceReview Model ---
class ServiceReview(models.Model):
    """
    Represents a review and rating submitted by a user for a service.
    """
    RATING_CHOICES = (
        (1, '1 - Terrible'),
        (2, '2 - Poor'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    )
    service = models.ForeignKey(Service, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='service_reviews', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(_("Review"), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True, help_text="Is this review visible to the public? (For moderation)")

    class Meta:
        unique_together = ('service', 'user') # User can only review a service once
        ordering = ('-created_at',)
        verbose_name = 'Service Review'
        verbose_name_plural = 'Service Reviews'

    def __str__(self):
        return f"Review for '{self.service.title}' by {self.user.username} ({self.rating} stars)"
# --- END: ServiceReview Model ---

# --- START: ServiceImage Model ---
class ServiceImage(models.Model):
    """
    Represents an individual image associated with a Service (gallery/portfolio).
    """
    service = models.ForeignKey(Service, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='services/gallery/', help_text=_("Upload an image showcasing the service or portfolio work."))
    alt_text = models.CharField(max_length=255, blank=True, null=True, help_text=_("Optional: Descriptive text for accessibility."))
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at'] # Default order images are shown
        verbose_name = _("Service Image")
        verbose_name_plural = _("Service Images")

    def __str__(self):
        return f"Image for {self.service.title} ({self.id})"
# --- END: ServiceImage Model ---

# --- START: ServiceVideo Model ---
class ServiceVideo(models.Model):
    """
    Represents a video associated with a Service (e.g., demo, explanation).
    """
    service = models.ForeignKey(Service, related_name='videos', on_delete=models.CASCADE)
    video = models.FileField(upload_to='services/videos/', help_text=_("Upload a video showcasing the service (MP4, WebM recommended)."))
    title = models.CharField(max_length=255, blank=True, null=True, help_text=_("Optional title for the video."))
    description = models.TextField(blank=True, null=True, help_text=_("Optional description."))
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']
        verbose_name = _("Service Video")
        verbose_name_plural = _("Service Videos")

    def __str__(self):
        return self.title or f"Video for {self.service.title} ({self.id})"
# --- END: ServiceVideo Model ---

# --- START: Service Provider Profile Model ---
class ServiceProviderProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_provider_profile',
        verbose_name=_("User")
    )
    business_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Business Name (Optional)"),
        help_text=_("If different from your personal name.")
    )
    bio = models.TextField(
        verbose_name=_("Service Provider Bio/Description"),
        help_text=_("Describe your services, experience, and what you offer.")
    )
    # --- START: Payout Information ---
    PAYOUT_MM_PROVIDER_CHOICES = (
        ('', _('Select Provider')),
        ('MTN', _('MTN Mobile Money')),
        ('VODAFONE', _('Vodafone Cash')),
        ('AIRTELTIGO', _('AirtelTigo Money')),
    )
    mobile_money_provider = models.CharField(
        max_length=50, choices=PAYOUT_MM_PROVIDER_CHOICES, blank=True, null=True,
        verbose_name=_("Payout Mobile Money Provider")
    )
    mobile_money_number = models.CharField(
        max_length=15, blank=True, null=True, verbose_name=_("Payout Mobile Money Number")
    )
    # --- START: Added missing payout fields ---
    paypal_email = models.EmailField(blank=True, null=True, verbose_name=_("PayPal Email Address"))
    bank_account_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Bank Account Holder's Name"))
    bank_account_number = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Bank Account Number"))
    bank_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Bank Name"))
    bank_branch = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Bank Branch Name/Address"))
    # --- END: Added missing payout fields ---
    paystack_recipient_code = models.CharField(
        max_length=100, blank=True, null=True, editable=False, # System-managed
        verbose_name=_("Paystack Recipient Code")
    )
    # --- START: Advanced Payout Options ---
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Stripe Connect Account ID"), help_text=_("Your Stripe Connect account ID (e.g., acct_xxxxxxxx)."))
    payoneer_email = models.EmailField(blank=True, null=True, verbose_name=_("Payoneer Email Address"))
    wise_email = models.EmailField(blank=True, null=True, verbose_name=_("Wise (formerly TransferWise) Email Address"))
    crypto_wallet_address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Cryptocurrency Wallet Address"))
    crypto_wallet_network = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Crypto Network"), help_text=_("e.g., Bitcoin, Ethereum (ERC20), Tron (TRC20), etc."))
    # --- END: Advanced Payout Options ---
    # --- END: Payout Information ---
    is_approved = models.BooleanField(default=False, help_text=_("Is this service provider profile approved by admin?"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Profile Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Profile Updated At"))

    class Meta:
        verbose_name = _("Service Provider Profile")
        verbose_name_plural = _("Service Provider Profiles")

    def __str__(self):
        return f"Service Provider Profile for {self.user.username}"

    def get_available_payout_balance(self):
        """
        Calculates the available payout balance for this service provider.
        """
        completed_bookings = ServiceBooking.objects.filter(
            provider=self.user,
            status='COMPLETED'
        ).select_related('service_package')

        gross_earnings = sum((booking.service_package.price for booking in completed_bookings if booking.service_package), Decimal('0.00'))

        raw_commission_rate = getattr(settings, 'PLATFORM_SERVICE_COMMISSION_RATE', Decimal('0.10'))
        if not isinstance(raw_commission_rate, Decimal):
            commission_rate = Decimal(str(raw_commission_rate))
        else:
            commission_rate = raw_commission_rate
        total_commission = gross_earnings * commission_rate
        net_earnings = gross_earnings - total_commission

        completed_payouts = PayoutRequest.objects.filter(
            service_provider_profile=self,
            status='completed'
        ).aggregate(total_paid=Sum('amount_requested'))['total_paid'] or Decimal('0.00')

        return (net_earnings - completed_payouts).quantize(Decimal('0.01'))

# --- START: PortfolioItem Model ---
class PortfolioItem(models.Model):
    """
    Represents a single portfolio item for a Service Provider to showcase their work.
    """
    provider_profile = models.ForeignKey(ServiceProviderProfile, on_delete=models.CASCADE, related_name='portfolio_items')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='portfolio_images/', blank=True, null=True, help_text=_("Upload an image for your portfolio item."))
    link = models.URLField(max_length=255, blank=True, null=True, help_text=_("Or, provide a link to a video (e.g., YouTube, Vimeo) or external project."))
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = _("Portfolio Item")
        verbose_name_plural = _("Portfolio Items")
        # This constraint ensures that an item has an image OR a link, but not both.
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(image__isnull=False, link__isnull=True) |
                    models.Q(image__isnull=True, link__isnull=False)
                ),
                name='image_or_link_present',
                violation_error_message=_("A portfolio item must have either an image or a link, but not both.")
            )
        ]

    def __str__(self):
        return f"{self.title} for {self.provider_profile.user.username}"

# --- END: PortfolioItem Model ---


# --- START: Rider Model ---
class RiderProfile(models.Model):
    VEHICLE_CHOICES = [
        ('motorcycle', _('Motorcycle')),
        ('bicycle', _('Bicycle')),
        ('car', _('Car')),
        ('van', _('Van')),
        ('other', _('Other')),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rider_profile')
    phone_number = models.CharField(_("Phone Number"), max_length=20, blank=True, null=True, help_text=_("Your primary contact number for deliveries.")) # Can be pre-filled from UserProfile
    vehicle_type = models.CharField(_("Vehicle Type"), max_length=20, choices=VEHICLE_CHOICES, default='motorcycle')
    vehicle_registration_number = models.CharField(_("Current Vehicle Registration Number"), max_length=50, blank=True, null=True)
    license_number = models.CharField(_("Driver's License Number"), max_length=50, blank=True, null=True) # Optional, depending on vehicle
    address = models.TextField(_("Operating Address / Area"), blank=True, null=True, help_text=_("Primary area you operate in."))
    # For live tracking (Phase 2 and beyond)
    current_latitude = models.DecimalField(_("Current Latitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(_("Current Longitude"), max_digits=9, decimal_places=6, null=True, blank=True)

    
    # Current/Active Documents for Approved Rider (can be updated)
    # These can be initially populated from RiderApplication upon approval
    current_vehicle_registration_document = models.FileField(upload_to='rider_profiles/registrations/', blank=True, null=True, help_text=_("Current vehicle registration document."))
    current_drivers_license_front = models.FileField(upload_to='rider_profiles/licenses/', blank=True, null=True, help_text=_("Current driver's license (front)."))
    current_drivers_license_back = models.FileField(upload_to='rider_profiles/licenses/', blank=True, null=True, help_text=_("Current driver's license (back)."))
    current_id_card_front = models.FileField(upload_to='rider_profiles/ids/', blank=True, null=True, help_text=_("Current national ID card (front)."))
    current_id_card_back = models.FileField(upload_to='rider_profiles/ids/', blank=True, null=True, help_text=_("Current national ID card (back)."))
    current_vehicle_picture = models.FileField(upload_to='rider_profiles/vehicle_pictures/', blank=True, null=True, help_text=_("Current picture of the vehicle."))
    is_approved = models.BooleanField(_("Approved by Admin"), default=False, help_text=_("Designates whether the rider has been approved by platform admins."))
    is_available = models.BooleanField(_("Available for Deliveries"), default=False, help_text=_("Is the rider currently available to take new delivery assignments?"))
    # current_location = models.PointField(null=True, blank=True) # For GeoDjango if you implement live tracking

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rider: {self.user.username}"

    class Meta:
        verbose_name = _("Rider Profile")
        verbose_name_plural = _("Rider Profiles")
        ordering = ['-created_at'] # Order by user for easier management
# --- END: Rider Model ---

# --- START: Rider Application Model ---
class RiderApplication(models.Model):
    """
    Stores details submitted by a user applying to become a rider.
    This is separate from RiderProfile which is created upon approval.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rider_application')
    phone_number = models.CharField(_("Phone Number"), max_length=20, help_text=_("Your primary contact number for deliveries."))
    vehicle_type = models.CharField(_("Vehicle Type"), max_length=20, choices=RiderProfile.VEHICLE_CHOICES, default='motorcycle') # Use choices from RiderProfile
    vehicle_registration_number = models.CharField(_("Vehicle Registration Number"), max_length=50) # Made required
    license_number = models.CharField(_("Driver's License Number"), max_length=50) # Made required
    address = models.TextField(_("Operating Address / Area"), help_text=_("Primary area you operate in."))

    # Documents (assuming these are part of the application)
    vehicle_registration_document = models.FileField(upload_to='rider_applications/docs/', blank=True, null=True, verbose_name=_("Vehicle Registration Document"))
    drivers_license_front = models.FileField(upload_to='rider_applications/docs/', verbose_name=_("Driver's License (Front)")) # Made required
    drivers_license_back = models.FileField(upload_to='rider_applications/docs/', verbose_name=_("Driver's License (Back)")) # Made required
    id_card_front = models.FileField(upload_to='rider_applications/docs/', blank=True, null=True, verbose_name=_("National ID (Front)"))
    id_card_back = models.FileField(upload_to='rider_applications/docs/', blank=True, null=True, verbose_name=_("National ID (Back)"))
    profile_picture = models.ImageField(upload_to='rider_applications/profile_pics/', blank=True, null=True, verbose_name=_("Profile Picture"))
    vehicle_picture = models.ImageField(upload_to='rider_applications/vehicle_pics/', verbose_name=_("Picture of Vehicle")) # Made required

    agreed_to_terms = models.BooleanField(_("Agreed to Terms"), default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_reviewed = models.BooleanField(_("Reviewed by Admin"), default=False)
    is_approved = models.BooleanField(_("Approved"), default=False) # Final decision

    def __str__(self):
        return f"Rider Application for {self.user.username}"
# --- END: Rider Application Model ---

# --- START: DeliveryTask Model ---
class DeliveryTask(models.Model):
    """
    Represents a single delivery task for an order, to be assigned to a rider.
    """
    STATUS_CHOICES = [
        ('PENDING_ASSIGNMENT', _('Pending Assignment')),
        ('ACCEPTED_BY_RIDER', _('Accepted by Rider')),
        ('PICKED_UP', _('Picked Up')),
        ('OUT_FOR_DELIVERY', _('Out for Delivery')),
        ('DELIVERED', _('Delivered')),
        ('CANCELLED', _('Cancelled')),
        ('FAILED', _('Failed')),
    ]

    task_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True, verbose_name=_("Task ID"))
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='delivery_tasks', verbose_name=_("Order"))
    rider = models.ForeignKey('RiderProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_tasks', verbose_name=_("Assigned Rider"))
    status = models.CharField(_("Task Status"), max_length=30, choices=STATUS_CHOICES, default='PENDING_ASSIGNMENT', db_index=True)

    # Address Information (denormalized for performance and history)
    pickup_address_text = models.TextField(_("Pickup Address"), blank=True)
    pickup_latitude = models.DecimalField(_("Pickup Latitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    pickup_longitude = models.DecimalField(_("Pickup Longitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_address_text = models.TextField(_("Delivery Address"))
    delivery_latitude = models.DecimalField(_("Delivery Latitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_longitude = models.DecimalField(_("Delivery Longitude"), max_digits=9, decimal_places=6, null=True, blank=True)

    # Financials
    delivery_fee = models.DecimalField(_("Total Delivery Fee"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    rider_earning = models.DecimalField(_("Rider Earning"), max_digits=10, decimal_places=2, null=True, blank=True, help_text=_("Amount the rider earns from this delivery."))
    platform_commission = models.DecimalField(_("Platform Commission"), max_digits=10, decimal_places=2, null=True, blank=True, help_text=_("Commission earned by the platform for this delivery."))

    # Timestamps
    estimated_pickup_time = models.DateTimeField(_("Estimated Pickup Time"), null=True, blank=True)
    actual_pickup_time = models.DateTimeField(_("Actual Pickup Time"), null=True, blank=True)
    estimated_delivery_time = models.DateTimeField(_("Estimated Delivery Time"), null=True, blank=True)
    actual_delivery_time = models.DateTimeField(_("Actual Delivery Time"), null=True, blank=True)

    special_instructions = models.TextField(_("Special Instructions"), blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Delivery Task")
        verbose_name_plural = _("Delivery Tasks")
        ordering = ['-created_at']

    def __str__(self):
        return f"Task {self.task_id} for Order {self.order.order_id}"

    def get_absolute_url(self):
        return reverse('core:rider_task_detail', kwargs={'task_id': self.task_id})
# --- END: DeliveryTask Model ---

# --- START: Rider Boost Visibility Models ---
class BoostPackage(models.Model):
    BOOST_TYPE_CHOICES = [
        ('search_top', _('Top of Search Results')),
        ('featured_profile', _('Featured Profile Section')),
        # Add other types as needed, e.g., 'category_boost'
    ]

    name = models.CharField(_("Package Name"), max_length=100, unique=True, help_text=_("e.g., 24-Hour Search Boost, 7-Day Featured Rider"))
    description = models.TextField(_("Description"), help_text=_("Detailed description of what this boost package offers."))
    boost_type = models.CharField(_("Boost Type"), max_length=50, choices=BOOST_TYPE_CHOICES)
    duration_hours = models.PositiveIntegerField(_("Duration (in hours)"), help_text=_("How long this boost will be active once purchased."))
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2, help_text=_("Price of this boost package in GHS."))
    is_active = models.BooleanField(_("Is Active?"), default=True, help_text=_("Is this package currently available for purchase?"))
    icon_class = models.CharField(_("Font Awesome Icon Class"), max_length=50, blank=True, null=True, help_text=_("e.g., fas fa-rocket, fas fa-star"))
    display_order = models.PositiveIntegerField(_("Display Order"), default=0, help_text=_("Order in which packages are displayed to riders."))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Boost Package")
        verbose_name_plural = _("Boost Packages")
        ordering = ['display_order', 'price']

    def __str__(self):
        return f"{self.name} ({self.get_boost_type_display()}) - GH₵{self.price}"

    @property
    def duration_timedelta(self):
        return timezone.timedelta(hours=self.duration_hours)

# Moved ActiveRiderBoost outside of BoostPackage
class ActiveRiderBoost(models.Model):
    rider_profile = models.ForeignKey(RiderProfile, on_delete=models.CASCADE, related_name='active_boosts', verbose_name=_("Rider Profile"))
    boost_package = models.ForeignKey(BoostPackage, on_delete=models.PROTECT, related_name='activations', verbose_name=_("Boost Package"))
    activated_at = models.DateTimeField(_("Activated At"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Expires At"))
    is_active = models.BooleanField(_("Is Currently Active?"), default=True, help_text=_("Automatically set based on expiry. Can be manually overridden."))

    class Meta:
        verbose_name = _("Active Rider Boost")
        verbose_name_plural = _("Active Rider Boosts")
        ordering = ['-expires_at', 'rider_profile']

    def __str__(self):
        return f"{self.rider_profile.user.username}'s {self.boost_package.name} (Expires: {self.expires_at.strftime('%Y-%m-%d %H:%M')})"

    def save(self, *args, **kwargs):
        if not self.expires_at and self.boost_package:
            self.expires_at = timezone.now() + self.boost_package.duration_timedelta
        if self.expires_at and self.is_active and self.expires_at < timezone.now():
            self.is_active = False
        super().save(*args, **kwargs)

# --- OrderNote Model ---
class OrderNote(models.Model):
    order = models.ForeignKey(Order, related_name='notes_history', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, help_text="User who added the note (can be admin, vendor, or customer).")
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_customer_notified = models.BooleanField(default=False, help_text="Was the customer notified about this note?")

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Order Note")
        verbose_name_plural = _("Order Notes")

    def __str__(self):
        user_display = self.user.username if self.user else "System"
        return f"Note for Order {self.order.order_id} by {user_display} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
# --- END: OrderNote Model ---

# --- START: ProductVariant Model ---
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, help_text=_("e.g., Color, Size")) # Attribute name
    value = models.CharField(max_length=100, help_text=_("e.g., Red, Large")) # Attribute value
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text=_("Additional price for this variant, if any."))
    stock = models.PositiveIntegerField(default=0, help_text=_("Stock for this specific variant."))
    sku = models.CharField(max_length=100, blank=True, null=True, unique=True, help_text=_("Stock Keeping Unit for this variant."))

    class Meta:
        unique_together = ('product', 'name', 'value') # Ensure unique combinations
        verbose_name = _("Product Variant")
        verbose_name_plural = _("Product Variants")

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"
# --- END: ProductVariant Model ---

# --- START: ServiceBooking Model ---
class ServiceBooking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', _('Pending Confirmation')),
        ('ACCEPTED', _('Accepted by Provider')),
        ('IN_PROGRESS', _('In Progress')),
        ('COMPLETED', _('Completed')),
        ('CANCELLED_BY_USER', _('Cancelled by User')),
        ('CANCELLED_BY_PROVIDER', _('Cancelled by Provider')),
        ('DISPUTED', _('Disputed')),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='service_bookings', help_text=_("The overall order this booking belongs to."))
    service_package = models.ForeignKey(ServicePackage, on_delete=models.PROTECT, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='service_bookings_made')
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='service_bookings_received')
    booking_date = models.DateTimeField(default=timezone.now, help_text=_("Date and time the booking was made."))
    # Optional: preferred_start_date, specific_requirements
    preferred_start_date = models.DateTimeField(null=True, blank=True, help_text=_("User's preferred start date/time for the service."))
    specific_requirements = models.TextField(blank=True, help_text=_("Any specific requirements or notes from the user for this service."))
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-booking_date']
        verbose_name = _("Service Booking")
        verbose_name_plural = _("Service Bookings")

    def __str__(self):
        return f"Booking for {self.service_package.name} by {self.user.username} with {self.provider.username}"
# --- END: ServiceBooking Model ---

# --- START: ServiceAvailability Model ---
class ServiceAvailability(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='availability_slots')
    # Or link to ServiceProviderProfile if availability is per provider, not per service
    # provider_profile = models.ForeignKey(ServiceProviderProfile, on_delete=models.CASCADE, related_name='availability_slots')

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)
    # Optional: recurring rules (e.g., weekly on Mondays 9-5) - complex, consider libraries like `django-scheduler`

    class Meta:
        ordering = ['start_time']
        verbose_name = _("Service Availability Slot")
        verbose_name_plural = _("Service Availability Slots")
        constraints = [
            models.CheckConstraint(check=models.Q(end_time__gt=models.F('start_time')), name='end_time_after_start_time')
        ]

    def __str__(self):
        return f"Availability for {self.service.title}: {self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')}"
# --- END: ServiceAvailability Model ---

# --- START: ServiceAddon Model ---
class ServiceAddon(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='addons')
    # Or link to ServicePackage if addons are per-package
    # service_package = models.ForeignKey(ServicePackage, on_delete=models.CASCADE, related_name='addons')
    name = models.CharField(max_length=100, help_text=_("e.g., Extra Fast Delivery, Source File"))
    description = models.TextField(blank=True, help_text=_("Describe what this addon includes."))
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text=_("Additional price for this addon."))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Service Add-on")
        verbose_name_plural = _("Service Add-ons")

    def __str__(self):
        return f"{self.name} for {self.service.title} (+{self.price})"
# --- END: ServiceAddon Model ---

# --- START: UserFeedback Model ---
class UserFeedback(models.Model):
    FEEDBACK_TYPES = (
        ('general', _('General Feedback')),
        ('bug_report', _('Bug Report')),
        ('feature_request', _('Feature Request')),
        ('complaint', _('Complaint')),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, help_text=_("User providing feedback (if logged in)."))
    email = models.EmailField(blank=True, help_text=_("Email if user is not logged in or wants to provide a different one."))
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES, default='general')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    attachment = models.FileField(upload_to='feedback_attachments/', blank=True, null=True, help_text=_("Optional: Screenshot or other relevant file."))
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("User Feedback")
        verbose_name_plural = _("User Feedback")

    def __str__(self):
        user_display = self.user.username if self.user else self.email or "Anonymous"
        return f"{self.get_feedback_type_display()} from {user_display}: {self.subject}"
# --- END: UserFeedback Model ---

# --- START: SystemNotification Model ---
class SystemNotification(models.Model):
    LEVEL_CHOICES = (
        ('info', _('Information')),
        ('warning', _('Warning')),
        ('error', _('Error')),
        ('success', _('Success')),
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='info')
    start_display_at = models.DateTimeField(default=timezone.now, help_text=_("When to start showing this notification."))
    end_display_at = models.DateTimeField(null=True, blank=True, help_text=_("When to stop showing this notification (optional)."))
    is_active = models.BooleanField(default=True, help_text=_("Is this notification currently active?"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_display_at']
        verbose_name = _("System Notification")
        verbose_name_plural = _("System Notifications")

    def __str__(self):
        return f"[{self.get_level_display().upper()}] {self.title}"
# --- END: SystemNotification Model ---

# --- START: UserPreferences Model ---
class UserPreferences(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    receive_email_notifications = models.BooleanField(default=True, help_text=_("Receive general email notifications."))
    receive_promotional_emails = models.BooleanField(default=False, help_text=_("Receive promotional emails and newsletters."))
    # Add more preference fields as needed, e.g., theme, language (if not handled by Django's i18n)
    # preferred_language = models.CharField(max_length=10, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.username}"
# --- END: UserPreferences Model ---

# --- START: SecurityLog Model ---
class SecurityLog(models.Model):
    ACTION_CHOICES = (
        ('login_success', _('Login Success')),
        ('login_failed', _('Login Failed')),
        ('logout', _('Logout')),
        ('password_change', _('Password Changed')),
        ('password_reset_request', _('Password Reset Requested')),
        ('password_reset_success', _('Password Reset Successful')),
        # Add more security-related actions
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True, help_text=_("Additional details about the event."))

    class Meta:
        ordering = ['-timestamp']
        verbose_name = _("Security Log")
        verbose_name_plural = _("Security Logs")

    def __str__(self):
        user_display = self.user.username if self.user else "Anonymous/System"
        return f"{self.action} by {user_display} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
# --- END: SecurityLog Model ---

# --- START: TermsAndConditions / PrivacyPolicy Models ---
class LegalDocument(models.Model):
    """Abstract base class for legal documents like T&C and Privacy Policy."""
    version = models.CharField(max_length=20, unique=True, help_text=_("e.g., '1.0', '2023-03-15'"))
    content = models.TextField()
    effective_date = models.DateField()
    published_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False, help_text=_("Is this the currently active version? Only one version should be active."))

    class Meta:
        abstract = True
        ordering = ['-effective_date', '-version']

    def save(self, *args, **kwargs):
        # Ensure only one version is active
        if self.is_active:
            type(self).objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

class TermsAndConditions(LegalDocument):
    class Meta(LegalDocument.Meta): # Inherit ordering
        verbose_name = _("Terms and Conditions")
        verbose_name_plural = _("Terms and Conditions")

    def __str__(self):
        return f"Terms and Conditions v{self.version} (Effective: {self.effective_date})"

class PrivacyPolicy(LegalDocument):
    class Meta(LegalDocument.Meta): # Inherit ordering
        verbose_name = _("Privacy Policy")
        verbose_name_plural = _("Privacy Policies")

    def __str__(self):
        return f"Privacy Policy v{self.version} (Effective: {self.effective_date})"
# --- END: TermsAndConditions / PrivacyPolicy Models ---

# --- START: Transaction Model ---
class Transaction(models.Model):
    """
    Records financial transactions (e.g., payments, refunds, payouts).
    """
    TRANSACTION_TYPES = (
        ('payment', _('Payment')),
        ('refund', _('Refund')),
        ('payout', _('Payout to Vendor/Provider')),
        ('platform_commission', _('Platform Commission')), # <!-- <<< Add this -->
        ('vendor_plan_purchase', _('Vendor Plan Purchase')),
        ('boost_purchase', _('Rider Boost Purchase')),
        ('escrow_hold', _('Escrow Hold')),
        ('escrow_release', _('Escrow Release')),
        ('reward_redemption', _('Reward Redemption')),
        # Add more types as needed
    )
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', help_text=_("User initiating or receiving the transaction."))
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', help_text=_("Associated order, if any."))
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default=settings.DEFAULT_CURRENCY_CODE if hasattr(settings, 'DEFAULT_CURRENCY_CODE') else 'GHS') # Use your default currency
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway_transaction_id = models.CharField(max_length=255, blank=True, null=True, help_text=_("ID from the payment gateway (e.g., Paystack ref)."))
    description = models.TextField(blank=True, null=True, help_text=_("Optional description of the transaction."))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")

    def __str__(self):
        user_display = self.user.username if self.user else "System"
        return f"{self.get_transaction_type_display()} of {self.currency} {self.amount} for {user_display} ({self.get_status_display()})"
# --- END: Transaction Model ---

# --- START: PayoutRequest Model ---
class PayoutRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Pending Admin Review')),
        ('processing', _('Processing Payout')),
        ('completed', _('Payout Completed')),
        ('rejected', _('Payout Rejected')),
        ('failed', # New status for when a payout attempt fails
         _('Payout Failed')),
    )
    rider_profile = models.ForeignKey(RiderProfile, on_delete=models.CASCADE, related_name='payout_requests', verbose_name=_("Rider"), null=True, blank=True)
    vendor_profile = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='payout_requests', verbose_name=_("Vendor"), null=True, blank=True) # Added Vendor link
    service_provider_profile = models.ForeignKey(ServiceProviderProfile, on_delete=models.CASCADE, related_name='payout_requests', verbose_name=_("Service Provider"), null=True, blank=True)
    amount_requested = models.DecimalField(_("Amount Requested"), max_digits=10, decimal_places=2)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method_details = models.TextField(_("Payment Method Details"), blank=True, null=True, help_text=_("E.g., Bank Name, Account Number, Mobile Money Number & Name."))
    requested_at = models.DateTimeField(_("Requested At"), auto_now_add=True)
    processed_at = models.DateTimeField(_("Processed At"), null=True, blank=True)
    admin_notes = models.TextField(_("Admin Notes"), blank=True, null=True, help_text=_("Notes from admin regarding this payout request (e.g., reason for rejection)."))
    # Link to the actual transaction once the payout is made
    transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='payout_request_fulfilled', verbose_name=_("Fulfilled by Transaction"))

    class Meta:
        verbose_name = _("Payout Request")
        verbose_name_plural = _("Payout Requests")
        ordering = ['-requested_at']

    def __str__(self):
        if self.rider_profile:
            profile_user = self.rider_profile.user.username
        elif self.vendor_profile:
            profile_user = self.vendor_profile.name
        elif self.service_provider_profile:
            profile_user = self.service_provider_profile.user.username
        else:
            profile_user = "Unknown Profile"
        return f"Payout request of {self.amount_requested} for {profile_user} ({self.get_status_display()})"


    def clean(self):
        super().clean()
        profiles_count = sum(p is not None for p in [self.rider_profile, self.vendor_profile, self.service_provider_profile])
        if profiles_count == 0:
            raise ValidationError(_("A payout request must be associated with a rider, vendor, or service provider."))
        if profiles_count > 1:
            raise ValidationError(_("A payout request can only be associated with one profile type (rider, vendor, or service provider)."))
    # You can add methods here, e.g., to check if a rider has a pending request
# --- END: Transaction Model ---

# --- START: Escrow Model ---
class Escrow(models.Model):
    """
    Manages funds held in escrow for an order.
    """
    STATUS_CHOICES = (
        ('HELD', _('Funds Held')),
        ('RELEASED_TO_PROVIDER', _('Released to Provider')),
        ('REFUNDED_TO_USER', _('Refunded to User')),
        ('DISPUTED', _('Disputed')),
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='escrow_details')
    amount_held = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='HELD')
    # Timestamps for status changes
    held_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    # Link to related transactions
    hold_transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='escrow_holds')
    release_transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='escrow_releases')
    refund_transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='escrow_refunds')

    class Meta:
        verbose_name = _("Escrow Record")
        verbose_name_plural = _("Escrow Records")

    def __str__(self):
        return f"Escrow for Order {self.order.order_id} - Status: {self.get_status_display()}"
# --- END: Escrow Model ---

# --- START: Dispute Model ---
class Dispute(models.Model):
    """
    Manages disputes raised for an order.
    """
    STATUS_CHOICES = (
        ('OPEN', _('Open')),
        ('UNDER_REVIEW', _('Under Review')),
        ('RESOLVED_FAVOR_USER', _('Resolved in Favor of User')),
        ('RESOLVED_FAVOR_PROVIDER', _('Resolved in Favor of Provider/Vendor')),
        ('CLOSED', _('Closed')),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='disputes')
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='raised_disputes')
    reason = models.TextField(help_text=_("Reason for the dispute."))
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='OPEN')
    # Optional: Link to Escrow if dispute is about escrowed funds
    escrow = models.ForeignKey(Escrow, on_delete=models.SET_NULL, null=True, blank=True, related_name='disputes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_details = models.TextField(blank=True, null=True, help_text=_("Details of how the dispute was resolved."))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Dispute")
        verbose_name_plural = _("Disputes")

    def __str__(self):
        return f"Dispute for Order {self.order.order_id} by {self.raised_by.username} ({self.get_status_display()})"
# --- END: Dispute Model ---

# --- START: Conversation & Message Models (for messaging system) ---
class Conversation(models.Model):
    """
    Represents a conversation between users, often related to an order or service.
    """
    # Participants can be more than two, e.g., user, provider, and admin for dispute resolution
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    # Optional: Link to a specific context like an order or dispute
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    dispute = models.ForeignKey(Dispute, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    subject = models.CharField(max_length=255, blank=True, help_text=_("Optional subject for the conversation."))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Timestamp of the last message

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")

    def __str__(self):
        participant_names = ", ".join([p.username for p in self.participants.all()])
        return f"Conversation between {participant_names}" + (f" re: {self.subject}" if self.subject else "")

    def get_other_participant(self, user):
        """
        Given a user, returns the other participant in a 2-person conversation.
        Returns the first other participant if more than 2 are involved.
        Returns None if the user is not a participant.
        """
        if user in self.participants.all():
            # Prefetching participants in the view is recommended for performance
            return self.participants.exclude(id=user.id).first()
        return None

class Message(models.Model):
    """
    Represents a single message within a conversation.
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(_("Read At"), null=True, blank=True)
    is_read = models.BooleanField(default=False) # Could be more complex with read receipts per participant

    class Meta:
        ordering = ['timestamp']
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")

    def save(self, *args, **kwargs):
        # Update conversation's updated_at timestamp when a new message is saved
        if not self.pk: # Only on creation
            self.conversation.updated_at = timezone.now()
            self.conversation.save(update_fields=['updated_at'])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
# --- END: Conversation & Message Models ---

# --- START: ShippingMethod Model ---
class ShippingMethod(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    base_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Optional: Fields for cost calculation (e.g., per_kg_cost, per_km_cost)
    # is_active = models.BooleanField(default=True)
    # vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True, blank=True, help_text="If specific to a vendor")

    def __str__(self):
        return self.name
# --- END: ShippingMethod Model ---

# --- START: PaymentGateway Model ---
class PaymentGateway(models.Model):
    name = models.CharField(max_length=100, unique=True) # e.g., Paystack, Stripe, PayPal
    # Configuration details (store securely, e.g., using django-environ or HashiCorp Vault)
    # api_key = models.CharField(max_length=255, blank=True)
    # secret_key = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    supports_escrow = models.BooleanField(default=False)

    def __str__(self):
        return self.name
# --- END: PaymentGateway Model ---

# --- START: TaxRate Model ---
class TaxRate(models.Model):
    name = models.CharField(max_length=100) # e.g., VAT, Sales Tax
    rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="e.g., 15.00 for 15%")
    country = models.CharField(max_length=2, blank=True, null=True, help_text="ISO 3166-1 alpha-2 country code (e.g., GH, US).")
    # region = models.CharField(max_length=100, blank=True, null=True, help_text="Specific state/province if applicable.")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.rate_percentage}%)"
# --- END: TaxRate Model ---

# --- START: Currency Model ---
class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True, help_text="ISO 4217 currency code (e.g., GHS, USD, EUR).")
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5)
    exchange_rate_to_base = models.DecimalField(max_digits=12, decimal_places=6, default=1.000000, help_text="Exchange rate relative to the site's base currency.")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} ({self.symbol})"
# --- END: Currency Model ---

# --- START: SiteSettings Model ---
class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default="NEXUS Marketplace")
    # base_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='+', help_text="The primary currency for the site.")
    # default_language = models.CharField(max_length=10, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)
    # contact_email = models.EmailField(blank=True)
    # social_media_links = models.JSONField(blank=True, null=True, help_text="e.g., {'facebook': 'url', 'twitter': 'url'}")
    # maintenance_mode = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Site Setting" # Singular
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Site Settings"

    # Ensure only one instance of SiteSettings can be created (Singleton pattern)
    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            # This should be ValidationError from django.core.exceptions
            from django.core.exceptions import ValidationError
            raise ValidationError('There can be only one SiteSettings instance')
        return super(SiteSettings, self).save(*args, **kwargs)
# --- END: SiteSettings Model ---

# --- START: Blog Models ---
class BlogCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    def __str__(self): return self.name

class BlogPost(models.Model):
    STATUS_CHOICES = ( ('draft', 'Draft'), ('published', 'Published'), )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique_for_date='publish_date', blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_posts')
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    content = models.TextField()
    publish_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    # featured_image = models.ImageField(upload_to='blog_featured_images/', blank=True, null=True)
    # tags = TaggableManager(blank=True) # Requires django-taggit

    class Meta:
        ordering = ('-publish_date',)
    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    def __str__(self): return self.title
    def get_absolute_url(self): return reverse('core:blog_post_detail', args=[self.publish_date.year, self.publish_date.month, self.publish_date.day, self.slug])
# --- END: Blog Models ---

# --- START: FAQ Model ---
class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    # category = models.CharField(max_length=100, blank=True, help_text="e.g., Account, Payments, Shipping")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'question']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    def __str__(self): return self.question
# --- END: FAQ Model ---

# --- START: SupportTicket Models ---
class SupportTicket(models.Model):
    STATUS_CHOICES = ( ('open', 'Open'), ('in_progress', 'In Progress'), ('resolved', 'Resolved'), ('closed', 'Closed'), )
    PRIORITY_CHOICES = ( ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent'), )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    # order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_tickets')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', limit_choices_to={'is_staff': True})

    class Meta:
        ordering = ['-created_at']
    def __str__(self): return f"Ticket #{self.id}: {self.subject} ({self.get_status_display()})"

class TicketResponse(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # User who wrote the response
    message = models.TextField()




# --- START: UserActivity Model ---
class UserActivity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=100) # e.g., 'viewed_product', 'added_to_cart', 'placed_order'
    # content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    # object_id = models.PositiveIntegerField(null=True, blank=True)
    # content_object = GenericForeignKey('content_type', 'object_id') # Link to any model
    details = models.JSONField(blank=True, null=True, help_text="e.g., {'product_id': 123, 'page_url': '/product/xyz/'}")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "User Activities"
    def __str__(self): return f"{self.user.username} - {self.activity_type} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
# --- END: UserActivity Model ---

# --- START: AuditLog Model ---
class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, help_text="User who performed the action (if applicable).")
    action = models.CharField(max_length=255, help_text="Description of the action performed.")
    # content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True, help_text="Model affected.")
    # object_id = models.PositiveIntegerField(null=True, blank=True, help_text="Primary key of the object affected.")
    # content_object = GenericForeignKey('content_type', 'object_id')
    # changes = models.JSONField(blank=True, null=True, help_text="JSON detailing what changed (e.g., {'field': {'old': 'val1', 'new': 'val2'}}).")
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
    def __str__(self):
        user_display = self.user.username if self.user else "System"
        return f"{self.action} by {user_display} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
# --- END: AuditLog Model ---

# --- START: APIKey Model ---
class APIKey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_keys')
    key = models.CharField(max_length=64, unique=True, editable=False) # Generated key
    name = models.CharField(max_length=100, help_text="A descriptive name for this API key (e.g., 'Mobile App Key').")
    is_active = models.BooleanField(default=True)
    # permissions = models.JSONField(blank=True, null=True, help_text="Define specific permissions for this key (e.g., {'read_products': true, 'write_orders': false}).")
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.key:
            import secrets
            self.key = secrets.token_hex(32)
        super().save(*args, **kwargs)
    def __str__(self): return f"API Key for {self.user.username}: {self.name}"
# --- END: APIKey Model ---

# --- START: WebhookEvent Model ---
class WebhookEvent(models.Model):
    STATUS_CHOICES = ( ('pending', 'Pending'), ('processing', 'Processing'), ('success', 'Success'), ('failed', 'Failed'), )
    event_type = models.CharField(max_length=100, db_index=True) # e.g., 'order.created', 'payment.succeeded'
    payload = models.JSONField() # The data received from the webhook
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    # source = models.CharField(max_length=50, help_text="e.g., 'paystack', 'stripe', 'internal'")
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    # error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-received_at']
    def __str__(self): return f"Webhook: {self.event_type} ({self.get_status_display()}) at {self.received_at.strftime('%Y-%m-%d %H:%M')}"
# --- END: WebhookEvent Model ---

# --- START: FeatureFlag / ABTest Models ---
class FeatureFlag(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Unique name for the feature flag (e.g., 'new_checkout_flow').")
    is_active = models.BooleanField(default=False, help_text="Is this feature globally active?")
    # rollout_percentage = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Percentage of users to whom this feature is rolled out (0-100).")
    # target_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, help_text="Specific users to enable this feature for.")
    # target_groups = models.ManyToManyField(Group, blank=True, help_text="Specific groups to enable this feature for.") # Requires from django.contrib.auth.models import Group
    description = models.TextField(blank=True)

    def __str__(self): return f"Feature: {self.name} (Active: {self.is_active})"

class ABTest(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # control_group_percentage = models.PositiveSmallIntegerField(default=50, validators=[MinValueValidator(0), MaxValueValidator(100)])
    # variant_a_feature = models.ForeignKey(FeatureFlag, on_delete=models.SET_NULL, null=True, blank=True, related_name='ab_test_variant_a')
    # variant_b_feature = models.ForeignKey(FeatureFlag, on_delete=models.SET_NULL, null=True, blank=True, related_name='ab_test_variant_b')
    is_active = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self): return f"A/B Test: {self.name} (Active: {self.is_active})"

class UserSegment(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # rules = models.JSONField(help_text="Define rules for segmenting users (e.g., {'country': 'GH', 'total_spent__gt': 1000}).")
    # users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='segments')

    def __str__(self): return self.name
# --- END: FeatureFlag / ABTest Models ---

# --- START: Notification Template Models ---
class EmailTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g., 'order_confirmation', 'password_reset'")
    subject = models.CharField(max_length=255)
    html_content = models.TextField(help_text="HTML content with placeholders (e.g., {{ username }}, {{ order_id }}).")
    plain_text_content = models.TextField(blank=True, help_text="Plain text version (optional).")

    def __str__(self): return self.name

class SMSTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g., 'shipping_update', 'otp_verification'")
    content = models.CharField(max_length=160, help_text="SMS content with placeholders (max 160 chars).") # Max length might vary

    def __str__(self): return self.name

class PushNotificationTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g., 'new_message_alert', 'sale_starts_now'")
    title = models.CharField(max_length=100)
    body = models.CharField(max_length=255)
    # icon_url = models.URLField(blank=True, null=True)
    # click_action_url = models.URLField(blank=True, null=True)

    def __str__(self): return self.name
# --- END: Notification Template Models ---

# --- START: Affiliate Marketing Models ---
class Affiliate(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='affiliate_profile')
    referral_code = models.CharField(max_length=20, unique=True, blank=True)
    # commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00, help_text="Percentage commission (e.g., 5.00 for 5%).")
    # website_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            import secrets
            self.referral_code = secrets.token_urlsafe(8).upper() # Generate a unique code
        super().save(*args, **kwargs)
    def __str__(self): return f"Affiliate: {self.user.username} ({self.referral_code})"

class AffiliateClick(models.Model):
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name='clicks')
    # referred_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_by_clicks')
    # product_clicked = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Click for {self.affiliate.referral_code} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class AffiliatePayout(models.Model):
    STATUS_CHOICES = ( ('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed'), )
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # payment_method_details = models.TextField(help_text="e.g., Mobile Money number, Bank Account details.")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    # transaction_reference = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self): return f"Payout of {self.amount} to {self.affiliate.user.username} ({self.get_status_display()})"
# --- END: Affiliate Marketing Models ---

# --- START: Loyalty Program Models ---
class LoyaltyProgram(models.Model):
    name = models.CharField(max_length=100, default="NEXUS Rewards")
    # points_per_currency_spent = models.PositiveIntegerField(default=1, help_text="Points earned per unit of base currency spent.")
    # min_purchase_for_points = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    def __str__(self): return self.name

class LoyaltyTier(models.Model):
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='tiers')
    name = models.CharField(max_length=50) # e.g., Bronze, Silver, Gold
    # min_points_required = models.PositiveIntegerField(default=0)
    # benefits_description = models.TextField(blank=True) # e.g., "Exclusive discounts, early access to sales"
    # discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['program'] # Add min_points_required to ordering if used
    def __str__(self): return f"{self.program.name} - {self.name} Tier"

class UserPoints(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loyalty_points')
    # current_tier = models.ForeignKey(LoyaltyTier, on_delete=models.SET_NULL, null=True, blank=True)
    total_points_earned = models.PositiveIntegerField(default=0)
    points_balance = models.PositiveIntegerField(default=0) # Spendable points
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self): return f"{self.user.username}'s Points: {self.points_balance}"

class Reward(models.Model):
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='rewards')
    name = models.CharField(max_length=100) # e.g., "GH₵10 Discount Coupon", "Free Shipping"
    description = models.TextField(blank=True)
    points_cost = models.PositiveIntegerField(_("Points Cost"), default=0)
    # reward_type = models.CharField(max_length=20, choices=(('coupon', 'Coupon'), ('discount', 'Discount'), ('free_item', 'Free Item')))
    # reward_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # If applicable
    is_active = models.BooleanField(default=True)

    def __str__(self): return self.name

class UserReward(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='redeemed_rewards')
    reward = models.ForeignKey(Reward, on_delete=models.PROTECT) # Don't delete reward if user has it
    redeemed_at = models.DateTimeField(auto_now_add=True)
    # is_used = models.BooleanField(default=False)
    # expiry_date = models.DateTimeField(null=True, blank=True)

    def __str__(self): return f"{self.user.username} redeemed {self.reward.name}"
# --- END: Loyalty Program Models ---

# --- START: Coupon & Gift Card Models ---
class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    # discount_type = models.CharField(max_length=10, choices=(('percent', 'Percentage'), ('fixed', 'Fixed')))
    # discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    # valid_from = models.DateTimeField()
    # valid_to = models.DateTimeField()
    # min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    # max_uses = models.PositiveIntegerField(blank=True, null=True)
    # uses_per_customer = models.PositiveIntegerField(default=1)
    # current_uses = models.PositiveIntegerField(default=0, editable=False)
    is_active = models.BooleanField(default=True)

    def __str__(self): return self.code

class UserCoupon(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coupons')
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    # order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, help_text="Order where this coupon was used.")
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'coupon') # User can use a specific coupon instance once
    def __str__(self): return f"{self.user.username} used coupon {self.coupon.code}"

class GiftCard(models.Model):
    code = models.CharField(max_length=20, unique=True, blank=True) # Auto-generate
    initial_balance = models.DecimalField(max_digits=10, decimal_places=2)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    # created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_gift_cards') # Admin or system
    # purchased_for_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_gift_cards')
    # expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            import secrets
            self.code = f"NEXUSGC-{secrets.token_hex(6).upper()}"
        if self.pk is None: # On creation
            self.current_balance = self.initial_balance
        super().save(*args, **kwargs)
    def __str__(self): return f"Gift Card {self.code} (Balance: {self.current_balance})"

class UserGiftCard(models.Model): # Tracks usage of a gift card
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='used_gift_cards')
    gift_card = models.ForeignKey(GiftCard, on_delete=models.PROTECT)
    # order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount_used = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.user.username} used {self.amount_used} from Gift Card {self.gift_card.code}"
# --- END: Coupon & Gift Card Models ---

# --- START: Pricing Plan Model ---
class PricingPlan(models.Model):
    PLAN_TYPE_CHOICES = (
        ('vendor_premium', _('Vendor Premium Plan')),
        # Add other types here if you expand, e.g., ('rider_boost_pack', 'Rider Boost Pack')
    )
    name = models.CharField(max_length=100, verbose_name=_("Plan Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    plan_type = models.CharField(max_length=50, choices=PLAN_TYPE_CHOICES, default='vendor_premium')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Price"))
    currency = models.CharField(max_length=3, default='GHS', help_text=_("ISO 4217 currency code."))
    duration_days = models.PositiveIntegerField(help_text=_("Duration of the plan in days (e.g., 30 for monthly, 365 for yearly)."))
    features = models.TextField(blank=True, help_text=_("List of features, one per line."))
    is_active = models.BooleanField(default=True, help_text=_("Is this plan available for purchase?"))
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'price']
        verbose_name = _("Pricing Plan")
        verbose_name_plural = _("Pricing Plans")

    def __str__(self):
        return f"{self.name} - {self.currency} {self.price}"

    def get_features_list(self):
        return [feature.strip() for feature in self.features.split('\n') if feature.strip()]
# --- END: Pricing Plan Model ---

class ProductQuestion(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class ProductAnswer(models.Model):
    question = models.ForeignKey(ProductQuestion, on_delete=models.CASCADE, related_name='answers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # Can be vendor or another user
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# --- START: FraudReport Model ---
class FraudReport(models.Model):
    """
    Represents a fraud report for an order.
    """
    STATUS_CHOICES = (
        ('OPEN', _('Open')),
        ('UNDER_REVIEW', _('Under Review')),
        ('RESOLVED', _('Resolved')),
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='fraud_report')
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    reasons = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Fraud Report")
        verbose_name_plural = _("Fraud Reports")

    def __str__(self):
        return f"Fraud Report for Order {self.order.order_id}"
# --- END: FraudReport Model ---
