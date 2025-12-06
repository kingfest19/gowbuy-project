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

    # Product pages
    # Catalog pages (These match the get_absolute_url methods in models)
    path('category/<slug:category_slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('product/<slug:product_slug>/', views.ProductDetailView.as_view(), name='product_detail'),

    # Search page
    path('search/', views.search_results, name='search_results'),

    path('products/', views.ProductListView.as_view(), name='product_list'), # For ProductListView
    # Offers page
    path('offers/', views.daily_offers, name='daily_offers'),

    # Sell on Nexus page
    path('sell/', views.sell_on_nexus, name='sell_on_nexus'),

    # Vendor Registration page
    path('register-vendor/', views.vendor_registration_view, name='register_vendor'),

    # Vendor Dashboard page
    path('dashboard/', views.VendorDashboardView.as_view(), name='vendor_dashboard'),

    # Vendor Verification page
     path('dashboard/verify/', views.MultiStepVendorVerificationView.as_view(), name='vendor_verification_multistep'), # Changed view and name

    # Vendor Profile Edit page
    path('dashboard/profile/edit/', views.EditVendorProfileView.as_view(), name='vendor_profile_edit'), # Corrected name

    # Vendor Shipping Settings page (assuming this is what edit_vendor_shipping was for)
    path('dashboard/shipping/', views.EditVendorShippingView.as_view(), name='vendor_shipping_settings'),

    # Vendor Payment Edit page
      path('dashboard/payment/edit/', views.EditVendorPaymentView.as_view(), name='vendor_payment_settings'), # Corrected name

    # --- Vendor Additional Info ---
    path('dashboard/additional-info/', views.EditVendorAdditionalInfoView.as_view(), name='edit_vendor_additional_info'),

    # --- Vendor Orders ---
    path('dashboard/orders/', views.VendorOrderListView.as_view(), name='vendor_orders'),
    path('dashboard/orders/<int:pk>/', views.VendorOrderDetailView.as_view(), name='vendor_order_detail'),

    # --- Vendor Reports ---
    path('dashboard/reports/', views.VendorReportsView.as_view(), name='vendor_reports'),

    # --- Vendor Promotions ---
    path('dashboard/promotions/', views.VendorPromotionListView.as_view(), name='vendor_promotions'),
    path('dashboard/promotions/create/', views.VendorPromotionCreateView.as_view(), name='vendor_promotion_create'),
    path('dashboard/promotions/<int:pk>/edit/', views.VendorPromotionUpdateView.as_view(), name='vendor_promotion_edit'),
    path('dashboard/promotions/<int:pk>/delete/', views.VendorPromotionDeleteView.as_view(), name='vendor_promotion_delete'),

    # --- Vendor Ad Campaigns ---
    path('dashboard/campaigns/', views.VendorCampaignListView.as_view(), name='vendor_ads'),  # Name used in sidebar, more relevant now
       path('dashboard/campaigns/create/', views.VendorCampaignCreateView.as_view(), name='vendor_campaign_create'), # Corrected name
    path('dashboard/campaigns/<int:pk>/edit/', views.VendorCampaignUpdateView.as_view(), name='vendor_campaign_edit'), # Assuming pk
    path('dashboard/campaigns/<int:pk>/delete/', views.VendorCampaignDeleteView.as_view(), name='vendor_campaign_delete'), # Assuming pk

    # --- Vendor Notifications ---
    path('dashboard/notifications/', views.VendorNotificationListView.as_view(), name='vendor_notification_list'),

    # --- Vendor Products ---
    path('dashboard/products/', views.VendorProductListView.as_view(), name='vendor_products'), # Corrected name to vendor_products
    path('dashboard/products/create/', views.VendorProductCreateView.as_view(), name='vendor_product_create'),
    path('dashboard/products/<int:pk>/edit/', views.VendorProductUpdateView.as_view(), name='vendor_product_edit'),
    path('dashboard/products/<int:pk>/delete/', views.VendorProductDeleteView.as_view(), name='vendor_product_delete'),


    # Vendor pages
    path('vendors/', views.VendorListView.as_view(), name='vendor_list'),
    path('vendor/<slug:vendor_slug>/', views.VendorDetailView.as_view(), name='vendor_detail'),

    # --- Cart URLs ---
    path('cart/', views.cart_detail, name='cart_detail'), # <<< Reverted to use function-based view
    # path('cart/', views.CartDetailView.as_view(), name='cart_detail'), # <<< Updated to use CartDetailView
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'), # Ensure this line captures product_id
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),

    # Order pages (These require login via decorators in views)
    path('orders/', views.OrderHistoryView.as_view(), name='order_history'),
    path('order/<str:order_id>/', views.OrderDetailView.as_view(), name='order_detail'),
    # path('order/<str:order_id>/download/<int:product_id>/', views.download_digital_product, name='download_digital_product'), # Keep if function-based

    # Checkout & Order Placement
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/add-address/', views.add_checkout_address, name='add_checkout_address'),   # Ensure POST to this URL
    path('place-order/', views.place_order, name='place_order'),                       # Ensure POST to this URL
    path('ajax/calculate-delivery-fee/', views.calculate_delivery_fee_ajax, name='calculate_delivery_fee_ajax'), # New AJAX endpoint
    path('order/<str:order_id>/process-choice/', views.process_checkout_choice, name='process_checkout_choice'), # Handle checkout choice
    path('order/<int:order_id>/initiate-payment/', views.initiate_paystack_payment, name='initiate_paystack_payment'),
    path('paystack/callback/', views.paystack_callback, name='paystack_callback'), # Keep if function-based
    path('order/<str:order_id>/confirm-delivery/', views.customer_confirm_product_delivery, name='customer_confirm_product_delivery'), # Order ID
    path('order/<str:order_id>/confirm-completion/', views.customer_confirm_service_completion, name='customer_confirm_service_completion'),  # Order ID

    # Wishlist
    path('wishlist/', views.view_wishlist, name='wishlist_detail'), # Changed from wishlist_detail to view_wishlist
    path('wishlist/add/', views.add_to_wishlist, name='add_to_wishlist'), # Changed URL to be more generic for POST
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # Review pages
    path('product/<int:product_id>/add-review/', views.submit_product_review, name='submit_product_review'),
    path('vendor/<int:vendor_id>/add-review/', views.submit_vendor_review, name='submit_vendor_review'),
    path('vendor/<slug:vendor_slug>/review/add/', views.submit_vendor_review, name='add_vendor_review'),
# Or if it takes vendor_id:
# path('vendor/<int:vendor_id>/review/add/', views.submit_vendor_review, name='add_vendor_review'),



    # Location Update URL
    path('update-location/', views.update_location, name='update_location'),

    # Language Update URL
    path('update-language/', views.update_language, name='update_language'),

    # User Profile URL
    path('profile/edit/', views.edit_user_profile, name='edit_user_profile'), # More specific URL first
    path('profile/', views.user_profile_view, name='user_profile'), # General profile view for the logged-in user
    path('profile/change-password/', views.change_password, name='change_password'),


    # Service Provider
    path('dashboard/provider/', views.ProviderDashboardView.as_view(), name='provider_dashboard'),

    path('become-service-provider/', views.become_service_provider, name='become_service_provider'),


    # Public Provider Profile
    path('service_providers/<str:username>/', views.ProviderProfileDetailView.as_view(), name='provider_profile_detail'),

    # Edit Service Provider Profile & Portfolio
    path('dashboard/provider/edit-profile/', views.edit_service_provider_profile, name='edit_service_provider_profile'),
    path('dashboard/provider/portfolio/delete/<int:item_id>/', views.delete_portfolio_item, name='delete_portfolio_item'),
    
    # Vendor Payouts (ensure these are defined if used in sidebar)
    path('dashboard/payouts/', views.VendorPayoutListView.as_view(), name='vendor_payout_requests'), # requests
    path('dashboard/payouts/request/', views.VendorPayoutRequestCreateView.as_view(), name='vendor_payout_request_create'), # Create

    # --- Vendor Reviews --- # <-- Added comment for clarity
    path('dashboard/reviews/', views.VendorReviewListView.as_view(), name='vendor_reviews'), # <-- This is the line for vendor reviews

    # --- AJAX URLs ---
    path('ajax/enhance-description/', views.ajax_enhance_product_description, name='ajax_enhance_product_description'),
    path('ajax/chatbot-message/', views.ajax_chatbot_message, name='ajax_chatbot_message'),
    path('ajax/visual-search/', views.ajax_visual_search, name='ajax_visual_search'),
    path('ajax/generate-3d-model/', views.ajax_generate_3d_model, name='ajax_generate_3d_model'), # <<< Add this URL

]

# --- START: Service Marketplace URLs ---
urlpatterns += [
    path('services/', views.ServiceListView.as_view(), name='service_list'),
    path('services/search/', views.ServiceSearchResultsView.as_view(), name='service_search_results'), # New URL for search results
    path('services/category/<slug:category_slug>/', views.ServiceCategoryDetailView.as_view(), name='service_category_detail'),
    path('services/create/', views.ServiceCreateView.as_view(), name='service_create'),
    path('service/<slug:service_slug>/', views.ServiceDetailView.as_view(), name='service_detail'), # Changed path prefix for clarity
    path('service/<slug:service_slug>/edit/', views.ServiceUpdateView.as_view(), name='service_edit'),
    path('service/<slug:service_slug>/delete/', views.ServiceDeleteView.as_view(), name='service_delete'),
    path('service/<slug:service_slug>/add-review/', views.submit_service_review, name='submit_service_review'),
    path('services/add-package-to-order/<int:package_id>/', views.add_service_to_order, name='add_service_to_order'),
    path('services/category/<slug:category_slug>/', views.CategoryServiceListView.as_view(), name='services_by_category'),
]
# --- END: Service Marketplace URLs ---

# --- START: Rider URLs ---
urlpatterns += [
    path('riders/apply/', views.BecomeRiderView.as_view(), name='become_rider'),
    path('riders/dashboard/', views.RiderDashboardView.as_view(), name='rider_dashboard'), 
    path('riders/dashboard/toggle-availability/', views.toggle_rider_availability, name='toggle_rider_availability'),
    path('riders/task/<uuid:task_id>/accept/', views.accept_delivery_task, name='accept_delivery_task'),
    path('riders/task/<uuid:task_id>/', views.RiderTaskDetailView.as_view(), name='rider_task_detail'),
    path('riders/task/<uuid:task_id>/picked-up/', views.update_task_status_picked_up, name='update_task_status_picked_up'),
    path('riders/task/<uuid:task_id>/delivered/', views.update_task_status_delivered, name='update_task_status_delivered'),
    
        # Rider Dashboard Sections
        path('riders/dashboard/earnings-reports/', views.RiderEarningsReportsView.as_view(), name='rider_earnings_reports'),
    path('riders/dashboard/profile/', views.RiderProfileView.as_view(), name='rider_profile_view'), # Points to the new view page
    path('riders/dashboard/profile/edit/', views.RiderProfileEditView.as_view(), name='rider_profile_edit'), # Edit page has its own URL
    path('riders/dashboard/verification/', views.RiderVerificationView.as_view(), name='rider_verification'),
    path('riders/dashboard/boost/', views.RiderBoostVisibilityView.as_view(), name='rider_boost_visibility'),
    path('riders/dashboard/boost/activate/', views.ActivateRiderBoostView.as_view(), name='activate_rider_boost'),
    path('riders/paystack-boost-callback/', views.paystack_boost_callback, name='paystack_boost_callback'),
    path('riders/dashboard/earnings/request-payout/', views.RequestPayoutView.as_view(), name='rider_request_payout'), # This should be nested or distinct
    path('riders/dashboard/earnings/', views.RiderEarningsView.as_view(), name='rider_earnings'), # Changed path to match desired URL
    path('riders/dashboard/notifications/', views.RiderNotificationListView.as_view(), name='rider_notification_list'),
    path('riders/why-join/', views.BecomeRiderInfoView.as_view(), name='become_rider_info_page'),
]
# --- END: Rider URLs ---


# --- START: Service Provider Dashboard URLs ---
urlpatterns += [
    path('provider/dashboard/', views.ServiceProviderDashboardView.as_view(), name='service_provider_dashboard'),
    path('provider/services/', views.ServiceProviderServicesListView.as_view(), name='service_provider_services_list'),
    path('provider/services/create/', views.ServiceCreateView.as_view(), name='service_provider_service_create'), # Reusing ServiceCreateView
    path('provider/services/<slug:service_slug>/edit/', views.ServiceUpdateView.as_view(), name='service_provider_service_edit'), # Reusing ServiceUpdateView
    path('provider/services/<slug:service_slug>/delete/', views.ServiceDeleteView.as_view(), name='service_provider_service_delete'), # Reusing ServiceDeleteView
    path('provider/bookings/', views.ServiceProviderBookingsListView.as_view(), name='service_provider_bookings_list'), # Placeholder
    path('provider/verify/', views.MultiStepVendorVerificationView.as_view(), name='service_provider_verification_multistep'), # Placeholder, ensure you have a view for this
    path('provider/payouts/', views.ServiceProviderPayoutRequestListView.as_view(), name='service_provider_payout_requests'),
    path('provider/payouts/request/', views.ServiceProviderPayoutRequestCreateView.as_view(), name='service_provider_payout_request_create'),
    # path('provider/profile/edit/', views.EditServiceProviderProfileView.as_view(), name='service_provider_profile_edit'), # Placeholder
]
# --- END: Service Provider Dashboard URLs ---

# --- START: Customer Notification URL ---
urlpatterns += [path('notifications/', views.CustomerNotificationListView.as_view(), name='customer_notification_list'),]
# END: Customer Notification URL
