import logging
import yaml
import datetime

from click.testing import CliRunner
import pytest
from mock import Mock, patch, sentinel

import sceptre.cli_v2
from sceptre.cli_v2 import cli
from sceptre.exceptions import SceptreException
from sceptre.stack_status import StackStatus
from sceptre.stack_status import StackChangeSetStatus


class TestCli(object):

    def setup_method(self, test_method):
        self.runner = CliRunner()

    @patch("sys.exit")
    def test_catch_excecptions(self, mock_exit):
            @sceptre.cli_v2.catch_exceptions
            def raises_exception():
                raise SceptreException

            raises_exception()
            mock_exit.assert_called_once_with(1)

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_validate_template(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["validate-template", "config/dev/vpc.yaml"])
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.validate_template.assert_called_with()

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_generate_template(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        result = self.runner.invoke(
            cli, ["generate-template", "config/dev/vpc.yaml"])
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})

        assert result.output == "{0}\n".format(
            mock_get_stack.return_value.template.body
        )

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_lock_stack(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["lock", "config/dev/vpc.yaml"])
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.lock.assert_called_with()

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_unlock_stack(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["unlock", "config/dev/vpc.yaml"])
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.unlock.assert_called_with()

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_env")
    def test_describe_env_resources(self, mock_get_env, mock_getcwd):
        describe_response = {
            "stack-name-1": {
                "StackResources": [
                    {
                        "LogicalResourceId": "logical-resource-id",
                        "PhysicalResourceId": "physical-resource-id"
                    }
                ]
            },
            "stack-name-2": {
                "StackResources": [
                    {
                        "LogicalResourceId": "logical-resource-id",
                        "PhysicalResourceId": "physical-resource-id"
                    }
                ]
            }
        }
        mock_get_env.return_value.describe_resources.return_value = \
            describe_response
        mock_getcwd.return_value = sentinel.cwd
        result = self.runner.invoke(
            cli, ["describe-resources", "-r", "config/dev"])
        mock_get_env.assert_called_with(sentinel.cwd, "config/dev", {})
        mock_get_env.return_value.describe_resources\
            .assert_called_with()
        assert yaml.safe_load(result.output) == describe_response

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_describe_stack_resources(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        describe_response = {
            "StackResources": [
                {
                    "LogicalResourceId": "logical-resource-id",
                    "PhysicalResourceId": "physical-resource-id"
                }
            ]
        }

        mock_get_stack.return_value.describe_resources.return_value = \
            describe_response
        result = self.runner.invoke(
            cli, ["describe-resources", "config/dev/vpc.yaml"]
        )
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.describe_resources.assert_called_with()
        assert yaml.safe_load(result.output) == describe_response

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_create_stack(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["create", "config/dev/vpc.yaml"])
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.create.assert_called_with()

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_delete_stack(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["delete", "config/dev/vpc.yaml"])
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.delete.assert_called_with()

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_update_stack(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["update", "config/dev/vpc.yaml"])
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.update.assert_called_with()

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_launch_stack(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["launch", "config/dev/vpc.yaml"])
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.launch.assert_called_with()

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_env")
    def test_launch_env(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["launch", "-r", "config/dev"])
        mock_get_env.assert_called_with(sentinel.cwd, "config/dev", {})
        mock_get_env.return_value.launch.assert_called_with()

    @patch("sceptre.cli_v2._get_env")
    def test_launch_env_returns_zero_correctly(self, mock_get_env):
        mock_get_env.return_value.launch.return_value = dict(
            (sentinel.stack_name, StackStatus.COMPLETE) for _ in range(5)
        )
        result = self.runner.invoke(cli, ["launch", "-r", "config/env"])
        assert result.exit_code == 0

    @patch("sceptre.cli_v2._get_env")
    def test_launch_env_returns_non_zero_correctly(self, mock_get_env):
        mock_get_env.return_value.launch.return_value = dict(
            (sentinel.stack_name, StackStatus.FAILED) for _ in range(5)
        )
        result = self.runner.invoke(cli, ["launch", "-r", "env"])
        assert result.exit_code == 1

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_env")
    def test_delete_env(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        mock_get_env.return_value.delete.return_value = \
            sentinel.response
        self.runner.invoke(cli, ["delete", "-r", "config/dev"])
        mock_get_env.assert_called_with(sentinel.cwd, "config/dev", {})
        mock_get_env.return_value.delete.assert_called_with()

    @patch("sceptre.cli_v2._get_env")
    def test_delete_env_returns_zero_correctly(self, mock_get_env):
        mock_get_env.return_value.delete.return_value = dict(
            (sentinel.stack_name, StackStatus.COMPLETE) for _ in range(5)
        )
        result = self.runner.invoke(
            cli, ["delete", "-r", "config/environment"])
        assert result.exit_code == 0

    @patch("sceptre.cli_v2._get_env")
    def test_delete_env_returns_non_zero_correctly(self, mock_get_env):
        mock_get_env.return_value.delete.return_value = dict(
            (sentinel.stack_name, StackStatus.FAILED) for _ in range(5)
        )
        result = self.runner.invoke(
            cli, ["delete", "-r", "config/environment"])
        assert result.exit_code == 1

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_continue_update_rollback(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(
            cli, ["continue-update-rollback", "config/dev/vpc.yaml"])
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.continue_update_rollback\
            .assert_called_with()

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_create_change_set(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(
            cli, ["create-change-set", "config/dev/vpc.yaml", "cs1"]
        )
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.create_change_set\
            .assert_called_with("cs1")

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_delete_change_set(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(
            cli, ["delete-change-set", "config/dev/vpc.yaml", "cs1"]
        )
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.delete_change_set\
            .assert_called_with("cs1")

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_describe_change_set(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        mock_get_stack.return_value.describe_change_set.return_value = {
            "ChangeSetName": "change-set-1",
            "Changes": [
                {
                    "ResourceChange": {
                        "ResourceType": "AWS::EC2::InternetGateway",
                        "Replacement": "True",
                        "PhysicalResourceId": "igw-04a59561",
                        "Details": [],
                        "Action": "Remove",
                        "Scope": [],
                        "LogicalResourceId": "InternetGateway"
                    }
                }
            ],
            "CreationTime": "2017-01-20 14:10:25.239000+00:00",
            "ExecutionStatus": "AVAILABLE",
            "StackName": "example-dev-vpc",
            "Status": "CREATE_COMPLETE"
        }
        result = self.runner.invoke(
            cli, ["describe-change-set", "config/dev/vpc.yaml", "cs1"]
        )
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.describe_change_set\
            .assert_called_with("cs1")
        assert yaml.safe_load(result.output) == {
            "ChangeSetName": "change-set-1",
            "Changes": [
                {
                    "ResourceChange": {
                        "ResourceType": "AWS::EC2::InternetGateway",
                        "Replacement": "True",
                        "PhysicalResourceId": "igw-04a59561",
                        "Action": "Remove",
                        "LogicalResourceId": "InternetGateway",
                        "Scope": []
                    }
                }
            ],
            "CreationTime": "2017-01-20 14:10:25.239000+00:00",
            "ExecutionStatus": "AVAILABLE",
            "StackName": "example-dev-vpc",
            "Status": "CREATE_COMPLETE"
        }

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_describe_change_set_with_verbose_flag(
        self, mock_get_stack, mock_getcwd
    ):
        mock_getcwd.return_value = sentinel.cwd
        mock_get_stack.return_value.describe_change_set.return_value = {
            "Changes": [
                {
                    "ResourceChange": {
                        "ResourceType": "AWS::EC2::InternetGateway",
                        "PhysicalResourceId": "igw-04a59561",
                        "Details": [],
                        "Action": "Remove",
                        "Scope": [],
                        "LogicalResourceId": "InternetGateway"
                    }
                }
            ]
        }
        result = self.runner.invoke(
            cli,
            ["describe-change-set", "--verbose", "config/dev/vpc.yaml", "cs1"]
        )
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.describe_change_set\
            .assert_called_with("cs1")
        assert yaml.safe_load(result.output) == {
            "Changes": [
                {
                    "ResourceChange": {
                        "ResourceType": "AWS::EC2::InternetGateway",
                        "PhysicalResourceId": "igw-04a59561",
                        "Details": [],
                        "Action": "Remove",
                        "Scope": [],
                        "LogicalResourceId": "InternetGateway"
                        }
                    }
                ]
        }

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_execute_change_set(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(
            cli, ["execute-change-set", "config/dev/vpc.yaml", "cs1"])
        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.execute_change_set\
            .assert_called_with("cs1")

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_stack")
    def test_list_change_sets(self, mock_get_stack, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["list-change-sets", "config/dev/vpc.yaml"])

        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_stack.return_value.list_change_sets.assert_called_with()

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2.uuid1")
    @patch("sceptre.cli_v2._get_stack")
    def test_update_with_change_set_with_input_yes(
            self, mock_get_stack, mock_uuid1, mock_getcwd
    ):
        mock_getcwd.return_value = sentinel.cwd
        mock_stack = Mock()
        mock_stack.wait_for_cs_completion.return_value = \
            StackChangeSetStatus.READY
        mock_stack.describe_change_set.return_value = "description"
        mock_get_stack.return_value = mock_stack
        mock_uuid1().hex = "1"

        result = self.runner.invoke(
            cli, ["update-cs", "config/dev/vpc.yaml", "--verbose"], input="yes"
        )

        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_stack.create_change_set.assert_called_with("change-set-1")
        mock_stack.wait_for_cs_completion.assert_called_with("change-set-1")
        mock_stack.execute_change_set.assert_called_with("change-set-1")

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._simplify_change_set_description")
    @patch("sceptre.cli_v2.uuid1")
    @patch("sceptre.cli_v2._get_stack")
    def test_update_with_change_set_without_verbose_flag(
            self, mock_get_stack, mock_uuid1,
            mock_simplify_change_set_description, mock_getcwd
    ):
        mock_getcwd.return_value = sentinel.cwd
        mock_stack = Mock()
        mock_stack.wait_for_cs_completion.return_value = \
            StackChangeSetStatus.READY
        mock_stack.describe_change_set.return_value = "description"
        mock_get_stack.return_value = mock_stack
        mock_uuid1().hex = "1"
        mock_simplify_change_set_description.return_value = \
            "simplified_description"
        response = self.runner.invoke(
            cli, ["update-cs", "config/dev/vpc.yaml"], input="y"
        )
        assert "simplified_description" in response.output

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2.uuid1")
    @patch("sceptre.cli_v2._get_stack")
    def test_update_with_change_set_with_input_no(
            self, mock_get_stack, mock_uuid1, mock_getcwd
    ):
        mock_getcwd.return_value = sentinel.cwd
        mock_stack = Mock()
        mock_stack.wait_for_cs_completion.return_value = \
            StackChangeSetStatus.READY
        mock_stack.describe_change_set.return_value = "description"
        mock_get_stack.return_value = mock_stack
        mock_uuid1().hex = "1"

        result = self.runner.invoke(
            cli, ["update-cs", "config/dev/vpc.yaml", "--verbose"], input="n"
        )

        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_stack.create_change_set.assert_called_with("change-set-1")
        mock_stack.wait_for_cs_completion.assert_called_with("change-set-1")
        mock_stack.delete_change_set.assert_called_with("change-set-1")

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2.uuid1")
    @patch("sceptre.cli_v2._get_stack")
    def test_update_cs_with_status_defunct(
            self, mock_get_stack, mock_uuid1, mock_getcwd
    ):
        mock_getcwd.return_value = sentinel.cwd
        mock_stack = Mock()
        mock_stack.wait_for_cs_completion.return_value = \
            StackChangeSetStatus.DEFUNCT
        mock_stack.describe_change_set.return_value = "description"
        mock_get_stack.return_value = mock_stack
        mock_uuid1().hex = "1"

        result = self.runner.invoke(
            cli, ["update-cs", "config/dev/vpc.yaml", "--verbose"]
        )

        mock_get_stack.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_stack.create_change_set.assert_called_with("change-set-1")
        mock_stack.wait_for_cs_completion.assert_called_with("change-set-1")
        assert result.exit_code == 1

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_env")
    def test_describe_outputs(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["describe-outputs", "config/dev/vpc.yaml"])
        mock_get_env.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {})
        mock_get_env.return_value.stacks["vpc"].describe_outputs\
            .assert_called_with()

    @patch("sceptre.cli_v2._get_env")
    def test_describe_outputs_handles_envvar_flag(self, mock_get_env):
        mock_get_env.return_value.stacks["vpc"].describe_outputs\
            .return_value = [
                {
                    "OutputKey": "key",
                    "OutputValue": "value"
                }
            ]
        result = self.runner.invoke(
            cli,
            ["describe-outputs", "--export=envvar", "config/dev/vpc.yaml"])
        assert result.output == "export SCEPTRE_key=value\n"

    @patch("sceptre.cli_v2._get_env")
    def test_describe_env(self, mock_get_env):
        mock_Environment = Mock()
        mock_Environment.describe.return_value = {"stack": "status"}
        mock_get_env.return_value = mock_Environment

        result = self.runner.invoke(
            cli, ["describe-status", "-r", "config/dev"])
        assert result.output == "stack: status\n\n"

    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2._get_env")
    def test_set_stack_policy_with_file_flag(
        self, mock_get_env, mock_getcwd
    ):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, [
            "set-stack-policy", "config/dev/vpc.yaml",
            "--policy-file=tests/fixtures/stack_policies/lock.json"
        ])
        mock_Environment = Mock()
        mock_get_env.assert_called_with(
            sentinel.cwd, "config/dev/vpc.yaml", {}
        )
        mock_get_env.return_value = mock_Environment

    @patch("sceptre.cli_v2._get_env")
    def test_get_stack_policy_with_existing_policy(self, mock_get_env):
        mock_get_env.return_value.stacks["vpc"].get_policy\
            .return_value = {
                "StackPolicyBody": "policy"
            }

        result = self.runner.invoke(
            cli, ["get-stack-policy", "config/dev/vpc.yaml"])
        assert result.output == "policy\n"

    @patch("sceptre.cli_v2._get_env")
    def test_get_stack_policy_without_existing_policy(
            self, mock_get_env
    ):
        mock_get_env.return_value.stacks["vpc"].get_policy\
            .return_value = {}

        result = self.runner.invoke(
            cli, ["get-stack-policy", "config/dev/vpc.yaml"])
        assert result.output == "{}\n"

    @pytest.mark.parametrize("path,name", [
        ("config/dev/vpc.yaml", "vpc")
    ])
    def test_get_stack_name(self, path, name):
        assert sceptre.cli_v2._get_stack_name(path) == name


    @pytest.mark.parametrize("path,env_path", [
        ("config/dev/vpc.yaml", "dev"),
        ("config/dev/ew1/vpc.yaml", "dev/ew1")
    ])
    def test_get_env_path(self, path, env_path):
        assert sceptre.cli_v2._get_env_path(path), env_path


    @patch("sceptre.cli_v2.os.getcwd")
    @patch("sceptre.cli_v2.Environment")
    def test_get_env(self, mock_Environment, mock_getcwd):
        mock_Environment.return_value = sentinel.environment
        mock_getcwd.return_value = sentinel.cwd
        response = sceptre.cli_v2._get_env(
            sentinel.cwd, "config/dev/vpc.yaml", sentinel.options
        )
        mock_Environment.assert_called_once_with(
            sceptre_dir=sentinel.cwd,
            environment_path="dev",
            options=sentinel.options
        )
        assert response == sentinel.environment

    def test_setup_logging_with_debug(self):
        logger = sceptre.cli_v2.setup_logging(True, False)
        assert logger.getEffectiveLevel() == logging.DEBUG
        assert logging.getLogger("botocore").getEffectiveLevel() == \
            logging.INFO

        # Silence logging for the rest of the tests
        logger.setLevel(logging.CRITICAL)

    def test_setup_logging_without_debug(self):
        logger = sceptre.cli_v2.setup_logging(False, False)
        assert logger.getEffectiveLevel() == logging.INFO
        assert logging.getLogger("botocore").getEffectiveLevel() == \
            logging.CRITICAL

        # Silence logging for the rest of the tests
        logger.setLevel(logging.CRITICAL)

    @patch("sceptre.cli_v2.click.echo")
    def test_write_with_yaml_format(self, mock_echo):
        sceptre.cli_v2.write({"key": "value"}, "yaml")
        mock_echo.assert_called_once_with("key: value\n")

    @patch("sceptre.cli_v2.click.echo")
    def test_write_with_json_format(self, mock_echo):
        sceptre.cli_v2.write({"key": "value"}, "json")
        mock_echo.assert_called_once_with('{"key": "value"}')

    @patch("sceptre.cli_v2.StackStatusColourer.colour")
    @patch("sceptre.cli_v2.Formatter.format")
    def test_ColouredFormatter_format_with_string(
            self, mock_format, mock_colour
    ):
        mock_format.return_value = sentinel.response
        mock_colour.return_value = sentinel.coloured_response
        coloured_formatter = sceptre.cli_v2.ColouredFormatter()
        response = coloured_formatter.format("string")
        mock_format.assert_called_once_with("string")
        mock_colour.assert_called_once_with(sentinel.response)
        assert response == sentinel.coloured_response

    def test_CustomJsonEncoder_with_non_json_serialisable_object(self):
        encoder = sceptre.cli_v2.CustomJsonEncoder()
        response = encoder.encode(datetime.datetime(2016, 5, 3))
        assert response == '"2016-05-03 00:00:00"'
