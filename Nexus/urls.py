# Nexus/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# --- Import the specific view ---
from core.views import add_to_cart, cart, checkout, place_order, signin, signout, terms, privacy, help_page # Add other needed views
from authapp.views import register_view # Assuming signup is here

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core app URLs (namespaced)
    path('', include('core.urls', namespace='core')), # Includes home, product_detail etc.

    # --- Cart URLs (Not namespaced in this example) ---
    path('cart/', cart, name='cart'),
    path('add-to-cart/', add_to_cart, name='add_to_cart'), # <<< THIS LINE
    path('checkout/', checkout, name='checkout'),
    path('place-order/', place_order, name='place_order'),
    # -------------------------------------------------

    # Authentication URLs (Not namespaced)
    path('signin/', signin, name='signin'),
    path('signup/', register_view, name='signup'), # Assuming signup view is register_view
    path('logout/', signout, name='logout'),

    # Allauth URLs
    path('accounts/', include('allauth.urls')), # Handles password reset etc.

    # Static Pages (Not namespaced)
    path('terms/', terms, name='terms'),
    path('privacy/', privacy, name='privacy'),
    path('help/', help_page, name='help'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

