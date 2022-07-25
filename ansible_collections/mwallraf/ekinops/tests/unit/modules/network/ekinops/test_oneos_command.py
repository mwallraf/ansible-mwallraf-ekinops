# -*- coding: utf-8 -*-
#
# Copyright: (c) 2022 - 2NMS bv
# GNU General Public License v3.0
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.mwallraf.ekinops.plugins.modules import oneos_command
from ansible_collections.mwallraf.ekinops.tests.unit.compat.mock import patch
from ansible_collections.mwallraf.ekinops.tests.unit.modules.utils import (
    set_module_args,
)
from ansible_collections.mwallraf.ekinops.tests.unit.modules.network.ekinops.base import (  # noqa:E501
    TestOneOsModule,
    load_fixture,
)


class TestOneOsCommandModule(TestOneOsModule):

    module = oneos_command

    def setUp(self):
        super(TestOneOsCommandModule, self).setUp()

        self.mock_run_commands = patch(
            "ansible_collections.mwallraf.ekinops.plugins.modules."
            "oneos_command.run_commands"
        )

        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestOneOsCommandModule, self).tearDown()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            module, commands = args
            output = []

            if isinstance(commands, str):
                filename = "command_" + str(commands).replace(" ", "_")
                output.append(load_fixture(filename))
                return output

            for item in commands:
                oneos_version = 5
                print(item)
                try:
                    # obj = json.loads(item)
                    command = item["command"]
                    oneos_version = item["oneos_version"]
                except (ValueError, TypeError):
                    command = item
                filename = "command_" + str(command).replace(" ", "_")
                output.append(load_fixture(filename, oneos_version))
            return output

        self.run_commands.side_effect = load_from_file

    def test_oneos_5_command_simple(self):
        set_module_args(
            dict(commands=[{"command": "show version", "oneos_version": 5}])
        )
        result = self.execute_module()
        self.assertTrue(result["stdout"][0].startswith("Software version"))
        self.assertFalse(result["stdout"][0].startswith("SOMETHING WRONG"))
        self.assertIn("2R2E7_HA8", result["stdout"][0])
        self.assertEqual(len(result["stdout"]), 1)

    def test_oneos_6_command_simple(self):
        set_module_args(
            dict(commands=[{"command": "show version", "oneos_version": 6}])
        )
        result = self.execute_module()
        self.assertTrue(result["stdout"][0].startswith("Software version"))
        self.assertFalse(result["stdout"][0].startswith("SOMETHING WRONG"))
        self.assertIn("ARM_pi1-6.2.2", result["stdout"][0])
        self.assertEqual(len(result["stdout"]), 1)

    def test_oneos_command_multiple(self):
        set_module_args(dict(commands=["show version", "show system status"]))
        result = self.execute_module()
        self.assertIsNotNone(result["stdout"][0])
        self.assertEqual(len(result["stdout"]), 2)
        self.assertTrue(result["stdout"][0].startswith("Software version"))
        self.assertNotEqual(result["stdout"][0], "SOMETHING WRONG")
        self.assertIsNotNone(result["stdout"][1])
        self.assertIn("2R2E7_HA8", result["stdout"][1])

    def test_oneos_command_wait_for(self):
        wait_for = 'result[0] contains "ONEOS"'
        set_module_args(dict(commands=["show version"], wait_for=wait_for))
        result = self.execute_module()
        self.assertIn("ONEOS", result["stdout"][0])

    def test_oneos_command_wait_for_fails(self):
        wait_for = 'result[0] contains "test"'
        set_module_args(dict(commands=["show version"], wait_for=wait_for))
        self.execute_module(failed=True)
        self.assertEqual(self.run_commands.call_count, 10)

    def test_oneos_command_retries(self):
        wait_for = 'result[0] contains "ONEOS"'
        set_module_args(
            dict(commands=["show version"], wait_for=wait_for, retries=2)
        )
        self.execute_module()

    def test_oneos_command_retries_failure(self):
        wait_for = 'result[0] contains "test"'
        set_module_args(
            dict(commands=["show version"], wait_for=wait_for, retries=2)
        )
        self.execute_module(failed=True)

    def test_oneos_command_match_any(self):
        wait_for = [
            'result[0] contains "ONEOS"',
            'result[0] contains "test"',
        ]
        set_module_args(
            dict(commands=["show version"], wait_for=wait_for, match="any")
        )
        self.execute_module()

    def test_oneos_command_match_any_failure(self):
        wait_for = [
            'result[0] contains "test1"',
            'result[0] contains "test2"',
        ]
        set_module_args(
            dict(commands=["show version"], wait_for=wait_for, match="any")
        )
        self.execute_module(failed=True)

    def test_oneos_command_match_all(self):
        wait_for = [
            'result[0] contains "version"',
            'result[0] contains "ONEOS"',
        ]
        set_module_args(
            dict(commands=["show version"], wait_for=wait_for, match="all")
        )
        self.execute_module()

    def test_oneos_command_match_all_failure(self):
        wait_for = [
            'result[0] contains "version"',
            'result[0] contains "test"',
        ]
        commands = ["show version", "show version"]
        set_module_args(
            dict(commands=commands, wait_for=wait_for, match="all")
        )
        self.execute_module(failed=True)

    def test_oneos_command_configure_check_warning(self):
        commands = ["configure"]
        set_module_args(
            {
                "commands": commands,
                "_ansible_check_mode": True,
            }
        )
        result = self.execute_module()
        self.assertEqual(
            result["warnings"],
            [
                (
                    "Only show commands are supported when using check mode"
                    ", not executing configure"
                )
            ],
        )

    def test_oneos_command_configure_no_warning(self):
        commands = ["configure"]
        set_module_args(
            {
                "commands": commands,
                "_ansible_check_mode": True,
            }
        )
        result = self.execute_module()
        self.assertNotEqual(result["warnings"], [])
