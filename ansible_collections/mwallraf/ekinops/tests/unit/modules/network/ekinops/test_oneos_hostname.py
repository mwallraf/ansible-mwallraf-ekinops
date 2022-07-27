# -*- coding: utf-8 -*-
#
# Copyright: (c) 2022 - 2NMS bv
# GNU General Public License v3.0
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from textwrap import dedent

from ansible_collections.mwallraf.ekinops.plugins.modules import oneos_hostname
from ansible_collections.mwallraf.ekinops.tests.unit.compat.mock import patch
from ansible_collections.mwallraf.ekinops.tests.unit.modules.utils import (
    set_module_args,
)
from ansible_collections.mwallraf.ekinops.tests.unit.modules.network.ekinops.base import (  # noqa:E501
    TestOneOsModule,
    load_fixture,
)


class TestOneHostnameModule(TestOneOsModule):

    module = oneos_hostname

    def setUp(self):
        super(TestOneHostnameModule, self).setUp()

        self.mock_get_config = patch(
            "ansible_collections.ansible.netcommon.plugins.module_utils.network.common.network.Config.get_config",
        )
        self.get_config = self.mock_get_config.start()

        self.mock_execute_show_command = patch(
            "ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.facts.hostname.hostname."
            "HostnameFacts.get_hostname_data"
        )
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestOneHostnameModule, self).tearDown()

        self.mock_get_config.stop()
        self.mock_execute_show_command.stop()

    def test_oneos_hostname_merged_idempotent(self):
        self.execute_show_command.return_value = dedent(
            """\
            hostname test-lbb320
            """
        )
        set_module_args(
            dict(config=dict(hostname="test-lbb320"), state="merged")
        )
        commands = []
        result = self.execute_module(changed=False)
        self.assertEqual(sorted(result["commands"]), sorted(commands))
