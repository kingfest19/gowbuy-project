# core/admin.py
from django.contrib import admin
from django.utils.html import format_html # For user_link helper
from django.urls import reverse # For user_link helper

# Import your user model (adjust path if needed)
from authapp.models import CustomUser

# Import ALL your core models correctly from .models
# Import ProductImage as well
from .models import (
    Category, Vendor, Product, Address, Order, OrderItem, WishlistItem, ProductReview, VendorReview, ProductImage
, ProductVideo # <<< Import ProductVideo
) # <<< Add the closing parenthesis here

# --- CustomUser Admin (Keep as is, or move to authapp/admin.py) ---
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'bio', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active')
    ordering = ('username',)
# Ensure CustomUser is only registered once (here or in authapp/admin.py)
# Avoid registering it in both places. Assuming it's okay here for now.
admin.site.register(CustomUser, CustomUserAdmin)

# --- Register Core Models ---

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

# --- UPDATED Vendor Admin ---
@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_link', 'is_approved', 'is_verified', 'view_business_doc_link', 'view_national_id_doc_link', 'created_at') # Added doc links
    list_filter = ('is_approved', 'is_verified', 'created_at', 'location_country') # Add country filter
    list_editable = ('is_approved', 'is_verified')
    search_fields = ('name', 'user__username', 'description', 'location_city', 'location_country', 'national_id_number') # Added ID number search
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('user',)
    ordering = ('name',)

    # --- Add Fieldsets for better organization ---
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'slug') # <<< Removed 'logo' from here
        }),
        ('Status & Verification', {
            'fields': ('is_approved', 'is_verified')
        }),
        ('Profile Information', {
            'fields': ('description', 'contact_email', 'phone_number', 'logo', 'location_city', 'location_country') # Added contact info
        }),
        ('Verification Documents', { # New section for verification fields
            'fields': ('business_registration_doc', 'national_id_type', 'national_id_number', 'national_id_doc')
        }),
        ('Policies', {
            'fields': ('shipping_policy', 'return_policy'),
            'classes': ('collapse',) # Make policies collapsible
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'view_business_doc_link', 'view_national_id_doc_link') # Add link methods here too
    # ------------------------------------------

    def user_link(self, obj):
        # ... (user_link method remains the same) ...
        if obj.user:
            # Make sure 'authapp_customuser_change' is the correct admin URL name
            link = reverse("admin:authapp_customuser_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', link, obj.user.username) # Corrected HTML format
        return "N/A"
    user_link.short_description = 'User Account'

    # --- Methods to display links to uploaded documents ---
    def view_business_doc_link(self, obj):
        if obj.business_registration_doc:
            return format_html('<a href="{}" target="_blank">View Document</a>', obj.business_registration_doc.url)
        return "N/A"
    view_business_doc_link.short_description = 'Business Doc'

    def view_national_id_doc_link(self, obj):
        if obj.national_id_doc:
            return format_html('<a href="{}" target="_blank">View ID</a>', obj.national_id_doc.url)
        return "N/A"
    view_national_id_doc_link.short_description = 'National ID'
    # ------------------------------------------------------
# --- END UPDATED Vendor Admin ---

# --- Inline Admin for Product Images ---
class ProductImageInline(admin.TabularInline): # Or admin.StackedInline for a different layout
    model = ProductImage
    extra = 1 # Number of empty forms to display
    fields = ('image', 'alt_text') # Fields to show in the inline form
    readonly_fields = ('uploaded_at',) # Optional: show upload time

# --- Inline Admin for Product Videos ---
class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 1 # Number of empty forms
    fields = ('video', 'title', 'description')
    readonly_fields = ('uploaded_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # --- UPDATED list_display, list_filter, search_fields, raw_id_fields ---
    list_display = ('name', 'slug', 'vendor', 'category', 'price', 'stock', 'is_active', 'is_available', 'is_featured', 'created_at')
    list_filter = ('is_active', 'is_featured', 'category', 'vendor', 'created_at')
    search_fields = ('name', 'description', 'slug', 'vendor__name', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'stock', 'is_active', 'is_featured')
    raw_id_fields = ('vendor', 'category') # Add vendor here
    ordering = ('-created_at',)
    inlines = [ProductImageInline, ProductVideoInline] # <<< Add video inline
    date_hierarchy = 'created_at'

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'address_type', 'street_address', 'city', 'state', 'country', 'is_default')
    list_filter = ('address_type', 'is_default', 'country', 'state', 'city')
    search_fields = ('user__username', 'full_name', 'street_address', 'city', 'zip_code', 'country')
    list_select_related = ('user',)
    raw_id_fields = ('user',)
    ordering = ('user__username', '-is_default', '-created_at')

# --- OrderItemInline (Unchanged, but consider adding vendor if model changes) ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ('product', 'product_name', 'price', 'quantity', 'get_total_item_price')
    readonly_fields = ('product_name', 'price', 'get_total_item_price')
    extra = 0
    raw_id_fields = ('product',)
    # --- CONSIDER: Add 'vendor' if added to OrderItem model ---
    # fields = ('product', 'vendor', 'product_name', 'price', 'quantity', 'get_total_item_price')
    # readonly_fields = ('vendor', 'product_name', 'price', 'get_total_item_price')
    # raw_id_fields = ('product', 'vendor')

    def get_total_item_price(self, obj):
        return obj.get_total_item_price()
    get_total_item_price.short_description = 'Item Total'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user_link', 'status', 'payment_status', 'total_amount', 'created_at', 'shipping_address_present', 'billing_address_present')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_id', 'user__username', 'transaction_id', 'shipping_address_text', 'billing_address_text')
    list_editable = ('status', 'payment_status')
    readonly_fields = ('order_id', 'user', 'created_at', 'updated_at', 'total_amount', 'shipping_address_text', 'billing_address_text', 'transaction_id', 'user_link')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    inlines = [OrderItemInline]
    list_select_related = ('user',)
    raw_id_fields = ('user', 'shipping_address', 'billing_address')
    fieldsets = (
        (None, {'fields': ('order_id', 'user_link', 'status', 'payment_status', 'transaction_id')}),
        ('Amount & Timing', {'fields': ('total_amount', 'created_at', 'updated_at')}),
        ('Addresses', {'fields': ('shipping_address', 'shipping_address_text', 'billing_address', 'billing_address_text')}),
        ('Notes', {'fields': ('notes',), 'classes': ('collapse',)}),
    )
    def user_link(self, obj):
        if obj.user:
            link = reverse("admin:authapp_customuser_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', link, obj.user.username) # Corrected HTML format
        return "Guest / Deleted User"
    user_link.short_description = 'User'
    def shipping_address_present(self, obj): return bool(obj.shipping_address or obj.shipping_address_text)
    shipping_address_present.boolean = True; shipping_address_present.short_description = 'Ship Addr'
    def billing_address_present(self, obj): return bool(obj.billing_address or obj.billing_address_text)
    billing_address_present.boolean = True; billing_address_present.short_description = 'Bill Addr'

# --- NEW: WishlistItem Admin ---
@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_link', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'product__name', 'product__vendor__name')
    list_select_related = ('user', 'product', 'product__vendor') # Optimize lookups
    raw_id_fields = ('user', 'product')
    ordering = ('-added_at',)

    def product_link(self, obj):
        if obj.product:
            link = reverse("admin:core_product_change", args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', link, obj.product.name)
        return "N/A"
    product_link.short_description = 'Product'

# --- NEW: ProductReview Admin ---
@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product_link', 'user_link', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__username', 'review')
    list_editable = ('is_approved',)
    list_select_related = ('product', 'user', 'product__vendor') # Optimize lookups
    raw_id_fields = ('product', 'user') # Add 'order_item' if using verified purchase link
    ordering = ('-created_at',)

    def product_link(self, obj):
        if obj.product:
            link = reverse("admin:core_product_change", args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', link, obj.product.name)
        return "N/A"
    product_link.short_description = 'Product'

    def user_link(self, obj):
        if obj.user:
            link = reverse("admin:authapp_customuser_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "N/A"
    user_link.short_description = 'User'


# --- NEW: VendorReview Admin ---
@admin.register(VendorReview)
class VendorReviewAdmin(admin.ModelAdmin):
    list_display = ('vendor_link', 'user_link', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('vendor__name', 'user__username', 'comment')
    list_editable = ('is_approved',)
    list_select_related = ('vendor', 'user') # Optimize lookups
    raw_id_fields = ('vendor', 'user')
    ordering = ('-created_at',)

    def vendor_link(self, obj):
        if obj.vendor:
            # Assuming you have a 'vendor_detail' admin URL (usually default)
            link = reverse("admin:core_vendor_change", args=[obj.vendor.id])
            return format_html('<a href="{}">{}</a>', link, obj.vendor.name)
        return "N/A"
    vendor_link.short_description = 'Vendor'

    def user_link(self, obj):
        if obj.user:
            link = reverse("admin:authapp_customuser_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "N/A"
    user_link.short_description = 'User'

# ProductImage is managed via the ProductAdmin inline, no need to register it separately unless desired.
# ProductVideo is managed via the ProductAdmin inline.
