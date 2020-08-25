import io
import textwrap

import pensieve.dotfile
import pensieve.clients
import pensieve.exceptions

import pytest


EXAMPLE = textwrap.dedent(
    f"""
    stores:
        home:
            type: pensieve
            host: tester@0.0.0.0:1234
            path: /home/tester/pensieve
            agent: /home/tester/env/bin/_pensieve-agent
        github:
            type: github
            user: pensieve-test-user
            token: abcdef
    """
)


def test_load_returns_clients():
    # given
    fileobj = io.StringIO(EXAMPLE)

    # when
    clients = pensieve.dotfile.load(fileobj)

    # then
    assert isinstance(clients["home"], pensieve.clients.PensieveClient)
    assert isinstance(clients["github"], pensieve.clients.GitHubClient)

    assert clients["home"].host == "ssh://tester@0.0.0.0:1234"
    assert clients["home"].path == "/home/tester/pensieve"
    assert clients["home"].agent == "/home/tester/env/bin/_pensieve-agent"

    assert clients["github"].user == "pensieve-test-user"
    assert clients["github"].token == "abcdef"


def test_load_raises_if_missing_attribute():
    # given - missing "agent" in home
    bad_example = textwrap.dedent(
        f"""
        stores:
            home:
                type: pensieve
                host: tester@0.0.0.0:1234
                path: /home/tester/pensieve
            github:
                type: github
                user: pensieve-test-user
                token: abcdef
        """
    )

    # when then
    fileobj = io.StringIO(bad_example)

    with pytest.raises(pensieve.exceptions.Error):
        pensieve.dotfile.load(fileobj)
