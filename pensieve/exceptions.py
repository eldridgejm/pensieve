class Error(Exception):
    """General client exception."""


class ClientError(Error):
    """A client returns an error."""


class CloneError(ClientError):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        s = 'Could not clone the repository "{}" from the server.'
        return s.format(self.name)
