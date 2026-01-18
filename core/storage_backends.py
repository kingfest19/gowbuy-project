from whitenoise.storage import CompressedManifestStaticFilesStorage, MissingFileError

class WhiteNoiseStaticFilesStorage(CompressedManifestStaticFilesStorage):
    manifest_strict = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manifest_strict = False

    def hashed_name(self, name, content=None, filename=None):
        try:
            return super().hashed_name(name, content, filename)
        except MissingFileError:
            return name
