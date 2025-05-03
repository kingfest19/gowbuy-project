# core/urls.py
from django.urls import path
# Import all necessary views from core.views that are handled by this file
from .views import (
    home,
    menu,
    category_detail, # View for category pages
    product_detail,  # View for product pages
    order_detail,    # View for a single order's details
    order_history,   # View for the user's list of orders

    # --- NEW VIEW IMPORTS ---
    vendor_list,
    vendor_detail,
    wishlist_detail,
    add_to_wishlist,
    remove_from_wishlist,
    add_product_review,
    add_vendor_review,
    search_results, # <<< Import search_results view
    update_location, # <<< Import update_location view
    update_language, # <<< Import update_language view
    daily_offers,    # <<< Import daily_offers view
    sell_on_nexus,   # <<< Import sell_on_nexus view
    register_vendor, # <<< Import register_vendor view
    vendor_dashboard,# <<< Import vendor_dashboard view
    vendor_verification, # <<< Import vendor_verification view
    edit_vendor_profile, # <<< Import edit_vendor_profile view
    edit_vendor_shipping, # <<< Import shipping view
    edit_vendor_payment, # <<< Import payment view
    # --- Promotion/Campaign Views ---
    vendor_promotion_list,
    vendor_promotion_create,
    vendor_promotion_edit,
    vendor_campaign_list,
    vendor_campaign_create,
    # --- Product Management Views ---
    vendor_product_list,
    vendor_product_create,
    vendor_product_edit,
    vendor_order_list, # <<< Import the new view
    vendor_product_delete,
    # -----------------------
)

app_name = 'core' # Namespace for reversing URLs (e.g., {% url 'core:product_detail' ... %})

urlpatterns = [
    # Main pages
    path('', home, name='home'),
    path('menu/', menu, name='menu'),

    # Catalog pages (These match the get_absolute_url methods in models)
    path('category/<slug:category_slug>/', category_detail, name='category_detail'),
    path('product/<slug:product_slug>/', product_detail, name='product_detail'),

    # Search page
    path('search/', search_results, name='search_results'), # <<< Added search URL

    # Offers page
    path('offers/', daily_offers, name='daily_offers'), # <<< Added offers URL

    # Sell on Nexus page
    path('sell/', sell_on_nexus, name='sell_on_nexus'), # <<< Added sell page URL

    # Vendor Registration page
    path('register-vendor/', register_vendor, name='register_vendor'), # <<< Added vendor registration URL

    # Vendor Dashboard page
    path('dashboard/', vendor_dashboard, name='vendor_dashboard'), # <<< Added vendor dashboard URL

    # Vendor Verification page
    path('dashboard/verify/', vendor_verification, name='vendor_verification'), # <<< Added vendor verification URL

    # Vendor Profile Edit page
    path('dashboard/profile/edit/', edit_vendor_profile, name='edit_vendor_profile'), # <<< Added vendor profile edit URL

    # Vendor Shipping Edit page
    path('dashboard/shipping/edit/', edit_vendor_shipping, name='edit_vendor_shipping'), # <<< Added vendor shipping edit URL

    # Vendor Payment Edit page
    path('dashboard/payment/edit/', edit_vendor_payment, name='edit_vendor_payment'), # <<< Added vendor payment edit URL

    # --- Vendor Orders ---
    path('dashboard/orders/', vendor_order_list, name='vendor_order_list'), # <<< Added this line

    # --- Vendor Promotions ---
    path('dashboard/promotions/', vendor_promotion_list, name='vendor_promotion_list'),
    path('dashboard/promotions/create/', vendor_promotion_create, name='vendor_promotion_create'),
    path('dashboard/promotions/<int:promotion_id>/edit/', vendor_promotion_edit, name='vendor_promotion_edit'),
    # TODO: Add URL for promotion delete

    # --- Vendor Ad Campaigns ---
    path('dashboard/campaigns/', vendor_campaign_list, name='vendor_campaign_list'),
    path('dashboard/campaigns/create/', vendor_campaign_create, name='vendor_campaign_create'),
    # TODO: Add URL for campaign edit/delete

    # --- Vendor Products ---
    path('dashboard/products/', vendor_product_list, name='vendor_product_list'),
    path('dashboard/products/create/', vendor_product_create, name='vendor_product_create'),
    path('dashboard/products/<int:product_id>/edit/', vendor_product_edit, name='vendor_product_edit'),
    path('dashboard/products/<int:product_id>/delete/', vendor_product_delete, name='vendor_product_delete'),


    # Vendor pages
    path('vendors/', vendor_list, name='vendor_list'),
    path('vendor/<slug:vendor_slug>/', vendor_detail, name='vendor_detail'), # Corrected angle brackets

    # Order pages (These require login via decorators in views)
    path('orders/', order_history, name='order_history'), # List of user's orders
    path('order/<str:order_id>/', order_detail, name='order_detail'), # Detail of a specific order

    # Wishlist pages
    path('wishlist/', wishlist_detail, name='wishlist_detail'),
    path('wishlist/add/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', remove_from_wishlist, name='remove_from_wishlist'),

    # Review pages
    path('product/<int:product_id>/add-review/', add_product_review, name='add_product_review'),
    path('vendor/<int:vendor_id>/add-review/', add_vendor_review, name='add_vendor_review'), # Corrected angle brackets

    # Location Update URL
    path('update-location/', update_location, name='update_location'), # <<< Add this line

    # Language Update URL
    path('update-language/', update_language, name='update_language'), # <<< Add this line

]
