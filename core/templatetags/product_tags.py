from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()

LOW_STOCK_THRESHOLD = 5

@register.filter
def product_status_badge(status):
    """
    Returns a dictionary with Bootstrap class and display text for a product status.
    """
    status_map = {
        'published': {'class': 'bg-success', 'text': _('Published')},
        'pending': {'class': 'bg-info text-dark', 'text': _('Pending Review')},
        'draft': {'class': 'bg-secondary', 'text': _('Draft')},
        'rejected': {'class': 'bg-danger', 'text': _('Rejected')},
    }
    return status_map.get(status, {'class': 'bg-light text-dark', 'text': status.replace('_', ' ').title()})


@register.filter
def product_stock_badge(stock_count):
    """
    Returns a dictionary with Bootstrap class and display text for a product's stock level.
    """
    if stock_count <= 0:
        return {'class': 'bg-danger', 'text': _('Out of Stock')}
    elif stock_count <= LOW_STOCK_THRESHOLD:
        return {'class': 'bg-warning text-dark', 'text': _('Low Stock')}
    else:
        return {'class': 'bg-success', 'text': _('In Stock')}
