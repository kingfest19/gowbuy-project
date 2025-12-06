# c:\Users\Hp\Desktop\Nexus\core\urls.py
# core/urls.py
from django.urls import path
# Import all necessary views from core.views that are handled by this file
from . import views, payment_views # <<< Import the views module itself
from .views import VendorUpgradeView # Make sure to import the new view



app_name = 'core' # Namespace for reversing URLs (e.g., {% url 'core:product_detail' ... %})

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),

    # --- Help/Static Pages ---
    path('help/creating-3d-models/', views.Creating3DModelsHelpView.as_view(), name='help_creating_3d_models'),
    path('terms/', views.TermsView.as_view(), name='terms_and_conditions'),
    path('privacy/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),

    # Product pages
    # Catalog pages (These match the get_absolute_url methods in models)
    path('category/<slug:category_slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('product/<slug:product_slug>/', views.ProductDetailView.as_view(), name='product_detail'),

    # Search page
    path('search/', views.search_results, name='search_results'),

    path('product_list/', views.ProductListView.as_view(), name='product_list'), # For ProductListView
    # Offers page
    path('offers/', views.daily_offers, name='daily_offers'),

    # Sell on Nexus page
    path('sell/', views.sell_on_nexus, name='sell_on_nexus'),

    # Shop Local page
    path('shop-local/', views.shop_local, name='shop_local'),

    # Vendor Registration page
    path('register-vendor/', views.vendor_registration_view, name='register_vendor'),

    # Vendor Dashboard page
    path('dashboard/', views.VendorDashboardView.as_view(), name='vendor_dashboard'),

    # Vendor Verification page
     path('dashboard/verify/', views.MultiStepVendorVerificationView.as_view(), name='vendor_verification'),

    # Vendor Profile Edit page
    path('dashboard/profile/edit/', views.EditVendorProfileView.as_view(), name='edit_vendor_profile'),

    # Vendor Shipping Settings page (assuming this is what edit_vendor_shipping was for)
    path('dashboard/shipping/', views.EditVendorShippingView.as_view(), name='vendor_shipping_settings'),

    # Vendor Payment Edit page
      path('dashboard/payment/edit/', views.EditVendorPaymentView.as_view(), name='vendor_payment_settings'), # Corrected name

    # --- Vendor Additional Info ---
    path('dashboard/additional-info/', views.EditVendorAdditionalInfoView.as_view(), name='edit_vendor_additional_info'),

    # --- Vendor Orders ---
    path('dashboard/orders/', views.VendorOrderListView.as_view(), name='vendor_order_list'),
    path('dashboard/orders/<int:pk>/', views.VendorOrderDetailView.as_view(), name='vendor_order_detail'),
    path('dashboard/orders/<int:order_id>/mark-shipped/', views.vendor_mark_order_shipped, name='vendor_mark_order_shipped'),
    path('dashboard/upgrade/pay/<int:plan_id>/', views.initiate_plan_payment, name='initiate_plan_payment'),
    path('vendor/orders/<int:pk>/email-packing-slip/', views.vendor_email_packing_slip, name='vendor_email_packing_slip'),
    path('vendor/orders/<int:pk>/packing-slip/', views.vendor_generate_packing_slip, name='vendor_generate_packing_slip'),
    path('dashboard/upgrade/callback/', views.plan_payment_callback, name='plan_payment_callback'),
    path('dashboard/upgrade/', VendorUpgradeView.as_view(), name='vendor_upgrade'),

    # --- Vendor Reports ---
    path('dashboard/reports/', views.VendorReportsView.as_view(), name='vendor_reports'),

    # --- Vendor Promotions ---
    path('dashboard/promotions/', views.VendorPromotionListView.as_view(), name='vendor_promotion_list'),
    path('dashboard/promotions/create/', views.VendorPromotionCreateView.as_view(), name='vendor_promotion_create'),
    path('dashboard/promotions/<int:pk>/edit/', views.VendorPromotionUpdateView.as_view(), name='vendor_promotion_edit'),
    path('dashboard/promotions/<int:pk>/delete/', views.VendorPromotionDeleteView.as_view(), name='vendor_promotion_delete'),

    # --- Vendor Ad Campaigns ---
    path('dashboard/campaigns/', views.VendorCampaignListView.as_view(), name='vendor_campaign_list'),  # Corrected name to match template usage
       path('dashboard/campaigns/create/', views.VendorCampaignCreateView.as_view(), name='vendor_campaign_create'), # Corrected name
    path('dashboard/campaigns/<int:pk>/edit/', views.VendorCampaignUpdateView.as_view(), name='vendor_campaign_edit'), # Assuming pk
    path('dashboard/campaigns/<int:pk>/delete/', views.VendorCampaignDeleteView.as_view(), name='vendor_campaign_delete'), # Assuming pk

    # --- Vendor Notifications ---
    path('dashboard/notifications/', views.VendorNotificationListView.as_view(), name='vendor_notification_list'),
    path('dashboard/notifications/mark-all-read/', views.vendor_mark_all_notifications_read, name='vendor_mark_all_notifications_read'),
    path('dashboard/notifications/<int:pk>/delete/', views.vendor_delete_notification, name='vendor_delete_notification'),
    path('dashboard/notifications/delete-all/', views.vendor_delete_all_notifications, name='vendor_delete_all_notifications'),

    # --- Vendor Products ---
    path('dashboard/products/', views.VendorProductListView.as_view(), name='vendor_product_list'),
    path('dashboard/products/create/', views.VendorProductCreateView.as_view(), name='vendor_product_create'), # Corrected
    path('dashboard/products/<int:pk>/update/', views.VendorProductUpdateView.as_view(), name='vendor_product_update'),
    path('dashboard/products/<int:pk>/delete/', views.VendorProductDeleteView.as_view(), name='vendor_product_delete'), # Corrected


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
    path('cart/save-for-later/<int:item_id>/', views.save_for_later, name='save_for_later'),
    path('cart/move-to-cart/<int:saved_item_id>/', views.move_to_cart, name='move_to_cart'),
    path('cart/delete-saved-item/<int:saved_item_id>/', views.delete_saved_item, name='delete_saved_item'),
    # --- Coupon URLs ---
    path('coupon/apply/', views.apply_coupon, name='apply_coupon'),
    path('coupon/remove/', views.remove_coupon, name='remove_coupon'),
    # --- End Coupon URLs ---

    # Order pages (These require login via decorators in views)
    path('orders/', views.OrderHistoryView.as_view(), name='order_history'),
    path('order/<str:order_id>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('order/<str:order_id>/invoice/print/', views.customer_generate_invoice, name='customer_generate_invoice'),
    path('order/<str:order_id>/invoice/email/', views.customer_email_invoice, name='customer_email_invoice'),
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
    
    # --- PayPal Payment URLs ---
    path('process-payment/<int:order_id>/', payment_views.process_payment, name='process_payment'),
    path('payment-done/', payment_views.payment_done, name='payment_done'),
    path('payment-cancelled/', payment_views.payment_cancelled, name='payment_cancelled'),

    #Address URLs
    path('profile/addresses/', views.address_list_view, name='address_list'),
    path('profile/addresses/edit/<int:address_id>/', views.address_edit_view, name='address_edit'),
    path('profile/addresses/delete/<int:address_id>/', views.address_delete_view, name='address_delete'),
    path('products/download/<int:product_id>/', views.download_digital_product, name='download_digital_product'),

    # Wishlist
    path('wishlist/', views.view_wishlist, name='wishlist_detail'), # Changed from wishlist_detail to view_wishlist
    path('wishlist/add/', views.add_to_wishlist, name='add_to_wishlist'), # Changed URL to be more generic for POST
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # Review pages
    path('product/<int:product_id>/add-review/', views.submit_product_review, name='submit_product_review'),
    path('vendor/<int:vendor_id>/add-review/', views.submit_vendor_review, name='submit_vendor_review'),

    # Location Update URL
    path('update-location/', views.update_location, name='update_location'),

    # Language Update URL
    path('update-language/', views.update_language, name='update_language'),

    # User Profile URL
    path('profile/edit/', views.edit_user_profile, name='edit_user_profile'), # More specific URL first
    path('profile/', views.user_profile_view, name='user_profile'), # General profile view for the logged-in user
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/reviews/', views.customer_review_list, name='customer_review_list'),
    path('profile/reviews/edit/<str:review_type>/<int:review_id>/', views.edit_review, name='edit_review'),
    path('profile/messages/', views.ConversationListView.as_view(), name='customer_message_list'), # List for customers
    path('profile/messages/<int:pk>/', views.ConversationDetailView.as_view(), name='customer_message_detail'), # Detail for customers
    path('profile/reviews/delete/<str:review_type>/<int:review_id>/', views.delete_review, name='delete_review'),
    path('profile/rewards/', views.render_rewards_page, name='rewards_page'),
    path('profile/security/login-history/', views.LoginHistoryView.as_view(), name='login_history'),
    path('profile/security/sessions/', views.session_management_view, name='session_management'),
    path('profile/security/sessions/logout-others/', views.logout_other_sessions_view, name='logout_other_sessions'),


    # Service Provider
    path('dashboard/provider/', views.ProviderDashboardView.as_view(), name='provider_dashboard'),

    path('become-service-provider/', views.become_service_provider, name='become_service_provider'),


    # Public Provider Profile
    path('service_providers/<str:username>/', views.ProviderProfileDetailView.as_view(), name='provider_profile_detail'),

    # Edit Service Provider Profile & Portfolio
    path('dashboard/provider/edit-profile/', views.edit_service_provider_profile, name='edit_service_provider_profile'),
    path('dashboard/provider/portfolio/delete/<int:item_id>/', views.delete_portfolio_item, name='delete_portfolio_item'),
    path('dashboard/provider/portfolio/edit/<int:item_id>/', views.PortfolioItemUpdateView.as_view(), name='edit_portfolio_item'),
    
    # Vendor Payouts (ensure these are defined if used in sidebar)
    path('dashboard/payouts/', views.VendorPayoutListView.as_view(), name='vendor_payout_request_list'),
    path('dashboard/payouts/request/', views.VendorPayoutRequestCreateView.as_view(), name='vendor_payout_request_create'), # Create

    # --- Vendor Reviews --- # <-- Added comment for clarity
    path('dashboard/reviews/', views.VendorReviewListView.as_view(), name='vendor_review_list'), # <-- Corrected name for consistency
    path('dashboard/reviews/<int:pk>/reply/', views.VendorReviewReplyView.as_view(), name='vendor_review_reply'),

    # --- Vendor Messaging ---
    path('dashboard/messages/', views.ConversationListView.as_view(), name='vendor_message_list'),
    path('dashboard/messages/<int:pk>/', views.ConversationDetailView.as_view(), name='vendor_message_detail'),
    path('product/<int:product_id>/contact-vendor/', views.StartConversationView.as_view(), name='start_conversation'),


    # --- AJAX URLs ---
    path('ajax/enhance-description/', views.ajax_enhance_product_description, name='ajax_enhance_product_description'),
    path('ajax/chatbot-message/', views.ajax_chatbot_message, name='ajax_chatbot_message'),
    path('ajax/get-product-details/', views.ajax_get_product_details, name='ajax_get_product_details'),
    path('ajax/get-item-details/', views.ajax_get_item_details, name='ajax_get_item_details'), # New endpoint for chatbot
    path('ajax/visual-search/', views.ajax_visual_search, name='ajax_visual_search'),
    path('ajax/generate-3d-model/', views.ajax_generate_3d_model, name='ajax_generate_3d_model'), # <<< Add this URL
    # --- START: New AJAX Image Tool URLs ---
    path('ajax/product-image/enhance/', views.ajax_enhance_product_image, name='ajax_enhance_product_image'),
    path('ajax/product-image/remove-background/', views.ajax_remove_image_background, name='ajax_remove_image_background'),
    # --- END: New AJAX Image Tool URLs ---
  # --- API Endpoints for Mobile App ---
    path('api/v1/product/<int:product_id>/upload-3d-model/', views.api_upload_3d_model, name='api_upload_3d_model'),
]

# --- START: Product Q&A URLs ---
urlpatterns += [
    path('product/<int:product_id>/ask-question/', views.add_product_question, name='add_product_question'),
    path('question/<int:question_id>/add-answer/', views.add_product_answer, name='add_product_answer'),
]
# --- END: Product Q&A URLs ---



# --- START: Service Marketplace URLs ---
urlpatterns += [
    path('services/', views.ServiceListView.as_view(), name='service_list'),
    path('services/category/<slug:category_slug>/', views.CategoryServiceListView.as_view(), name='services_by_category'),
    path('service-category/<slug:category_slug>/', views.ServiceCategoryDetailView.as_view(), name='service_category_detail'),
    path('services/search/', views.ServiceSearchResultsView.as_view(), name='service_search_results'),
    path('services/create/', views.ServiceCreateView.as_view(), name='service_create'),
    path('service/<slug:service_slug>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('service/<slug:service_slug>/edit/', views.ServiceUpdateView.as_view(), name='service_edit'),
    path('service/<slug:service_slug>/delete/', views.ServiceDeleteView.as_view(), name='service_delete'),
    path('service/<slug:service_slug>/add-review/', views.submit_service_review, name='submit_service_review'),

    path('book-service/<int:package_id>/', views.create_service_booking, name='create_service_booking'),
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
    path('provider/dashboard/', views.ProviderDashboardView.as_view(), name='service_provider_dashboard'),
    path('provider/services/', views.ServiceProviderServicesListView.as_view(), name='service_provider_services_list'),
    path('provider/services/create/', views.ServiceCreateView.as_view(), name='service_provider_service_create'), # Reusing ServiceCreateView
    path('provider/services/<slug:service_slug>/edit/', views.ServiceUpdateView.as_view(), name='service_provider_service_edit'), # Reusing ServiceUpdateView
    path('provider/services/<slug:service_slug>/delete/', views.ServiceDeleteView.as_view(), name='service_provider_service_delete'), # Reusing ServiceDeleteView
    path('provider/advertisements/', views.service_provider_advertisements, name='service_provider_advertisements'),
    path('provider/advertisements/create/', views.ServiceProviderAdCampaignCreateView.as_view(), name='service_provider_ad_campaign_create'),
    path('provider/payout-settings/', views.EditServiceProviderPayoutView.as_view(), name='service_provider_payout_settings'),
    path('provider/bookings/', views.ServiceProviderBookingsListView.as_view(), name='service_provider_bookings_list'),
    path('provider/bookings/<int:booking_id>/', views.ServiceProviderBookingDetailView.as_view(), name='service_provider_booking_detail'),
    path('provider/bookings/<int:booking_id>/confirm/', views.service_provider_confirm_booking, name='service_provider_confirm_booking'),
    path('provider/verify/', views.MultiStepVendorVerificationView.as_view(), name='service_provider_verification_multistep'), # Placeholder, ensure you have a view for this
    # --- Service Provider Reviews ---
    path('provider/reviews/', views.ServiceProviderReviewListView.as_view(), name='service_provider_review_list'),
    path('provider/reviews/<int:pk>/reply/', views.ServiceProviderReviewReplyView.as_view(), name='service_provider_review_reply'),
    # --- Service Provider Notifications ---
    path('provider/notifications/', views.ServiceProviderNotificationListView.as_view(), name='service_provider_notification_list'),
    path('provider/notifications/mark-all-read/', views.service_provider_mark_all_notifications_read, name='service_provider_mark_all_notifications_read'),
    path('provider/notifications/<int:pk>/delete/', views.service_provider_delete_notification, name='service_provider_delete_notification'),
    path('provider/notifications/delete-all/', views.service_provider_delete_all_notifications, name='service_provider_delete_all_notifications'),
        path('provider/payouts/', views.ServiceProviderPayoutRequestListView.as_view(), name='service_provider_payout_requests'),
    path('provider/payouts/request/', views.ServiceProviderPayoutRequestCreateView.as_view(), name='service_provider_payout_request_create'),
    # --- Service Provider Availability ---
    path('provider/availability/', views.ServiceAvailabilityListView.as_view(), name='service_provider_availability_list'),
    path('provider/availability/create/', views.ServiceAvailabilityCreateView.as_view(), name='service_provider_availability_create'),
    path('provider/availability/<int:pk>/edit/', views.ServiceAvailabilityUpdateView.as_view(), name='service_provider_availability_edit'),
    path('provider/availability/<int:pk>/delete/', views.ServiceAvailabilityDeleteView.as_view(), name='service_provider_availability_delete'),
    # --- Service Provider Messaging ---
    path('provider/messages/', views.ConversationListView.as_view(), name='service_provider_message_list'), # Now uses the generic view
    path('provider/messages/<int:pk>/', views.ConversationDetailView.as_view(), name='service_provider_message_detail'),
    # path('provider/profile/edit/', views.EditServiceProviderProfileView.as_view(), name='service_provider_profile_edit'), # Placeholder
]
# --- END: Service Provider Dashboard URLs ---

# --- START: Customer Notification URL ---
urlpatterns += [path('notifications/', views.CustomerNotificationListView.as_view(), name='customer_notification_list'),]
# END: Customer Notification URL
