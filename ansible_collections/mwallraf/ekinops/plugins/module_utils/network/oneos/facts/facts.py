# -*- coding: utf-8 -*-
# Copyright 2022 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
The facts class for oneos
this file validates each subset of facts and selectively
calls the appropriate facts gathering function
"""

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.facts.facts import (  # noqa:E501
    FactsBase,
)
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.facts.legacy.base import (  # noqa:E501
    Default,
    Hardware,
    Config,
    Interfaces,
)
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.facts.hostname.hostname import (  # noqa:E501
    HostnameFacts,
)

from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.facts.acl_interfaces.acl_interfaces import (  # noqa:E501
    Acl_interfacesFacts,
)


FACT_LEGACY_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    config=Config,
    interfaces=Interfaces,
)

FACT_RESOURCE_SUBSETS = dict(
    hostname=HostnameFacts,
    acl_interfaces=Acl_interfacesFacts,
)


class Facts(FactsBase):
    """The fact class for oneos"""

    VALID_LEGACY_GATHER_SUBSETS = frozenset(FACT_LEGACY_SUBSETS.keys())
    VALID_RESOURCE_SUBSETS = frozenset(FACT_RESOURCE_SUBSETS.keys())

    def __init__(self, module):
        super(Facts, self).__init__(module)

    def get_facts(
        self, legacy_facts_type=None, resource_facts_type=None, data=None
    ):
        """Collect the facts for oneos

        :param legacy_facts_type: List of legacy facts types
        :param resource_facts_type: List of resource fact types
        :param data: previously collected conf
        :rtype: dict
        :return: the facts gathered
        """

        if self.VALID_RESOURCE_SUBSETS:
            self.get_network_resources_facts(
                FACT_RESOURCE_SUBSETS, resource_facts_type, data
            )

        if self.VALID_LEGACY_GATHER_SUBSETS:
            self.get_network_legacy_facts(
                FACT_LEGACY_SUBSETS, legacy_facts_type
            )

        return self.ansible_facts, self._warnings
