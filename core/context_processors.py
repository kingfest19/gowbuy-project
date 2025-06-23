from .models import Service, Category # Assuming Service model is in core.models
from django.db.models import Count

def provider_info(request):
    is_provider = False
    if request.user.is_authenticated:
        # A user is considered a provider if they have at least one service listed
        is_provider = Service.objects.filter(provider=request.user).exists()
    return {'is_provider': is_provider}

def categories_processor(request):
    """
    Makes categories available to all templates.
    Fetches top-level active categories.
    """
    menu_categories = Category.objects.filter(is_active=True, parent__isnull=True).annotate(
        product_count=Count('products')).order_by('name')
    return {'menu_categories': menu_categories}