from django import template

register = template.Library()

@register.filter(name='replace')
def replace_filter(value, args_str):
    # Expects args_str to be "old_substring,new_substring"
    try:
        old, new = args_str.split(',', 1)
        return str(value).replace(old, new)
    except ValueError:
        return value # Or handle error differently, e.g., log it or return original value