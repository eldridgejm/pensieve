"""Command line interface."""

import argparse
import collections
import inspect
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import textwrap

import yaml

from . import exceptions, settings, dotfile
from .clients import GitHubClient


HAS_FZF = bool(shutil.which('fzf'))


try:
    _, COLUMNS = os.popen("stty size", "r").read().split()
    COLUMNS = int(COLUMNS)
except ValueError:
    COLUMNS = 120


CACHE_FILENAME = ".cache.json"


def colorizer(wrapped):
    """Decorator to return unformatted message if PENSIEVE_COLOR is set."""

    def wrapper(message):
        if os.getenv("PENSIEVE_COLOR", "yes") == "no":
            return message

        return wrapped(message)

    return wrapper


_RESET = "\u001b[0m"


@colorizer
def faded(message):
    return "\u001b[30;1m" + message + _RESET


@colorizer
def info(message):
    return "\u001b[35m" + message + _RESET


@colorizer
def info_heading(message):
    return "\u001b[34m" + message + _RESET


@colorizer
def highlight(message):
    return "\u001b[37;1m" + message + _RESET


@colorizer
def bad(message):
    return "\u001b[31m" + message + _RESET


@colorizer
def good(message):
    return "\u001b[32m" + message + _RESET


def fatal_error(msg, code=1):
    print(bad(msg), file=sys.stdout)
    sys.exit(code)


def parse_repository_locator(locator_string, clients):
    try:
        store, rest = locator_string.split(":")
    except Exception:
        raise ValueError("Must include store name.")

    if store not in clients:
        raise ValueError(f"{store} not a valid store.")
    else:
        client = clients[store]

    if "/" in rest:
        parts = rest.split("/")
        user_or_org_prefix = parts[0] + "/"
        repo_name = parts[1]
    else:
        user_or_org_prefix = ""
        repo_name = rest

    if isinstance(client, GitHubClient) and not user_or_org_prefix:
        user_or_org_prefix = client.user + "/"

    full_name = user_or_org_prefix + repo_name

    Location = collections.namedtuple(
        "RepoPath",
        ["store_name", "client", "user_or_org_prefix", "repo_name", "full_name"],
    )
    return Location(store, client, user_or_org_prefix, repo_name, full_name)


def RepositoryLocator(clients):
    """Creates an argument checker for a repository locator string.

    A repo locator string looks like this:
        store:user_or_org_prefix/repo_name
    or
        store:repo_name
    when the user_or_org_prefix is irrelevant or can be inferred.
    """

    def checker(value):
        try:
            return parse_repository_locator(value, clients)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(str(exc))

    return checker


def configure_new_parser(subparsers, clients):
    new_parser = subparsers.add_parser("new")
    help_msg = """
        Repository locator. Format: <store_name>:<full_repo_name>.
        In the case of a GitHub store, "full_repo_name" can either be a full
        repository path, like eldridgejm/pensieve, or simply a repository name,
        like pensieve. In the latter case, the new repository is assumed to be a
        user repository under the authenticated user's account.
    """
    new_parser.add_argument("locator", type=RepositoryLocator(clients), help=help_msg)
    new_parser.set_defaults(cmd=cmd_new)


def cmd_new(args):
    # we must construct the repository's "full name". If the store is a GitHub
    # store, this means including the username or organization as a prefix. The
    # user may omit this information, in which case it is assumed that the repo
    # will be a user repository instead of an organization repo, and the user is
    # inferred to be the authenticated user used to configure the store.
    args.locator.client.new(args.locator.full_name)

    print(f'New repository "{args.locator.store_name}:{args.locator.full_name}" created.')
    args.locator.client.clone(args.locator.full_name, pathlib.Path.cwd())


def configure_clone_parser(subparsers, clients):
    if HAS_FZF:
        nargs = '?'
    else:
        nargs = 1

    clone_parser = subparsers.add_parser("clone")
    clone_parser.add_argument(
        "locator",
        type=RepositoryLocator(clients),
        help="The store to clone from.",
        nargs=nargs
    )
    help_msg = """
        Repository locator. Format: <store_name>:<full_repo_name>.
        In the case of a GitHub store, "full_repo_name" can either be a full
        repository path, like eldridgejm/pensieve, or simply a repository name,
        like pensieve. In the latter case, the new repository is assumed to be a
        user repository under the authenticated user's account.
    """
    clone_parser.set_defaults(cmd=cmd_clone)


def _fzf_select_repo():
    cache = _read_cache()
    names = _cached_names(cache)

    result = subprocess.run('fzf', input='\n'.join(names).encode(), stdout=subprocess.PIPE)
    return result.stdout.decode().strip()


def cmd_clone(args):
    if args.locator is None:
        selection = _fzf_select_repo()
        args.locator = parse_repository_locator(selection, args.clients)

    try:
        args.locator.client.clone(args.locator.full_name, args.cwd)
    except exceptions.ClientError as exc:
        fatal_error(str(exc))
    else:
        print(good(f'Cloned repository "{args.locator.store_name}:{args.locator.full_name}".'))


def configure_list_parser(subparsers, clients):
    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(cmd=cmd_list)


def _format_meta(msg, level=0, spacer="    "):
    """Indent the first line once, the remaining lines twice."""
    lines = textwrap.wrap(msg, COLUMNS)
    msg = spacer * level + lines[0]
    if len(lines) > 1:
        msg += "\n" + textwrap.indent("\n".join(lines[1:]), prefix=spacer * (level + 1))
    return msg


def _update_cache(store, repos_on_store):
    """Update the cache file with information about the repos on the store.

    Creates a JSON file named `CACHE_FILENAME` in the pensieve directory. The
    file is a JSON dict whose keys are the store names. The value is a list
    of dictionaries, one for each repo, each dictionary containing attributes
    `name`, `topics`, and `description`.

    """
    cache_path = pathlib.Path.cwd() / CACHE_FILENAME

    try:
        with cache_path.open() as fileobj:
            cache = json.load(fileobj)
    except FileNotFoundError:
        cache = {}

    cache[store] = [r._asdict() for r in repos_on_store]

    with cache_path.open("w") as fileobj:
        json.dump(cache, fileobj)


def cmd_list(args):
    for store in sorted(args.clients):
        client = args.clients[store]

        repos_on_store = client.list()
        _update_cache(store, repos_on_store)

        for repo in sorted(repos_on_store):
            topics = ", ".join(repo.topics)
            print(highlight(repo.name) + faded(f" :: {store}"))

            if repo.description is not None:
                print(
                    _format_meta(
                        f"{info_heading('description')}: {info(repo.description)}",
                        level=1,
                    )
                )

            if topics:
                print(
                    _format_meta(f"{info_heading('topics')}: {info(topics)}", level=1)
                )


def configure_cached_parser(subparsers, clients):
    cached_parser = subparsers.add_parser("cached")
    cached_parser.add_argument("what", choices={"stores", "topics", "names"})
    cached_parser.set_defaults(cmd=cmd_cached)


def _read_cache():
    cache_path = pathlib.Path.cwd() / CACHE_FILENAME

    try:
        with cache_path.open() as fileobj:
            cache = json.load(fileobj)
    except FileNotFoundError:
        cache = {}

    return cache


def _cached_topics(cache):
    """Extract the set of topics from the cache."""
    topics = set()
    for store, repos in cache.items():
        for repo in repos:
            topics.update(repo["topics"])
    return topics


def _cached_names(cache):
    """
    Extract all repo names from the cache.

    Format: <store_name>:<full_repo_name>, so that the repo can be cloned by
    writing pensieve clone <store_name> <full_repo_name>.
    """
    names = []
    for store, repos in cache.items():
        for repo in repos:
            name = store + ":" + repo["name"]
            names.append(name)
    return names


def cmd_cached(args):
    """Print info from the cache for usage in other scripts."""
    cache = _read_cache()
    if args.what == "stores":
        print("\n".join(cache.keys()))
    elif args.what == "topics":
        topics = _cached_topics(cache)
        print("\n".join(topics))
    elif args.what == "names":
        names = _cached_names(cache)
        print("\n".join(names))

    sys.exit()


def main():
    try:
        with (pathlib.Path.cwd() / settings.DOTFILE).open() as fileobj:
            clients = dotfile.load(fileobj)
    except exceptions.Error as exc:
        fatal_error("Error: " + str(exc))
    except FileNotFoundError:
        fatal_error("Pensieve dotfile not found. Is this a pensieve?")

    parser = argparse.ArgumentParser()
    parser.set_defaults(cwd=pathlib.Path.cwd(), clients=clients)
    subparsers = parser.add_subparsers()

    configure_clone_parser(subparsers, clients)
    configure_list_parser(subparsers, clients)
    configure_new_parser(subparsers, clients)
    configure_cached_parser(subparsers, clients)

    args = parser.parse_args()

    if "cmd" not in args:
        parser.print_usage()
        sys.exit(0)

    try:
        args.cmd(args)
    except exceptions.Error as exc:
        fatal_error("Error: " + str(exc))
