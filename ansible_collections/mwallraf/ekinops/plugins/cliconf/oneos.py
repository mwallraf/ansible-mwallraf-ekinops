# (c) 2019 Nokia
#
# Licensed under the BSD 3 Clause license
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import absolute_import, division, print_function
from ansible.utils.display import Display
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import (  # noqa: E501
    NetworkConfig,
)
from ansible.plugins.cliconf import CliconfBase, enable_mode
from ansible.module_utils._text import to_text, to_bytes
from ansible.module_utils.common._collections_compat import Mapping
from ansible.errors import AnsibleConnectionFailure
import json
import re

__metaclass__ = type

DOCUMENTATION = """
---
author: Maarten Wallraf
name: mwallraf.ekinops.oneos
short_description: Cliconf plugin to configure and run CLI commands on
                   Ekinops OneOS 5 + OneOS 6 devices
description:
  - This plugin provides low level abstraction APIs for sending CLI
    commands and
    receiving responses from Ekinops OneOS network devices.
"""


try:

    from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (  # noqa: E501
        to_list,
    )

except ImportError:
    # if netcommon is not installed, fallback for Ansible 2.8 and 2.9
    from ansible.module_utils.network.common.utils import (  # type: ignore
        to_list,
    )


display = Display()


__supported_oneos_versions__ = [5, 6]


class Cliconf(CliconfBase):
    ONEOS5_OPERATIONS = {
        "supports_diff_replace": True,
        "supports_commit": False,
        "supports_rollback": False,
        "supports_defaults": True,
        "supports_commit_comment": False,
        "supports_onbox_diff": False,
        "supports_generate_diff": True,
        "supports_multiline_delimiter": False,
        "supports_diff_match": False,
        "supports_diff_ignore_lines": False,
        "supports_config_replace": False,
        "supports_admin": True,
        "supports_commit_label": False,
    }

    ONEOS6_OPERATIONS = {
        "supports_diff_replace": True,
        "supports_commit": False,
        "supports_rollback": False,
        "supports_defaults": True,
        "supports_commit_comment": False,
        "supports_onbox_diff": False,
        "supports_generate_diff": True,
        "supports_multiline_delimiter": False,
        "supports_diff_match": False,
        "supports_diff_ignore_lines": False,
        "supports_config_replace": False,
        "supports_admin": True,
        "supports_commit_label": False,
    }

    def __init__(self, *args, **kwargs):
        super(Cliconf, self).__init__(*args, **kwargs)

        self._device_info = {}
        self._oneos_version = None  # could be either 5 or 6

    @property
    def oneos_version(self):
        """Returns the ekinops OneOS version.

        returns 5 or 6

        This runs 'show version' and looks for "-V5" or "-6"

        Examples:
            #show version  (oneos5)
            Software version    : ONEOS16-MONO_FT-V5.2R2E7_HA8
            Software created on : 04/08/20 18:14:48

            #show version (oneos6)
            Software version    : OneOS-pCPE-ARM_pi1-6.3.1m1
            Software created on : 2019-10-04 10:21:52

        """
        if self._oneos_version:
            return int(self._oneos_version)

        version = None

        kwargs = {
            "command": to_bytes("show version"),
            "sendonly": False,
            "newline": True,
            "prompt_retry_check": False,
            "check_all": False,
            # "strip_prompt": True,
        }
        # output = self.get_command_output("show version")
        # output = self.send_command("show version")
        output = self._connection.send(**kwargs)

        if "-V5" in output:
            version = int(5)
        elif "-6" in output:
            version = int(6)

        if version and version in __supported_oneos_versions__:
            self._oneos_version = version
            return int(self._oneos_version)

        raise ValueError(
            f"ekinops os version is not supported or not found ({version})"
        )

    def send_command(self, *args, **kwargs):
        # display.vvvv("oneos version {}".format(self.oneos_version))
        # oneos_version = self.oneos_version
        res = super(Cliconf, self).send_command(*args, **kwargs)
        return res

    def get_oneos_version(self):
        return self.oneos_version

    def get_diff(
        self,
        candidate=None,
        running=None,
        diff_match="line",
        diff_ignore_lines=None,
        path=None,
        diff_replace="line",
    ):
        diff = {}

        device_operations = self.get_device_operations()
        option_values = self.get_option_values()

        if (
            candidate is None
            and device_operations["supports_generate_diff"]
            and diff_match != "none"
        ):
            raise ValueError(
                "candidate configuration is required to generate diff"
            )

        if diff_match not in option_values["diff_match"]:
            raise ValueError(
                "'match' value %s in invalid, valid values are %s"
                % (diff_match, ", ".join(option_values["diff_match"]))
            )

        if diff_replace not in option_values["diff_replace"]:
            raise ValueError(
                "'replace' value %s in invalid, valid values are %s"
                % (diff_replace, ", ".join(option_values["diff_replace"]))
            )

        # prepare candidate configuration
        candidate_obj = NetworkConfig(indent=1)
        candidate_obj.load(candidate)

        if running and diff_match != "none":
            # running configuration
            running_obj = NetworkConfig(
                indent=1, contents=running, ignore_lines=diff_ignore_lines
            )
            configdiffobjs = candidate_obj.difference(
                running_obj, path=path, match=diff_match, replace=diff_replace
            )
        else:
            configdiffobjs = candidate_obj.items

        if configdiffobjs and diff_replace == "config":
            diff["config_diff"] = candidate
        elif configdiffobjs:
            configlines = list()
            for i, o in enumerate(configdiffobjs):
                configlines.append(o.text)
                if i + 1 < len(configdiffobjs):
                    levels = len(o.parents) - len(
                        configdiffobjs[i + 1].parents
                    )
                else:
                    levels = len(o.parents)
                if o.text == "exit":
                    levels -= 1
                if levels > 0:
                    for i in range(levels):
                        configlines.append("exit")
            diff["config_diff"] = "\n".join(configlines)
        else:
            diff["config_diff"] = ""

        # TODO: cfr cisco ios repo we may need to treat banners seperately
        diff["banner_diff"] = ""

        return diff

    # @enable_mode
    def get_device_info(self):
        """Gets basic device info:

        network_os_vendor  =  'ekinops'
        network_os_vendor_alt  =  'oneaccess'
        network_os  =  oneos
        network_os_version  =  5 | 6
        network_os_model  =  ex. LBB_4G+
        network_os_commercial_model  =  ex. LBB4G+
        network_os_hostname  =  configured hostname
        network_os_serial_number  =  serial number

        """
        device_info = {}

        device_info["network_os_vendor"] = "ekinops"
        device_info["network_os_vendor_alt"] = "oneaccess"
        device_info["network_os"] = "oneos"
        device_info["network_os_version"] = str(self.oneos_version)

        cmd_product_info_area = "show product-info-area"
        cmd_hostname = "hostname"

        data = self.get_command_output(cmd_hostname)
        device_info["network_os_hostname"] = data

        data = self.get_command_output(cmd_product_info_area)

        match = re.search(r"\W*[pP]roduct [Nn]ame\W+(\S+)\W+$", data, re.M)
        if match:
            device_info["network_os_model"] = match.group(1)

        match = re.search(r"\W*[cC]ommercial [Nn]ame\W+(.*\w)\W+$", data, re.M)
        if match:
            device_info["network_os_commercial_model"] = match.group(1)

        match = re.search(r"\W*[sS]erial [Nn]umber\W+(\S+)\W+$", data, re.M)
        if match:
            device_info["network_os_serial_number"] = match.group(1)

        return device_info

    @enable_mode
    def get_config(self, source="running", flags=None, format=None):
        """Retrieves the specified configuration from the device
        This method will retrieve the configuration specified by source and
        return it to the caller as a string.  Subsequent calls to this method
        will retrieve a new configuration from the device
        :param source: The configuration source to return from the device.
            This argument accepts either
            `running` or `startup` as valid values.
        :param flags: For devices that support configuration filtering, this
            keyword argument is used to filter the returned configuration.
            The use of this keyword argument is device dependent adn will be
            silently ignored on devices that do not support it.
        :param format: For devices that support fetching different
            configuration format, this keyword argument is used to
            specify the format in which configuration is to be retrieved.
        :return: The device configuration as specified by the source argument.
        """
        acceptable_sources = ["running"]
        if self.oneos_version > 5:
            acceptable_sources += ["startup"]

        if source not in acceptable_sources:
            raise ValueError(
                "fetching configuration from {} is not supported".format(
                    source
                )
            )

        lookup = {
            "running": "running-config",
            "startup": "startup-config",
        }

        # TODO: output format for ONEOS 6 can be xml, json, xpath, ..

        # oneos5 = show run all
        # oneos6 = show run | detail
        cmd = "show {0} ".format(lookup[source])
        if self.oneos_version > 5:
            cmd += " | ".join(to_list(flags))
        else:
            cmd += " ".join(to_list(flags))

        cmd = cmd.strip()

        return self.send_command(cmd)

    @enable_mode
    def edit_config(
        self, candidate=None, commit=True, replace=None, comment=None
    ):
        """edits the config that is defined in candidate"""
        resp = {}
        results = []
        requests = []

        operations = self.get_device_operations()
        self.check_edit_config_capability(
            operations, candidate, commit, replace, comment
        )

        if commit:
            for cmd in ["end", "configure terminal"]:
                self.send_command(cmd)

            for line in to_list(candidate):
                if not isinstance(line, Mapping):
                    line = {"command": line}

                cmd = line["command"]
                if cmd != "end" and cmd[0] != "!":
                    results.append(self.send_command(**line))
                    requests.append(cmd)

            self.send_command("end")
        else:
            raise ValueError("check mode is not supported, use commit=True")

        resp["request"] = requests
        resp["response"] = results
        return resp

    # @enable_mode
    def run_commands(self, commands=None, check_rc=True):

        if commands is None:
            raise ValueError("'commands' value is required")
        responses = list()
        for cmd in to_list(commands):
            if not isinstance(cmd, Mapping):
                cmd = {"command": cmd}

            output = cmd.pop("output", None)
            if output:
                raise ValueError(
                    "'output' value {} is not supported for \
                        run_commands".format(
                        output
                    )
                )

            try:
                out = self.send_command(**cmd)
            except AnsibleConnectionFailure as e:
                if check_rc:
                    raise
                out = getattr(e, "err", e)

            if out is not None:
                try:
                    out = to_text(out, errors="surrogate_or_strict").strip()
                except UnicodeError:
                    raise ConnectionError(
                        message="Failed to decode output from %s: %s"
                        % (cmd, to_text(out))
                    )

                try:
                    out = json.loads(out)
                except ValueError:
                    pass

                responses.append(out)
        return responses

    def get_command_output(self, command):
        """Wrapper around get() function"""
        reply = self.get(command)
        data = to_text(reply, errors="surrogate_or_strict").strip()
        return data

    # @enable_mode
    def get(
        self,
        command=None,
        prompt=None,
        answer=None,
        sendonly=False,
        newline=True,
        output=None,
        check_all=False,
    ):
        """Execute specified command on remote device
        This method will retrieve the specified data and
        return it to the caller as a string.
        :param command: command in string format to be executed on
                        remote device
        :param prompt: the expected prompt generated by executing command,
                        this can be a string or a list of strings
        :param answer: the string to respond to the prompt with
        :param sendonly: bool to disable waiting for response, default is false
        :param newline: bool to indicate if newline should be added at
                        end of answer or not
        :param output: For devices that support fetching command output in
                        different format, this keyword argument is used to
                        specify the output in which response is to be
                        retrieved.
        :param check_all: Bool value to indicate if all the values in prompt
                        sequence should be matched or any one of given prompt.
        :return: The output from the device after executing the command
        """
        if output:
            raise ValueError(
                "'output' value {} is not supported for get".format(output)
            )
        return self.send_command(
            command=command,
            prompt=prompt,
            answer=answer,
            sendonly=sendonly,
            newline=newline,
            check_all=check_all,
        )

    def get_defaults_flag(self):
        """
        The method identifies the filter that should be used to fetch
        running-configuration with defaults.
        :return: valid default filter
        """
        if self.oneos_version > 5:
            return "| default"
        else:
            return "all"

    def get_device_operations(self):
        if self.oneos_version == 5:
            return self.ONEOS5_OPERATIONS
        if self.oneos_version == 6:
            return self.ONEOS6_OPERATIONS

    def get_rpc(self):
        """returns oneos specific rpc
        defaults are:
            "get_config",
            "edit_config",
            "get_capabilities",
            "get",
            "enable_response_logging",
            "disable_response_logging",
        """
        return [
            # "get_diff",
            "run_commands",
        ]

    def get_option_values(self):
        return {
            "format": ["text"],
            "diff_match": ["line", "strict", "exact", "none"],
            "diff_replace": ["line", "block", "config"],
            "output": [],
        }

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        result["device_operations"] = self.get_device_operations()
        result["rpc"] = result["rpc"] + self.get_rpc()
        result.update(self.get_option_values())
        return json.dumps(result)
