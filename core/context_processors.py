# core/context_processors.py
from django.conf import settings # <<< Import settings
from django.utils.translation import get_language # <<< Import get_language
from .models import Category # <<< Import Category model
from django.db.models import Prefetch # <<< Import Prefetch

def site_context(request): # <<< Renamed function for broader scope
    """Adds site-wide context like delivery location and language."""
    # Get location from session, default to 'United States' if not set
    delivery_location = request.session.get('delivery_location', 'United States')
    # Get the currently active language for the request
    current_language = get_language() # <<< Use Django's function to get active language
    # Fetch categories for the modal menu
    modal_categories = Category.objects.filter(
        is_active=True, parent=None
    ).prefetch_related(
        Prefetch('subcategories', queryset=Category.objects.filter(is_active=True).order_by('name'))
    ).order_by('name')
    return {
        'delivery_location': delivery_location,
        'current_language': current_language, # <<< Add language to context
        'modal_categories': modal_categories, # <<< Add categories for the modal
    }
