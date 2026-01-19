from django.contrib.staticfiles.storage import ManifestStaticFilesStorage

class ForgivingManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """
    A custom storage backend that extends Django's ManifestStaticFilesStorage
    but disables strict mode. This prevents the build from failing if a 
    CSS file references a missing asset (like a .map file).
    """
    manifest_strict = False
