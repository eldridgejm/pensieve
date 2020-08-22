import datetime
import subprocess
import pathlib
import json
import tempfile
import os
import textwrap

from behave import fixture, use_fixture
import yaml


DOCKER_DIRECTORY = pathlib.Path(__file__).parent / "../../docker"


def process_name_list(names):
    """Process a string like "foo, bar, baz" into a list of strings."""
    return [n.strip().strip('"') for n in names.split(",")]


class Client:
    def __init__(self, path):
        self.path = path

    def run(self, cmd, check=True):
        return subprocess.run(cmd, capture_output=True, check=check, cwd=self.path)


@fixture
def client_fixture(context):
    tempdir = tempfile.TemporaryDirectory(suffix="pensieve-test-client")
    temp_path = pathlib.Path(tempdir.name) / "pensieve"
    temp_path.mkdir()

    config_yaml = textwrap.dedent(
        f"""
    stores:
        home:
            type: pensieve
            config:
                host: tester@0.0.0.0:{context.server.port}
                path: /home/tester/pensieve
        github:
            type: github
            config:
                user: pensieve-test-user
    """
    )

    with (temp_path / ".pensieve.yaml").open("w") as fileobj:
        fileobj.write(config_yaml)

    # set up the client's GIT SSH settings so that no password is required
    os.environ["GIT_SSH_COMMAND"] = (
        f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
        f"-i {DOCKER_DIRECTORY}/id_rsa"
    )

    os.environ["PENSIEVE_SSH_OPTIONS"] = (
        f"-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
        f"-i {DOCKER_DIRECTORY}/id_rsa"
    )

    yield Client(temp_path)


class PensieveServer:
    def __init__(self, path, container_id, host, port):
        # path to the server's temporary pensieve
        self.path = path

        self.host = host
        self.port = port
        self.container_id = container_id

    def run(self, cmd, check=True):
        ssh_cmd = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            f"tester@{self.host}",
            "-p",
            self.port,
            "-i",
            str(DOCKER_DIRECTORY / "id_rsa"),
            cmd,
        ]
        return subprocess.run(ssh_cmd, capture_output=True, check=check)


@fixture
def pensieve_server_fixture(context):
    """Start the server containing the agent using docker."""
    # build the docker image, if it hasn't already been built
    # name it 'pensieve-test-server'
    subprocess.run(
        ["docker", "build", ".", "-t", "pensieve-test-server"],
        cwd=pathlib.Path(__file__).parent / "../../docker",
        check=True,
        capture_output=True,
    )

    # create a temporary directory for the pensieve
    tempdir = tempfile.TemporaryDirectory(suffix="pensieve-test-pensieve-server")
    temp_path = pathlib.Path(tempdir.name) / "pensieve"
    temp_path.mkdir()

    # create and run the container
    result = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "-P",
            "--mount",
            f"type=bind,source={temp_path},dst=/home/tester/pensieve",
            "pensieve-test-server",
        ],
        capture_output=True,
        check=True,
    )

    # the container ID is returned
    container_id = result.stdout.decode().strip()

    # but we also want the port
    result = subprocess.run(
        ["docker", "port", container_id, "22"], capture_output=True, check=True
    )

    # the port is displayed in the form 0.0.0.0:port
    host, port = result.stdout.decode().strip().split(":")

    yield PensieveServer(temp_path, container_id, host, port)

    # kill the container
    subprocess.run(["docker", "kill", container_id])



# pylint: disable=function-redefined,undefined-variable
@given("the home store has repos {names}.")
def step_impl(context, names):
    context.server = use_fixture(pensieve_server_fixture, context)
    names = process_name_list(names)
    cmd = "./initialize_repositories.sh " + " ".join(names)
    context.server.run(cmd)


@given("the home store has repos {names} with metadata")
def step_impl(context, names):
    step = f'Given the home store has repos {names}.'
    context.execute_steps(step)

    # read the metadata
    meta = json.loads(context.text.strip())

    for name in process_name_list(names):
        with (context.server.path / name / 'meta.json').open('w') as fileobj:
            json.dump(meta, fileobj)


@when("the user invokes")
def step_impl(context):
    context.client = use_fixture(client_fixture, context)
    command = context.text.strip()
    context.proc = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(context.client.path),
    )


@then("the output is")
def step_impl(context):
    output = context.proc.stdout.decode()
    assert context.text == output, (context.text, output)


@then('the repository "{name}" exists on the {where}.')
def step_impl(context, name, where):
    inst = {"client": context.client, "home store": context.server}[where]

    msg = f'The repo "{name}" does not exist on the {where}.'
    entries = [f.name for f in inst.path.iterdir() if f.is_dir()]
    if entries:
        msg += "The repositories that *do* exist are:\n" + "\n".join(entries)
    assert (inst.path / name).is_dir(), msg


@then('the repository "{name}" with prepended date exists on the {where}.')
def step_impl(context, name, where):
    today = datetime.date.today()
    prefix = today.strftime("%Y-%m-%d")
    name = "__" + prefix + "__" + name
    step = 'then the repository "{}" exists on the {}.'.format(name, where)
    context.execute_steps(step)
