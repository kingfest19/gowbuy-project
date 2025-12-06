# Nexus/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# --- Import the specific view ---
from core.views import (
    add_to_cart, cart_detail, checkout, place_order, 
    TermsView, PrivacyPolicyView, HelpPageView # Changed to class-based views
)
# --- START: Imports for Rate Limiting ---
from allauth.account import views as allauth_views
from django_ratelimit.decorators import ratelimit
# --- END: Imports for Rate Limiting ---
# Import views from authapp if they are used directly here
# If signin, signup, logout are handled by authapp.urls or allauth.urls, these imports might not be needed
# For now, assuming they are used for global, non-namespaced URLs as per the urlpatterns
from authapp.views import register_view, signin, signout

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core app URLs (namespaced)
    # This will handle URLs like /profile/, /profile/edit/ etc. via core.urls
    path('', include('core.urls', namespace='core')), 

    # --- Cart URLs (Globally accessible, not namespaced under 'core' or 'authapp') ---
    # These are directly defined here using views imported from core.views
    path('cart/', cart_detail, name='cart'), 
    path('add-to-cart/', add_to_cart, name='add_to_cart'), # Assuming add_to_cart is a view in core.views
    # path('checkout/', checkout, name='checkout'), # This is also in core.urls, ensure no conflict or decide where it lives
    # path('place-order/', place_order, name='place_order'), # Also in core.urls

    # Authentication URLs (Globally accessible, not namespaced under 'authapp' here)
    # These are directly defined here using views imported from authapp.views
    # This means URLs like /signin/, /signup/ will work.
    path('signin/', signin, name='signin'), 
    path('signup/', register_view, name='signup'), 
    path('logout/', signout, name='logout'), 
    
    # Authapp namespaced URLs (e.g., for /auth/signin/, /auth/signup/ if needed)
    # This allows for {% url 'authapp:signin' %} if you have URLs defined in authapp.urls
    path('auth/', include('authapp.urls', namespace='authapp')),

    # --- START: Rate-Limited Allauth URLs ---
    # By placing these before the generic include, they will be matched first.
    # Limits login attempts to 10 per minute per IP.
    path(
        "accounts/login/",
        ratelimit(key="ip", rate="10/m", block=True)(allauth_views.LoginView.as_view()),
        name="account_login",
    ),
    # Limits signup attempts to 10 per hour per IP.
    path(
        "accounts/signup/",
        ratelimit(key="ip", rate="10/h", block=True)(allauth_views.SignupView.as_view()),
        name="account_signup",
    ),
    # Limits password reset requests to 10 per hour per IP.
    path(
        "accounts/password/reset/",
        ratelimit(key="ip", rate="10/h", block=True)(allauth_views.PasswordResetView.as_view()),
        name="account_reset_password",
    ),
    # Allauth URLs (handles /accounts/login/, /accounts/signup/, /accounts/password/reset/, etc.)
    # The custom URLs above will be matched first.
    path('accounts/', include('allauth.urls')),
    path('accounts/mfa/', include('allauth.mfa.urls')), # Add allauth's MFA URLs

    # PayPal IPN listener
    path('paypal/', include('paypal.standard.ipn.urls')),

    # Static Pages (Globally accessible)
    path('terms/', TermsView.as_view(), name='terms'),
    path('privacy/', PrivacyPolicyView.as_view(), name='privacy'),
    path('help/', HelpPageView.as_view(), name='help'),

]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serving static files with runserver is usually handled automatically by Django when DEBUG=True
    # So the next line is often not strictly necessary for development but doesn't hurt.
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
