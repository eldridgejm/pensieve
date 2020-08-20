import pathlib
import os

import yaml

from .clients import PensieveClient


def main():
    with (pathlib.Path.cwd() / '.pensieve.yaml').open() as fileobj:
        config = yaml.load(fileobj, Loader=yaml.Loader)

    port = config['stores']['home']['config']['port']

    client = PensieveClient(f'ssh://tester@0.0.0.0:{port}', '/home/tester/pensieve')
    print('Cloned repository "foo".')
    client.clone('foo', pathlib.Path.cwd())
