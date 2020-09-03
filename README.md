pensieve
========

A tool to manage your git repositories.

Pensieve can create, clone, and search git repositories, whether they are hosted
on GitHub or on a remote server running pensieve-agent.


Configuration
-------------

In a new directory, create a file named `.pensieve.yaml`. The file should have
one top-level key: `stores`. Under this key, name each place that your git
repositories are kept. Each store must be one of two types: a "github" store or
a "pensieve" store. The general structure of the file is shown below:

    stores:
        github:
            type: github
            user: eldridgejm
            token: ba3c9001fa1... # your GitHub private token
        home:
            type: pensieve
            host: eldridge@home:22 # user@hostname:port
            path: /mnt/dc/pensieve # where the git repositories are stored
            agent: _pensieve-agent # the pensieve agent command that will be run over ssh

Usage
-----

Several of the pensieve subcommands require a repository locator. A locator has
the following form:

    <store_name>:<full_repository_name>

If the store is a GitHub store, the full repository name can include a user or
organization name. For instance:

    github:eldridgejm/pensieve

If the user/org name is omitted, it is inferred to be the username associated
with the store found in `.pensieve.yaml`. Therefore, the below refers to the
same repository as the above:

    github:pensieve

There are several subcommands:

- `pensieve new <locator>`: Create and clone a new repository.
- `pensieve clone [locator]`: Clone a repository. If the locator is omitted and
  `fzf` is installed, it will be opened to allow for selecting the repository
  interactively.
- `pensieve list [--topic [TOPIC]] [--show-archived]`: List the repositories on
  every store. By default, repositories labeled with an "archived" topic are not
  shown. Only those repositories which have a specific topic can be show with
  `--topic`.
- `pensieve cached {stores,topics,names}`: Returns information about
  repositories from the known cache.


The Cache
---------

Whenever `pensieve list` is invoked, all information about the repositories
discovered is stored in `.cache.json` in the same directory as `.pensieve.yaml`.
This cache is used to provide autocompletion. If the cache is found to be
out-of-date, running `pensieve list` will update it.
