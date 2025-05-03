# core/models.py
from django.db import models
from django.conf import settings # To link to your custom user model
from django.utils.text import slugify # To generate slugs automatically
from django.urls import reverse # To generate URLs for models
from decimal import Decimal # For accurate price representation
from django.core.validators import MinValueValidator, MaxValueValidator # For review ratings
from django.utils.translation import gettext_lazy as _ # For verbose names in ProductImage

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
    """
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
    # Removed the single image field to replace with gallery via ProductImage model
    # image = models.ImageField(upload_to='products/%Y/%m/%d/', blank=True, null=True, help_text="Main product image.")
    stock = models.PositiveIntegerField(default=0, help_text="Number of items currently in stock.")
    is_active = models.BooleanField(default=True, db_index=True, help_text="Is the product available for purchase (requires vendor approval too)?")
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
    STATUS_CHOICES = ( ('pending', 'Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled'), ('refunded', 'Refunded'), )
    PAYMENT_STATUS_CHOICES = ( ('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed'), )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True)
    order_id = models.CharField(max_length=120, unique=True, blank=True, help_text="Unique order identifier. Auto-generated.")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', db_index=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    shipping_address = models.ForeignKey(Address, related_name='shipping_orders', on_delete=models.SET_NULL, null=True, blank=True)
    billing_address = models.ForeignKey(Address, related_name='billing_orders', on_delete=models.SET_NULL, null=True, blank=True)
    shipping_address_text = models.TextField(blank=True, null=True, help_text="Snapshot of shipping address at time of order.")
    billing_address_text = models.TextField(blank=True, null=True, help_text="Snapshot of billing address at time of order.")
    transaction_id = models.CharField(max_length=255, blank=True, null=True, help_text="Payment gateway transaction ID.")
    notes = models.TextField(blank=True, null=True, help_text="Internal notes about the order.")
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
        import datetime, uuid
        now = datetime.datetime.now()
        random_part = uuid.uuid4().hex[:6].upper()
        return f"NEXUS-{now.strftime('%Y%m%d')}-{random_part}"
    def __str__(self):
        return f"Order {self.order_id} ({self.get_status_display()})"
    def calculate_total(self):
        total = sum(item.get_total_item_price() for item in self.items.all())
        self.total_amount = total
        return total
    def get_absolute_url(self):
        return reverse('core:order_detail', kwargs={'order_id': self.order_id})

# --- OrderItem Model ---
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255, blank=True, help_text="Snapshot of product name at time of order.")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per unit at the time of order.")
    quantity = models.PositiveIntegerField(default=1)
    class Meta:
        ordering = ('order', 'product_name')
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
    def save(self, *args, **kwargs):
        if self.product and not self.product_name: self.product_name = self.product.name
        super().save(*args, **kwargs)
    def __str__(self):
        product_desc = self.product.name if self.product else self.product_name or "[Deleted Product]"
        return f"{self.quantity} x {product_desc} for Order {self.order.order_id}"
    def get_total_item_price(self):
        return self.price * self.quantity

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
