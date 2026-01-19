from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
import logging

logger = logging.getLogger(__name__)

class ForgivingManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """
    A custom storage backend that extends Django's ManifestStaticFilesStorage
    but disables strict mode and handles missing files gracefully.
    """
    manifest_strict = False

    def hashed_name(self, name, content=None, filename=None):
        try:
            return super().hashed_name(name, content, filename)
        except ValueError:
            # Log the missing file and return the original name to prevent build failure
            logger.warning(f"Missing file during collectstatic: {name}")
            return name
