"""Command line interface."""

import argparse
import datetime
import inspect
import os
import pathlib
import sys
import textwrap

import yaml

from . import exceptions, settings, dotfile


def colorizer(wrapped):
    """Decorator to return unformatted message if PENSIEVE_COLOR is set."""

    def wrapper(message):
        if os.getenv('PENSIEVE_COLOR', 'yes') == 'no':
            return message

        return wrapped(message)

    return wrapper


_RESET =  '\u001b[0m'


@colorizer
def faded(message):
    return '\u001b[30;1m' + message + _RESET

@colorizer
def info(message):
    return '\u001b[35m' + message + _RESET

@colorizer
def info_heading(message):
    return '\u001b[34m' + message + _RESET

@colorizer
def highlight(message):
    return '\u001b[37;1m' + message + _RESET


@colorizer
def bad(message):
    return '\u001b[31m' + message + _RESET


@colorizer
def good(message):
    return  '\u001b[32m' + message + _RESET


def fatal_error(msg, code=1):
    print(bad(msg), file=sys.stdout)
    sys.exit(code)


def valid_store(clients):
    """Creates a function which checks an argparse argument against valid stores."""
    def checker(value):
        if value not in clients:
            raise argparse.ArgumentTypeError(f'{value} not a valid store.')
        else:
            return clients[value]
    return checker


def configure_new_parser(subparsers, clients):
    new_parser = subparsers.add_parser("new")
    new_parser.add_argument("store", type=valid_store(clients))
    new_parser.add_argument("repository_name")
    new_parser.add_argument("--date", action="store_true")
    new_parser.set_defaults(cmd=cmd_new)


def cmd_new(args):
    if args.date:
        today = datetime.date.today()
        prefix = today.strftime(settings.DATE_FORMAT)
        args.repository_name = (
            settings.HIGHLIGHT + prefix + settings.HIGHLIGHT + args.repository_name
        )

    args.store.new(args.repository_name)

    print(f'New repository "{args.repository_name}" created.')
    args.store.clone(args.repository_name, pathlib.Path.cwd())


def configure_clone_parser(subparsers, clients):
    clone_parser = subparsers.add_parser("clone")
    clone_parser.add_argument("store", type=valid_store(clients))
    clone_parser.add_argument("repository_name")
    clone_parser.set_defaults(cmd=cmd_clone)


def cmd_clone(args):
    try:
        args.store.clone(args.repository_name, args.cwd)
    except exceptions.ClientError as exc:
        fatal_error(str(exc))
    else:
        print(good(f'Cloned repository "{args.repository_name}".'))


def configure_list_parser(subparsers, clients):
    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(cmd=cmd_list)


def _format_meta(msg, level=0, spacer='    '):
    """Indent the first line once, the remaining lines twice."""
    lines = textwrap.wrap(msg, 80)
    msg = spacer * level + lines[0]
    if len(lines) > 1:
        msg += '\n' + textwrap.indent('\n'.join(lines[1:]), prefix=spacer * (level + 1))
    return msg


def cmd_list(args):
    for store in sorted(args.clients):
        client = args.clients[store]

        repos_on_store = client.list()
        for repo in sorted(repos_on_store):
            topics = ", ".join(repo.topics)
            print(highlight(repo.name) + faded(f' :: {store}'))

            if repo.description is not None:
                print(_format_meta(f"{info_heading('description')}: {info(repo.description)}", level=1))

            if topics:
                print(_format_meta(f"{info_heading('topics')}: {info(topics)}", level=1))


def main():
    try:
        with (pathlib.Path.cwd() / settings.DOTFILE).open() as fileobj:
            clients = dotfile.load(fileobj)
    except exceptions.Error as exc:
        fatal_error('Error: ' + str(exc))
    except FileNotFoundError:
        fatal_error('Pensieve dotfile not found. Is this a pensieve?')

    parser = argparse.ArgumentParser()
    parser.set_defaults(cwd=pathlib.Path.cwd(), clients=clients)
    subparsers = parser.add_subparsers()

    configure_clone_parser(subparsers, clients)
    configure_list_parser(subparsers, clients)
    configure_new_parser(subparsers, clients)

    args = parser.parse_args()

    if 'cmd' not in args:
        parser.print_usage()
        sys.exit(0)

    try:
        args.cmd(args)
    except exceptions.Error as exc:
        fatal_error('Error: ' + str(exc))
