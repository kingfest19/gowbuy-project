# core/models.py
from django.db import models
from django.conf import settings # To link to your custom user model
from django.utils.text import slugify # To generate slugs automatically
from django.utils import timezone # To record confirmation time
from django.urls import reverse # To generate URLs for models
from decimal import Decimal # For accurate price representation
from django.core.validators import MinValueValidator, MaxValueValidator # For review ratings
from django.utils.translation import gettext_lazy as _ # For verbose names in ProductImage
import uuid # For generating order IDs

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

# --- Vendor Model ---  <<< DEFINED BEFORE VendorReview
class Vendor(models.Model):
    """
    Represents a seller in the marketplace.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='vendor_profile', on_delete=models.CASCADE, help_text="The user account managing this vendor profile.")
    name = models.CharField(max_length=200, unique=True, help_text="Public name of the vendor/store.")
    slug = models.SlugField(max_length=200, unique=True, blank=True, help_text="URL-friendly version of the vendor name. Leave blank to auto-generate.")
    description = models.TextField(blank=True, null=True, help_text="Public description of the vendor.")
    contact_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    logo = models.ImageField(upload_to=vendor_directory_path, blank=True, null=True, help_text="Optional logo for the vendor.")
    # --- Location Fields ---
    location_city = models.CharField(max_length=100, blank=True, null=True)
    location_country = models.CharField(max_length=100, blank=True, null=True) # Consider django-countries app later
    # -----------------------
    # --- Verification Documents (Conditional based on registration type) ---
    business_registration_doc = models.FileField(upload_to=vendor_directory_path, blank=True, null=True, verbose_name=_("Business Registration Document"))
    national_id_type = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Type of National ID")) # E.g., Ghana Card, Passport
    tax_id_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Tax Identification Number (TIN)"))
    other_business_doc = models.FileField(upload_to=vendor_directory_path, blank=True, null=True, verbose_name=_("Other Supporting Document (Optional)"))
    national_id_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("National ID Number"))
    national_id_doc = models.FileField(upload_to=vendor_directory_path, blank=True, null=True, verbose_name=_("National ID Document"))
    # --- Shipping & Payment Info ---
    shipping_policy = models.TextField(blank=True, null=True, verbose_name=_("Shipping Policy"))
    return_policy = models.TextField(blank=True, null=True, verbose_name=_("Return Policy")) # Moved here for grouping
    # Example Mobile Money Fields (Adjust as needed)
    mobile_money_provider = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Mobile Money Provider")) # e.g., MTN, Vodafone, AirtelTigo
    mobile_money_number = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Mobile Money Number"))
    # --- End Shipping & Payment Info ---
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
    # --- Timestamps ---
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
    # --- VENDOR FIELD (Still temporarily nullable) ---
    vendor = models.ForeignKey(
        Vendor,
        related_name='products',
        on_delete=models.CASCADE,
        null=True,  # <<< KEEP THIS TEMPORARILY until all products assigned
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

    is_active = models.BooleanField(default=True, db_index=True, help_text="Is the product available for purchase (requires vendor approval too)?")
    # requires_shipping = models.BooleanField(default=True, help_text="Does this product require shipping? (Auto-set based on type)") # Consider adding this later
    is_featured = models.BooleanField(default=False, db_index=True, help_text="Should this product be featured (e.g., on homepage)?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    # --- Updated Status Choices ---
    STATUS_CHOICES = (
        ('PENDING', _('Pending Payment Choice')), # Initial state for service orders
        ('AWAITING_ESCROW_PAYMENT', _('Awaiting Escrow Payment')),
        ('AWAITING_DIRECT_PAYMENT', _('Awaiting Direct Payment Confirmation')),
        ('PROCESSING', _('Processing')), # Payment received (escrow) or confirmed (direct)
        ('IN_PROGRESS', _('Service In Progress')),
        ('COMPLETED', _('Completed')),
        ('CANCELLED', _('Cancelled')),
        ('DISPUTED', _('Disputed')),
        # Keep old product statuses if needed, or migrate existing orders
        ('pending', _('Pending (Product Order)')),
        ('processing', _('Processing (Product Order)')),
        ('shipped', _('Shipped (Product Order)')),
        ('delivered', _('Delivered (Product Order)')),
        ('cancelled', _('Cancelled (Product Order)')),
        ('refunded', _('Refunded (Product Order)')),
    )
    PAYMENT_METHOD_CHOICES = (
        ('escrow', _('Escrow (Paystack)')),
        ('direct', _('Direct Arrangement')),
    )
    # PAYMENT_STATUS_CHOICES = ( ('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed'), ) # Can be simplified or derived from STATUS

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True)
    order_id = models.CharField(max_length=120, unique=True, blank=True, help_text="Unique order identifier. Auto-generated.")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING', db_index=True) # Default to new initial status
    # payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', db_index=True) # Consider removing if status covers it
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
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
    customer_confirmed_completion_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Customer Confirmed Completion At"))

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
    def __str__(self):
        return f"Order {self.order_id} ({self.get_status_display()})"
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
        return self.price * self.quantity

    # Add a property to easily access the service title if needed
    @property
    def service_title(self):
        return self.service_package.service.title if self.service_package and self.service_package.service else _("N/A")
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

# --- VendorReview Model --- <<< DEFINED AFTER Vendor
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
    comment = models.TextField(blank=True, null=True)
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

    class Meta:
        ordering = ['uploaded_at']
        verbose_name = _("Product Video")
        verbose_name_plural = _("Product Videos")

    def __str__(self):
        return self.title or f"Video for {self.product.name} ({self.id})"

# --- CartItem Model (Still commented out - using session cart) ---
# class CartItem(models.Model): ...

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
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Minimum cart total required to apply (optional).")
    max_uses = models.PositiveIntegerField(blank=True, null=True, help_text="Maximum number of times this promotion can be used in total (optional).")
    uses_per_customer = models.PositiveIntegerField(blank=True, null=True, help_text="Maximum number of times a single customer can use this promotion (optional).")
    current_uses = models.PositiveIntegerField(default=0, editable=False)
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
    comment = models.TextField(blank=True, null=True)
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

# --- END: Service Marketplace Models ---
