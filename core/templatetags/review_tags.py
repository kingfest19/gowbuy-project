from django import template
from django.utils.html import format_html, mark_safe

register = template.Library()


@register.simple_tag
def render_stars(rating, max_stars=5):
    """
    Renders a star rating display.
    """
    try:
        rating = int(rating)
    except (ValueError, TypeError):
        rating = 0

    filled_stars = min(max_stars, max(0, rating))
    empty_stars = max_stars - filled_stars
    html = f'<i class="bi bi-star-fill"></i>' * filled_stars + f'<i class="bi bi-star"></i>' * empty_stars
    return mark_safe(html)
