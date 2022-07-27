# -*- coding: utf-8 -*-
#
# Copyright: (c) 2020, A10 Networks Inc.
# GNU General Public License v3.0
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.mwallraf.ekinops.plugins.modules import oneos_facts
from ansible_collections.mwallraf.ekinops.tests.unit.compat.mock import patch
from ansible_collections.mwallraf.ekinops.tests.unit.modules.utils import (
    set_module_args,
    AnsibleFailJson,
)
from ansible_collections.mwallraf.ekinops.tests.unit.modules.network.ekinops.base import (  # noqa:E501
    TestOneOsModule,
    load_fixture,
)


class TestOneosFactsModule(TestOneOsModule):

    module = oneos_facts

    def setUp(self):
        super(TestOneosFactsModule, self).setUp()
        self.mock_run_commands = patch(
            "ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.facts.legacy.base.run_commands"
        )
        self.run_commands = self.mock_run_commands.start()

        self.mock_get_capabilities = patch(
            "ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.facts.legacy.base.get_capabilities"
        )
        self.get_capabilities = self.mock_get_capabilities.start()
        # self.get_capabilities.return_value = {
        #     "device_info": {
        #         "ansible_net_hostname": "lab-lbb150",
        #         "ansible_net_model": "LBB_150",
        #         "ansible_net_serial_number": "T1914008214019302",
        #         "network_os": "oneos",
        #         "ansible_net_vendor": "ekinops",
        #         "network_os_version": "6",
        #         # "network_os": "acos",
        #         # "network_os_image": "4.1.1-P9.105",
        #         # "network_os_model": "Thunder Series Unified Application Service Gateway vThunder",
        #         # "network_os_version": "64-bit Advanced Core OS (ACOS) version 4.1.1-P9, build 105 (Sep-21-2018,22:25)",
        #     },
        #     "network_api": "cliconf",
        # }

    def tearDown(self):
        super(TestOneosFactsModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_get_capabilities.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            commands = kwargs["commands"]
            output = []

            for command in commands:
                filename = str(command).replace(" | ", "_").replace(" ", "_")
                output.append(load_fixture("oneos_facts_%s" % filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_oneos_facts_default(self):
        set_module_args(dict(gather_subset="default"))
        result = self.execute_module()
        # raise Exception(result)
        # self.assertEqual(
        #     result["ansible_facts"]["ansible_net_hostid"], "ABCDEFGHIJKLMNOPQ"
        # )
        # self.assertEqual(
        #     result["ansible_facts"]["ansible_net_image"], "4.1.1-P9.105"
        # )
        # self.assertEqual(
        #     result["ansible_facts"]["ansible_net_model"],
        #     "Thunder Series Unified Application Service Gateway vThunder",
        # )
        # self.assertEqual(
        #     result["ansible_facts"]["ansible_net_version"],
        #     "64-bit Advanced Core OS (ACOS) version 4.1.1-P9, build 105 (Sep-21-2018,22:25)",
        # )
