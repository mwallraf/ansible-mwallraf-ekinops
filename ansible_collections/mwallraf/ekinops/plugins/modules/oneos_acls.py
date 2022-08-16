#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2022 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
The module file for oneos_acls
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: oneos_acls
version_added: "1.0.1"
short_description: Manages named or numbered ACLs on ONEOS devices.
description: This module configures and manages the named or numbered ACLs on ONEOS platforms.
author: Maarten Wallraf (based on IOS collection by Sumit Jaiswal)
notes:
  - Tested against OneOS v5 + v6
  - This module works with connection C(network_cli).
options:
  config:
    description: A dictionary of ACL options.
    type: list
    elements: dict
    suboptions:
      afi:
        description:
          - The Address Family Indicator (AFI) for the Access Control Lists (ACL).
        required: true
        type: str
        choices:
          - ipv4
          - ipv6
      acls:
        description:
          - A list of Access Control Lists (ACL).
        type: list
        elements: dict
        suboptions:
          name:
            description: The name or the number of the ACL.
            type: str
            required: true
          acl_type:
            description:
              - ACL type
              - Note, it's mandatory and required for Named ACL, but for
                Numbered ACL it's not mandatory.
            type: str
            choices:
              - extended
              - standard
              - remark
          aces:
            description: The entries within the ACL.
            mutually_exclusive: [[name], [number]]
            elements: dict
            # required_together: [[action, protocol, source, destination]]
            type: list
            suboptions:
              grant:
                description: Specify the action.
                type: str
                choice: ["permit", "deny"]
              protocol_options:
                description: protocol type.
                type: dict
                suboptions:
                  protocol:
                    description: Name of the protocol
                    type: str
                  protocol_number:
                    description: An IP protocol number
                    type: int
                  icmp_message_type:
                    description:
                      - icmp message type (0-255)
                    type: int
                  icmp_message_code:
                    description:
                      - icmp message code (0-255)
                    type: int
              remarks:
                description:
                  - ACL remark entries
                type: list
                elements: str
              sequence:
                description:
                  - ACL sequence number
                type: int
              source:
                description: Specify the packet source.
                type: dict
                mutually_exclusive: [[address, any], [wildcard_bits, any]]
                required_together: [address, wildcard_bits]
                suboptions:
                  host:
                    description: Source host address.
                    type: str
                  address:
                    description: Source network address.
                    type: str
                  wildcard_bits:
                    description: Destination wildcard bits, valid with IPV4 address.
                    type: str
                  any:
                    description:
                      - Match any source address.
                    type: bool
                  port_protocol:
                    description:
                      - Specify the destination port along with protocol.
                      - Note, Valid with TCP/UDP protocol_options
                    type: dict
                    suboptions:
                      eq:
                        description: Match only packets on a given port number.
                        type: str
                      range:
                        description: Port group.
                        type: dict
                        suboptions:
                          start:
                            description: Specify the start of the port range.
                            type: int
                          end:
                            description: Specify the end of the port range.
                            type: int
              destination:
                description: Specify the packet destination.
                mutually_exclusive: [[address, any], [wildcard_bits, any]]
                required_together: [address, wildcard_bits]
                type: dict
                suboptions:
                  host:
                    description: Source host address.
                    type: str
                  address:
                    description: Host address to match, or any single host address.
                    type: str
                  wildcard_bits:
                    description: Destination wildcard bits, valid with IPV4 address.
                    type: str
                  any:
                    description:
                      - Match any source address.
                    type: bool
                  port_protocol:
                    description:
                      - Specify the destination port along with protocol.
                      - Note, Valid with TCP/UDP protocol_options
                    type: dict
                    suboptions:
                      eq:
                        description: Match only packets on a given port number.
                        type: str
                      range:
                        description: Port group.
                        type: dict
                        suboptions:
                          start:
                            description: Specify the start of the port range.
                            type: int
                          end:
                            description: Specify the end of the port range.
                            type: int
              dscp:
                description: Match packets with given dscp value.
                type: int
              fragments:
                description: Check non-initial fragments.
                type: bool
              reflexive:
                description: Check if the ACL should work in both directions.
                type: bool
              log:
                description: Log matches against this entry.
                type: bool
              option:
                description:
                  - Match packets with given IP Options value.
                  - Valid only for named acls.
                type: dict
                suboptions:
                  ip_option_value:
                    description:
                      - IP Options value
                      - Note, refer vendor documentation for respective values
                    type: int
              precedence:
                description: Match packets with given precedence value.
                type: int
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
      - rendered
      - parsed
    default: merged
EXAMPLES:
  - deleted_example_01.txt
  - merged_example_01.txt
  - replaced_example_01.txt
  - overridden_example_01.txt
  - gathered_example_01.txt
  - rendered_example_01.txt
  - parsed_example_01.txt
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
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.argspec.acls.acls import (
    AclsArgs,
)
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.config.acls.acls import (
    Acls,
)


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(
        argument_spec=AclsArgs.argument_spec,
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

    result = Acls(module).execute_module()
    module.exit_json(**result)


if __name__ == "__main__":
    main()
