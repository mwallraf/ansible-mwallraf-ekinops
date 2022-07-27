# -*- coding: utf-8 -*-
# Copyright 2022 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

"""
The oneos acl_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from copy import deepcopy

from ansible.module_utils.six import iteritems
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import (  # noqa: E501
    utils,
)
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.rm_templates.acl_interfaces import (  # noqa: E501
    Acl_interfacesTemplate,
)
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.argspec.acl_interfaces.acl_interfaces import (  # noqa: E501
    Acl_interfacesArgs,
)


class Acl_interfacesFacts(object):
    """The oneos acl_interfaces facts class"""

    def __init__(self, module, subspec="config", options="options"):
        self._module = module
        self.argument_spec = Acl_interfacesArgs.argument_spec

    def get_acl_interfaces_data(self, connection):
        return connection.get("alias-get-interface-acl")

    def populate_facts(self, connection, ansible_facts, data=None):
        """Populate the facts for Acl_interfaces network resource

        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf

        :rtype: dictionary
        :returns: facts
        """
        facts = {"acl_interfaces": []}

        if not data:
            data = self.get_acl_interfaces_data(connection)

        # parse native config using the Acl_interfaces template
        acl_interfaces_parser = Acl_interfacesTemplate(
            lines=data.splitlines(), module=self._module
        )
        entry = sorted(
            list(acl_interfaces_parser.parse().values()),
            key=lambda k, sk="name": k[sk],
        )

        if entry:
            for item in entry:
                item["access_groups"] = sorted(
                    list(item["access_groups"].values()),
                    key=lambda k, sk="afi": k[sk],
                )

        ansible_facts["ansible_network_resources"].pop("acl_interfaces", None)

        facts = {"acl_interfaces": []}

        for cfg in entry:
            utils.remove_empties(cfg)
            if cfg.get("access_groups"):
                facts["acl_interfaces"].append(cfg)

        utils.validate_config(
            self.argument_spec,
            {"config": facts.get("acl_interfaces")},
        )

        ansible_facts["ansible_network_resources"].update(facts)

        return ansible_facts
