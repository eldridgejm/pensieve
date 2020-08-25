"""Client interacting with a store managed by pensieve-agent.

pensieve-agent is a command line tool that manages a collection of GitHub
repositories. It accepts its input as JSON via STDIN, and responds with JSON
via STDOUT. We typically communicate with an agent over SSH.

"""
import os
import json
import subprocess
import collections

from .abc import ClientABC, RepositoryMetadata
from .. import exceptions


# how long to wait until the SSH connection is considered dead.
CONNECTION_TIMEOUT = os.getenv("PENSIEVE_TIMEOUT", 5)

# options that should be used when creating an ssh connection
SSH_OPTIONS = os.getenv("PENSIEVE_SSH_OPTIONS", "")


class PensieveClient(ClientABC):
    """Interact with a store managed by pensieve-agent.

    Arguments
    ---------
    host : str
        A string of the form 'ssh://<username>@<hostname_or_ip>:port' describing
        the location of the store.
    path : str
        A string describing the location of the store on the filesystem of the
        remote machine.
    agent : str
        The path to the pensieve agent binary on the remote machine. If the 
        envvar PENSIEVE_AGENT_COMMAND is set, it will be used instead.

    """
    def __init__(self, host, path, agent):
        self.host = host
        self.path = path

        agent_envvar = os.getenv('PENSIEVE_AGENT_COMMAND')
        if agent_envvar is not None:
            self.agent = agent_envvar
        else:
            self.agent = agent

    def _communicate_json_over_ssh(self, message):
        """Send a JSON message over SSH."""
        server, port = self.host.rsplit(":", 1)
        remote_command = "cd {} && {}".format(self.path, self.agent)
        ssh_command = [
            "ssh",
            "-o",
            "ConnectTimeout={}".format(CONNECTION_TIMEOUT),
            *SSH_OPTIONS.split(),
            "-p",
            port,
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
        """Invoke a command on the remote server by sending and receiving JSON data."""
        if data is None:
            data = {}

        message = {"command": command, "data": data}
        response = self._communicate_json_over_ssh(message)

        if response["error"]["code"]:
            raise exceptions.ClientError(response["error"]["msg"])

        return response["data"]

    def clone(self, repo_name, cwd):
        """Clone the repository into the current working directory.

        Arguments
        ---------
        repo_name : str
            The name of the repository.
        cwd : pathlib.Path
            The path to the current working directory; the repo will be cloned to
            this directory.

        Raises
        ------
        ClientError
            If there is a problem while cloning.
        """
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
            raise exceptions.ClientError(
                f'Could not clone the repository "{repo_name}" from the server.'
            )

    def new(self, repo_name, cwd):
        """Create a new repository on the store.

        Arguments
        ---------
        repo_name : str
            The name of the repository.

        Raises
        ------
        ClientError
            If there is a problem while creating a new repository..

        """
        self._invoke("new", {"name": repo_name})

    def list(self):
        """List all of the repositories on the store.

        Returns
        -------
        List[RepositoryMetadata]
            A list of Repository objects, each with `.name`, `.description`,
            and `.topics` attributes.

        """
        repositories = []
        for name, meta in self._invoke("list").items():
            repo = RepositoryMetadata(name, meta["description"], sorted(meta["topics"]))
            repositories.append(repo)
        return repositories
