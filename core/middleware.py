from django.utils import translation
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from urllib.parse import quote_plus
# from django.utils.translation.trans_real import check_for_language # No longer needed
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class SanitizeLanguageMiddleware:
    """
    Ensures that the activated language is one of the supported languages.
    This middleware should run AFTER Django's LocaleMiddleware.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        logger.info("[SanitizeLangMiddleware] Initialized.") # Check if middleware is loaded

    def __call__(self, request):
        logger.debug(f"[SanitizeLangMiddleware] Request path: {request.path}")
        # This part runs before the view.
        # LocaleMiddleware.process_request has already run and activated a language.
        current_lang_before_mw = translation.get_language()
        logger.info(f"[SanitizeLangMiddleware] Path: {request.path} - Language BEFORE sanitization: '{current_lang_before_mw}'")
        
        # Forcefully check for '.' or None/empty
        if current_lang_before_mw == '.' or not current_lang_before_mw:
            logger.warning(f"[SanitizeLangMiddleware] Invalid language '{current_lang_before_mw}' detected. Forcing reset to default '{settings.LANGUAGE_CODE}'.")
            translation.activate(settings.LANGUAGE_CODE)
            # Also update request.LANGUAGE_CODE if LocaleMiddleware set it
            if hasattr(request, 'LANGUAGE_CODE'):
                request.LANGUAGE_CODE = settings.LANGUAGE_CODE
            
            current_lang_after_force_reset = translation.get_language()
            logger.info(f"[SanitizeLangMiddleware] Language AFTER forced reset: '{current_lang_after_force_reset}'")
            if current_lang_after_force_reset != settings.LANGUAGE_CODE:
                 logger.error(f"[SanitizeLangMiddleware] FAILED to force reset language! Still '{current_lang_after_force_reset}'")

        else: # Language was not '.' or empty, now check if it's valid according to settings.LANGUAGES
            try:
                translation.get_language_info(current_lang_before_mw)
                logger.debug(f"[SanitizeLangMiddleware] Language '{current_lang_before_mw}' is valid and known.")
            except KeyError:
                logger.warning(f"[SanitizeLangMiddleware] Language '{current_lang_before_mw}' is UNKNOWN (KeyError). Resetting to default '{settings.LANGUAGE_CODE}'.")
                translation.activate(settings.LANGUAGE_CODE)
                if hasattr(request, 'LANGUAGE_CODE'):
                    request.LANGUAGE_CODE = settings.LANGUAGE_CODE
                
                current_lang_after_unknown_reset = translation.get_language()
                logger.info(f"[SanitizeLangMiddleware] Language AFTER unknown reset: '{current_lang_after_unknown_reset}'")
                if current_lang_after_unknown_reset != settings.LANGUAGE_CODE:
                    logger.error(f"[SanitizeLangMiddleware] FAILED to reset unknown language! Still '{current_lang_after_unknown_reset}'")

        final_lang_before_view = translation.get_language()
        logger.info(f"[SanitizeLangMiddleware] Language being passed to next middleware/view: '{final_lang_before_view}'")

        response = self.get_response(request)

        # This part runs after the view.
        # LocaleMiddleware.process_response will use translation.get_language() to set the cookie.
        # We want to ensure it uses the sanitized language.
        lang_for_cookie = translation.get_language()
        logger.debug(f"[SanitizeLangMiddleware] Language for response/cookie: '{lang_for_cookie}'")

        return response


class GuestAccessRestrictionMiddleware:
    """
    Restricts anonymous users from protected areas while allowing guest browsing
    on selected public pages.
    """

    PUBLIC_EXACT_PATHS = {
        '/',
        '/signin/',
        '/signup/',
        '/logout/',
        '/robots.txt',
        '/sitemap.xml',
        '/update-location/',
        '/update-currency/',
        '/update-language/',
        '/guest/continue/',
    }

    PUBLIC_PREFIXES = (
        '/static/',
        '/media/',
        '/admin/',
        '/tinymce/',
        '/i18n/',
        '/accounts/',
        '/auth/',
        '/menu/',
        '/blog/',
        '/category/',
        '/product/',
        '/products/',
        '/origin/',
        '/search/',
        '/compare/',
        '/offers/',
        '/sell/',
        '/shop-local/',
        '/vendors/',
        '/vendor/',
        '/services/',
        '/service/',
        '/service-category/',
        '/help/',
        '/terms/',
        '/privacy/',
        '/about/',
        '/careers/',
        '/press/',
        '/blog-info/',
        '/affiliate/',
        '/advertise/',
        '/delivery-partner/',
        '/shipping-rates/',
        '/returns/',
        '/contact/',
        '/site-map/',
        '/accessibility/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated or request.method == 'OPTIONS':
            return self.get_response(request)

        path = request.path or '/'
        if self._is_public_path(path):
            return self.get_response(request)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'detail': 'Authentication required.'}, status=401)

        signin_url = reverse('signin')
        next_param = quote_plus(request.get_full_path() or '/')
        return redirect(f"{signin_url}?next={next_param}")

    def _is_public_path(self, path):
        if path in self.PUBLIC_EXACT_PATHS:
            return True
        return any(path.startswith(prefix) for prefix in self.PUBLIC_PREFIXES)
