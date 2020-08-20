class Error(Exception):
    """General client exception."""


class CloneError(Error):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        s = 'Could not clone the repository "{}" from the server.'
        return s.format(self.name)


class CommandError(Error):
    """A command returns an error."""
