#
# -*- coding: utf-8 -*-
# Copyright 2022 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import absolute_import, division, print_function

__metaclass__ = type

"""
The oneos_acl_interfaces config file.
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to its desired end-state is
created.
"""

from copy import deepcopy

from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_text
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
    dict_merge,
)
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.rm_base.resource_module import (
    ResourceModule,
)
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.facts.facts import (
    Facts,
)
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.rm_templates.acl_interfaces import (
    Acl_interfacesTemplate,
)


class Acl_interfaces(ResourceModule):
    """
    The oneos_acl_interfaces config class
    """

    def __init__(self, module):
        super(Acl_interfaces, self).__init__(
            empty_fact_val={},
            facts_module=Facts(module),
            module=module,
            resource="acl_interfaces",
            tmplt=Acl_interfacesTemplate(),
        )

    def execute_module(self):
        """Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        if self.state not in ["parsed", "gathered"]:
            self.generate_commands()
            self.run_commands()
        return self.result

    def generate_commands(self):
        """Generate configuration commands to send based on
        want, have and desired state.
        """

        # oneos 6 has a discrepancy between the interface name output
        # of "show run" and "show int", we will converty all names
        # to lowercase for comparison

        wantd = {entry["name"].lower(): entry for entry in self.want}
        haved = {entry["name"].lower(): entry for entry in self.have}

        # turn all lists of dicts into dicts prior to merge
        for entry in wantd, haved:
            self._list_to_dict(entry)

        # if state is merged, merge want onto have and then compare
        if self.state == "merged":
            wantd = dict_merge(haved, wantd)

        # if state is deleted, empty out wantd and set haved to wantd
        if self.state == "deleted":
            haved = {
                k: v for k, v in iteritems(haved) if k in wantd or not wantd
            }
            wantd = {}

        # remove superfluous config for overridden and deleted
        if self.state in ["overridden", "deleted"]:
            for k, have in iteritems(haved):
                if k not in wantd:
                    self._compare(want={}, have=have)

        for k, want in iteritems(wantd):
            self._compare(want=want, have=haved.pop(k, {}))

    def _compare(self, want, have):
        """Leverages the base class `compare()` method and
        populates the list of commands to be run by comparing
        the `want` and `have` data with the `parsers` defined
        for the Acl_interfaces network resource.
        """
        begin = len(self.commands)
        self._compare_lists(want=want, have=have)
        if len(self.commands) != begin:
            self.commands.insert(
                begin,
                self._tmplt.render(want or have, "interface", False),
            )

    def _compare_lists(self, want, have):
        wdict = want.get("access_groups", {})
        hdict = have.get("access_groups", {})

        for afi in ("ipv4", "ipv6"):
            wacls = wdict.pop(afi, {}).pop("acls", {})
            hacls = hdict.pop(afi, {}).pop("acls", {})

            for key, entry in wacls.items():
                if entry != hacls.pop(key, {}):
                    entry["afi"] = afi
                    self.addcmd(entry, "access_groups", False)
            # remove remaining items in have for replaced
            for entry in hacls.values():
                entry["afi"] = afi
                self.addcmd(entry, "access_groups", True)

    def _list_to_dict(self, entry):
        for item in entry.values():
            for ag in item.get("access_groups", []):
                ag["acls"] = {
                    subentry["direction"]: {
                        "name": to_text(subentry["name"]),
                        "direction": subentry["direction"],
                    }
                    for subentry in ag.get("acls", [])
                }

            # oneos 6 has a discrepancy between the interface name output
            # of "show run" and "show int", we will converty all names
            # to lowercase for comparison
            # item["name"] = item["name"].lower()
            item["access_groups"] = {
                subentry["afi"]: subentry
                for subentry in item.get("access_groups", [])
            }
