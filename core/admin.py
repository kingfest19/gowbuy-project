# core/admin.py
from django.contrib import admin
from django.utils.html import format_html # For user_link helper
from django.urls import reverse # For user_link helper

# Import your user model (adjust path if needed)
from authapp.models import CustomUser

# Import ALL your core models correctly from .models
# Import ProductImage as well
from .models import (
    Category, Vendor, Product, Address, Order, OrderItem, WishlistItem, ProductReview, VendorReview, ProductImage,
    ProductVideo, # <<< Import ProductVideo
    ServiceCategory, Service, ServiceReview, ServiceImage, ServiceVideo, ServicePackage # <<< Import ServicePackage
)

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
    list_display = ('name', 'user_link', 'is_approved', 'is_verified', 'view_business_doc_link', 'view_national_id_doc_link', 'created_at') # Restored doc links
    list_filter = ('is_approved', 'is_verified', 'created_at', 'location_country') # Restored country filter
    list_editable = ('is_approved', 'is_verified')
    search_fields = ('name', 'user__username', 'description', 'location_city', 'location_country', 'national_id_number') # Restored ID number search
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('user',)
    ordering = ('name',)

    # --- Add Fieldsets for better organization ---
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'slug')
        }),
        ('Status & Verification', {
            'fields': ('is_approved', 'is_verified')
        }),
        ('Profile Information', {
            'fields': ('description', 'contact_email', 'phone_number', 'logo', 'location_city', 'location_country')
        }),
        ('Verification Documents', {
            'fields': ('business_registration_doc', 'national_id_type', 'national_id_number', 'national_id_doc')
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
    readonly_fields = ('created_at', 'updated_at', 'view_business_doc_link', 'view_national_id_doc_link') # Restored
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
    list_display = ('name', 'slug', 'vendor', 'category', 'price', 'stock', 'is_active', 'is_available', 'is_featured', 'created_at') # Restored 'is_available'
    list_filter = ('is_active', 'is_featured', 'category', 'vendor', 'created_at') # Restored
    search_fields = ('name', 'description', 'slug', 'vendor__name', 'category__name') # Restored
    prepopulated_fields = {'slug': ('name',)} # Restored
    list_editable = ('price', 'stock', 'is_active', 'is_featured') # Restored
    raw_id_fields = ('vendor', 'category') # Restored
    ordering = ('-created_at',) # Restored
    inlines = [ProductImageInline, ProductVideoInline] # Restored inlines
    date_hierarchy = 'created_at' # Restored

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'address_type', 'street_address', 'city', 'state', 'country', 'is_default')
    list_filter = ('address_type', 'is_default', 'country', 'state', 'city')
    search_fields = ('user__username', 'full_name', 'street_address', 'city', 'zip_code', 'country')
    list_select_related = ('user',)
    raw_id_fields = ('user',)
    ordering = ('user__username', '-is_default', '-created_at')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ('product', 'service_package', 'product_name', 'price', 'quantity', 'get_total_item_price')
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


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user_link', 'status', 'payment_method', 'total_amount', 'created_at', 'customer_confirmed_completion_at')
    list_filter = ('status', 'payment_method', 'created_at', 'customer_confirmed_completion_at')
    search_fields = ('order_id', 'user__username', 'transaction_id', 'shipping_address_text', 'billing_address_text', 'paystack_ref')
    list_editable = ('status',)
    readonly_fields = (
        'order_id', 'user', 'created_at', 'updated_at',
        'total_amount', 'shipping_address_text', 'billing_address_text',
        'transaction_id', 'user_link', 'paystack_ref',
        'customer_confirmed_completion_at'
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
    actions = [mark_direct_payment_received]
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
    list_display = ('title', 'provider', 'category', 'price', 'location', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'location', 'created_at')
    search_fields = ('title', 'description', 'provider__username', 'category__name')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('provider', 'category')
    ordering = ('-created_at',)
    inlines = [ServicePackageInline, ServiceImageInline, ServiceVideoInline]

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
