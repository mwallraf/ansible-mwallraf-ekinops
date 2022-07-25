#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2022 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
The module file for oneos_hostname
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: oneos_hostname
short_description: hostname resource module for Ekinops OneOS devices
description:
  - This module provides declarative management of hostname on Ekinops
    OneOS devices.
version_added: 1.0.0
author:
  - Maarten Wallraf (mwallraf@2nms.com)
notes:
  - Tested against Ekinops OneOS v5 + v6
  - This module works with connection C(network_cli).

options:
  config:
    description: A dictionary of hostname options
    type: dict
    suboptions:
      hostname:
        description: set hostname for device
        type: str
  startup_config:
    type: dict
    descripton: A dictionary of the startup router configuration
    state:
      choices:
        - merged
  running_config:
    description:
      - This option is used only with state I(parsed).
      - The value of this option should be the output received from the OneOS
        device by executing the command B(show runn | include hostname) on
        OneOS v5 or by executing the command B(show running-config hostname)
        on OneOS v6
      - The state I(parsed) reads the configuration from C(running_config)
        option and transforms it into Ansible structured data as per the
        resource module's argspec and the value is then returned in the
        I(parsed) key within the result.
    type: str
  state:
    choices:
      - merged
      - replaced
      - overridden
      - deleted
      - rendered
      - gathered
      - parsed
    default: merged
    description:
      - The state the configuration should be left in
      - The states I(rendered), I(gathered) and I(parsed) does not perform any
        change on the device.
      - The state I(rendered) will transform the configuration in C(config)
        option to platform specific CLI commands which will be returned in
        the I(rendered) key within the result. For state I(rendered) active
        connection to remote host is not required.
      - The states I(merged), I(replaced) and I(overridden) have identical
        behaviour for this module.
      - The state I(gathered) will fetch the running configuration from device
        and transform it into structured data in the format as per the resource
        module argspec and the value is returned in the I(gathered) key
        within the result.
      - The state I(parsed) reads the configuration from C(running_config)
        option and transforms it into JSON format as per the resource module
        parameters and the value is returned in the I(parsed) key within the
        result. The value of C(running_config) option should be the same
        format as the output of
        command I(show running-config | include hostname) executed on device.
        For state I(parsed) active connection to remote host is not required.
    type: str
"""

EXAMPLES = """

"""

RETURN = """
before:
  description: The configuration prior to the module execution.
  returned: when I(state) is C(merged), C(replaced), C(overridden), C(deleted)
            or C(purged)
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
  returned: when I(state) is C(merged), C(replaced), C(overridden), C(deleted)
            or C(purged)
  type: list
  sample:
    - sample command 1
    - sample command 2
    - sample command 3
rendered:
  description: The provided configuration in the task rendered in
               device-native format (offline).
  returned: when I(state) is C(rendered)
  type: list
  sample:
    - sample command 1
    - sample command 2
    - sample command 3
gathered:
  description: Facts about the network resource gathered from the remote
               device as structured data.
  returned: when I(state) is C(gathered)
  type: list
  sample: >
    This output will always be in the same format as the
    module argspec.
parsed:
  description: The device native config provided in I(running_config) option
               parsed into structured data as per module argspec.
  returned: when I(state) is C(parsed)
  type: list
  sample: >
    This output will always be in the same format as the
    module argspec.
"""

from ansible.module_utils.basic import AnsibleModule  # noqa:E402
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.argspec.hostname.hostname import (  # noqa:E402,E501
    HostnameArgs,
)
from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.config.hostname.hostname import (  # noqa:E402,E501
    Hostname,
)


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(
        argument_spec=HostnameArgs.argument_spec,
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

    result = Hostname(module).execute_module()
    module.exit_json(**result)


if __name__ == "__main__":
    main()
