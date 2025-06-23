from django import template
from core.models import Notification # Assuming your Notification model is in core.models

register = template.Library()

@register.simple_tag(takes_context=True)
def service_provider_unread_notification_count(context):
    """
    Returns the count of unread notifications for the logged-in user (service provider context).
    """
    request = context.get('request')
    if request and request.user.is_authenticated:
        return Notification.objects.filter(recipient=request.user, is_read=False).count()
    return 0


# You can add other notification-related tags here later, e.g., to get the actual notifications.