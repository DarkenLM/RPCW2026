class RDFRef:
    def __init__(self, prefix: str, uri: str):
        self.prefix = prefix
        self.uri = uri
        self.short = ":" + uri.replace(prefix, "")
