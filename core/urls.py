# c:\Users\Hp\Desktop\Nexus\core\urls.py
# core/urls.py
from django.urls import path
# Import all necessary views from core.views that are handled by this file
from . import views # <<< Import the views module itself

app_name = 'core' # Namespace for reversing URLs (e.g., {% url 'core:product_detail' ... %})

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),

    # Catalog pages (These match the get_absolute_url methods in models)
    path('category/<slug:category_slug>/', views.category_detail, name='category_detail'),
    path('product/<slug:product_slug>/', views.product_detail, name='product_detail'),

    # Search page
    path('search/', views.search_results, name='search_results'), # <<< Added search URL

    # Offers page
    path('offers/', views.daily_offers, name='daily_offers'), # <<< Added offers URL

    # Sell on Nexus page
    path('sell/', views.sell_on_nexus, name='sell_on_nexus'), # <<< Added sell page URL

    # Vendor Registration page
    path('register-vendor/', views.register_vendor, name='register_vendor'), # <<< Added vendor registration URL

    # Vendor Dashboard page
    path('dashboard/', views.vendor_dashboard, name='vendor_dashboard'), # <<< Added vendor dashboard URL

    # Vendor Verification page
    path('dashboard/verify/', views.vendor_verification, name='vendor_verification'), # <<< Added vendor verification URL

    # Vendor Profile Edit page
    path('dashboard/profile/edit/', views.edit_vendor_profile, name='edit_vendor_profile'), # <<< Added vendor profile edit URL

    # Vendor Shipping Edit page
    path('dashboard/shipping/edit/', views.edit_vendor_shipping, name='edit_vendor_shipping'), # <<< Added vendor shipping edit URL

    # Vendor Payment Edit page
    path('dashboard/payment/edit/', views.edit_vendor_payment, name='edit_vendor_payment'), # <<< Added vendor payment edit URL

    # --- Vendor Additional Info ---
    path('dashboard/additional-info/', views.edit_vendor_additional_info, name='edit_vendor_additional_info'), # <<< Added this line

    # --- Vendor Orders ---
    path('dashboard/orders/', views.vendor_order_list, name='vendor_order_list'), # <<< Added this line

    # --- Vendor Reports ---
    path('dashboard/reports/', views.vendor_reports, name='vendor_reports'), # <<< Added this line

    # --- Vendor Promotions ---
    path('dashboard/promotions/', views.vendor_promotion_list, name='vendor_promotion_list'),
    path('dashboard/promotions/create/', views.vendor_promotion_create, name='vendor_promotion_create'),
    path('dashboard/promotions/<int:promotion_id>/edit/', views.vendor_promotion_edit, name='vendor_promotion_edit'),
    # TODO: Add URL for promotion delete

    # --- Vendor Ad Campaigns ---
    path('dashboard/campaigns/', views.vendor_campaign_list, name='vendor_campaign_list'),
    path('dashboard/campaigns/create/', views.vendor_campaign_create, name='vendor_campaign_create'),
    # TODO: Add URL for campaign edit/delete

    # --- Vendor Products ---
    path('dashboard/products/', views.vendor_product_list, name='vendor_product_list'),
    path('dashboard/products/create/', views.vendor_product_create, name='vendor_product_create'),
    path('dashboard/products/<int:product_id>/edit/', views.vendor_product_edit, name='vendor_product_edit'),
    path('dashboard/products/<int:product_id>/delete/', views.vendor_product_delete, name='vendor_product_delete'),


    # Vendor pages
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendor/<slug:vendor_slug>/', views.vendor_detail, name='vendor_detail'), # Corrected angle brackets

    # Order pages (These require login via decorators in views)
    path('orders/', views.order_history, name='order_history'), # List of user's orders
    path('order/<str:order_id>/', views.order_detail, name='order_detail'), # Detail of a specific order
    path('order/<str:order_id>/download/<int:product_id>/', views.download_digital_product, name='download_digital_product'), # <<< Added download URL

    # Checkout & Order Placement
    path('checkout/', views.checkout, name='checkout'), # Uncommented for product checkout
    path('place-order/', views.place_order, name='place_order'), # Uncommented for product order placement
    path('order-summary/', views.order_summary_view, name='order_summary'), # Assuming this view exists for services
    path('checkout/process-choice/', views.process_checkout_choice, name='process_checkout_choice'),
    path('paystack/callback/', views.paystack_callback, name='paystack_callback'), # <<< ADD THIS LINE FOR PAYSTACK CALLBACK
    path('order/<str:order_id>/confirm-completion/', views.customer_confirm_service_completion, name='customer_confirm_service_completion'), # <<< For customer confirmation
    
    # Wishlist pages
    path('wishlist/', views.wishlist_detail, name='wishlist_detail'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # Review pages
    path('product/<int:product_id>/add-review/', views.add_product_review, name='add_product_review'),
    path('vendor/<int:vendor_id>/add-review/', views.add_vendor_review, name='add_vendor_review'), # Corrected angle brackets

    # Location Update URL
    path('update-location/', views.update_location, name='update_location'), # <<< Add this line

    # Language Update URL
    path('update-language/', views.update_language, name='update_language'), # <<< Add this line

    # User Profile URL
    path('profile/', views.user_profile_view, name='user_profile'), # <<< Add this line

    # Provider Dashboard
    path('dashboard/provider/', views.provider_dashboard, name='provider_dashboard'),

    # Public Provider Profile
    path('provider/<str:username>/', views.provider_profile_detail, name='provider_profile_detail'),

]

# --- START: Service Marketplace URLs ---
urlpatterns += [
    path('services/', views.service_list, name='service_list'),
    path('services/category/<slug:category_slug>/', views.service_category_detail, name='service_category_detail'),
    path('services/create/', views.service_create, name='service_create'),
    path('services/<slug:service_slug>/', views.service_detail, name='service_detail'),
    path('services/<slug:service_slug>/edit/', views.service_edit, name='service_edit'),
    path('services/<slug:service_slug>/delete/', views.service_delete, name='service_delete'),
    path('services/<slug:service_slug>/add-review/', views.add_service_review, name='add_service_review'), # <<< Added review URL
    path('services/add-package-to-order/<int:package_id>/', views.add_service_to_order, name='add_service_to_order'), # <<< Add this line
    path('order/<int:order_id>/initiate-payment/', views.initiate_paystack_payment, name='initiate_paystack_payment'), # <-- New URL for Paystack
]
# --- END: Service Marketplace URLs ---
