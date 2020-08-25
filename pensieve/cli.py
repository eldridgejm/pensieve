import argparse
import datetime
import inspect
import pathlib
import os

import yaml

from . import exceptions, settings
from .clients import PensieveClient, GitHubClient


class command(object):
    def __init__(self, function):
        self.function = function
        self.requires = tuple(inspect.signature(function).parameters)
        self._setup = None

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def parser(self, setup):
        self._setup = setup
        return self

    @property
    def setup(self):
        if self._setup is None:
            return lambda x: x
        else:
            return self._setup


def cmd_new(args, config):
    if args.date:
        today = datetime.date.today()
        prefix = today.strftime(settings.DATE_FORMAT)
        args.repository_name = settings.HIGHLIGHT + prefix + settings.HIGHLIGHT + args.repository_name

    client = PensieveClient(
        "ssh://" + config["stores"][args.store]["host"],
        config["stores"][args.store]["path"],
        config["stores"][args.store]["agent"]
    )
    client.new(args.repository_name, args.cwd)

    print(f'New repository "{args.repository_name}" created on "{args.store}".')
    client.clone(args.repository_name, pathlib.Path.cwd())


def cmd_clone(args, config):
    host = config["stores"][args.store]["host"]
    path = config["stores"][args.store]["path"]
    agent = config["stores"][args.store]["agent"]

    client = PensieveClient(f"ssh://{host}", path, agent)
    try:
        client.clone(args.repository_name, args.cwd)
    except exceptions.ClientError as exc:
        print(str(exc))
    else:
        print('Cloned repository "foo".')


def cmd_list(args, config_file):
    for store in sorted(config_file['stores']):
        config = config_file['stores'][store]

        if config['type'] == 'pensieve':
            client = PensieveClient(f"ssh://{config['host']}", config["path"], config["agent"])
        elif config['type'] == 'github':
            client = GitHubClient(config['user'], config['token'])

        repos_on_store = client.list()
        for repo in sorted(repos_on_store):
            topics = ', '.join(repo.topics) if repo.topics else 'None'
            print(f'{repo.name} :: {store}')
            print(f'    description: {repo.description}')
            print(f'    topics: {topics}')


def main():
    parser = argparse.ArgumentParser()
    parser.set_defaults(cwd=pathlib.Path.cwd())
    subparsers = parser.add_subparsers()

    clone_parser = subparsers.add_parser("clone")
    clone_parser.add_argument('store')
    clone_parser.add_argument("repository_name")
    clone_parser.set_defaults(cmd=cmd_clone)

    new_parser = subparsers.add_parser("new")
    new_parser.add_argument("store")
    new_parser.add_argument("repository_name")
    new_parser.add_argument("--date", action="store_true")
    new_parser.set_defaults(cmd=cmd_new)

    list_parser = subparsers.add_parser('list')
    list_parser.set_defaults(cmd=cmd_list)

    args = parser.parse_args()

    with (pathlib.Path.cwd() / ".pensieve.yaml").open() as fileobj:
        config = yaml.load(fileobj, Loader=yaml.Loader)

    args.cmd(args, config)
