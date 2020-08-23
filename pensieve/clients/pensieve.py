import os
import json
import subprocess
import collections

from .abc import ClientABC
from .. import exceptions


AGENT_COMMAND = os.getenv("PENSIEVE_AGENT_COMMAND", "/home/tester/env/bin/_pensieve-agent")
CONNECTION_TIMEOUT = os.getenv("PENSIEVE_TIMEOUT", 5)
SSH_OPTIONS = os.getenv("PENSIEVE_SSH_OPTIONS", '')


class PensieveClient(ClientABC):
    def __init__(self, host, path):
        self.host = host
        self.path = path

    def _communicate_over_ssh(self, message, agent_command=AGENT_COMMAND):
        server, port = self.host.rsplit(':', 1)
        remote_command = "cd {} && {}".format(self.path, agent_command)
        ssh_command = [
            "ssh",
            "-o",
            "ConnectTimeout={}".format(CONNECTION_TIMEOUT),
            *SSH_OPTIONS.split(),
            '-p', port,
            server,
            'bash -c "{}"'.format(remote_command),
        ]

        message_string = json.dumps(message).encode()

        proc = subprocess.run(
            ssh_command,
            input=message_string,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        result = proc.stdout.decode().strip()
        result_err = proc.stderr.decode().strip()

        if proc.returncode:
            if "No such file" in result:
                err = 'The server has no pensieve "{}".'.format(self.path)
            else:
                err = "Connection failed with error: {}".format(result + result_err)
            raise exceptions.Error(err)

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            err = "Problem decoding when communicating JSON over SSH."
            err += "\nSent: {}".format(message_string)
            err += "\nReceived: {}".format(result)
            raise exceptions.Error(err)

    def _invoke(self, command, data=None):
        if data is None:
            data = {}

        message = {"command": command, "data": data}
        response = self._communicate_over_ssh(message)

        if response["error"]["code"]:
            raise exceptions.CommandError(response["error"]["msg"])

        return response["data"]

    def clone(self, repo_name, cwd):
        """Clone the remote repository into the cwd."""
        command = [
            "git",
            "clone",
            self.host + os.path.join(self.path, repo_name, "repo.git"),
            repo_name,
        ]
        proc = subprocess.run(
            command, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )

        if proc.returncode:
            raise exceptions.CloneError(repo_name)

    def new(self, repo_name):
        self._invoke('new', {'name': repo_name})

    def list(self):
        Repository = collections.namedtuple('Repository', 'name description tags')
        repositories = []
        for name, meta in self._invoke('list').items():
            repo = Repository(name, meta['description'], sorted(meta['tags']))
            repositories.append(repo)
        return repositories
