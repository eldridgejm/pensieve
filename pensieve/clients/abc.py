"""The abstract base class defining the Client interface.

A client interacts with a store and performs all of the basic operations,
including: cloning repos, creating new repos, listing all of the repos, etc.

"""


import abc


class ClientABC(abc.ABC):
    @abc.abstractmethod
    def clone(self, repo_name, cwd):
        """Clone the repository into the current working directory.

        Arguments
        ---------
        repo_name : str
            The name of the repository.
        cwd : pathlib.Path
            The path to the current working directory; the repo will be cloned to
            this directory.

        Raises
        ------
        ClientError
            If there is a problem while cloning.
        """

    @abc.abstractmethod
    def new(self, repo_name):
        """Create a new repository on the store.

        Arguments
        ---------
        repo_name : str
            The name of the repository.

        Raises
        ------
        ClientError
            If there is a problem while creating a new repository..

        """

    @abc.abstractmethod
    def list(self):
        """List all of the repositories on the store.

        Returns
        -------
        List[Repository]
            A list of Repository objects, each with `.name`, `.description`,
            and `.topics` attributes.

        """
