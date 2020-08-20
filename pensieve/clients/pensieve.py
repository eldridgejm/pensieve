import os
import subprocess

from .abc import ClientABC
from .. import exceptions


class PensieveClient(ClientABC):

    def __init__(self, host, path):
        self.host = host
        self.path = path

    def clone(self, repo_name, cwd):
        """Clone the remote repository into the cwd."""
        command = ['git', 'clone', self.host + '/' + os.path.join(self.path, repo_name, 'repo.git'), repo_name]
        proc = subprocess.run(
                command, 
                cwd=str(cwd), 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                )

        if proc.returncode:
            raise Exception(proc.stdout)
            raise exceptions.CloneError(repo_name)
