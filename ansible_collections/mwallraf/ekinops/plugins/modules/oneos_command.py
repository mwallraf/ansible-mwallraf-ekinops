#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+
#   (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function


DOCUMENTATION = """
---
module: oneos_command
author: "Maarten Wallraf"
short_description: Run commands on remote devices running Ekinops OneOs
description:
  - Sends arbitrary commands to an ONEOS node and returns the results
    read from the device. This module includes an argument that will
    cause the module to wait for a specific condition before returning
    or timing out if the condition is not met.
  - This module does not support running commands in configuration mode.

options:
  commands:
    description:
      - List of commands to send to the remote ONEOS device over the
        configured provider. The resulting output from the command
        is returned. If the I(wait_for) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of retries has expired.
    required: true
  wait_for:
    description:
      - List of conditions to evaluate against the output of the
        command. The task will wait for each condition to be true
        before moving forward. If the conditional is not true
        within the configured number of retries, the task fails.
        See examples.
    aliases: ['waitfor']
  match:
    description:
      - The I(match) argument is used in conjunction with the
        I(wait_for) argument to specify the match policy.  Valid
        values are C(all) or C(any).  If the value is set to C(all)
        then all conditionals in the wait_for must be satisfied.  If
        the value is set to C(any) then only one of the values must be
        satisfied.
    default: all
    choices: ['any', 'all']
  retries:
    description:
      - Specifies the number of retries a command should by tried
        before it is considered failed. The command is run on the
        target device every retry and evaluated against the
        I(wait_for) conditions.
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command. If the command does not pass the specified
        conditions, the interval indicates how long to wait before
        trying the command again.
    default: 1
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
---
tasks:
  - name: Run show version on remote devices
    mwallraf.ekinops.oneos_command:
      commands: show version

  - name: Run show version and check to see if output contains sros
    mwallraf.ekinops.oneos_command:
      commands: show system status
      wait_for: result[0] contains OneOs

  - name: Run multiple commands on remote nodes
    mwallraf.ekinops.oneos_command:
      commands:
        - show version
        - show system status

  - name: Run multiple commands and evaluate the output
    mwallraf.ekinops.oneos_command:
      commands:
        - show version
        - show system status
      wait_for:
        - result[0] contains OneOs

  - name: Reboot ONEOS device
    mwallraf.ekinops.oneos_command:
      commands:
        - command: 'reboot'
          prompt: "[yes/no]"
          answer: "yes"
        interval: 3
"""

RETURN = """
stdout:
  description: The set of responses from the commands
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: ['...', '...']

stdout_lines:
  description: The value of stdout split into a list
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: [['...', '...'], ['...'], ['...']]

failed_conditions:
  description: The list of conditionals that have failed
  returned: failed
  type: list
  sample: ['...', '...']
"""

__metaclass__ = type

import time  # noqa:E402

from ansible.module_utils._text import to_text  # noqa:E402
from ansible.module_utils.basic import AnsibleModule  # noqa:E402
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.parsing import (  # noqa:E501,E402
    Conditional,
)

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (  # noqa:E501,E402
    to_lines,
)

from ansible_collections.mwallraf.ekinops.plugins.module_utils.network.oneos.oneos import (  # noqa:E501,E402
    run_commands,
    oneos_argument_spec,
)


def parse_commands(module, warnings):
    commands = module.params["commands"]
    for item in list(commands):
        try:
            command = item["command"]
        except Exception:
            command = item
        if module.check_mode and not command.startswith("show"):
            warnings.append(
                "Only show commands are supported when using check mode, not "
                "executing %s" % command
            )
            commands.remove(item)

    return commands


def main():
    """main entry point for module execution"""
    argument_spec = dict(
        commands=dict(type="list", required=True),
        wait_for=dict(type="list", aliases=["waitfor"]),
        match=dict(default="all", choices=["all", "any"]),
        retries=dict(default=10, type="int"),
        interval=dict(default=1, type="int"),
    )

    argument_spec.update(oneos_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec, supports_check_mode=True
    )

    warnings = list()
    result = {"changed": False, "warnings": warnings}
    commands = parse_commands(module, warnings)
    wait_for = module.params["wait_for"] or list()

    try:
        conditionals = [Conditional(c) for c in wait_for]
    except AttributeError as exc:
        module.fail_json(msg=to_text(exc))

    retries = module.params["retries"]
    interval = module.params["interval"]
    match = module.params["match"]

    while retries > 0:
        responses = run_commands(module, commands)

        for item in list(conditionals):
            if item(responses):
                if match == "any":
                    conditionals = list()
                    break
                conditionals.remove(item)

        if not conditionals:
            break

        time.sleep(interval)
        retries -= 1

    if conditionals:
        failed_conditions = [item.raw for item in conditionals]
        msg = "One or more conditional statements have not been satisfied"
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    result.update(
        {"stdout": responses, "stdout_lines": list(to_lines(responses))}
    )

    module.exit_json(**result)


if __name__ == "__main__":
    main()
