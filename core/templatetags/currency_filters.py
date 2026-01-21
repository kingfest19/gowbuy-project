from django import template
from decimal import Decimal

register = template.Library()

@register.simple_tag(takes_context=True)
def convert_price(context, price):
    """
    Converts a price to the selected currency using the rate in the context.
    Usage: {% convert_price product.price %}
    """
    if price is None:
        return ""
        
    rate = context.get('currency_rate', Decimal('1.0'))
    symbol = context.get('currency_symbol', '£')
    
    try:
        # Ensure price is a Decimal
        if not isinstance(price, Decimal):
            price = Decimal(str(price))
            
        converted_price = price * rate
        return f"{symbol}{converted_price:,.2f}"
    except (ValueError, TypeError, ArithmeticError):
        return f"{symbol}{price}"

@register.filter
def currency_symbol(code):
    """
    Returns the symbol for a given currency code.
    Usage: {{ order.currency|currency_symbol }}
    """
    symbols = {
        'GBP': '£',
        'USD': '$',
        'EUR': '€',
        'GHS': 'GH₵',
        'NGN': '₦',
    }
    return symbols.get(code, '') # Return empty string if code not found