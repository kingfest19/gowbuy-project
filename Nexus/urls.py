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

    # Allauth URLs (handles /accounts/login/, /accounts/signup/, /accounts/password/reset/, etc.)
    path('accounts/', include('allauth.urls')),

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
