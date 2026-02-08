from .models import Service, Category, Message, Product # Import Message and Product models
from django.db.models import Count, Prefetch
from django.conf import settings
from .utils import get_exchange_rate # Import the helper function
from django_countries import countries

# Eager-load up to three levels of subcategories to support nested menu rendering without N+1 queries
def _prefetch_category_tree(queryset):
    return queryset.prefetch_related(
        Prefetch('subcategories', queryset=Category.objects.filter(is_active=True).order_by('name').prefetch_related(
            Prefetch('subcategories', queryset=Category.objects.filter(is_active=True).order_by('name').prefetch_related(
                Prefetch('subcategories', queryset=Category.objects.filter(is_active=True).order_by('name'))
            ))
        ))
    )

def provider_info(request):
    is_provider = False
    if request.user.is_authenticated:
        # A user is considered a provider if they have at least one service listed
        is_provider = Service.objects.filter(provider=request.user).exists()
    return {'is_provider': is_provider}

def categories_processor(request):
    """
    Makes categories (and origin countries) available to all templates.
    Fetches top-level active categories and aggregates product counts by origin country.
    """
    menu_categories = _prefetch_category_tree(Category.objects.filter(is_active=True, parent__isnull=True).annotate(
        product_count=Count('products')).order_by('name'))

    # Aggregate top countries from active products for use in menus/modals
    country_counts = (
        Product.objects.filter(is_active=True)
        .exclude(origin_country__isnull=True)
        .values('origin_country')
        .annotate(count=Count('id'))
        .order_by('-count')[:20]
    )
    menu_countries = []
    for entry in country_counts:
        code = entry.get('origin_country') or ''
        name = countries.name(code) if code else ''
        menu_countries.append({'code': code, 'name': name or code, 'count': entry.get('count', 0)})

    return {'menu_categories': menu_categories, 'menu_countries': menu_countries}

def unread_message_count(request):
    """
    Calculates the number of unread messages for the logged-in user.
    """
    if not request.user.is_authenticated:
        return {'unread_message_count': 0}

    count = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False
    ).exclude(sender=request.user).count()
    return {'unread_message_count': count}

def currency_context(request):
    """
    Adds currency information to the context.
    """
    currency_code = request.session.get('currency_code', getattr(settings, 'DEFAULT_CURRENCY_CODE', 'GBP'))
    
    symbols = {
        'GBP': '£',
        'USD': '$',
        'EUR': '€',
        'GHS': 'GH₵',
        'NGN': '₦',
        'CAD': 'C$',
        'AUD': 'A$',
        'JPY': '¥',
        'CNY': '¥',
        'INR': '₹',
        'ZAR': 'R',
        'KES': 'KSh',
        'BRL': 'R$',
        'MXN': 'MX$',
        'AED': 'د.إ',
        'SAR': '﷼',
        'CHF': 'CHF',
        'SEK': 'kr',
        'NOK': 'kr',
        'DKK': 'kr',
        'PLN': 'zł',
        'TRY': '₺',
        'RUB': '₽',
        'THB': '฿',
        'SGD': 'S$',
        'MYR': 'RM',
        'PHP': '₱',
        'IDR': 'Rp',
        'VND': '₫',
        'EGP': 'E£',
        'MAD': 'د.م.',
        'NZD': 'NZ$',
        'HKD': 'HK$',
        'KRW': '₩',
        'ILS': '₪',
        'CZK': 'Kč',
        'HUF': 'Ft'
    }
    currency_symbol = symbols.get(currency_code, '£')
    
    # Fetch exchange rate (Base is GBP defined in settings)
    currency_rate = get_exchange_rate(currency_code)
    
    return {
        'currency_code': currency_code,
        'currency_symbol': currency_symbol,
        'currency_rate': currency_rate, # Pass rate to templates
    }
