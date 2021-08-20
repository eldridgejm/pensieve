"""Client of a GitHub store.

This client uses the GitHub API to create, clone, and list repositories
associated with a user account. It requires an API token.

"""

import collections
import itertools
import requests
import subprocess

from .abc import ClientABC, RepositoryMetadata
from ..exceptions import ClientError


def _make_error_message(json):
    """Given a JSON response from the API, format a nice error message."""
    return json["message"] + " " + json["errors"][0]["message"]


def _extract_repo_info_from_json(json):
    """Given some JSON representing a repository, extract metadata.

    Returns
    -------
    RepositoryMetadata

    """
    return RepositoryMetadata(
        name=json["full_name"], description=json["description"], topics=json["topics"]
    )


class GitHubClient(ClientABC):
    """Client of a GitHub store.

    Arguments
    ---------
    user : str
        The user whose account will be accessed.
    token : str
        The API token used for authentication.

    """

    def __init__(self, user, token):
        self.user = user
        self.token = token

    def clone(self, full_name, cwd):
        """Clone the repository into the current working directory.

        Arguments
        ---------
        full_name : str
            The full name of the repository, in the form of <user_or_org>/<repo_name>.
        cwd : pathlib.Path
            The path to the current working directory; the repo will be cloned to
            this directory.

        Raises
        ------
        ClientError
            If there is a problem while cloning.
        """
        # if a full name is not provided, assume the user is self.user
        url = f"ssh://git@github.com/{full_name}"
        command = ["git", "clone", url]
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        if proc.returncode:
            raise ClientError(proc.stdout.decode())

    def _create_new_user_repository(self, repo_name, private):
        result = requests.post(
            "https://api.github.com/user/repos",
            auth=(self.user, self.token),
            json={"name": repo_name, "private": private},
        )
        if result.status_code != 201:
            raise ClientError(_make_error_message(result.json()))

    def _create_new_org_repository(self, org, repo_name, private):
        result = requests.post(
            f"https://api.github.com/orgs/{org}/repos",
            auth=(self.user, self.token),
            json={"name": repo_name, "private": private},
        )
        if result.status_code != 201:
            raise ClientError(_make_error_message(result.json()))

    def new(self, full_name, private=True):
        """Create a new repository on the store.

        Arguments
        ---------
        full_name : str
            The full name of the repository, in the form of <user_or_org>/<repo_name>.
        private : bool
            Whether the repo should be private or public. Default: True (private)

        Raises
        ------
        ClientError
            If there is a problem while creating a new repository..

        """
        user_or_org, repo_name = full_name.split("/")

        if user_or_org == self.user:
            self._create_new_user_repository(repo_name, private)
        else:
            self._create_new_org_repository(user_or_org, repo_name, private)

    def list(self):
        """List all of the repositories on the store.

        Returns
        -------
        List[RepositoryMetadata]
            A list of Repository objects, each with `.name`, `.description`,
            and `.topics` attributes.

        """
        repos = []

        def is_admin(r):
            return r["permissions"]["admin"]

        for page in itertools.count(1):
            # must have the right Accept header to get topics
            results = requests.get(
                f"https://api.github.com/user/repos",
                auth=(self.user, self.token),
                params={"per_page": 100, "page": page},
                headers={"Accept": "application/vnd.github.mercy-preview+json"},
            )
            if not results.json():
                break

            repos_on_page = [
                _extract_repo_info_from_json(r) for r in results.json() if is_admin(r)
            ]
            repos.extend(repos_on_page)

        return repos
