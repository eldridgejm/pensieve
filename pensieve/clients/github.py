import collections
import requests
import subprocess
import itertools

from .abc import ClientABC
from ..exceptions import ClientError


def _make_error_message(json):
    return json['message'] + ' ' + json['errors'][0]['message']


def _extract_repo_info_from_json(json):
    Repository = collections.namedtuple('Repository', 'name description topics')
    return Repository(
            name=json['name'],
            description=json['description'],
            topics=json['topics']
            )


class GitHubClient(ClientABC):

    def __init__(self, user, token):
        self.user = user
        self.token = token

    def clone(self, name, cwd):
        url = f'git@github.com/{self.user}/{name}'
        command = [
            "git",
            "clone",
            url
        ]
        proc = subprocess.run(
            command, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )

        if proc.returncode:
            raise ClientError(name)

    def new(self, name, private=True):
        result = requests.post(
                'https://api.github.com/user/repos', 
                auth=(self.user, self.token),
                json={
                    'name': name,
                    'private': private
                }
        )
        if result.status_code != 201:
            raise ClientError(_make_error_message(result.json()))

    def list(self):
        repos = []
        for page in itertools.count(1):
            # must have the right Accept header to get topics
            results = requests.get(
                    f'https://api.github.com/user/repos',
                    auth=(self.user, self.token),
                    params={'per_page': 100, 'page': page},
                    headers={'Accept': 'application/vnd.github.mercy-preview+json'}
                    )
            if not results.json():
                break

            repos_on_page = [_extract_repo_info_from_json(r) for r in results.json()]
            repos.extend(repos_on_page)

        return repos
