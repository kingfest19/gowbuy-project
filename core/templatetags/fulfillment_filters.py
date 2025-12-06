from django import template

register = template.Library()

@register.filter(name='filtered_by_fulfillment')
def filtered_by_fulfillment(order_items, fulfillment_type):
    """
    Filters a queryset of OrderItem objects by their fulfillment_method.
    """
    return order_items.filter(fulfillment_method=fulfillment_type)

@register.filter(name='filtered_by_type')
def filtered_by_type(order_items, product_type):
    """
    Filters a queryset of OrderItem objects by their product's product_type.
    """
    return order_items.filter(product__product_type=product_type)
