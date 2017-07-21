# -*- coding: utf-8 -*-

"""
sceptre.cli

This module implements Sceptre's CLI, and should not be directly imported.
"""

import contextlib
from json import JSONEncoder
import os
import logging
from logging import Formatter
import sys
from uuid import uuid1
from functools import wraps

import click
import colorama
import yaml
from boto3.exceptions import Boto3Error
from botocore.exceptions import BotoCoreError, ClientError
from jinja2.exceptions import TemplateError

from .environment import Environment
from .exceptions import SceptreException, StackDoesNotExistError
from .stack_status import StackStatus, StackChangeSetStatus
from .stack_status_colourer import StackStatusColourer
from . import __version__


def catch_exceptions(func):
    """
    Catches and simplifies expected errors thrown by sceptre.

    catch_exceptions should be used as a decorator.

    :param func: The function which may throw exceptions which should be
        simplified.
    :type func: func
    :returns: The decorated function.
    :rtype: func
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        """
        Invokes ``func``, catches expected errors, prints the error message and
        exits sceptre with a non-zero exit code.
        """
        try:
            return func(*args, **kwargs)
        except (SceptreException, BotoCoreError, ClientError, Boto3Error,
                TemplateError) as error:
            write(error)
            sys.exit(1)

    return decorated


@click.group()
@click.version_option(version=__version__, prog_name="Sceptre")
@click.option("--debug", is_flag=True, help="Turn on debug logging.")
@click.option("--dir", "directory", help="Specify sceptre directory.")
@click.option(
    "--output", type=click.Choice(["yaml", "json"]), default="yaml",
    help="The formatting style for command output.")
@click.option("--no-colour", is_flag=True, help="Turn off output colouring.")
@click.option(
    "--var", multiple=True, help="A variable to template into config files.")
@click.option(
    "--var-file", type=click.File("rb"),
    help="A YAML file of variables to template into config files.")
@click.pass_context
def cli(
        ctx, debug, directory, no_colour, output, var, var_file
):  # pragma: no cover
    """
    Implements sceptre's CLI.
    """
    setup_logging(debug, no_colour)
    colorama.init()
    ctx.obj = {
        "options": {},
        "output_format": output,
        "sceptre_dir": directory if directory else os.getcwd()
    }
    user_variables = {}
    if var_file:
        user_variables.update(yaml.safe_load(var_file.read()))
    if var:
        # --var options overwrite --var-file options
        for variable in var:
            variable_key, variable_value = variable.split("=")
            user_variables.update({variable_key: variable_value})
    if user_variables:
        ctx.obj["options"]["user_variables"] = user_variables


@cli.command(name="validate-template")
@click.argument("path")
@click.pass_context
@catch_exceptions
def validate_template(ctx, path):
    """
    Validates a template.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    result = stack.validate_template()
    write(result, ctx.obj["output_format"])


@cli.command(name="generate-template")
@click.argument("path")
@click.pass_context
@catch_exceptions
def generate_template(ctx, path):
    """
    Generates and isplays a template.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    template_output = stack.template.body
    write(template_output)


@cli.command(name="lock")
@click.argument("path")
@click.pass_context
@catch_exceptions
def lock(ctx, path):
    """
    Locks a stack to prevents updates.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    stack.lock()


@cli.command(name="unlock")
@click.argument("path")
@click.pass_context
@catch_exceptions
def unlock(ctx, path):
    """
    Unlocks a stack to allow updates.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    stack.unlock()


@cli.command(name="describe-resources")
@click.argument("path")
@click.option(
    "--recursive", "-r", is_flag=True,
    help="Recursively apply operation to all stacks."
)
@click.pass_context
@catch_exceptions
def describe_resources(ctx, path, recursive):
    """
    Describes a stack or environment's resources.
    """
    if recursive:
        env = _get_env(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
        response = env.describe_resources()
    else:
        stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
        response = stack.describe_resources()
    write(response, ctx.obj["output_format"])


@cli.command(name="create")
@click.argument("path")
@click.pass_context
@catch_exceptions
def create(ctx, path):
    """
    Creates a stack.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    response = stack.create()
    if response != StackStatus.COMPLETE:
        exit(1)


@cli.command(name="delete")
@click.argument("path")
@click.option(
    "--recursive", "-r", is_flag=True,
    help="Recursively apply operation to all stacks."
)
@click.pass_context
@catch_exceptions
def delete(ctx, path, recursive):
    """
    Deletes a stack.
    """
    if recursive:
        env = _get_env(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
        response = env.delete()
        if not all(
                status == StackStatus.COMPLETE for status in response.values()
        ):
            exit(1)
    else:
        stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
        response = stack.delete()
        if response != StackStatus.COMPLETE:
            exit(1)


@cli.command(name="update")
@click.argument("path")
@click.pass_context
@catch_exceptions
def update(ctx, path):
    """
    Updates a stack.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    response = stack.update()
    if response != StackStatus.COMPLETE:
        exit(1)


@cli.command(name="launch")
@click.argument("path")
@click.option(
    "--recursive", "-r", is_flag=True,
    help="Recursively apply operation to all stacks."
)
@click.pass_context
@catch_exceptions
def launch(ctx, path, recursive):
    """
    Creates or updates a stack or environment.

    Launch attempts to create a stack. If the stack is in a CREATE_FAILED,
    the failed stack is deleted before being created. If the stack aleady
    exists, it is updated.
    """
    if recursive:
        env = _get_env(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
        response = env.launch()
        if not all(
                status == StackStatus.COMPLETE for status in response.values()
        ):
            exit(1)
    else:
        stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
        response = stack.launch()
        if response != StackStatus.COMPLETE:
            exit(1)


@cli.command(name="continue-update-rollback")
@click.argument("path")
@click.pass_context
@catch_exceptions
def continue_update_rollback(ctx, path):
    """
    Rolls a stack back to a working state.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    stack.continue_update_rollback()


@cli.command(name="create-change-set")
@click.argument("path")
@click.argument("change_set_name")
@click.pass_context
@catch_exceptions
def create_change_set(ctx, path, change_set_name):
    """
    Creates a change set.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    stack.create_change_set(change_set_name)


@cli.command(name="delete-change-set")
@click.argument("path")
@click.argument("change_set_name")
@click.pass_context
@catch_exceptions
def delete_change_set(ctx, path, change_set_name):
    """
    Deletes a change set.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    stack.delete_change_set(change_set_name)


@cli.command(name="describe-change-set")
@click.argument("path")
@click.argument("change_set_name")
@click.option("--verbose", is_flag=True)
@click.pass_context
@catch_exceptions
def describe_change_set(ctx, path, change_set_name, verbose):
    """
    Describes a change set.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    description = stack.describe_change_set(change_set_name)
    if not verbose:
        description = _simplify_change_set_description(description)
    write(description, ctx.obj["output_format"])


def _simplify_change_set_description(response):
    desired_response_items = [
        "ChangeSetName",
        "CreationTime",
        "ExecutionStatus",
        "StackName",
        "Status",
        "StatusReason"
    ]
    desired_resource_changes = [
        "Action",
        "LogicalResourceId",
        "PhysicalResourceId",
        "Replacement",
        "ResourceType",
        "Scope"
    ]
    formatted_response = {
        k: v
        for k, v in response.items()
        if k in desired_response_items
    }
    formatted_response["Changes"] = [
        {
            "ResourceChange": {
                k: v
                for k, v in change["ResourceChange"].items()
                if k in desired_resource_changes
            }
        }
        for change in response["Changes"]
    ]
    return formatted_response


@cli.command(name="execute-change-set")
@click.argument("path")
@click.argument("change_set_name")
@click.pass_context
@catch_exceptions
def execute_change_set(ctx, path, change_set_name):
    """
    Executes a change set.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    stack.execute_change_set(change_set_name)


@cli.command(name="list-change-sets")
@click.argument("path")
@click.pass_context
@catch_exceptions
def list_change_sets(ctx, path):
    """
    Lists a stack's change sets.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    response = stack.list_change_sets()
    formatted_response = {
        k: v
        for k, v in response.items()
        if k != "ResponseMetadata"
    }
    write(formatted_response, ctx.obj["output_format"])


@cli.command(name="update-cs")
@click.argument("path")
@click.option("--verbose", is_flag=True)
@click.pass_context
@catch_exceptions
def update_cs(ctx, path, verbose):
    """
    Updates the stack using a change set.

    Creates a new change set, prints out the description of the changes,
    asks the user whether to execute or delete the change set.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    change_set_name = "-".join(["change-set", uuid1().hex])
    with change_set(stack, change_set_name):
        status = stack.wait_for_cs_completion(change_set_name)
        description = stack.describe_change_set(change_set_name)
        if not verbose:
            description = _simplify_change_set_description(description)
        write(description, ctx.obj["output_format"])
        if status != StackChangeSetStatus.READY:
            exit(1)
        if click.confirm("Proceed with stack update?"):
            stack.execute_change_set(change_set_name)


@contextlib.contextmanager
def change_set(stack, name):
    """
    Creates and yields and deletes a change set.

    :param stack: The stack to create the change set for.
    :type stack: sceptre.stack.Stack
    :param name: The name of the change set.
    :type name: str
    """
    stack.create_change_set(name)
    try:
        yield
    finally:
        stack.delete_change_set(name)


@cli.command(name="describe-outputs")
@click.argument("path")
@click.option("--export", type=click.Choice(["envvar"]))
@click.pass_context
@catch_exceptions
def describe_outputs(ctx, path, export):
    """
    Describes a stack's outputs.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    response = stack.describe_outputs()

    if export == "envvar":
        write("\n".join(
            [
                "export SCEPTRE_{0}={1}".format(
                    output["OutputKey"], output["OutputValue"]
                )
                for output in response
            ]
        ))
    else:
        write(response, ctx.obj["output_format"])


@cli.command(name="describe-status")
@click.argument("path")
@click.option(
    "--recursive", "-r", is_flag=True,
    help="Recursively apply operation to all stacks."
)
@click.pass_context
@catch_exceptions
def describe_status(ctx, path, recursive):
    """
    Describes a stack or environment's statuses.
    """
    if recursive:
        env = _get_env(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
        responses = env.describe()
    else:
        stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
        try:
            status = stack.get_status()
        except StackDoesNotExistError:
            status = "PENDING"
        responses = {stack.name: status}
    write(responses, ctx.obj["output_format"])


@cli.command(name="set-stack-policy")
@click.argument("path")
@click.option("--policy-file")
@click.pass_context
@catch_exceptions
def set_stack_policy(ctx, path, policy_file):
    """
    Sets a stack policy.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    stack.set_policy(policy_file)


@cli.command(name="get-stack-policy")
@click.argument("path")
@click.pass_context
@catch_exceptions
def get_stack_policy(ctx, path):
    """
    Displays a stack's stack policy.
    """
    stack = _get_stack(ctx.obj["sceptre_dir"], path, ctx.obj["options"])
    response = stack.get_policy()

    write(response.get('StackPolicyBody', {}))


def _get_stack_name(path):
    """
    Returns the name of the stack at 'path'.

    :param path: The path to the stack
    :type path: str
    :returns: The stack name
    :rtype: str
    """
    stack_basename = os.path.basename(path)
    return os.path.splitext(stack_basename)[0]


def _get_stack(sceptre_dir, path, options):
    """
    Returns the stack at 'path'

    :param path: The path to the stack
    :type path: str
    :returns: The stack
    :rtype: sceptre.stack.Stack
    """
    env = _get_env(sceptre_dir, path, options)
    stack = _get_stack_name(path)
    return env.stacks[stack]


def _get_env_path(path):
    """
    Returns the environment path pointed to by 'path'.

    :param path: The path to the environment
    :type path: str
    :returns: The environment path
    :rtype: str
    """
    abs_env_path = os.path.dirname(path)
    return "/".join(abs_env_path.split(os.path.sep)[1:])


def _get_env(sceptre_dir, path, options):
    """
    Initialises and returns a sceptre.environment.Environment().

    :param sceptre_dir: The absolute path to the Sceptre directory.
    :type project dir: str
    :param environment_path: The name of the environment.
    :type environment_path: str
    :param options: A dict of key-value pairs to update self.config with.
    :type debug: dict
    :returns: An Environment.
    :rtype: sceptre.environment.Environment
    """
    environment_path = _get_env_path(path)
    return Environment(
        sceptre_dir=sceptre_dir,
        environment_path=environment_path,
        options=options
    )


def setup_logging(debug, no_colour):
    """
    Sets up logging.

    By default, the python logging module is configured to push logs to stdout
    as long as their level is at least INFO. The log format is set to
    "[%(asctime)s] - %(name)s - %(message)s" and the date format is set to
    "%Y-%m-%d %H:%M:%S".

    After this function has run, modules should:

    .. code:: python

        import logging

        logging.getLogger(__name__).info("my log message")

    :param debug: A flag indication whether to turn on debug logging.
    :type debug: bool
    :no_colour: A flag to indicating whether to turn off coloured output.
    :type no_colour: bool
    :returns: A logger.
    :rtype: logging.Logger
    """
    if debug:
        sceptre_logging_level = logging.DEBUG
        logging.getLogger("botocore").setLevel(logging.INFO)
    else:
        sceptre_logging_level = logging.INFO
        # Silence botocore logs
        logging.getLogger("botocore").setLevel(logging.CRITICAL)

    formatter_class = Formatter if no_colour else ColouredFormatter

    formatter = formatter_class(
        fmt="[%(asctime)s] - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    log_handler = logging.StreamHandler()
    log_handler.setFormatter(formatter)
    logger = logging.getLogger("sceptre")
    logger.addHandler(log_handler)
    logger.setLevel(sceptre_logging_level)
    return logger


def write(var, output_format="str"):
    """
    Writes ``var`` to stdout. If output_format is set to "json" or "yaml",
    write ``var`` as a JSON or YAML string.

    :param var: The object to print
    :type var: obj
    :param output_format: The format to print the output as. Allowed values: \
    "str", "json", "yaml"
    :type output_format: str
    """
    if output_format == "json":
        encoder = CustomJsonEncoder()
        stream = encoder.encode(var)
    if output_format == "yaml":
        stream = yaml.safe_dump(var, default_flow_style=False)
    if output_format == "str":
        stream = var
    click.echo(stream)


class ColouredFormatter(Formatter):
    """
    ColouredFormatter add colours to all stack statuses that appear in log
    messages.
    """

    stack_status_colourer = StackStatusColourer()

    def format(self, record):
        """
        Colours and returns all stack statuses in ``record``.

        :param record: The log item to format.
        :type record: str
        :returns: str
        """
        response = super(ColouredFormatter, self).format(record)
        coloured_response = self.stack_status_colourer.colour(response)
        return coloured_response


class CustomJsonEncoder(JSONEncoder):
    """
    CustomJsonEncoder is a JSONEncoder which encodes all items as JSON by
    calling their __str__() method.
    """

    def default(self, item):
        """
        Returns stringified version of item.

        :param item: An arbitrary object to stringify.
        :type item: obj
        :returns: The stringified object.
        :rtype: str
        """
        return str(item)
