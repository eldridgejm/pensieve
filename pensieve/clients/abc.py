import abc


class ClientABC(abc.ABC):

    @abc.abstractmethod
    def clone(self, repo_name):
        ...
