# -*- coding: utf-8 -*-
#
# Copyright: (c) 2022, 2NMS bv
# GNU General Public License v3.0
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (  # noqa:E501
    to_list,
)
from ansible.module_utils.connection import Connection, ConnectionError

_DEVICE_CONFIGS = {}

oneos_provider_spec = {
    "host": dict(),
    "port": dict(type="int"),
    "username": dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"])),
    "password": dict(
        fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True
    ),
    "ssh_keyfile": dict(
        fallback=(env_fallback, ["ANSIBLE_NET_SSH_KEYFILE"]), type="path"
    ),
    "timeout": dict(type="int"),
    "transport": dict(type="str", default="cli", choices=["cli"]),
}

oneos_argument_spec = {
    "provider": dict(
        type="dict",
        options=oneos_provider_spec,
        removed_at_date="2022-06-01",
        removed_from_collection="mwallraf.ekinops",
    )
}


def get_connection(module):
    if hasattr(module, "_one_os_connection"):
        return module._one_os_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get("network_api")
    if network_api == "cliconf":
        module._one_os_connection = Connection(module._socket_path)
    else:
        module.fail_json(
            msg="Invalid connection type {0!s}".format(network_api)
        )

    return module._one_os_connection


def get_capabilities(module):
    if hasattr(module, "_oneos_capabilities"):
        return module._oneos_capabilities
    try:
        capabilities = Connection(module._socket_path).get_capabilities()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors="surrogate_then_replace"))
    module._oneos_capabilities = json.loads(capabilities)

    return module._oneos_capabilities


def get_defaults_flag(module):
    connection = get_connection(module)
    try:
        out = connection.get_defaults_flag()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors="surrogate_then_replace"))
    return to_text(out, errors="surrogate_then_replace").strip()


def get_oneos_version(module):
    if hasattr(module, "oneos_version"):
        return module.oneos_version
    try:
        oneos_version = Connection(module._socket_path).get_oneos_version()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors="surrogate_then_replace"))
    module.oneos_version = oneos_version

    return module.oneos_version


def run_commands(module, commands, check_rc=True):
    connection = get_connection(module)
    try:
        return connection.run_commands(commands=commands, check_rc=check_rc)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def get_config(module, flags=None):
    flags = to_list(flags)

    # TODO: add section filtering for oneos5 + oneos6
    section_filter = False
    # if flags and "section" in flags[-1]:
    #     section_filter = True

    flag_str = " ".join(flags)

    try:
        return _DEVICE_CONFIGS[flag_str]
    except KeyError:
        connection = get_connection(module)
        try:
            out = connection.get_config(flags=flags)
        except ConnectionError as exc:
            if section_filter:
                # Some ios devices don't understand `| section foo`
                out = get_config(module, flags=flags[:-1])
            else:
                module.fail_json(
                    msg=to_text(exc, errors="surrogate_then_replace")
                )
        cfg = to_text(out, errors="surrogate_then_replace").strip()
        _DEVICE_CONFIGS[flag_str] = cfg
        return cfg


def commands_add_exit(
    commands: list, start_command: str = None, final_exit: bool = True
) -> list:
    """Takes a list of commands and adds 'exit' statements
    based on the indentation of the text

    :start_command: if provided then reset the counter each time we find
                    a command that starts with the provided string
    :commands: list of commands
    :final_exit: adds a final exit statement at the end

    Example:

        Input:
            interface dot11radio 0/0.100
                dot11 qos wmm
                acl-mode allow
                bridge-group 30
                ssid SSID2.4
                    wps enable
                    authentication wpa2-psk
                    encryption aes-ccm
                    passphrase myppass
            shutdown

        Output:
            interface dot11radio 0/0.100
                dot11 qos wmm
                acl-mode allow
                bridge-group 30
                ssid SSID2.4
                    wps enable
                    authentication wpa2-psk
                    encryption aes-ccm
                    passphrase myppass
                exit
                shutdown
            exit

    """

    def _add_final_exit(_new_commands, final_exit, exits):
        if final_exit:
            for x in reversed(range(exits)):
                _new_commands.append(f"{' ' * x}exit")

    new_commands = []
    exits = 0
    cur_len = 0
    for cmd in commands:
        # if start_command and cmd.startswith(start_command):
        #     exits = 0
        #     cur_len = 0
        #     continue
        length = len(cmd) - len(cmd.lstrip())
        if length < cur_len:
            new_commands.append(f"{' ' * length}exit")
            cur_len = length
            exits -= 1
        if length > cur_len:
            cur_len = length
            exits += 1
        new_commands.append(cmd)
        if start_command and cmd.startswith(start_command):
            # _add_final_exit(new_commands, final_exit, exits)
            exits = 0
            cur_len = 0

    if final_exit:
        for x in reversed(range(exits)):
            new_commands.append(f"{' ' * x}exit")

    return new_commands
