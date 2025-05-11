from .models import Service # Assuming Service model is in core.models

def provider_info(request):
    is_provider = False
    if request.user.is_authenticated:
        # A user is considered a provider if they have at least one service listed
        is_provider = Service.objects.filter(provider=request.user).exists()
    return {'is_provider': is_provider}