#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2022 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
The module file for oneos_acl_interfaces
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: oneos_acl_interfaces
version_added: "1.0.1"
short_description: Configure and manage access-control (ACL) attributes of interfaces on ONEOS devices.
description: This module configures and manages the access-control (ACL) attributes of interfaces on ONEOS platforms.
author: Maarten Wallraf (based on IOS version by Sumit Jaiswal (@justjais) )
notes:
  - Tested against OneOS v5 + v6
  - This module works with connection C(network_cli).
options:
  config:
    description: A dictionary of ACL options
    type: list
    elements: dict
    suboptions:
      name:
        description: Full and exact name of the interface excluding any logical unit number, i.e. GigabitEthernet 0/1
        type: str
        required: True
      access_groups:
        description: Specify access-group for IP access list (standard or extended).
        type: list
        elements: dict
        suboptions:
          afi:
            description:
              - Specifies the AFI for the ACLs to be configured on this interface.
            type: str
            choices:
              - ipv4
              - ipv6
          acls:
            type: list
            description:
              - Specifies the ACLs for the provided AFI.
            elements: dict
            suboptions:
              name:
                description:
                  - Specifies the name of the IPv4/IPv4 ACL for the interface.
                type: str
                required: True
              direction:
                description:
                  - Specifies the direction of packets that the ACL will be applied on.
                type: str
                choices:
                  - in
                  - out
  running_config:
    description:
      - Running config for parsing commands
    type: str
  state:
    description:
      - The state the configuration should be left in
    type: str
    choices:
      - merged
      - replaced
      - overridden
      - deleted
      - gathered
      - parsed
      - rendered
    default: merged
EXAMPLES:
  - deleted_example_01.txt
  - merged_example_01.txt
  - replaced_example_01.txt
  - overridden_example_01.txt
"""

EXAMPLES = """

"""

RETURN = """
before:
  description: The configuration prior to the module execution.
  returned: when I(state) is C(merged), C(replaced), C(overridden), C(deleted) or C(purged)
  type: dict
  sample: >
    This output will always be in the same format as the
    module argspec.
after:
  description: The resulting configuration after module execution.
  returned: when changed
  type: dict
  sample: >
    This output will always be in the same format as the
    module argspec.
commands:
  description: The set of commands pushed to the remote device.
  returned: when I(state) is C(merged), C(replaced), C(overridden), C(deleted) or C(purged)
  type: list
  sample:
    - sample command 1
    - sample command 2
    - sample command 3
rendered:
  description: The provided configuration in the task rendered in device-native format (offline).
  returned: when I(state) is C(rendered)
  type: list
  sample:
    - sample command 1
    - sample command 2
    - sample command 3
gathered:
  description: Facts about the network resource gathered from the remote device as structured data.
  returned: when I(state) is C(gathered)
  type: list
  sample: >
    This output will always be in the same format as the
    module argspec.
parsed:
  description: The device native config provided in I(running_config) option parsed into structured data as per module argspec.
  returned: when I(state) is C(parsed)
  type: list
  sample: >
    This output will always be in the same format as the
    module argspec.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.argspec.acl_interfaces.acl_interfaces import (
    Acl_interfacesArgs,
)
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.config.acl_interfaces.acl_interfaces import (
    Acl_interfaces,
)


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(
        argument_spec=Acl_interfacesArgs.argument_spec,
        mutually_exclusive=[["config", "running_config"]],
        required_if=[
            ["state", "merged", ["config"]],
            ["state", "replaced", ["config"]],
            ["state", "overridden", ["config"]],
            ["state", "rendered", ["config"]],
            ["state", "parsed", ["running_config"]],
        ],
        supports_check_mode=True,
    )

    result = Acl_interfaces(module).execute_module()

    # make sure that something was really changed
    if result["changed"] is True and result["before"] == result["after"]:
        warnings = ["something went wrong changing the interface acl entries"]
        result["warnings"] = warnings
        module.fail_json(msg=warnings, failed_conditions=warnings)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
