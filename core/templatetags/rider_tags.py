from django import template
from core.models import RiderProfile # Make sure RiderProfile is imported from your models

register = template.Library()

@register.filter
def can_apply_as_rider(user):
    """
    Checks if a user can apply to be a rider.
    Returns True if the user is authenticated and does not already have a RiderProfile.
    """
    if not user.is_authenticated:
        return False
    # Check if a RiderProfile already exists for this user
    return not RiderProfile.objects.filter(user=user).exists()

@register.filter
def has_rider_profile(user):
    """
    Checks if a user has a RiderProfile.
    Returns True if the user is authenticated and has a RiderProfile.
    """
    if not user.is_authenticated:
        return False
    return RiderProfile.objects.filter(user=user).exists()
