import argparse
import datetime
import inspect
import pathlib
import os

import yaml

from . import exceptions
from .clients import PensieveClient


DATE_FORMAT = "%Y-%m-%d"
HIGHLIGHT = "__"


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
        prefix = today.strftime(DATE_FORMAT)
        args.repository_name = HIGHLIGHT + prefix + HIGHLIGHT + args.repository_name

    client = PensieveClient(
        "ssh://" + config["stores"][args.store]["config"]["host"],
        config["stores"][args.store]["config"]["path"],
    )
    client.new(args.repository_name)

    print(f'New repository "{args.repository_name}" created on "{args.store}".')
    client.clone(args.repository_name, pathlib.Path.cwd())


def cmd_clone(args, config):
    host = config["stores"][args.store]["config"]["host"]
    path = config["stores"][args.store]["config"]["path"]

    client = PensieveClient(f"ssh://{host}", path)
    try:
        client.clone(args.repository_name, pathlib.Path.cwd())
    except exceptions.CloneError as exc:
        print(str(exc))
    else:
        print('Cloned repository "foo".')


def main():

    parser = argparse.ArgumentParser()
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

    args = parser.parse_args()

    with (pathlib.Path.cwd() / ".pensieve.yaml").open() as fileobj:
        config = yaml.load(fileobj, Loader=yaml.Loader)

    args.cmd(args, config)
