from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Returns the URL-encoded query string for the current page,
    updating the given query parameters.

    For example, if the current URL is /products/?page=1&color=blue,
    then {% query_transform page=2 sort="name" %} would return
    'color=blue&page=2&sort=name'.
    
    Empty string or None values will remove the parameter from the query string.
    """
    query = context['request'].GET.copy()
    for k, v in kwargs.items():
        if v == '' or v is None:
            # Remove the parameter if value is empty or None
            if k in query:
                del query[k]
        else:
            query[k] = v
    return query.urlencode()