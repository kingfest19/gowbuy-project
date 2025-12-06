from django import template
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

register = template.Library()

@register.filter(name='promotion_status_badge')
def promotion_status_badge(promotion):
    """
    Determines the status of a promotion and returns a dictionary
    containing the status text and a corresponding Bootstrap badge class.
    """
    now = timezone.now()
    status = {
        'text': _('Unknown'),
        'class': 'bg-secondary'
    }

    if not promotion.is_active:
        status['text'] = _('Inactive')
        status['class'] = 'bg-secondary'
        return status

    if promotion.usage_limit is not None and promotion.usage_count >= promotion.usage_limit:
        status['text'] = _('Used Up')
        status['class'] = 'bg-warning text-dark'
        return status

    if promotion.end_date and promotion.end_date < now:
        status['text'] = _('Expired')
        status['class'] = 'bg-danger'
        return status

    if promotion.start_date > now:
        status['text'] = _('Scheduled')
        status['class'] = 'bg-info text-dark'
        return status

    # If we reach here, the promotion is currently active
    status['text'] = _('Active')
    status['class'] = 'bg-success'
    return status