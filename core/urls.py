# c:\Users\Hp\Desktop\Nexus\core\urls.py
# core/urls.py
from django.urls import path, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
# Import all necessary views from core.views that are handled by this file
from . import views, payment_views # <<< Import the views module itself
from .views import VendorUpgradeView # Make sure to import the new view



app_name = 'core' # Namespace for reversing URLs (e.g., {% url 'core:product_detail' ... %})

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),

    # --- Blog URLs ---
    path('blog/', views.BlogPostListView.as_view(), name='blog_post_list'),
    path('blog/<int:year>/<int:month>/<int:day>/<slug:slug>/', views.BlogPostDetailView.as_view(), name='blog_post_detail'),
    path('feed/rss/', views.LatestPostsFeed(), name='blog_rss'),

    # --- Help/Static Pages ---
    path('help/creating-3d-models/', views.Creating3DModelsHelpView.as_view(), name='help_creating_3d_models'),
    path('terms/', views.TermsView.as_view(), name='terms_and_conditions'),
    path('privacy/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('about/', TemplateView.as_view(template_name='core/info/about_gowbuy.html', extra_context={'page_title': 'About GOWBUY'}), name='info_about'),
    path('careers/', TemplateView.as_view(template_name='core/info/careers.html', extra_context={'page_title': 'Careers'}), name='info_careers'),
    path('press/', TemplateView.as_view(template_name='core/info/press_releases.html', extra_context={'page_title': 'Press Releases'}), name='info_press'),
    path('blog-info/', TemplateView.as_view(template_name='core/info/gowbuy_blog.html', extra_context={'page_title': 'GOWBUY Blog'}), name='info_blog'),
    path('affiliate/', TemplateView.as_view(template_name='core/info/affiliate.html', extra_context={'page_title': 'Become an Affiliate'}), name='info_affiliate'),
    path('advertise/', TemplateView.as_view(template_name='core/info/advertise_products.html', extra_context={'page_title': 'Advertise Your Products'}), name='info_advertise'),
    path('delivery-partner/', TemplateView.as_view(template_name='core/info/delivery_partner.html', extra_context={'page_title': 'Become a Delivery Partner'}), name='info_delivery_partner'),
    path('shipping-rates/', TemplateView.as_view(template_name='core/info/shipping_rates_policies.html', extra_context={'page_title': 'Shipping Rates & Policies'}), name='info_shipping'),
    path('returns/', TemplateView.as_view(template_name='core/info/returns_replacements.html', extra_context={'page_title': 'Returns & Replacements'}), name='info_returns'),
    path('contact/', TemplateView.as_view(template_name='core/info/contact_us.html', extra_context={'page_title': 'Contact Us'}), name='info_contact'),
    path('site-map/', TemplateView.as_view(template_name='core/info/site_map.html', extra_context={'page_title': 'Site Map'}), name='info_sitemap'),
    path('accessibility/', TemplateView.as_view(template_name='core/info/accessibility.html', extra_context={'page_title': 'Accessibility'}), name='info_accessibility'),

    # Product pages
    # Catalog pages (These match the get_absolute_url methods in models)
    path('category/<slug:category_slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('product/<slug:product_slug>/', views.ProductDetailView.as_view(), name='product_detail'),

    # Search page
    path('search/', views.search_results, name='search_results'),
    path('compare/', views.compare_products, name='compare_products'),

    path('product_list/', views.ProductListView.as_view(), name='product_list'), # For ProductListView
    path('origin/<str:country_code>/', views.OriginDetailView.as_view(), name='origin_detail'),
    # Offers page
    path('offers/', views.daily_offers, name='daily_offers'),

    # Sell on Gowbuy page
    path('sell/', views.sell_on_gowbuy, name='sell_on_gowbuy'),

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
    
    # --- Bulk Code Generator ---
    path('dashboard/promotions/bulk-codes/generate/', views.VendorBulkCodeGeneratorView.as_view(), name='vendor_bulk_code_generator'),
    path('dashboard/promotions/bulk-codes/confirm/', views.VendorBulkCodeConfirmView.as_view(), name='vendor_bulk_code_confirm'),

    # --- Vendor Ad Campaigns ---
    path('dashboard/campaigns/', views.VendorCampaignListView.as_view(), name='vendor_campaign_list'),  # Corrected name to match template usage
       path('dashboard/campaigns/create/', views.VendorCampaignCreateView.as_view(), name='vendor_campaign_create'), # Corrected name
    path('dashboard/campaigns/<int:pk>/edit/', views.VendorCampaignUpdateView.as_view(), name='vendor_campaign_edit'), # Assuming pk
    path('dashboard/campaigns/<int:pk>/delete/', views.VendorCampaignDeleteView.as_view(), name='vendor_campaign_delete'), # Assuming pk
    path('dashboard/campaigns/<int:pk>/pause/', views.VendorCampaignPauseView.as_view(), name='vendor_campaign_pause'),
    path('dashboard/campaigns/<int:pk>/duplicate/', views.VendorCampaignDuplicateView.as_view(), name='vendor_campaign_duplicate'),
    path('dashboard/campaigns/<int:pk>/analytics/', views.VendorCampaignAnalyticsView.as_view(), name='vendor_campaign_analytics'),
    path('dashboard/campaigns/bulk-action/', views.VendorCampaignBulkActionView.as_view(), name='vendor_campaign_bulk_action'),
    
    # --- Campaign Templates ---
    path('dashboard/campaign-templates/', views.VendorCampaignTemplateListView.as_view(), name='vendor_campaign_template_list'),
    path('dashboard/campaign-templates/create/', views.VendorCampaignTemplateCreateView.as_view(), name='vendor_campaign_template_create'),
    path('dashboard/campaign-templates/<int:pk>/delete/', views.VendorCampaignTemplateDeleteView.as_view(), name='vendor_campaign_template_delete'),
    path('dashboard/campaign-templates/<int:pk>/use/', views.VendorCampaignFromTemplateView.as_view(), name='vendor_campaign_from_template'),

    # --- Vendor Notifications ---
    path('dashboard/notifications/', views.VendorNotificationListView.as_view(), name='vendor_notification_list'),
    path('dashboard/notifications/mark-all-read/', views.vendor_mark_all_notifications_read, name='vendor_mark_all_notifications_read'),
    path('dashboard/notifications/<int:pk>/delete/', views.vendor_delete_notification, name='vendor_delete_notification'),
    path('dashboard/notifications/delete-all/', views.vendor_delete_all_notifications, name='vendor_delete_all_notifications'),

    # --- Vendor Products ---
    path('dashboard/products/', views.VendorProductListView.as_view(), name='vendor_product_list'),
    path('dashboard/products/create/', views.VendorProductWizardView.as_view(), name='vendor_product_create'),
    path('dashboard/products/<int:pk>/update/', views.VendorProductWizardUpdateView.as_view(), name='vendor_product_update'),
    path('dashboard/products/<int:pk>/delete/', views.VendorProductDeleteView.as_view(), name='vendor_product_delete'), # Corrected
    path('dashboard/products/<int:pk>/restore/', views.vendor_restore_product, name='vendor_product_restore'),
    path('dashboard/products/bulk-delete/', views.vendor_bulk_delete_products, name='vendor_bulk_delete_products'),
    path('dashboard/products/bulk-update/', views.vendor_bulk_update_products, name='vendor_bulk_update_products'),


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
    path('order/<str:order_id>/invoice/download/', views.download_invoice, name='download_invoice'), # Updated
    path('order/<str:order_id>/invoice/email/', views.customer_email_invoice, name='customer_email_invoice'),
    # path('order/<str:order_id>/download/<int:product_id>/', views.download_digital_product, name='download_digital_product'), # Keep if function-based
    path('reorder/<str:order_id>/', views.reorder, name='reorder'), # Added
    path('order/<str:order_id>/cancel/', views.cancel_order, name='cancel_order'), # Added Cancel Order URL
    path('order/<str:order_id>/submit-payment-proof/', views.submit_payment_proof, name='submit_payment_proof'),

    # Checkout & Order Placement
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/add-address/', views.add_checkout_address, name='add_checkout_address'),   # Ensure POST to this URL
    path('place-order/', views.place_order, name='place_order'),                       # Ensure POST to this URL
    path('ajax/calculate-delivery-fee/', views.calculate_delivery_fee_ajax, name='calculate_delivery_fee_ajax'), # New AJAX endpoint
    path('order/<str:order_id>/process-choice/', views.process_checkout_choice, name='process_checkout_choice'), # Handle checkout choice
    path('order/<int:order_id>/initiate-payment/', views.initiate_paystack_payment, name='initiate_paystack_payment'),
    path('paystack/callback/', views.paystack_callback, name='paystack_callback'), # Keep if function-based
    path('order/<int:order_id>/initiate-stripe-payment/', views.initiate_stripe_payment, name='initiate_stripe_payment'),
    path('stripe/success/', views.stripe_payment_success, name='stripe_payment_success'),
    path('stripe/cancel/', views.stripe_payment_cancel, name='stripe_payment_cancel'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
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
    path('update-currency/', views.update_currency, name='update_currency'), # <<< Added

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
    path('profile/recent-comparisons/', views.RecentComparisonsView.as_view(), name='recent_comparisons'),
    path('profile/reviews/delete/<str:review_type>/<int:review_id>/', views.delete_review, name='delete_review'),
    path('profile/rewards/', views.render_rewards_page, name='rewards_page'),
    path('profile/security/login-history/', views.LoginHistoryView.as_view(), name='login_history'),
    path('profile/security/sessions/', views.session_management_view, name='session_management'),
    path('profile/security/sessions/logout-others/', views.logout_other_sessions_view, name='logout_other_sessions'),

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
    # --- START: Origin Verification AJAX URLs ---
    path('api/validate-origin/', views.ajax_validate_product_origin, name='ajax_validate_product_origin'),
    path('api/origin-suggestions/', views.ajax_get_origin_suggestions, name='ajax_get_origin_suggestions'),
    path('api/check-authenticity-risk/', views.ajax_check_authenticity_risk, name='ajax_check_authenticity_risk'),
    # --- END: Origin Verification AJAX URLs ---

    # Vendor product origin suggestion endpoints (AJAX)
    path('dashboard/products/<int:pk>/suggest-origin/', views.ajax_suggest_product_origin, name='vendor_product_suggest_origin'),
    path('dashboard/products/<int:pk>/apply-origin/', views.ajax_apply_product_origin, name='vendor_product_apply_origin'),
    
    # --- Phase 4: Authenticity Feedback Endpoint ---
    path('product/<int:pk>/report-authenticity/', views.report_product_authenticity, name='report_product_authenticity'),
    
    path('subscribe-newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
  # --- API Endpoints for Mobile App ---
    path('api/v1/product/<int:product_id>/upload-3d-model/', views.api_upload_3d_model, name='api_upload_3d_model'),
    
    # --- START: Artisan/Handmade Product Verification AJAX URLs ---
    path('api/verify-artisan-product/', views.ajax_verify_artisan_product, name='ajax_verify_artisan_product'),
    path('api/validate-acquisition-info/', views.ajax_validate_acquisition_info, name='ajax_validate_acquisition_info'),
    path('api/get-acquisition-options/', views.ajax_get_acquisition_options, name='ajax_get_acquisition_options'),
    path('api/get-vendor-tier-requirements/', views.ajax_get_vendor_tier_requirements, name='ajax_get_vendor_tier_requirements'),
    # --- END: Artisan/Handmade Product Verification AJAX URLs ---
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
    path('service/<slug:slug>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('service/<slug:slug>/edit/', views.ServiceUpdateView.as_view(), name='service_edit'),
    path('service/<slug:slug>/delete/', views.ServiceDeleteView.as_view(), name='service_delete'),
    path('service/<slug:slug>/add-review/', views.submit_service_review, name='submit_service_review'),
    path('service/<slug:service_slug>/contact/', views.contact_service_provider, name='contact_service_provider'),

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
    path('provider/services/<slug:service_slug>/edit/', views.ServiceUpdateView.as_view(slug_url_kwarg='service_slug'), name='service_provider_service_edit'), # Reusing ServiceUpdateView
    path('provider/services/<slug:service_slug>/delete/', views.ServiceDeleteView.as_view(slug_url_kwarg='service_slug'), name='service_provider_service_delete'), # Reusing ServiceDeleteView
    path('provider/advertisements/', views.service_provider_advertisements, name='service_provider_advertisements'),
    path('provider/advertisements/create/', views.ServiceProviderAdCampaignCreateView.as_view(), name='service_provider_ad_campaign_create'),
    path('provider/payout-settings/', views.EditServiceProviderPayoutView.as_view(), name='service_provider_payout_settings'),
    path('provider/bookings/', views.ServiceProviderBookingsListView.as_view(), name='service_provider_bookings_list'),
    path('provider/bookings/<int:booking_id>/', views.ServiceProviderBookingDetailView.as_view(), name='service_provider_booking_detail'),
    path('provider/bookings/<int:booking_id>/confirm/', views.service_provider_confirm_booking, name='service_provider_confirm_booking'),
    path('provider/verify/', views.ServiceProviderVerificationView.as_view(), name='service_provider_verification_multistep'),
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

# --- Media Files Serving (Fix for Production) ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
