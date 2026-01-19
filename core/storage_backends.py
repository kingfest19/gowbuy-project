from whitenoise.storage import CompressedManifestStaticFilesStorage, MissingFileError
import os

class WhiteNoiseStaticFilesStorage(CompressedManifestStaticFilesStorage):
    manifest_strict = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manifest_strict = False

    def hashed_name(self, name, content=None, filename=None):
        try:
            return super().hashed_name(name, content, filename)
        except (MissingFileError, ValueError):
            return name

    def _compress_path(self, path):
        if not os.path.exists(path):
            return []
        try:
            # Force list conversion to execute the generator and catch errors immediately
            return list(super()._compress_path(path))
        except FileNotFoundError:
            return []
