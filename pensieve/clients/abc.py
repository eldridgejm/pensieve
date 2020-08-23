import abc


class ClientABC(abc.ABC):

    @abc.abstractmethod
    def clone(self, repo_name, cwd):
        ...

    @abc.abstractmethod
    def new(self, repo_name):
        ...

    @abc.abstractmethod
    def list(self):
        ...
