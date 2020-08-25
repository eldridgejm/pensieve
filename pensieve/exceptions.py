class Error(Exception):
    """General client exception."""


class ClientError(Error):
    """A client returns an error."""
