"""Read a configuration from a .pensieve.yaml file."""

import yaml

from .clients import PensieveClient, GitHubClient
from .exceptions import Error


def _load_client_from_store_config(store, store_config):
    """Read a store config to create a client object.

    Arguments
    ---------
    store : str
        The name of the store. Used in error messages.
    store_config : dct
        The store definition section in the config file.

    Returns
    -------
    Client
        A client representing the store.

    Raises
    ------
    Error
        If there was a problem reading the config section.

    """
    invalid_store_msg = f'Invalid "{store}" definition in dotfile. '
    try:
        type_ = store_config['type']
    except KeyError:
        raise Error(invalid_store_msg + 'Missing a "type" key.')

    try:
        Client = {
            'github': GitHubClient,
            'pensieve': PensieveClient
        }[type_]
    except KeyError:
        raise Error(invalid_store_msg + f'Unknown client type {type_}.')

    # remove type; it isn't needed to create client
    del store_config['type']

    try:
        client = Client(**store_config)
    except Exception:
        raise Error(invalid_store_msg + f'Missing or unknown parameters.')

    return client


def load(fileobj):
    """Read a dotfile to create client objects.

    Arguments
    ---------
    fileobj
        A file-like object containing a YAML dotfile defining stores.

    Returns
    -------
    Dict[Client]
        A dictionary of clients by name.

    Raises
    ------
    Error
        If there was a problem reading the config file.

    """
    try:
        config = yaml.load(fileobj, Loader=yaml.Loader)
    except Exception:
        raise Error('Problem decoding the YAML dotfile.')

    clients = {}

    try:
        stores = config['stores']
    except KeyError:
        raise Error('Invalid dotfile. Missing "stores" key.')

    for store, store_config in stores.items():
        clients[store] = _load_client_from_store_config(store, store_config)

    return clients
